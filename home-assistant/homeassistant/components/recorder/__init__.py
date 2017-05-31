"""
Support for recording details.

Component that records all events and state changes. Allows other components
to query this database.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/recorder/
"""
import asyncio
import concurrent.futures
import logging
import queue
import threading
import time
from datetime import timedelta, datetime
from typing import Optional, Dict

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant, callback, split_entity_id, CoreState)
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_ENTITIES, CONF_EXCLUDE, CONF_DOMAINS,
    CONF_INCLUDE, EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START,
    EVENT_STATE_CHANGED, EVENT_TIME_CHANGED, MATCH_ALL)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
import homeassistant.util.dt as dt_util

from . import purge, migration
from .const import DATA_INSTANCE
from .util import session_scope

REQUIREMENTS = ['sqlalchemy==1.1.9']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'recorder'

DEFAULT_URL = 'sqlite:///{hass_config_path}'
DEFAULT_DB_FILE = 'home-assistant_v2.db'

CONF_DB_URL = 'db_url'
CONF_PURGE_DAYS = 'purge_days'
CONF_EVENT_TYPES = 'event_types'

CONNECT_RETRY_WAIT = 3

FILTER_SCHEMA = vol.Schema({
    vol.Optional(CONF_EXCLUDE, default={}): vol.Schema({
        vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
        vol.Optional(CONF_DOMAINS, default=[]):
            vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EVENT_TYPES, default=[]):
            vol.All(cv.ensure_list, [cv.string])
    }),
    vol.Optional(CONF_INCLUDE, default={}): vol.Schema({
        vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
        vol.Optional(CONF_DOMAINS, default=[]):
            vol.All(cv.ensure_list, [cv.string])
    })
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: FILTER_SCHEMA.extend({
        vol.Optional(CONF_PURGE_DAYS):
            vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(CONF_DB_URL): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


def wait_connection_ready(hass):
    """
    Wait till the connection is ready.

    Returns a coroutine object.
    """
    return hass.data[DATA_INSTANCE].async_db_ready


def run_information(hass, point_in_time: Optional[datetime]=None):
    """Return information about current run.

    There is also the run that covers point_in_time.
    """
    from . import models
    ins = hass.data[DATA_INSTANCE]

    recorder_runs = models.RecorderRuns
    if point_in_time is None or point_in_time > ins.recording_start:
        return ins.run_info

    with session_scope(hass=hass) as session:
        res = session.query(recorder_runs).filter(
            (recorder_runs.start < point_in_time) &
            (recorder_runs.end > point_in_time)).first()
        if res:
            session.expunge(res)
        return res


@asyncio.coroutine
def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the recorder."""
    conf = config.get(DOMAIN, {})
    purge_days = conf.get(CONF_PURGE_DAYS)

    db_url = conf.get(CONF_DB_URL, None)
    if not db_url:
        db_url = DEFAULT_URL.format(
            hass_config_path=hass.config.path(DEFAULT_DB_FILE))

    include = conf.get(CONF_INCLUDE, {})
    exclude = conf.get(CONF_EXCLUDE, {})
    instance = hass.data[DATA_INSTANCE] = Recorder(
        hass, purge_days=purge_days, uri=db_url, include=include,
        exclude=exclude)
    instance.async_initialize()
    instance.start()

    return (yield from instance.async_db_ready)


class Recorder(threading.Thread):
    """A threaded recorder class."""

    def __init__(self, hass: HomeAssistant, purge_days: int, uri: str,
                 include: Dict, exclude: Dict) -> None:
        """Initialize the recorder."""
        threading.Thread.__init__(self, name='Recorder')

        self.hass = hass
        self.purge_days = purge_days
        self.queue = queue.Queue()  # type: Any
        self.recording_start = dt_util.utcnow()
        self.db_url = uri
        self.async_db_ready = asyncio.Future(loop=hass.loop)
        self.engine = None  # type: Any
        self.run_info = None  # type: Any

        self.include_e = include.get(CONF_ENTITIES, [])
        self.include_d = include.get(CONF_DOMAINS, [])
        self.exclude = exclude.get(CONF_ENTITIES, []) + \
            exclude.get(CONF_DOMAINS, [])
        self.exclude_t = exclude.get(CONF_EVENT_TYPES, [])

        self.get_session = None

    @callback
    def async_initialize(self):
        """Initialize the recorder."""
        self.hass.bus.async_listen(MATCH_ALL, self.event_listener)

    def run(self):
        """Start processing events to save."""
        from .models import States, Events
        from homeassistant.components import persistent_notification

        tries = 1
        connected = False

        while not connected and tries <= 10:
            if tries != 1:
                time.sleep(CONNECT_RETRY_WAIT)
            try:
                self._setup_connection()
                migration.migrate_schema(self)
                self._setup_run()
                connected = True
                _LOGGER.debug("Connected to recorder database")
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Error during connection setup: %s (retrying "
                              "in %s seconds)", err, CONNECT_RETRY_WAIT)
                tries += 1

        if not connected:
            @callback
            def connection_failed():
                """Connect failed tasks."""
                self.async_db_ready.set_result(False)
                persistent_notification.async_create(
                    self.hass,
                    "The recorder could not start, please check the log",
                    "Recorder")

            self.hass.add_job(connection_failed)
            return

        purge_task = object()
        shutdown_task = object()
        hass_started = concurrent.futures.Future()

        @callback
        def register():
            """Post connection initialize."""
            self.async_db_ready.set_result(True)

            def shutdown(event):
                """Shut down the Recorder."""
                if not hass_started.done():
                    hass_started.set_result(shutdown_task)
                self.queue.put(None)
                self.join()

            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP,
                                            shutdown)

            if self.hass.state == CoreState.running:
                hass_started.set_result(None)
            else:
                @callback
                def notify_hass_started(event):
                    """Notify that hass has started."""
                    hass_started.set_result(None)

                self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START,
                                                notify_hass_started)

            if self.purge_days is not None:
                @callback
                def do_purge(now):
                    """Event listener for purging data."""
                    self.queue.put(purge_task)

                async_track_time_interval(self.hass, do_purge,
                                          timedelta(days=2))

        self.hass.add_job(register)
        result = hass_started.result()

        # If shutdown happened before HASS finished starting
        if result is shutdown_task:
            return

        while True:
            event = self.queue.get()

            if event is None:
                self._close_run()
                self._close_connection()
                self.queue.task_done()
                return
            elif event is purge_task:
                purge.purge_old_data(self, self.purge_days)
                continue
            elif event.event_type == EVENT_TIME_CHANGED:
                self.queue.task_done()
                continue
            elif event.event_type in self.exclude_t:
                self.queue.task_done()
                continue

            entity_id = event.data.get(ATTR_ENTITY_ID)
            if entity_id is not None:
                domain = split_entity_id(entity_id)[0]

                # Exclude entities OR
                # Exclude domains, but include specific entities
                if (entity_id in self.exclude) or \
                        (domain in self.exclude and
                         entity_id not in self.include_e):
                    self.queue.task_done()
                    continue

                # Included domains only (excluded entities above) OR
                # Include entities only, but only if no excludes
                if (self.include_d and domain not in self.include_d) or \
                        (self.include_e and entity_id not in self.include_e
                         and not self.exclude):
                    self.queue.task_done()
                    continue

            with session_scope(session=self.get_session()) as session:
                dbevent = Events.from_event(event)
                session.add(dbevent)

                if event.event_type == EVENT_STATE_CHANGED:
                    dbstate = States.from_event(event)
                    dbstate.event_id = dbevent.event_id
                    session.add(dbstate)

            self.queue.task_done()

    @callback
    def event_listener(self, event):
        """Listen for new events and put them in the process queue."""
        self.queue.put(event)

    def block_till_done(self):
        """Block till all events processed."""
        self.queue.join()

    def _setup_connection(self):
        """Ensure database is ready to fly."""
        from sqlalchemy import create_engine, event
        from sqlalchemy.engine import Engine
        from sqlalchemy.orm import scoped_session
        from sqlalchemy.orm import sessionmaker

        from . import models

        kwargs = {}

        # pylint: disable=unused-variable
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set sqlite's WAL mode."""
            if self.db_url.startswith("sqlite://"):
                old_isolation = dbapi_connection.isolation_level
                dbapi_connection.isolation_level = None
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()
                dbapi_connection.isolation_level = old_isolation

        if self.db_url == 'sqlite://' or ':memory:' in self.db_url:
            from sqlalchemy.pool import StaticPool

            kwargs['connect_args'] = {'check_same_thread': False}
            kwargs['poolclass'] = StaticPool
            kwargs['pool_reset_on_return'] = None
        else:
            kwargs['echo'] = False

        if self.engine is not None:
            self.engine.dispose()

        self.engine = create_engine(self.db_url, **kwargs)
        models.Base.metadata.create_all(self.engine)
        self.get_session = scoped_session(sessionmaker(bind=self.engine))

    def _close_connection(self):
        """Close the connection."""
        self.engine.dispose()
        self.engine = None
        self.get_session = None

    def _setup_run(self):
        """Log the start of the current run."""
        from .models import RecorderRuns

        with session_scope(session=self.get_session()) as session:
            for run in session.query(RecorderRuns).filter_by(end=None):
                run.closed_incorrect = True
                run.end = self.recording_start
                _LOGGER.warning("Ended unfinished session (id=%s from %s)",
                                run.run_id, run.start)
                session.add(run)

            self.run_info = RecorderRuns(
                start=self.recording_start,
                created=dt_util.utcnow()
            )
            session.add(self.run_info)
            session.flush()
            session.expunge(self.run_info)

    def _close_run(self):
        """Save end time for current run."""
        with session_scope(session=self.get_session()) as session:
            self.run_info.end = dt_util.utcnow()
            session.add(self.run_info)
        self.run_info = None
