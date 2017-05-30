"""
Support for Homematic thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.homematic/
"""
import logging
from homeassistant.components.climate import ClimateDevice, STATE_AUTO
from homeassistant.components.homematic import HMDevice, ATTR_DISCOVER_DEVICES
from homeassistant.util.temperature import convert
from homeassistant.const import TEMP_CELSIUS, STATE_UNKNOWN, ATTR_TEMPERATURE

DEPENDENCIES = ['homematic']

_LOGGER = logging.getLogger(__name__)

STATE_MANUAL = 'manual'
STATE_BOOST = 'boost'
STATE_COMFORT = 'comfort'
STATE_LOWERING = 'lowering'

HM_STATE_MAP = {
    'AUTO_MODE': STATE_AUTO,
    'MANU_MODE': STATE_MANUAL,
    'BOOST_MODE': STATE_BOOST,
    'COMFORT_MODE': STATE_COMFORT,
    'LOWERING_MODE': STATE_LOWERING
}

HM_TEMP_MAP = [
    'ACTUAL_TEMPERATURE',
    'TEMPERATURE',
]

HM_HUMI_MAP = [
    'ACTUAL_HUMIDITY',
    'HUMIDITY',
]

HM_CONTROL_MODE = 'CONTROL_MODE'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Homematic thermostat platform."""
    if discovery_info is None:
        return

    devices = []
    for config in discovery_info[ATTR_DISCOVER_DEVICES]:
        new_device = HMThermostat(hass, config)
        new_device.link_homematic()
        devices.append(new_device)

    add_devices(devices)


class HMThermostat(HMDevice, ClimateDevice):
    """Representation of a Homematic thermostat."""

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if HM_CONTROL_MODE not in self._data:
            return None

        # read state and search
        for mode, state in HM_STATE_MAP.items():
            code = getattr(self._hmdevice, mode, 0)
            if self._data.get('CONTROL_MODE') == code:
                return state

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        op_list = []

        for mode in self._hmdevice.ACTIONNODE:
            if mode in HM_STATE_MAP:
                op_list.append(HM_STATE_MAP.get(mode))

        return op_list

    @property
    def current_humidity(self):
        """Return the current humidity."""
        for node in HM_HUMI_MAP:
            if node in self._data:
                return self._data[node]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        for node in HM_TEMP_MAP:
            if node in self._data:
                return self._data[node]

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._data.get(self._state)

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return None

        self._hmdevice.writeNodeData(self._state, float(temperature))

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        for mode, state in HM_STATE_MAP.items():
            if state == operation_mode:
                code = getattr(self._hmdevice, mode, 0)
                self._hmdevice.MODE = code

    @property
    def min_temp(self):
        """Return the minimum temperature - 4.5 means off."""
        return convert(4.5, TEMP_CELSIUS, self.unit_of_measurement)

    @property
    def max_temp(self):
        """Return the maximum temperature - 30.5 means on."""
        return convert(30.5, TEMP_CELSIUS, self.unit_of_measurement)

    def _init_data_struct(self):
        """Generate a data dict (self._data) from the Homematic metadata."""
        self._state = next(iter(self._hmdevice.WRITENODE.keys()))
        self._data[self._state] = STATE_UNKNOWN

        if HM_CONTROL_MODE in self._hmdevice.ATTRIBUTENODE:
            self._data[HM_CONTROL_MODE] = STATE_UNKNOWN

        for node in self._hmdevice.SENSORNODE.keys():
            self._data[node] = STATE_UNKNOWN
