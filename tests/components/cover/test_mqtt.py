"""The tests for the MQTT cover platform."""
import unittest

from homeassistant.setup import setup_component
from homeassistant.const import STATE_OPEN, STATE_CLOSED, STATE_UNKNOWN
import homeassistant.components.cover as cover
from homeassistant.components.cover.mqtt import MqttCover

from tests.common import (
    get_test_home_assistant, mock_mqtt_component, fire_mqtt_message)


class TestCoverMQTT(unittest.TestCase):
    """Test the MQTT cover."""

    def setUp(self):  # pylint: disable=invalid-name
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.mock_publish = mock_mqtt_component(self.hass)

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop down everything that was started."""
        self.hass.stop()

    def test_state_via_state_topic(self):
        """Test the controlling state via topic."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP'
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '0')
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_CLOSED, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '50')
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_OPEN, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '100')
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_OPEN, state.state)

        fire_mqtt_message(self.hass, 'state-topic', STATE_CLOSED)
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_CLOSED, state.state)

        fire_mqtt_message(self.hass, 'state-topic', STATE_OPEN)
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_OPEN, state.state)

    def test_state_via_template(self):
        """Test the controlling state via topic."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'value_template': '{{ (value | multiply(0.01)) | int }}',
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '10000')
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_OPEN, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '99')
        self.hass.block_till_done()

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_CLOSED, state.state)

    def test_optimistic_state_change(self):
        """Test changing state optimistically."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'command_topic': 'command-topic',
                'qos': 0,
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        cover.open_cover(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('command-topic', 'OPEN', 0, False),
                         self.mock_publish.mock_calls[-2][1])
        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_OPEN, state.state)

        cover.close_cover(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('command-topic', 'CLOSE', 0, False),
                         self.mock_publish.mock_calls[-2][1])
        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_CLOSED, state.state)

    def test_send_open_cover_command(self):
        """Test the sending of open_cover."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 2
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        cover.open_cover(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('command-topic', 'OPEN', 2, False),
                         self.mock_publish.mock_calls[-2][1])
        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

    def test_send_close_cover_command(self):
        """Test the sending of close_cover."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 2
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        cover.close_cover(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('command-topic', 'CLOSE', 2, False),
                         self.mock_publish.mock_calls[-2][1])
        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

    def test_send_stop__cover_command(self):
        """Test the sending of stop_cover."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 2
            }
        }))

        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

        cover.stop_cover(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('command-topic', 'STOP', 2, False),
                         self.mock_publish.mock_calls[-2][1])
        state = self.hass.states.get('cover.test')
        self.assertEqual(STATE_UNKNOWN, state.state)

    def test_current_cover_position(self):
        """Test the current cover position."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP'
            }
        }))

        state_attributes_dict = self.hass.states.get(
            'cover.test').attributes
        self.assertFalse('current_position' in state_attributes_dict)
        self.assertFalse('current_tilt_position' in state_attributes_dict)

        fire_mqtt_message(self.hass, 'state-topic', '0')
        self.hass.block_till_done()
        current_cover_position = self.hass.states.get(
            'cover.test').attributes['current_position']
        self.assertEqual(0, current_cover_position)

        fire_mqtt_message(self.hass, 'state-topic', '50')
        self.hass.block_till_done()
        current_cover_position = self.hass.states.get(
            'cover.test').attributes['current_position']
        self.assertEqual(50, current_cover_position)

        fire_mqtt_message(self.hass, 'state-topic', '101')
        self.hass.block_till_done()
        current_cover_position = self.hass.states.get(
            'cover.test').attributes['current_position']
        self.assertEqual(50, current_cover_position)

        fire_mqtt_message(self.hass, 'state-topic', 'non-numeric')
        self.hass.block_till_done()
        current_cover_position = self.hass.states.get(
            'cover.test').attributes['current_position']
        self.assertEqual(50, current_cover_position)

    def test_tilt_defaults(self):
        """Test the defaults."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command',
                'tilt_status_topic': 'tilt-status'
            }
        }))

        state_attributes_dict = self.hass.states.get(
            'cover.test').attributes
        self.assertTrue('current_tilt_position' in state_attributes_dict)

        current_cover_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(STATE_UNKNOWN, current_cover_position)

    def test_tilt_via_invocation_defaults(self):
        """Test tilt defaults on close/open."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic'
            }
        }))

        cover.open_cover_tilt(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 100, 0, False),
                         self.mock_publish.mock_calls[-2][1])

        cover.close_cover_tilt(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 0, 0, False),
                         self.mock_publish.mock_calls[-2][1])

    def test_tilt_given_value(self):
        """Test tilting to a given value."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic',
                'tilt_opened_value': 400,
                'tilt_closed_value': 125
            }
        }))

        cover.open_cover_tilt(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 400, 0, False),
                         self.mock_publish.mock_calls[-2][1])

        cover.close_cover_tilt(self.hass, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 125, 0, False),
                         self.mock_publish.mock_calls[-2][1])

    def test_tilt_via_topic(self):
        """Test tilt by updating status via MQTT."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic',
                'tilt_opened_value': 400,
                'tilt_closed_value': 125
            }
        }))

        fire_mqtt_message(self.hass, 'tilt-status-topic', '0')
        self.hass.block_till_done()

        current_cover_tilt_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(0, current_cover_tilt_position)

        fire_mqtt_message(self.hass, 'tilt-status-topic', '50')
        self.hass.block_till_done()

        current_cover_tilt_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(50, current_cover_tilt_position)

    def test_tilt_via_topic_altered_range(self):
        """Test tilt status via MQTT with altered tilt range."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic',
                'tilt_opened_value': 400,
                'tilt_closed_value': 125,
                'tilt_min': 0,
                'tilt_max': 50
            }
        }))

        fire_mqtt_message(self.hass, 'tilt-status-topic', '0')
        self.hass.block_till_done()

        current_cover_tilt_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(0, current_cover_tilt_position)

        fire_mqtt_message(self.hass, 'tilt-status-topic', '50')
        self.hass.block_till_done()

        current_cover_tilt_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(100, current_cover_tilt_position)

        fire_mqtt_message(self.hass, 'tilt-status-topic', '25')
        self.hass.block_till_done()

        current_cover_tilt_position = self.hass.states.get(
            'cover.test').attributes['current_tilt_position']
        self.assertEqual(50, current_cover_tilt_position)

    def test_tilt_position(self):
        """Test tilt via method invocation."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic',
                'tilt_opened_value': 400,
                'tilt_closed_value': 125
            }
        }))

        cover.set_cover_tilt_position(self.hass, 50, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 50, 0, False),
                         self.mock_publish.mock_calls[-2][1])

    def test_tilt_position_altered_range(self):
        """Test tilt via method invocation with altered range."""
        self.assertTrue(setup_component(self.hass, cover.DOMAIN, {
            cover.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'qos': 0,
                'payload_open': 'OPEN',
                'payload_close': 'CLOSE',
                'payload_stop': 'STOP',
                'tilt_command_topic': 'tilt-command-topic',
                'tilt_status_topic': 'tilt-status-topic',
                'tilt_opened_value': 400,
                'tilt_closed_value': 125,
                'tilt_min': 0,
                'tilt_max': 50
            }
        }))

        cover.set_cover_tilt_position(self.hass, 50, 'cover.test')
        self.hass.block_till_done()

        self.assertEqual(('tilt-command-topic', 25, 0, False),
                         self.mock_publish.mock_calls[-2][1])

    def test_find_percentage_in_range_defaults(self):
        """Test find percentage in range with default range."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            100, 0, 0, 100, False, False)

        self.assertEqual(44, mqtt_cover.find_percentage_in_range(44))

    def test_find_percentage_in_range_altered(self):
        """Test find percentage in range with altered range."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            180, 80, 80, 180, False, False)

        self.assertEqual(40, mqtt_cover.find_percentage_in_range(120))

    def test_find_percentage_in_range_defaults_inverted(self):
        """Test find percentage in range with default range but inverted."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            100, 0, 0, 100, False, True)

        self.assertEqual(56, mqtt_cover.find_percentage_in_range(44))

    def test_find_percentage_in_range_altered_inverted(self):
        """Test find percentage in range with altered range and inverted."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            180, 80, 80, 180, False, True)

        self.assertEqual(60, mqtt_cover.find_percentage_in_range(120))

    def test_find_in_range_defaults(self):
        """Test find in range with default range."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            100, 0, 0, 100, False, False)

        self.assertEqual(44, mqtt_cover.find_in_range_from_percent(44))

    def test_find_in_range_altered(self):
        """Test find in range with altered range."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            180, 80, 80, 180, False, False)

        self.assertEqual(120, mqtt_cover.find_in_range_from_percent(40))

    def test_find_in_range_defaults_inverted(self):
        """Test find in range with default range but inverted."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            100, 0, 0, 100, False, True)

        self.assertEqual(44, mqtt_cover.find_in_range_from_percent(56))

    def test_find_in_range_altered_inverted(self):
        """Test find in range with altered range and inverted."""
        mqtt_cover = MqttCover(
            'cover.test', 'foo', 'bar', 'fooBar', "fooBarBaz", 0, False,
            'OPEN', 'CLOSE', 'OPEN', 'CLOSE', 'STOP', False, None,
            180, 80, 80, 180, False, True)

        self.assertEqual(120, mqtt_cover.find_in_range_from_percent(60))
