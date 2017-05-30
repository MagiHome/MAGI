"""The tests for the device tracker component."""
# pylint: disable=protected-access
import asyncio
import json
import logging
import unittest
from unittest.mock import call, patch
from datetime import datetime, timedelta
import os

from homeassistant.components import zone
from homeassistant.core import callback, State
from homeassistant.setup import setup_component
from homeassistant.helpers import discovery
from homeassistant.loader import get_component
from homeassistant.util.async import run_coroutine_threadsafe
import homeassistant.util.dt as dt_util
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_ENTITY_PICTURE, ATTR_FRIENDLY_NAME, ATTR_HIDDEN,
    STATE_HOME, STATE_NOT_HOME, CONF_PLATFORM, ATTR_ICON)
import homeassistant.components.device_tracker as device_tracker
from homeassistant.exceptions import HomeAssistantError
from homeassistant.remote import JSONEncoder

from tests.common import (
    get_test_home_assistant, fire_time_changed, fire_service_discovered,
    patch_yaml_files, assert_setup_component, mock_restore_cache, mock_coro)

from ...test_util.aiohttp import mock_aiohttp_client

TEST_PLATFORM = {device_tracker.DOMAIN: {CONF_PLATFORM: 'test'}}

_LOGGER = logging.getLogger(__name__)


