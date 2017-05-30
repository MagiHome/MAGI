"""
Support for Tado Smart Thermostat.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.tado/
"""
import logging
from datetime import timedelta
from collections import namedtuple

import asyncio
import aiohttp
import async_timeout
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.util import Throttle
from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.helpers.aiohttp_client import async_create_clientsession

_LOGGER = logging.getLogger(__name__)

CONF_HOME_ID = 'home_id'

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_HOME_ID): cv.string
})


def get_scanner(hass, config):
    """Return a Tado scanner."""
    scanner = TadoDeviceScanner(hass, config[DOMAIN])
    return scanner if scanner.success_init else None


Device = namedtuple("Device", ["mac", "name"])


class TadoDeviceScanner(DeviceScanner):
    """This class gets geofenced devices from Tado."""

    def __init__(self, hass, config):
        """Initialize the scanner."""
        self.last_results = []

        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]

        # The Tado device tracker can work with or without a home_id
        self.home_id = config[CONF_HOME_ID] if CONF_HOME_ID in config else None

        # If there's a home_id, we need a different API URL
        if self.home_id is None:
            self.tadoapiurl = 'https://my.tado.com/api/v2/me'
        else:
            self.tadoapiurl = 'https://my.tado.com/api/v2' \
                              '/homes/{home_id}/mobileDevices'

        # The API URL always needs a username and password
        self.tadoapiurl += '?username={username}&password={password}'

        self.websession = async_create_clientsession(
            hass, cookie_jar=aiohttp.CookieJar(unsafe=True, loop=hass.loop))

        self.success_init = self._update_info()
        _LOGGER.info("Scanner initialized")

    @asyncio.coroutine
    def async_scan_devices(self):
        """Scan for devices and return a list containing found device ids."""
        info = self._update_info()

        # Don't yield if we got None
        if info is not None:
            yield from info

        return [device.mac for device in self.last_results]

    @asyncio.coroutine
    def async_get_device_name(self, mac):
        """Return the name of the given device or None if we don't know."""
        filter_named = [device.name for device in self.last_results
                        if device.mac == mac]

        if filter_named:
            return filter_named[0]
        else:
            return None

    @Throttle(MIN_TIME_BETWEEN_SCANS)
    def _update_info(self):
        """
        Query Tado for device marked as at home.

        Returns boolean if scanning successful.
        """
        _LOGGER.debug("Requesting Tado")

        last_results = []

        try:
            with async_timeout.timeout(10, loop=self.hass.loop):
                # Format the URL here, so we can log the template URL if
                # anything goes wrong without exposing username and password.
                url = self.tadoapiurl.format(
                    home_id=self.home_id, username=self.username,
                    password=self.password)

                response = yield from self.websession.get(url)

                if response.status != 200:
                    _LOGGER.warning(
                        "Error %d on %s.", response.status, self.tadoapiurl)
                    return

                tado_json = yield from response.json()

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Cannot load Tado data")
            return False

        # Without a home_id, we fetched an URL where the mobile devices can be
        # found under the mobileDevices key.
        if 'mobileDevices' in tado_json:
            tado_json = tado_json['mobileDevices']

        # Find devices that have geofencing enabled, and are currently at home.
        for mobile_device in tado_json:
            if mobile_device.get('location'):
                if mobile_device['location']['atHome']:
                    device_id = mobile_device['id']
                    device_name = mobile_device['name']
                    last_results.append(Device(device_id, device_name))

        self.last_results = last_results

        _LOGGER.info(
            "Tado presence query successful, %d device(s) at home",
            len(self.last_results)
        )

        return True
