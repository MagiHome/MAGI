"""Zwave discovery schemas."""
from . import const

DEFAULT_VALUES_SCHEMA = {
    'power': {
        const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SENSOR_MULTILEVEL,
                                   const.COMMAND_CLASS_METER],
        const.DISC_LABEL: ['Power'],
        const.DISC_OPTIONAL: True,
        },
}

DISCOVERY_SCHEMAS = [
    {const.DISC_COMPONENT: 'binary_sensor',
     const.DISC_GENERIC_DEVICE_CLASS: [
         const.GENERIC_TYPE_SENSOR_ALARM,
         const.GENERIC_TYPE_SENSOR_BINARY,
         const.GENERIC_TYPE_SWITCH_BINARY,
         const.GENERIC_TYPE_METER,
         const.GENERIC_TYPE_SENSOR_MULTILEVEL,
         const.GENERIC_TYPE_SWITCH_MULTILEVEL,
         const.GENERIC_TYPE_SENSOR_NOTIFICATION,
         const.GENERIC_TYPE_THERMOSTAT],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SENSOR_BINARY],
             const.DISC_TYPE: const.TYPE_BOOL,
             const.DISC_GENRE: const.GENRE_USER
         }})},
    {const.DISC_COMPONENT: 'climate',
     const.DISC_GENERIC_DEVICE_CLASS: [const.GENERIC_TYPE_THERMOSTAT],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_THERMOSTAT_SETPOINT],
         },
         'temperature': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SENSOR_MULTILEVEL],
             const.DISC_LABEL: 'Temperature',
             const.DISC_OPTIONAL: True,
         },
         'mode': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_THERMOSTAT_MODE],
             const.DISC_OPTIONAL: True,
         },
         'fan_mode': {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_THERMOSTAT_FAN_MODE],
             const.DISC_OPTIONAL: True,
         },
         'operating_state': {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_THERMOSTAT_OPERATING_STATE],
             const.DISC_OPTIONAL: True,
         },
         'fan_state': {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_THERMOSTAT_FAN_STATE],
             const.DISC_OPTIONAL: True,
         },
         'zxt_120_swing_mode': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_CONFIGURATION],
             const.DISC_INDEX: [33],
             const.DISC_OPTIONAL: True,
         }})},
    {const.DISC_COMPONENT: 'cover',  # Rollershutter
     const.DISC_GENERIC_DEVICE_CLASS: [
         const.GENERIC_TYPE_SWITCH_MULTILEVEL,
         const.GENERIC_TYPE_ENTRY_CONTROL],
     const.DISC_SPECIFIC_DEVICE_CLASS: [
         const.SPECIFIC_TYPE_CLASS_A_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_CLASS_B_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_CLASS_C_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_MOTOR_MULTIPOSITION,
         const.SPECIFIC_TYPE_SECURE_BARRIER_ADDON,
         const.SPECIFIC_TYPE_SECURE_DOOR],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_MULTILEVEL],
             const.DISC_GENRE: const.GENRE_USER,
         },
         'open': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_MULTILEVEL],
             const.DISC_LABEL: ['Open', 'Up', 'Bright'],
             const.DISC_OPTIONAL: True,
         },
         'close': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_MULTILEVEL],
             const.DISC_LABEL: ['Close', 'Down', 'Dim'],
             const.DISC_OPTIONAL: True,
         }})},
    {const.DISC_COMPONENT: 'cover',  # Garage Door
     const.DISC_GENERIC_DEVICE_CLASS: [
         const.GENERIC_TYPE_SWITCH_MULTILEVEL,
         const.GENERIC_TYPE_ENTRY_CONTROL],
     const.DISC_SPECIFIC_DEVICE_CLASS: [
         const.SPECIFIC_TYPE_CLASS_A_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_CLASS_B_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_CLASS_C_MOTOR_CONTROL,
         const.SPECIFIC_TYPE_MOTOR_MULTIPOSITION,
         const.SPECIFIC_TYPE_SECURE_BARRIER_ADDON,
         const.SPECIFIC_TYPE_SECURE_DOOR],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_BARRIER_OPERATOR,
                 const.COMMAND_CLASS_SWITCH_BINARY],
             const.DISC_GENRE: const.GENRE_USER,
         }})},
    {const.DISC_COMPONENT: 'light',
     const.DISC_GENERIC_DEVICE_CLASS: [
         const.GENERIC_TYPE_SWITCH_MULTILEVEL,
         const.GENERIC_TYPE_SWITCH_REMOTE],
     const.DISC_SPECIFIC_DEVICE_CLASS: [
         const.SPECIFIC_TYPE_POWER_SWITCH_MULTILEVEL,
         const.SPECIFIC_TYPE_SCENE_SWITCH_MULTILEVEL,
         const.SPECIFIC_TYPE_NOT_USED],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_MULTILEVEL],
             const.DISC_GENRE: const.GENRE_USER,
             const.DISC_TYPE: const.TYPE_BYTE,
         },
         'dimming_duration': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_MULTILEVEL],
             const.DISC_GENRE: const.GENRE_SYSTEM,
             const.DISC_TYPE: const.TYPE_BYTE,
             const.DISC_LABEL: 'Dimming Duration',
             const.DISC_OPTIONAL: True,
         },
         'color': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_COLOR],
             const.DISC_GENRE: const.GENRE_USER,
             const.DISC_TYPE: const.TYPE_STRING,
             const.DISC_READONLY: False,
             const.DISC_WRITEONLY: False,
             const.DISC_OPTIONAL: True,
         },
         'color_channels': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_COLOR],
             const.DISC_GENRE: const.GENRE_SYSTEM,
             const.DISC_TYPE: const.TYPE_INT,
             const.DISC_OPTIONAL: True,
         }})},
    {const.DISC_COMPONENT: 'lock',
     const.DISC_GENERIC_DEVICE_CLASS: [const.GENERIC_TYPE_ENTRY_CONTROL],
     const.DISC_SPECIFIC_DEVICE_CLASS: [
         const.SPECIFIC_TYPE_ADVANCED_DOOR_LOCK,
         const.SPECIFIC_TYPE_SECURE_KEYPAD_DOOR_LOCK],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_DOOR_LOCK],
             const.DISC_TYPE: const.TYPE_BOOL,
             const.DISC_GENRE: const.GENRE_USER,
         },
         'access_control': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_ALARM],
             const.DISC_LABEL: 'Access Control',
             const.DISC_OPTIONAL: True,
         },
         'alarm_type': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_ALARM],
             const.DISC_LABEL: 'Alarm Type',
             const.DISC_OPTIONAL: True,
         },
         'alarm_level': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_ALARM],
             const.DISC_LABEL: 'Alarm Level',
             const.DISC_OPTIONAL: True,
         },
         'v2btze_advanced': {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_CONFIGURATION],
             const.DISC_INDEX: [12],
             const.DISC_OPTIONAL: True,
         }})},
    {const.DISC_COMPONENT: 'sensor',
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [
                 const.COMMAND_CLASS_SENSOR_MULTILEVEL,
                 const.COMMAND_CLASS_METER,
                 const.COMMAND_CLASS_ALARM,
                 const.COMMAND_CLASS_SENSOR_ALARM],
             const.DISC_GENRE: const.GENRE_USER,
         }})},
    {const.DISC_COMPONENT: 'switch',
     const.DISC_GENERIC_DEVICE_CLASS: [
         const.GENERIC_TYPE_SENSOR_ALARM,
         const.GENERIC_TYPE_SENSOR_BINARY,
         const.GENERIC_TYPE_SWITCH_BINARY,
         const.GENERIC_TYPE_ENTRY_CONTROL,
         const.GENERIC_TYPE_SENSOR_MULTILEVEL,
         const.GENERIC_TYPE_SWITCH_MULTILEVEL,
         const.GENERIC_TYPE_SENSOR_NOTIFICATION,
         const.GENERIC_TYPE_GENERIC_CONTROLLER,
         const.GENERIC_TYPE_SWITCH_REMOTE,
         const.GENERIC_TYPE_REPEATER_SLAVE,
         const.GENERIC_TYPE_THERMOSTAT,
         const.GENERIC_TYPE_WALL_CONTROLLER],
     const.DISC_VALUES: dict(DEFAULT_VALUES_SCHEMA, **{
         const.DISC_PRIMARY: {
             const.DISC_COMMAND_CLASS: [const.COMMAND_CLASS_SWITCH_BINARY],
             const.DISC_TYPE: const.TYPE_BOOL,
             const.DISC_GENRE: const.GENRE_USER,
         }})},
]
