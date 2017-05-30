"""
Support for Wink switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.wink/
"""
import asyncio

from homeassistant.components.wink import WinkDevice, DOMAIN
from homeassistant.helpers.entity import ToggleEntity

DEPENDENCIES = ['wink']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Wink platform."""
    import pywink

    for switch in pywink.get_switches():
        _id = switch.object_id() + switch.name()
        if _id not in hass.data[DOMAIN]['unique_ids']:
            add_devices([WinkToggleDevice(switch, hass)])
    for switch in pywink.get_powerstrips():
        _id = switch.object_id() + switch.name()
        if _id not in hass.data[DOMAIN]['unique_ids']:
            add_devices([WinkToggleDevice(switch, hass)])
    for switch in pywink.get_sirens():
        _id = switch.object_id() + switch.name()
        if _id not in hass.data[DOMAIN]['unique_ids']:
            add_devices([WinkToggleDevice(switch, hass)])
    for sprinkler in pywink.get_sprinklers():
        _id = sprinkler.object_id() + sprinkler.name()
        if _id not in hass.data[DOMAIN]['unique_ids']:
            add_devices([WinkToggleDevice(sprinkler, hass)])


class WinkToggleDevice(WinkDevice, ToggleEntity):
    """Representation of a Wink toggle device."""

    def __init__(self, wink, hass):
        """Initialize the Wink device."""
        super().__init__(wink, hass)

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Callback when entity is added to hass."""
        self.hass.data[DOMAIN]['entities']['switch'].append(self)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.wink.state()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.wink.set_state(True)

    def turn_off(self):
        """Turn the device off."""
        self.wink.set_state(False)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attributes = super(WinkToggleDevice, self).device_state_attributes
        try:
            event = self.wink.last_event()
            attributes["last_event"] = event
        except AttributeError:
            pass
        return attributes