class TestComponentsDeviceTracker(unittest.TestCase):
    """Test the Device tracker."""

    hass = None  # HomeAssistant
    yaml_devices = None  # type: str

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.yaml_devices = self.hass.config.path(device_tracker.YAML_DEVICES)

    # pylint: disable=invalid-name
    def tearDown(self):
        """Stop everything that was started."""
        if os.path.isfile(self.yaml_devices):
            os.remove(self.yaml_devices)

        self.hass.stop()

    def test_is_on(self):
        """Test is_on method."""
        entity_id = device_tracker.ENTITY_ID_FORMAT.format('test')

        self.hass.states.set(entity_id, STATE_HOME)

        self.assertTrue(device_tracker.is_on(self.hass, entity_id))

        self.hass.states.set(entity_id, STATE_NOT_HOME)

        self.assertFalse(device_tracker.is_on(self.hass, entity_id))

    # pylint: disable=no-self-use
    def test_reading_broken_yaml_config(self):
        """Test when known devices contains invalid data."""
        files = {'empty.yaml': '',
                 'nodict.yaml': '100',
                 'badkey.yaml': '@:\n  name: Device',
                 'noname.yaml': 'my_device:\n',
                 'allok.yaml':  'My Device:\n  name: Device',
                 'oneok.yaml':  ('My Device!:\n  name: Device\n'
                                 'bad_device:\n  nme: Device')}
        args = {'hass': self.hass, 'consider_home': timedelta(seconds=60)}
        with patch_yaml_files(files):
            assert device_tracker.load_config('empty.yaml', **args) == []
            assert device_tracker.load_config('nodict.yaml', **args) == []
            assert device_tracker.load_config('noname.yaml', **args) == []
            assert device_tracker.load_config('badkey.yaml', **args) == []

            res = device_tracker.load_config('allok.yaml', **args)
            assert len(res) == 1
            assert res[0].name == 'Device'
            assert res[0].dev_id == 'my_device'

            res = device_tracker.load_config('oneok.yaml', **args)
            assert len(res) == 1
            assert res[0].name == 'Device'
            assert res[0].dev_id == 'my_device'

    def test_reading_yaml_config(self):
        """Test the rendering of the YAML configuration."""
        dev_id = 'test'
        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id,
            'AB:CD:EF:GH:IJ', 'Test name', picture='http://test.picture',
            hide_if_away=True, icon='mdi:kettle')
        device_tracker.update_config(self.yaml_devices, dev_id, device)
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)
        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            device.consider_home)[0]
        self.assertEqual(device.dev_id, config.dev_id)
        self.assertEqual(device.track, config.track)
        self.assertEqual(device.mac, config.mac)
        self.assertEqual(device.config_picture, config.config_picture)
        self.assertEqual(device.away_hide, config.away_hide)
        self.assertEqual(device.consider_home, config.consider_home)
        self.assertEqual(device.vendor, config.vendor)
        self.assertEqual(device.icon, config.icon)

    # pylint: disable=invalid-name
    @patch('homeassistant.components.device_tracker._LOGGER.warning')
    def test_track_with_duplicate_mac_dev_id(self, mock_warning):
        """Test adding duplicate MACs or device IDs to DeviceTracker."""
        devices = [
            device_tracker.Device(self.hass, True, True, 'my_device', 'AB:01',
                                  'My device', None, None, False),
            device_tracker.Device(self.hass, True, True, 'your_device',
                                  'AB:01', 'Your device', None, None, False)]
        device_tracker.DeviceTracker(self.hass, False, True, devices)
        _LOGGER.debug(mock_warning.call_args_list)
        assert mock_warning.call_count == 1, \
            "The only warning call should be duplicates (check DEBUG)"
        args, _ = mock_warning.call_args
        assert 'Duplicate device MAC' in args[0], \
            'Duplicate MAC warning expected'

        mock_warning.reset_mock()
        devices = [
            device_tracker.Device(self.hass, True, True, 'my_device',
                                  'AB:01', 'My device', None, None, False),
            device_tracker.Device(self.hass, True, True, 'my_device',
                                  None, 'Your device', None, None, False)]
        device_tracker.DeviceTracker(self.hass, False, True, devices)

        _LOGGER.debug(mock_warning.call_args_list)
        assert mock_warning.call_count == 1, \
            "The only warning call should be duplicates (check DEBUG)"
        args, _ = mock_warning.call_args
        assert 'Duplicate device IDs' in args[0], \
            'Duplicate device IDs warning expected'

    def test_setup_without_yaml_file(self):
        """Test with no YAML file."""
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

    # pylint: disable=invalid-name
    def test_adding_unknown_device_to_config(self):
        """Test the adding of unknown devices to configuration file."""
        scanner = get_component('device_tracker.test').SCANNER
        scanner.reset()
        scanner.come_home('DEV1')

        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN, {
                device_tracker.DOMAIN: {CONF_PLATFORM: 'test'}})

        # wait for async calls (macvendor) to finish
        self.hass.block_till_done()

        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            timedelta(seconds=0))
        assert len(config) == 1
        assert config[0].dev_id == 'dev1'
        assert config[0].track

    def test_gravatar(self):
        """Test the Gravatar generation."""
        dev_id = 'test'
        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id,
            'AB:CD:EF:GH:IJ', 'Test name', gravatar='test@example.com')
        gravatar_url = ("https://www.gravatar.com/avatar/"
                        "55502f40dc8b7c769880b10874abc9d0.jpg?s=80&d=wavatar")
        self.assertEqual(device.config_picture, gravatar_url)

    def test_gravatar_and_picture(self):
        """Test that Gravatar overrides picture."""
        dev_id = 'test'
        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id,
            'AB:CD:EF:GH:IJ', 'Test name', picture='http://test.picture',
            gravatar='test@example.com')
        gravatar_url = ("https://www.gravatar.com/avatar/"
                        "55502f40dc8b7c769880b10874abc9d0.jpg?s=80&d=wavatar")
        self.assertEqual(device.config_picture, gravatar_url)

    def test_mac_vendor_lookup(self):
        """Test if vendor string is lookup on macvendors API."""
        mac = 'B8:27:EB:00:00:00'
        vendor_string = 'Raspberry Pi Foundation'

        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, 'test', mac, 'Test name')

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               text=vendor_string)

            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()
            assert aioclient_mock.call_count == 1

        self.assertEqual(device.vendor, vendor_string)

    def test_mac_vendor_mac_formats(self):
        """Verify all variations of MAC addresses are handled correctly."""
        vendor_string = 'Raspberry Pi Foundation'

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               text=vendor_string)
            aioclient_mock.get('http://api.macvendors.com/00:27:eb',
                               text=vendor_string)

            mac = 'B8:27:EB:00:00:00'
            device = device_tracker.Device(
                self.hass, timedelta(seconds=180),
                True, 'test', mac, 'Test name')
            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()
            self.assertEqual(device.vendor, vendor_string)

            mac = '0:27:EB:00:00:00'
            device = device_tracker.Device(
                self.hass, timedelta(seconds=180),
                True, 'test', mac, 'Test name')
            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()
            self.assertEqual(device.vendor, vendor_string)

            mac = 'PREFIXED_B8:27:EB:00:00:00'
            device = device_tracker.Device(
                self.hass, timedelta(seconds=180),
                True, 'test', mac, 'Test name')
            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()
            self.assertEqual(device.vendor, vendor_string)

    def test_mac_vendor_lookup_unknown(self):
        """Prevent another mac vendor lookup if was not found first time."""
        mac = 'B8:27:EB:00:00:00'

        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, 'test', mac, 'Test name')

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               status=404)

            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()

            self.assertEqual(device.vendor, 'unknown')

    def test_mac_vendor_lookup_error(self):
        """Prevent another lookup if failure during API call."""
        mac = 'B8:27:EB:00:00:00'

        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, 'test', mac, 'Test name')

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               status=500)

            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()

            self.assertEqual(device.vendor, 'unknown')

    def test_mac_vendor_lookup_exception(self):
        """Prevent another lookup if exception during API call."""
        mac = 'B8:27:EB:00:00:00'

        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, 'test', mac, 'Test name')

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               exc=asyncio.TimeoutError())

            run_coroutine_threadsafe(device.set_vendor_for_mac(),
                                     self.hass.loop).result()

            self.assertEqual(device.vendor, 'unknown')

    def test_mac_vendor_lookup_on_see(self):
        """Test if macvendor is looked up when device is seen."""
        mac = 'B8:27:EB:00:00:00'
        vendor_string = 'Raspberry Pi Foundation'

        tracker = device_tracker.DeviceTracker(
            self.hass, timedelta(seconds=60), 0, [])

        with mock_aiohttp_client() as aioclient_mock:
            aioclient_mock.get('http://api.macvendors.com/b8:27:eb',
                               text=vendor_string)

            run_coroutine_threadsafe(
                tracker.async_see(mac=mac), self.hass.loop).result()
            assert aioclient_mock.call_count == 1, \
                'No http request for macvendor made!'
        self.assertEqual(tracker.devices['b827eb000000'].vendor, vendor_string)

    def test_discovery(self):
        """Test discovery."""
        scanner = get_component('device_tracker.test').SCANNER

        with patch.dict(device_tracker.DISCOVERY_PLATFORMS, {'test': 'test'}):
            with patch.object(scanner, 'scan_devices',
                              autospec=True) as mock_scan:
                with assert_setup_component(1, device_tracker.DOMAIN):
                    assert setup_component(
                        self.hass, device_tracker.DOMAIN, TEST_PLATFORM)
                fire_service_discovered(self.hass, 'test', {})
                self.assertTrue(mock_scan.called)

    @patch(
        'homeassistant.components.device_tracker.DeviceTracker.see')
    @patch(
        'homeassistant.components.device_tracker.demo.setup_scanner',
        autospec=True)
    def test_discover_platform(self, mock_demo_setup_scanner, mock_see):
        """Test discovery of device_tracker demo platform."""
        assert device_tracker.DOMAIN not in self.hass.config.components
        discovery.load_platform(
            self.hass, device_tracker.DOMAIN, 'demo', {'test_key': 'test_val'},
            {})
        self.hass.block_till_done()
        assert device_tracker.DOMAIN in self.hass.config.components
        assert mock_demo_setup_scanner.called
        assert mock_demo_setup_scanner.call_args[0] == (
            self.hass, {}, mock_see, {'test_key': 'test_val'})

    def test_update_stale(self):
        """Test stalled update."""
        scanner = get_component('device_tracker.test').SCANNER
        scanner.reset()
        scanner.come_home('DEV1')

        register_time = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
        scan_time = datetime(2015, 9, 15, 23, 1, tzinfo=dt_util.UTC)

        with patch('homeassistant.components.device_tracker.dt_util.utcnow',
                   return_value=register_time):
            with assert_setup_component(1, device_tracker.DOMAIN):
                assert setup_component(self.hass, device_tracker.DOMAIN, {
                    device_tracker.DOMAIN: {
                        CONF_PLATFORM: 'test',
                        device_tracker.CONF_CONSIDER_HOME: 59,
                    }})

        self.assertEqual(STATE_HOME,
                         self.hass.states.get('device_tracker.dev1').state)

        scanner.leave_home('DEV1')

        with patch('homeassistant.components.device_tracker.dt_util.utcnow',
                   return_value=scan_time):
            fire_time_changed(self.hass, scan_time)
            self.hass.block_till_done()

        self.assertEqual(STATE_NOT_HOME,
                         self.hass.states.get('device_tracker.dev1').state)

    def test_entity_attributes(self):
        """Test the entity attributes."""
        dev_id = 'test_entity'
        entity_id = device_tracker.ENTITY_ID_FORMAT.format(dev_id)
        friendly_name = 'Paulus'
        picture = 'http://placehold.it/200x200'
        icon = 'mdi:kettle'

        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id, None,
            friendly_name, picture, hide_if_away=True, icon=icon)
        device_tracker.update_config(self.yaml_devices, dev_id, device)

        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

        attrs = self.hass.states.get(entity_id).attributes

        self.assertEqual(friendly_name, attrs.get(ATTR_FRIENDLY_NAME))
        self.assertEqual(icon, attrs.get(ATTR_ICON))
        self.assertEqual(picture, attrs.get(ATTR_ENTITY_PICTURE))

    def test_device_hidden(self):
        """Test hidden devices."""
        dev_id = 'test_entity'
        entity_id = device_tracker.ENTITY_ID_FORMAT.format(dev_id)
        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id, None,
            hide_if_away=True)
        device_tracker.update_config(self.yaml_devices, dev_id, device)

        scanner = get_component('device_tracker.test').SCANNER
        scanner.reset()

        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

        self.assertTrue(self.hass.states.get(entity_id)
                        .attributes.get(ATTR_HIDDEN))

    def test_group_all_devices(self):
        """Test grouping of devices."""
        dev_id = 'test_entity'
        entity_id = device_tracker.ENTITY_ID_FORMAT.format(dev_id)
        device = device_tracker.Device(
            self.hass, timedelta(seconds=180), True, dev_id, None,
            hide_if_away=True)
        device_tracker.update_config(self.yaml_devices, dev_id, device)

        scanner = get_component('device_tracker.test').SCANNER
        scanner.reset()

        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

        state = self.hass.states.get(device_tracker.ENTITY_ID_ALL_DEVICES)
        self.assertIsNotNone(state)
        self.assertEqual(STATE_NOT_HOME, state.state)
        self.assertSequenceEqual((entity_id,),
                                 state.attributes.get(ATTR_ENTITY_ID))

    @patch('homeassistant.components.device_tracker.DeviceTracker.async_see')
    def test_see_service(self, mock_see):
        """Test the see service with a unicode dev_id and NO MAC."""
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)
        params = {
            'dev_id': 'some_device',
            'host_name': 'example.com',
            'location_name': 'Work',
            'gps': [.3, .8],
            'attributes': {
                'test': 'test'
            }
        }
        device_tracker.see(self.hass, **params)
        self.hass.block_till_done()
        assert mock_see.call_count == 1
        self.assertEqual(mock_see.call_count, 1)
        self.assertEqual(mock_see.call_args, call(**params))

        mock_see.reset_mock()
        params['dev_id'] += chr(233)  # e' acute accent from icloud

        device_tracker.see(self.hass, **params)
        self.hass.block_till_done()
        assert mock_see.call_count == 1
        self.assertEqual(mock_see.call_count, 1)
        self.assertEqual(mock_see.call_args, call(**params))

    def test_new_device_event_fired(self):
        """Test that the device tracker will fire an event."""
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)
        test_events = []

        @callback
        def listener(event):
            """Helper method that will verify our event got called."""
            test_events.append(event)

        self.hass.bus.listen("device_tracker_new_device", listener)

        device_tracker.see(self.hass, 'mac_1', host_name='hello')
        device_tracker.see(self.hass, 'mac_1', host_name='hello')

        self.hass.block_till_done()

        assert len(test_events) == 1

        # Assert we can serialize the event
        json.dumps(test_events[0].as_dict(), cls=JSONEncoder)

        assert test_events[0].data == {
            'entity_id': 'device_tracker.hello',
            'host_name': 'hello',
        }

    # pylint: disable=invalid-name
    def test_not_write_duplicate_yaml_keys(self):
        """Test that the device tracker will not generate invalid YAML."""
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

        device_tracker.see(self.hass, 'mac_1', host_name='hello')
        device_tracker.see(self.hass, 'mac_2', host_name='hello')

        self.hass.block_till_done()

        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            timedelta(seconds=0))
        assert len(config) == 2

    # pylint: disable=invalid-name
    def test_not_allow_invalid_dev_id(self):
        """Test that the device tracker will not allow invalid dev ids."""
        with assert_setup_component(1, device_tracker.DOMAIN):
            assert setup_component(self.hass, device_tracker.DOMAIN,
                                   TEST_PLATFORM)

        device_tracker.see(self.hass, dev_id='hello-world')

        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            timedelta(seconds=0))
        assert len(config) == 0

    @patch('homeassistant.components.device_tracker.Device'
           '.set_vendor_for_mac', return_value=mock_coro())
    def test_see_state(self, mock_set_vendor):
        """Test device tracker see records state correctly."""
        self.assertTrue(setup_component(self.hass, device_tracker.DOMAIN,
                                        TEST_PLATFORM))

        params = {
            'mac': 'AA:BB:CC:DD:EE:FF',
            'dev_id': 'some_device',
            'host_name': 'example.com',
            'location_name': 'Work',
            'gps': [.3, .8],
            'gps_accuracy': 1,
            'battery': 100,
            'attributes': {
                'test': 'test',
                'number': 1,
            },
        }

        device_tracker.see(self.hass, **params)
        self.hass.block_till_done()

        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            timedelta(seconds=0))
        assert len(config) == 1

        state = self.hass.states.get('device_tracker.examplecom')
        attrs = state.attributes
        self.assertEqual(state.state, 'Work')
        self.assertEqual(state.object_id, 'examplecom')
        self.assertEqual(state.name, 'example.com')
        self.assertEqual(attrs['friendly_name'], 'example.com')
        self.assertEqual(attrs['battery'], 100)
        self.assertEqual(attrs['latitude'], 0.3)
        self.assertEqual(attrs['longitude'], 0.8)
        self.assertEqual(attrs['test'], 'test')
        self.assertEqual(attrs['gps_accuracy'], 1)
        self.assertEqual(attrs['source_type'], 'gps')
        self.assertEqual(attrs['number'], 1)

    def test_see_passive_zone_state(self):
        """Test that the device tracker sets gps for passive trackers."""
        register_time = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
        scan_time = datetime(2015, 9, 15, 23, 1, tzinfo=dt_util.UTC)

        with assert_setup_component(1, zone.DOMAIN):
            zone_info = {
                'name': 'Home',
                'latitude': 1,
                'longitude': 2,
                'radius': 250,
                'passive': False
            }

            setup_component(self.hass, zone.DOMAIN, {
                'zone': zone_info
            })

        scanner = get_component('device_tracker.test').SCANNER
        scanner.reset()
        scanner.come_home('dev1')

        with patch('homeassistant.components.device_tracker.dt_util.utcnow',
                   return_value=register_time):
            with assert_setup_component(1, device_tracker.DOMAIN):
                assert setup_component(self.hass, device_tracker.DOMAIN, {
                    device_tracker.DOMAIN: {
                        CONF_PLATFORM: 'test',
                        device_tracker.CONF_CONSIDER_HOME: 59,
                    }})

        state = self.hass.states.get('device_tracker.dev1')
        attrs = state.attributes
        self.assertEqual(STATE_HOME, state.state)
        self.assertEqual(state.object_id, 'dev1')
        self.assertEqual(state.name, 'dev1')
        self.assertEqual(attrs.get('friendly_name'), 'dev1')
        self.assertEqual(attrs.get('latitude'), 1)
        self.assertEqual(attrs.get('longitude'), 2)
        self.assertEqual(attrs.get('gps_accuracy'), 0)
        self.assertEqual(attrs.get('source_type'),
                         device_tracker.SOURCE_TYPE_ROUTER)

        scanner.leave_home('dev1')

        with patch('homeassistant.components.device_tracker.dt_util.utcnow',
                   return_value=scan_time):
            fire_time_changed(self.hass, scan_time)
            self.hass.block_till_done()

        state = self.hass.states.get('device_tracker.dev1')
        attrs = state.attributes
        self.assertEqual(STATE_NOT_HOME, state.state)
        self.assertEqual(state.object_id, 'dev1')
        self.assertEqual(state.name, 'dev1')
        self.assertEqual(attrs.get('friendly_name'), 'dev1')
        self.assertEqual(attrs.get('latitude'), None)
        self.assertEqual(attrs.get('longitude'), None)
        self.assertEqual(attrs.get('gps_accuracy'), None)
        self.assertEqual(attrs.get('source_type'),
                         device_tracker.SOURCE_TYPE_ROUTER)

    @patch('homeassistant.components.device_tracker._LOGGER.warning')
    def test_see_failures(self, mock_warning):
        """Test that the device tracker see failures."""
        tracker = device_tracker.DeviceTracker(
            self.hass, timedelta(seconds=60), 0, [])

        # MAC is not a string (but added)
        tracker.see(mac=567, host_name="Number MAC")

        # No device id or MAC(not added)
        with self.assertRaises(HomeAssistantError):
            run_coroutine_threadsafe(
                tracker.async_see(), self.hass.loop).result()
        assert mock_warning.call_count == 0

        # Ignore gps on invalid GPS (both added & warnings)
        tracker.see(mac='mac_1_bad_gps', gps=1)
        tracker.see(mac='mac_2_bad_gps', gps=[1])
        tracker.see(mac='mac_3_bad_gps', gps='gps')
        self.hass.block_till_done()
        config = device_tracker.load_config(self.yaml_devices, self.hass,
                                            timedelta(seconds=0))
        assert mock_warning.call_count == 3

        assert len(config) == 4

    @patch('homeassistant.components.device_tracker.async_log_exception')
    def test_config_failure(self, mock_ex):
        """Test that the device tracker see failures."""
        with assert_setup_component(0, device_tracker.DOMAIN):
            setup_component(self.hass, device_tracker.DOMAIN,
                            {device_tracker.DOMAIN: {
                                device_tracker.CONF_CONSIDER_HOME: -1}})


@asyncio.coroutine
def test_async_added_to_hass(hass):
    """Test resoring state."""
    attr = {
        device_tracker.ATTR_LONGITUDE: 18,
        device_tracker.ATTR_LATITUDE: -33,
        device_tracker.ATTR_LATITUDE: -33,
        device_tracker.ATTR_SOURCE_TYPE: 'gps',
        device_tracker.ATTR_GPS_ACCURACY: 2,
        device_tracker.ATTR_BATTERY: 100
    }
    mock_restore_cache(hass, [State('device_tracker.jk', 'home', attr)])

    path = hass.config.path(device_tracker.YAML_DEVICES)

    files = {
        path: 'jk:\n  name: JK Phone\n  track: True',
    }
    with patch_yaml_files(files):
        yield from device_tracker.async_setup(hass, {})

    state = hass.states.get('device_tracker.jk')
    assert state
    assert state.state == 'home'

    for key, val in attr.items():
        atr = state.attributes.get(key)
        assert atr == val, "{}={} expected: {}".format(key, atr, val)
