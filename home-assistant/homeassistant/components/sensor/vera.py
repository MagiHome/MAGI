"""
Support for Vera sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.vera/
"""
import logging
from datetime import timedelta

from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.util import convert
from homeassistant.components.vera import (
    VERA_CONTROLLER, VERA_DEVICES, VeraDevice)

DEPENDENCIES = ['vera']

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Vera controller devices."""
    add_devices(
        VeraSensor(device, VERA_CONTROLLER)
        for device in VERA_DEVICES['sensor'])


class VeraSensor(VeraDevice, Entity):
    """Representation of a Vera Sensor."""

    def __init__(self, vera_device, controller):
        """Initialize the sensor."""
        self.current_value = None
        self._temperature_units = None
        self.last_changed_time = None
        VeraDevice.__init__(self, vera_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)

    @property
    def state(self):
        """Return the name of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self.vera_device.category == "Temperature Sensor":
            return self._temperature_units
        elif self.vera_device.category == "Light Sensor":
            return 'lux'
        elif self.vera_device.category == "Humidity Sensor":
            return '%'
        elif self.vera_device.category == "Power meter":
            return 'watts'

    def update(self):
        """Update the state."""
        if self.vera_device.category == "Temperature Sensor":
            self.current_value = self.vera_device.temperature

            vera_temp_units = (
                self.vera_device.vera_controller.temperature_units)

            if vera_temp_units == 'F':
                self._temperature_units = TEMP_FAHRENHEIT
            else:
                self._temperature_units = TEMP_CELSIUS

        elif self.vera_device.category == "Light Sensor":
            self.current_value = self.vera_device.light
        elif self.vera_device.category == "Humidity Sensor":
            self.current_value = self.vera_device.humidity
        elif self.vera_device.category == "Scene Controller":
            value = self.vera_device.get_last_scene_id(True)
            time = self.vera_device.get_last_scene_time(True)
            if time == self.last_changed_time:
                self.current_value = None
            else:
                self.current_value = value
            self.last_changed_time = time
        elif self.vera_device.category == "Power meter":
            power = convert(self.vera_device.power, float, 0)
            self.current_value = int(round(power, 0))
        elif self.vera_device.category == "Sensor":
            tripped = self.vera_device.is_tripped
            self.current_value = 'Tripped' if tripped else 'Not Tripped'
        else:
            self.current_value = 'Unknown'
