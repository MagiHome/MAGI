"""
Support for Homematic binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homematic/
"""
import logging
from homeassistant.const import STATE_UNKNOWN
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.homematic import HMDevice, ATTR_DISCOVER_DEVICES

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homematic']

SENSOR_TYPES_CLASS = {
    'Remote': None,
    'ShutterContact': 'opening',
    'MaxShutterContact': 'opening',
    'IPShutterContact': 'opening',
    'Smoke': 'smoke',
    'SmokeV2': 'smoke',
    'Motion': 'motion',
    'MotionV2': 'motion',
    'RemoteMotion': None,
    'WeatherSensor': None,
    'TiltSensor': None,
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Homematic binary sensor platform."""
    if discovery_info is None:
        return

    devices = []
    for config in discovery_info[ATTR_DISCOVER_DEVICES]:
        new_device = HMBinarySensor(hass, config)
        new_device.link_homematic()
        devices.append(new_device)

    add_devices(devices)


class HMBinarySensor(HMDevice, BinarySensorDevice):
    """Representation of a binary Homematic device."""

    @property
    def is_on(self):
        """Return true if switch is on."""
        if not self.available:
            return False
        return bool(self._hm_get_state())

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        # If state is MOTION (RemoteMotion works only)
        if self._state == 'MOTION':
            return 'motion'
        return SENSOR_TYPES_CLASS.get(self._hmdevice.__class__.__name__, None)

    def _init_data_struct(self):
        """Generate a data struct (self._data) from the Homematic metadata."""
        # add state to data struct
        if self._state:
            _LOGGER.debug("%s init datastruct with main node '%s'", self._name,
                          self._state)
            self._data.update({self._state: STATE_UNKNOWN})
