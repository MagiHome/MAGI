"""Test for RFlink switch components.

Test setup of rflink switch component/platform. State tracking and
control of Rflink switch devices.

"""

import asyncio

from homeassistant.const import (
    ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON)

from ..test_rflink import mock_rflink

DOMAIN = 'switch'

CONFIG = {
    'rflink': {
        'port': '/dev/ttyABC0',
        'ignore_devices': ['ignore_wildcard_*', 'ignore_sensor'],
    },
    DOMAIN: {
        'platform': 'rflink',
        'devices': {
            'protocol_0_0': {
                'name': 'test',
                'aliasses': ['test_alias_0_0'],
            },
        },
    },
}


@asyncio.coroutine
def test_default_setup(hass, monkeypatch):
    """Test all basic functionality of the rflink switch component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = yield from mock_rflink(
        hass, CONFIG, DOMAIN, monkeypatch)

    # make sure arguments are passed
    assert create.call_args_list[0][1]['ignore']

    # test default state of switch loaded from config
    switch_initial = hass.states.get('switch.test')
    assert switch_initial.state == 'off'
    assert switch_initial.attributes['assumed_state']

    # switch should follow state of the hardware device by interpreting
    # incoming events for its name and aliasses

    # mock incoming command event for this device
    event_callback({
        'id': 'protocol_0_0',
        'command': 'on',
    })
    yield from hass.async_block_till_done()

    switch_after_first_command = hass.states.get('switch.test')
    assert switch_after_first_command.state == 'on'
    # also after receiving first command state not longer has to be assumed
    assert 'assumed_state' not in switch_after_first_command.attributes

    # mock incoming command event for this device
    event_callback({
        'id': 'protocol_0_0',
        'command': 'off',
    })
    yield from hass.async_block_till_done()

    assert hass.states.get('switch.test').state == 'off'

    # test following aliasses
    # mock incoming command event for this device alias
    event_callback({
        'id': 'test_alias_0_0',
        'command': 'on',
    })
    yield from hass.async_block_till_done()

    assert hass.states.get('switch.test').state == 'on'

    # The switch component does not support adding new devices for incoming
    # events because every new unkown device is added as a light by default.

    # test changing state from HA propagates to Rflink
    hass.async_add_job(
        hass.services.async_call(DOMAIN, SERVICE_TURN_OFF,
                                 {ATTR_ENTITY_ID: 'switch.test'}))
    yield from hass.async_block_till_done()
    assert hass.states.get('switch.test').state == 'off'
    assert protocol.send_command_ack.call_args_list[0][0][0] == 'protocol_0_0'
    assert protocol.send_command_ack.call_args_list[0][0][1] == 'off'

    hass.async_add_job(
        hass.services.async_call(DOMAIN, SERVICE_TURN_ON,
                                 {ATTR_ENTITY_ID: 'switch.test'}))
    yield from hass.async_block_till_done()
    assert hass.states.get('switch.test').state == 'on'
    assert protocol.send_command_ack.call_args_list[1][0][1] == 'on'
