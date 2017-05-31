"""
Support for AlarmDecoder devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/alarmdecoder/
"""
import asyncio
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send

REQUIREMENTS = ['alarmdecoder==0.12.1.0']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'alarmdecoder'

DATA_AD = 'alarmdecoder'

CONF_DEVICE = 'device'
CONF_DEVICE_BAUD = 'baudrate'
CONF_DEVICE_HOST = 'host'
CONF_DEVICE_PATH = 'path'
CONF_DEVICE_PORT = 'port'
CONF_DEVICE_TYPE = 'type'
CONF_PANEL_DISPLAY = 'panel_display'
CONF_ZONE_NAME = 'name'
CONF_ZONE_TYPE = 'type'
CONF_ZONES = 'zones'

DEFAULT_DEVICE_TYPE = 'socket'
DEFAULT_DEVICE_HOST = 'localhost'
DEFAULT_DEVICE_PORT = 10000
DEFAULT_DEVICE_PATH = '/dev/ttyUSB0'
DEFAULT_DEVICE_BAUD = 115200

DEFAULT_PANEL_DISPLAY = False

DEFAULT_ZONE_TYPE = 'opening'

SIGNAL_PANEL_MESSAGE = 'alarmdecoder.panel_message'
SIGNAL_PANEL_ARM_AWAY = 'alarmdecoder.panel_arm_away'
SIGNAL_PANEL_ARM_HOME = 'alarmdecoder.panel_arm_home'
SIGNAL_PANEL_DISARM = 'alarmdecoder.panel_disarm'

SIGNAL_ZONE_FAULT = 'alarmdecoder.zone_fault'
SIGNAL_ZONE_RESTORE = 'alarmdecoder.zone_restore'

DEVICE_SOCKET_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_TYPE): 'socket',
    vol.Optional(CONF_DEVICE_HOST, default=DEFAULT_DEVICE_HOST): cv.string,
    vol.Optional(CONF_DEVICE_PORT, default=DEFAULT_DEVICE_PORT): cv.port})

DEVICE_SERIAL_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_TYPE): 'serial',
    vol.Optional(CONF_DEVICE_PATH, default=DEFAULT_DEVICE_PATH): cv.string,
    vol.Optional(CONF_DEVICE_BAUD, default=DEFAULT_DEVICE_BAUD): cv.string})

DEVICE_USB_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_TYPE): 'usb'})

ZONE_SCHEMA = vol.Schema({
    vol.Required(CONF_ZONE_NAME): cv.string,
    vol.Optional(CONF_ZONE_TYPE, default=DEFAULT_ZONE_TYPE): cv.string})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICE): vol.Any(DEVICE_SOCKET_SCHEMA,
                                           DEVICE_SERIAL_SCHEMA,
                                           DEVICE_USB_SCHEMA),
        vol.Optional(CONF_PANEL_DISPLAY,
                     default=DEFAULT_PANEL_DISPLAY): cv.boolean,
        vol.Optional(CONF_ZONES): {vol.Coerce(int): ZONE_SCHEMA},
    }),
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Set up for the AlarmDecoder devices."""
    from alarmdecoder import AlarmDecoder
    from alarmdecoder.devices import (SocketDevice, SerialDevice, USBDevice)

    conf = config.get(DOMAIN)

    device = conf.get(CONF_DEVICE)
    display = conf.get(CONF_PANEL_DISPLAY)
    zones = conf.get(CONF_ZONES)

    device_type = device.get(CONF_DEVICE_TYPE)
    host = DEFAULT_DEVICE_HOST
    port = DEFAULT_DEVICE_PORT
    path = DEFAULT_DEVICE_PATH
    baud = DEFAULT_DEVICE_BAUD

    sync_connect = asyncio.Future(loop=hass.loop)

    def handle_open(device):
        """Handle the successful connection."""
        _LOGGER.info("Established a connection with the alarmdecoder")
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_alarmdecoder)
        sync_connect.set_result(True)

    @callback
    def stop_alarmdecoder(event):
        """Handle the shutdown of AlarmDecoder."""
        _LOGGER.debug("Shutting down alarmdecoder")
        controller.close()

    @callback
    def handle_message(sender, message):
        """Handle message from AlarmDecoder."""
        async_dispatcher_send(hass, SIGNAL_PANEL_MESSAGE, message)

    def zone_fault_callback(sender, zone):
        """Handle zone fault from AlarmDecoder."""
        async_dispatcher_send(hass, SIGNAL_ZONE_FAULT, zone)

    def zone_restore_callback(sender, zone):
        """Handle zone restore from AlarmDecoder."""
        async_dispatcher_send(hass, SIGNAL_ZONE_RESTORE, zone)

    controller = False
    if device_type == 'socket':
        host = device.get(CONF_DEVICE_HOST)
        port = device.get(CONF_DEVICE_PORT)
        controller = AlarmDecoder(SocketDevice(interface=(host, port)))
    elif device_type == 'serial':
        path = device.get(CONF_DEVICE_PATH)
        baud = device.get(CONF_DEVICE_BAUD)
        controller = AlarmDecoder(SerialDevice(interface=path))
    elif device_type == 'usb':
        AlarmDecoder(USBDevice.find())
        return False

    controller.on_open += handle_open
    controller.on_message += handle_message
    controller.on_zone_fault += zone_fault_callback
    controller.on_zone_restore += zone_restore_callback

    hass.data[DATA_AD] = controller

    controller.open(baud)

    result = yield from sync_connect

    if not result:
        return False

    hass.async_add_job(
        async_load_platform(hass, 'alarm_control_panel', DOMAIN, conf,
                            config))

    if zones:
        hass.async_add_job(async_load_platform(
            hass, 'binary_sensor', DOMAIN, {CONF_ZONES: zones}, config))

    if display:
        hass.async_add_job(async_load_platform(
            hass, 'sensor', DOMAIN, conf, config))

    return True
