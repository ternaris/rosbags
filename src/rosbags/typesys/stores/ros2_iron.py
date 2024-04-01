# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
#
# THIS FILE IS GENERATED, DO NOT EDIT
"""Message type definitions."""

# ruff: noqa: E501,F401,F403,F405,F821,N801,N814,TCH004

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype as T

from .ros2_humble import *

if TYPE_CHECKING:
    from typing import ClassVar

    import numpy as np


@dataclass
class rcl_interfaces__msg__LoggerLevel:
    """Class for rcl_interfaces/msg/LoggerLevel."""

    name: str
    level: int
    LOG_LEVEL_UNKNOWN: ClassVar[int] = 0
    LOG_LEVEL_DEBUG: ClassVar[int] = 10
    LOG_LEVEL_INFO: ClassVar[int] = 20
    LOG_LEVEL_WARN: ClassVar[int] = 30
    LOG_LEVEL_ERROR: ClassVar[int] = 40
    LOG_LEVEL_FATAL: ClassVar[int] = 50
    __msgtype__: ClassVar[str] = 'rcl_interfaces/msg/LoggerLevel'


@dataclass
class rcl_interfaces__msg__SetLoggerLevelsResult:
    """Class for rcl_interfaces/msg/SetLoggerLevelsResult."""

    successful: bool
    reason: str
    __msgtype__: ClassVar[str] = 'rcl_interfaces/msg/SetLoggerLevelsResult'


@dataclass
class rmw_dds_common__msg__Gid:  # type: ignore[no-redef]
    """Class for rmw_dds_common/msg/Gid."""

    data: np.ndarray[None, np.dtype[np.uint8]]
    __msgtype__: ClassVar[str] = 'rmw_dds_common/msg/Gid'


@dataclass
class sensor_msgs__msg__BatteryState:  # type: ignore[no-redef]
    """Class for sensor_msgs/msg/BatteryState."""

    header: std_msgs__msg__Header
    voltage: float
    temperature: float
    current: float
    charge: float
    capacity: float
    design_capacity: float
    percentage: float
    power_supply_status: int
    power_supply_health: int
    power_supply_technology: int
    present: bool
    cell_voltage: np.ndarray[None, np.dtype[np.float32]]
    cell_temperature: np.ndarray[None, np.dtype[np.float32]]
    location: str
    serial_number: str
    POWER_SUPPLY_STATUS_UNKNOWN: ClassVar[int] = 0
    POWER_SUPPLY_STATUS_CHARGING: ClassVar[int] = 1
    POWER_SUPPLY_STATUS_DISCHARGING: ClassVar[int] = 2
    POWER_SUPPLY_STATUS_NOT_CHARGING: ClassVar[int] = 3
    POWER_SUPPLY_STATUS_FULL: ClassVar[int] = 4
    POWER_SUPPLY_HEALTH_UNKNOWN: ClassVar[int] = 0
    POWER_SUPPLY_HEALTH_GOOD: ClassVar[int] = 1
    POWER_SUPPLY_HEALTH_OVERHEAT: ClassVar[int] = 2
    POWER_SUPPLY_HEALTH_DEAD: ClassVar[int] = 3
    POWER_SUPPLY_HEALTH_OVERVOLTAGE: ClassVar[int] = 4
    POWER_SUPPLY_HEALTH_UNSPEC_FAILURE: ClassVar[int] = 5
    POWER_SUPPLY_HEALTH_COLD: ClassVar[int] = 6
    POWER_SUPPLY_HEALTH_WATCHDOG_TIMER_EXPIRE: ClassVar[int] = 7
    POWER_SUPPLY_HEALTH_SAFETY_TIMER_EXPIRE: ClassVar[int] = 8
    POWER_SUPPLY_TECHNOLOGY_UNKNOWN: ClassVar[int] = 0
    POWER_SUPPLY_TECHNOLOGY_NIMH: ClassVar[int] = 1
    POWER_SUPPLY_TECHNOLOGY_LION: ClassVar[int] = 2
    POWER_SUPPLY_TECHNOLOGY_LIPO: ClassVar[int] = 3
    POWER_SUPPLY_TECHNOLOGY_LIFE: ClassVar[int] = 4
    POWER_SUPPLY_TECHNOLOGY_NICD: ClassVar[int] = 5
    POWER_SUPPLY_TECHNOLOGY_LIMN: ClassVar[int] = 6
    POWER_SUPPLY_TECHNOLOGY_TERNARY: ClassVar[int] = 7
    POWER_SUPPLY_TECHNOLOGY_VRLA: ClassVar[int] = 8
    __msgtype__: ClassVar[str] = 'sensor_msgs/msg/BatteryState'


@dataclass
class sensor_msgs__msg__Range:  # type: ignore[no-redef]
    """Class for sensor_msgs/msg/Range."""

    header: std_msgs__msg__Header
    radiation_type: int
    field_of_view: float
    min_range: float
    max_range: float
    range: float
    variance: float
    ULTRASOUND: ClassVar[int] = 0
    INFRARED: ClassVar[int] = 1
    __msgtype__: ClassVar[str] = 'sensor_msgs/msg/Range'


@dataclass
class service_msgs__msg__ServiceEventInfo:
    """Class for service_msgs/msg/ServiceEventInfo."""

    event_type: int
    stamp: builtin_interfaces__msg__Time
    client_gid: np.ndarray[None, np.dtype[np.uint8]]
    sequence_number: int
    REQUEST_SENT: ClassVar[int] = 0
    REQUEST_RECEIVED: ClassVar[int] = 1
    RESPONSE_SENT: ClassVar[int] = 2
    RESPONSE_RECEIVED: ClassVar[int] = 3
    __msgtype__: ClassVar[str] = 'service_msgs/msg/ServiceEventInfo'


@dataclass
class type_description_interfaces__msg__Field:
    """Class for type_description_interfaces/msg/Field."""

    name: str
    type: type_description_interfaces__msg__FieldType
    default_value: str
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/Field'


@dataclass
class type_description_interfaces__msg__FieldType:
    """Class for type_description_interfaces/msg/FieldType."""

    type_id: int
    capacity: int
    string_capacity: int
    nested_type_name: str
    FIELD_TYPE_NOT_SET: ClassVar[int] = 0
    FIELD_TYPE_NESTED_TYPE: ClassVar[int] = 1
    FIELD_TYPE_INT8: ClassVar[int] = 2
    FIELD_TYPE_UINT8: ClassVar[int] = 3
    FIELD_TYPE_INT16: ClassVar[int] = 4
    FIELD_TYPE_UINT16: ClassVar[int] = 5
    FIELD_TYPE_INT32: ClassVar[int] = 6
    FIELD_TYPE_UINT32: ClassVar[int] = 7
    FIELD_TYPE_INT64: ClassVar[int] = 8
    FIELD_TYPE_UINT64: ClassVar[int] = 9
    FIELD_TYPE_FLOAT: ClassVar[int] = 10
    FIELD_TYPE_DOUBLE: ClassVar[int] = 11
    FIELD_TYPE_LONG_DOUBLE: ClassVar[int] = 12
    FIELD_TYPE_CHAR: ClassVar[int] = 13
    FIELD_TYPE_WCHAR: ClassVar[int] = 14
    FIELD_TYPE_BOOLEAN: ClassVar[int] = 15
    FIELD_TYPE_BYTE: ClassVar[int] = 16
    FIELD_TYPE_STRING: ClassVar[int] = 17
    FIELD_TYPE_WSTRING: ClassVar[int] = 18
    FIELD_TYPE_FIXED_STRING: ClassVar[int] = 19
    FIELD_TYPE_FIXED_WSTRING: ClassVar[int] = 20
    FIELD_TYPE_BOUNDED_STRING: ClassVar[int] = 21
    FIELD_TYPE_BOUNDED_WSTRING: ClassVar[int] = 22
    FIELD_TYPE_NESTED_TYPE_ARRAY: ClassVar[int] = 49
    FIELD_TYPE_INT8_ARRAY: ClassVar[int] = 50
    FIELD_TYPE_UINT8_ARRAY: ClassVar[int] = 51
    FIELD_TYPE_INT16_ARRAY: ClassVar[int] = 52
    FIELD_TYPE_UINT16_ARRAY: ClassVar[int] = 53
    FIELD_TYPE_INT32_ARRAY: ClassVar[int] = 54
    FIELD_TYPE_UINT32_ARRAY: ClassVar[int] = 55
    FIELD_TYPE_INT64_ARRAY: ClassVar[int] = 56
    FIELD_TYPE_UINT64_ARRAY: ClassVar[int] = 57
    FIELD_TYPE_FLOAT_ARRAY: ClassVar[int] = 58
    FIELD_TYPE_DOUBLE_ARRAY: ClassVar[int] = 59
    FIELD_TYPE_LONG_DOUBLE_ARRAY: ClassVar[int] = 60
    FIELD_TYPE_CHAR_ARRAY: ClassVar[int] = 61
    FIELD_TYPE_WCHAR_ARRAY: ClassVar[int] = 62
    FIELD_TYPE_BOOLEAN_ARRAY: ClassVar[int] = 63
    FIELD_TYPE_BYTE_ARRAY: ClassVar[int] = 64
    FIELD_TYPE_STRING_ARRAY: ClassVar[int] = 65
    FIELD_TYPE_WSTRING_ARRAY: ClassVar[int] = 66
    FIELD_TYPE_FIXED_STRING_ARRAY: ClassVar[int] = 67
    FIELD_TYPE_FIXED_WSTRING_ARRAY: ClassVar[int] = 68
    FIELD_TYPE_BOUNDED_STRING_ARRAY: ClassVar[int] = 69
    FIELD_TYPE_BOUNDED_WSTRING_ARRAY: ClassVar[int] = 70
    FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE: ClassVar[int] = 97
    FIELD_TYPE_INT8_BOUNDED_SEQUENCE: ClassVar[int] = 98
    FIELD_TYPE_UINT8_BOUNDED_SEQUENCE: ClassVar[int] = 99
    FIELD_TYPE_INT16_BOUNDED_SEQUENCE: ClassVar[int] = 100
    FIELD_TYPE_UINT16_BOUNDED_SEQUENCE: ClassVar[int] = 101
    FIELD_TYPE_INT32_BOUNDED_SEQUENCE: ClassVar[int] = 102
    FIELD_TYPE_UINT32_BOUNDED_SEQUENCE: ClassVar[int] = 103
    FIELD_TYPE_INT64_BOUNDED_SEQUENCE: ClassVar[int] = 104
    FIELD_TYPE_UINT64_BOUNDED_SEQUENCE: ClassVar[int] = 105
    FIELD_TYPE_FLOAT_BOUNDED_SEQUENCE: ClassVar[int] = 106
    FIELD_TYPE_DOUBLE_BOUNDED_SEQUENCE: ClassVar[int] = 107
    FIELD_TYPE_LONG_DOUBLE_BOUNDED_SEQUENCE: ClassVar[int] = 108
    FIELD_TYPE_CHAR_BOUNDED_SEQUENCE: ClassVar[int] = 109
    FIELD_TYPE_WCHAR_BOUNDED_SEQUENCE: ClassVar[int] = 110
    FIELD_TYPE_BOOLEAN_BOUNDED_SEQUENCE: ClassVar[int] = 111
    FIELD_TYPE_BYTE_BOUNDED_SEQUENCE: ClassVar[int] = 112
    FIELD_TYPE_STRING_BOUNDED_SEQUENCE: ClassVar[int] = 113
    FIELD_TYPE_WSTRING_BOUNDED_SEQUENCE: ClassVar[int] = 114
    FIELD_TYPE_FIXED_STRING_BOUNDED_SEQUENCE: ClassVar[int] = 115
    FIELD_TYPE_FIXED_WSTRING_BOUNDED_SEQUENCE: ClassVar[int] = 116
    FIELD_TYPE_BOUNDED_STRING_BOUNDED_SEQUENCE: ClassVar[int] = 117
    FIELD_TYPE_BOUNDED_WSTRING_BOUNDED_SEQUENCE: ClassVar[int] = 118
    FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE: ClassVar[int] = 145
    FIELD_TYPE_INT8_UNBOUNDED_SEQUENCE: ClassVar[int] = 146
    FIELD_TYPE_UINT8_UNBOUNDED_SEQUENCE: ClassVar[int] = 147
    FIELD_TYPE_INT16_UNBOUNDED_SEQUENCE: ClassVar[int] = 148
    FIELD_TYPE_UINT16_UNBOUNDED_SEQUENCE: ClassVar[int] = 149
    FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE: ClassVar[int] = 150
    FIELD_TYPE_UINT32_UNBOUNDED_SEQUENCE: ClassVar[int] = 151
    FIELD_TYPE_INT64_UNBOUNDED_SEQUENCE: ClassVar[int] = 152
    FIELD_TYPE_UINT64_UNBOUNDED_SEQUENCE: ClassVar[int] = 153
    FIELD_TYPE_FLOAT_UNBOUNDED_SEQUENCE: ClassVar[int] = 154
    FIELD_TYPE_DOUBLE_UNBOUNDED_SEQUENCE: ClassVar[int] = 155
    FIELD_TYPE_LONG_DOUBLE_UNBOUNDED_SEQUENCE: ClassVar[int] = 156
    FIELD_TYPE_CHAR_UNBOUNDED_SEQUENCE: ClassVar[int] = 157
    FIELD_TYPE_WCHAR_UNBOUNDED_SEQUENCE: ClassVar[int] = 158
    FIELD_TYPE_BOOLEAN_UNBOUNDED_SEQUENCE: ClassVar[int] = 159
    FIELD_TYPE_BYTE_UNBOUNDED_SEQUENCE: ClassVar[int] = 160
    FIELD_TYPE_STRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 161
    FIELD_TYPE_WSTRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 162
    FIELD_TYPE_FIXED_STRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 163
    FIELD_TYPE_FIXED_WSTRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 164
    FIELD_TYPE_BOUNDED_STRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 165
    FIELD_TYPE_BOUNDED_WSTRING_UNBOUNDED_SEQUENCE: ClassVar[int] = 166
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/FieldType'


@dataclass
class type_description_interfaces__msg__IndividualTypeDescription:
    """Class for type_description_interfaces/msg/IndividualTypeDescription."""

    type_name: str
    fields: list[type_description_interfaces__msg__Field]
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/IndividualTypeDescription'


@dataclass
class type_description_interfaces__msg__KeyValue:
    """Class for type_description_interfaces/msg/KeyValue."""

    key: str
    value: str
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/KeyValue'


@dataclass
class type_description_interfaces__msg__TypeDescription:
    """Class for type_description_interfaces/msg/TypeDescription."""

    type_description: type_description_interfaces__msg__IndividualTypeDescription
    referenced_type_descriptions: list[type_description_interfaces__msg__IndividualTypeDescription]
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/TypeDescription'


@dataclass
class type_description_interfaces__msg__TypeSource:
    """Class for type_description_interfaces/msg/TypeSource."""

    type_name: str
    encoding: str
    raw_file_contents: str
    __msgtype__: ClassVar[str] = 'type_description_interfaces/msg/TypeSource'


FIELDDEFS = {
    **FIELDDEFS,
    'rcl_interfaces/msg/LoggerLevel': (
        [
            ('LOG_LEVEL_UNKNOWN', 'uint8', 0),
            ('LOG_LEVEL_DEBUG', 'uint8', 10),
            ('LOG_LEVEL_INFO', 'uint8', 20),
            ('LOG_LEVEL_WARN', 'uint8', 30),
            ('LOG_LEVEL_ERROR', 'uint8', 40),
            ('LOG_LEVEL_FATAL', 'uint8', 50),
        ],
        [
            ('name', (T.BASE, ('string', 0))),
            ('level', (T.BASE, ('uint32', 0))),
        ],
    ),
    'rcl_interfaces/msg/SetLoggerLevelsResult': (
        [],
        [
            ('successful', (T.BASE, ('bool', 0))),
            ('reason', (T.BASE, ('string', 0))),
        ],
    ),
    'rmw_dds_common/msg/Gid': (
        [],
        [
            ('data', (T.ARRAY, ((T.BASE, ('char', 0)), 16))),
        ],
    ),
    'sensor_msgs/msg/BatteryState': (
        [
            ('POWER_SUPPLY_STATUS_UNKNOWN', 'uint8', 0),
            ('POWER_SUPPLY_STATUS_CHARGING', 'uint8', 1),
            ('POWER_SUPPLY_STATUS_DISCHARGING', 'uint8', 2),
            ('POWER_SUPPLY_STATUS_NOT_CHARGING', 'uint8', 3),
            ('POWER_SUPPLY_STATUS_FULL', 'uint8', 4),
            ('POWER_SUPPLY_HEALTH_UNKNOWN', 'uint8', 0),
            ('POWER_SUPPLY_HEALTH_GOOD', 'uint8', 1),
            ('POWER_SUPPLY_HEALTH_OVERHEAT', 'uint8', 2),
            ('POWER_SUPPLY_HEALTH_DEAD', 'uint8', 3),
            ('POWER_SUPPLY_HEALTH_OVERVOLTAGE', 'uint8', 4),
            ('POWER_SUPPLY_HEALTH_UNSPEC_FAILURE', 'uint8', 5),
            ('POWER_SUPPLY_HEALTH_COLD', 'uint8', 6),
            ('POWER_SUPPLY_HEALTH_WATCHDOG_TIMER_EXPIRE', 'uint8', 7),
            ('POWER_SUPPLY_HEALTH_SAFETY_TIMER_EXPIRE', 'uint8', 8),
            ('POWER_SUPPLY_TECHNOLOGY_UNKNOWN', 'uint8', 0),
            ('POWER_SUPPLY_TECHNOLOGY_NIMH', 'uint8', 1),
            ('POWER_SUPPLY_TECHNOLOGY_LION', 'uint8', 2),
            ('POWER_SUPPLY_TECHNOLOGY_LIPO', 'uint8', 3),
            ('POWER_SUPPLY_TECHNOLOGY_LIFE', 'uint8', 4),
            ('POWER_SUPPLY_TECHNOLOGY_NICD', 'uint8', 5),
            ('POWER_SUPPLY_TECHNOLOGY_LIMN', 'uint8', 6),
            ('POWER_SUPPLY_TECHNOLOGY_TERNARY', 'uint8', 7),
            ('POWER_SUPPLY_TECHNOLOGY_VRLA', 'uint8', 8),
        ],
        [
            ('header', (T.NAME, 'std_msgs/msg/Header')),
            ('voltage', (T.BASE, ('float32', 0))),
            ('temperature', (T.BASE, ('float32', 0))),
            ('current', (T.BASE, ('float32', 0))),
            ('charge', (T.BASE, ('float32', 0))),
            ('capacity', (T.BASE, ('float32', 0))),
            ('design_capacity', (T.BASE, ('float32', 0))),
            ('percentage', (T.BASE, ('float32', 0))),
            ('power_supply_status', (T.BASE, ('uint8', 0))),
            ('power_supply_health', (T.BASE, ('uint8', 0))),
            ('power_supply_technology', (T.BASE, ('uint8', 0))),
            ('present', (T.BASE, ('bool', 0))),
            ('cell_voltage', (T.SEQUENCE, ((T.BASE, ('float32', 0)), 0))),
            ('cell_temperature', (T.SEQUENCE, ((T.BASE, ('float32', 0)), 0))),
            ('location', (T.BASE, ('string', 0))),
            ('serial_number', (T.BASE, ('string', 0))),
        ],
    ),
    'sensor_msgs/msg/Range': (
        [
            ('ULTRASOUND', 'uint8', 0),
            ('INFRARED', 'uint8', 1),
        ],
        [
            ('header', (T.NAME, 'std_msgs/msg/Header')),
            ('radiation_type', (T.BASE, ('uint8', 0))),
            ('field_of_view', (T.BASE, ('float32', 0))),
            ('min_range', (T.BASE, ('float32', 0))),
            ('max_range', (T.BASE, ('float32', 0))),
            ('range', (T.BASE, ('float32', 0))),
            ('variance', (T.BASE, ('float32', 0))),
        ],
    ),
    'service_msgs/msg/ServiceEventInfo': (
        [
            ('REQUEST_SENT', 'uint8', 0),
            ('REQUEST_RECEIVED', 'uint8', 1),
            ('RESPONSE_SENT', 'uint8', 2),
            ('RESPONSE_RECEIVED', 'uint8', 3),
        ],
        [
            ('event_type', (T.BASE, ('uint8', 0))),
            ('stamp', (T.NAME, 'builtin_interfaces/msg/Time')),
            ('client_gid', (T.ARRAY, ((T.BASE, ('char', 0)), 16))),
            ('sequence_number', (T.BASE, ('int64', 0))),
        ],
    ),
    'type_description_interfaces/msg/Field': (
        [],
        [
            ('name', (T.BASE, ('string', 0))),
            ('type', (T.NAME, 'type_description_interfaces/msg/FieldType')),
            ('default_value', (T.BASE, ('string', 0))),
        ],
    ),
    'type_description_interfaces/msg/FieldType': (
        [
            ('FIELD_TYPE_NOT_SET', 'uint8', 0),
            ('FIELD_TYPE_NESTED_TYPE', 'uint8', 1),
            ('FIELD_TYPE_INT8', 'uint8', 2),
            ('FIELD_TYPE_UINT8', 'uint8', 3),
            ('FIELD_TYPE_INT16', 'uint8', 4),
            ('FIELD_TYPE_UINT16', 'uint8', 5),
            ('FIELD_TYPE_INT32', 'uint8', 6),
            ('FIELD_TYPE_UINT32', 'uint8', 7),
            ('FIELD_TYPE_INT64', 'uint8', 8),
            ('FIELD_TYPE_UINT64', 'uint8', 9),
            ('FIELD_TYPE_FLOAT', 'uint8', 10),
            ('FIELD_TYPE_DOUBLE', 'uint8', 11),
            ('FIELD_TYPE_LONG_DOUBLE', 'uint8', 12),
            ('FIELD_TYPE_CHAR', 'uint8', 13),
            ('FIELD_TYPE_WCHAR', 'uint8', 14),
            ('FIELD_TYPE_BOOLEAN', 'uint8', 15),
            ('FIELD_TYPE_BYTE', 'uint8', 16),
            ('FIELD_TYPE_STRING', 'uint8', 17),
            ('FIELD_TYPE_WSTRING', 'uint8', 18),
            ('FIELD_TYPE_FIXED_STRING', 'uint8', 19),
            ('FIELD_TYPE_FIXED_WSTRING', 'uint8', 20),
            ('FIELD_TYPE_BOUNDED_STRING', 'uint8', 21),
            ('FIELD_TYPE_BOUNDED_WSTRING', 'uint8', 22),
            ('FIELD_TYPE_NESTED_TYPE_ARRAY', 'uint8', 49),
            ('FIELD_TYPE_INT8_ARRAY', 'uint8', 50),
            ('FIELD_TYPE_UINT8_ARRAY', 'uint8', 51),
            ('FIELD_TYPE_INT16_ARRAY', 'uint8', 52),
            ('FIELD_TYPE_UINT16_ARRAY', 'uint8', 53),
            ('FIELD_TYPE_INT32_ARRAY', 'uint8', 54),
            ('FIELD_TYPE_UINT32_ARRAY', 'uint8', 55),
            ('FIELD_TYPE_INT64_ARRAY', 'uint8', 56),
            ('FIELD_TYPE_UINT64_ARRAY', 'uint8', 57),
            ('FIELD_TYPE_FLOAT_ARRAY', 'uint8', 58),
            ('FIELD_TYPE_DOUBLE_ARRAY', 'uint8', 59),
            ('FIELD_TYPE_LONG_DOUBLE_ARRAY', 'uint8', 60),
            ('FIELD_TYPE_CHAR_ARRAY', 'uint8', 61),
            ('FIELD_TYPE_WCHAR_ARRAY', 'uint8', 62),
            ('FIELD_TYPE_BOOLEAN_ARRAY', 'uint8', 63),
            ('FIELD_TYPE_BYTE_ARRAY', 'uint8', 64),
            ('FIELD_TYPE_STRING_ARRAY', 'uint8', 65),
            ('FIELD_TYPE_WSTRING_ARRAY', 'uint8', 66),
            ('FIELD_TYPE_FIXED_STRING_ARRAY', 'uint8', 67),
            ('FIELD_TYPE_FIXED_WSTRING_ARRAY', 'uint8', 68),
            ('FIELD_TYPE_BOUNDED_STRING_ARRAY', 'uint8', 69),
            ('FIELD_TYPE_BOUNDED_WSTRING_ARRAY', 'uint8', 70),
            ('FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE', 'uint8', 97),
            ('FIELD_TYPE_INT8_BOUNDED_SEQUENCE', 'uint8', 98),
            ('FIELD_TYPE_UINT8_BOUNDED_SEQUENCE', 'uint8', 99),
            ('FIELD_TYPE_INT16_BOUNDED_SEQUENCE', 'uint8', 100),
            ('FIELD_TYPE_UINT16_BOUNDED_SEQUENCE', 'uint8', 101),
            ('FIELD_TYPE_INT32_BOUNDED_SEQUENCE', 'uint8', 102),
            ('FIELD_TYPE_UINT32_BOUNDED_SEQUENCE', 'uint8', 103),
            ('FIELD_TYPE_INT64_BOUNDED_SEQUENCE', 'uint8', 104),
            ('FIELD_TYPE_UINT64_BOUNDED_SEQUENCE', 'uint8', 105),
            ('FIELD_TYPE_FLOAT_BOUNDED_SEQUENCE', 'uint8', 106),
            ('FIELD_TYPE_DOUBLE_BOUNDED_SEQUENCE', 'uint8', 107),
            ('FIELD_TYPE_LONG_DOUBLE_BOUNDED_SEQUENCE', 'uint8', 108),
            ('FIELD_TYPE_CHAR_BOUNDED_SEQUENCE', 'uint8', 109),
            ('FIELD_TYPE_WCHAR_BOUNDED_SEQUENCE', 'uint8', 110),
            ('FIELD_TYPE_BOOLEAN_BOUNDED_SEQUENCE', 'uint8', 111),
            ('FIELD_TYPE_BYTE_BOUNDED_SEQUENCE', 'uint8', 112),
            ('FIELD_TYPE_STRING_BOUNDED_SEQUENCE', 'uint8', 113),
            ('FIELD_TYPE_WSTRING_BOUNDED_SEQUENCE', 'uint8', 114),
            ('FIELD_TYPE_FIXED_STRING_BOUNDED_SEQUENCE', 'uint8', 115),
            ('FIELD_TYPE_FIXED_WSTRING_BOUNDED_SEQUENCE', 'uint8', 116),
            ('FIELD_TYPE_BOUNDED_STRING_BOUNDED_SEQUENCE', 'uint8', 117),
            ('FIELD_TYPE_BOUNDED_WSTRING_BOUNDED_SEQUENCE', 'uint8', 118),
            ('FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE', 'uint8', 145),
            ('FIELD_TYPE_INT8_UNBOUNDED_SEQUENCE', 'uint8', 146),
            ('FIELD_TYPE_UINT8_UNBOUNDED_SEQUENCE', 'uint8', 147),
            ('FIELD_TYPE_INT16_UNBOUNDED_SEQUENCE', 'uint8', 148),
            ('FIELD_TYPE_UINT16_UNBOUNDED_SEQUENCE', 'uint8', 149),
            ('FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE', 'uint8', 150),
            ('FIELD_TYPE_UINT32_UNBOUNDED_SEQUENCE', 'uint8', 151),
            ('FIELD_TYPE_INT64_UNBOUNDED_SEQUENCE', 'uint8', 152),
            ('FIELD_TYPE_UINT64_UNBOUNDED_SEQUENCE', 'uint8', 153),
            ('FIELD_TYPE_FLOAT_UNBOUNDED_SEQUENCE', 'uint8', 154),
            ('FIELD_TYPE_DOUBLE_UNBOUNDED_SEQUENCE', 'uint8', 155),
            ('FIELD_TYPE_LONG_DOUBLE_UNBOUNDED_SEQUENCE', 'uint8', 156),
            ('FIELD_TYPE_CHAR_UNBOUNDED_SEQUENCE', 'uint8', 157),
            ('FIELD_TYPE_WCHAR_UNBOUNDED_SEQUENCE', 'uint8', 158),
            ('FIELD_TYPE_BOOLEAN_UNBOUNDED_SEQUENCE', 'uint8', 159),
            ('FIELD_TYPE_BYTE_UNBOUNDED_SEQUENCE', 'uint8', 160),
            ('FIELD_TYPE_STRING_UNBOUNDED_SEQUENCE', 'uint8', 161),
            ('FIELD_TYPE_WSTRING_UNBOUNDED_SEQUENCE', 'uint8', 162),
            ('FIELD_TYPE_FIXED_STRING_UNBOUNDED_SEQUENCE', 'uint8', 163),
            ('FIELD_TYPE_FIXED_WSTRING_UNBOUNDED_SEQUENCE', 'uint8', 164),
            ('FIELD_TYPE_BOUNDED_STRING_UNBOUNDED_SEQUENCE', 'uint8', 165),
            ('FIELD_TYPE_BOUNDED_WSTRING_UNBOUNDED_SEQUENCE', 'uint8', 166),
        ],
        [
            ('type_id', (T.BASE, ('uint8', 0))),
            ('capacity', (T.BASE, ('uint64', 0))),
            ('string_capacity', (T.BASE, ('uint64', 0))),
            ('nested_type_name', (T.BASE, ('string', 255))),
        ],
    ),
    'type_description_interfaces/msg/IndividualTypeDescription': (
        [],
        [
            ('type_name', (T.BASE, ('string', 255))),
            ('fields', (T.SEQUENCE, ((T.NAME, 'type_description_interfaces/msg/Field'), 0))),
        ],
    ),
    'type_description_interfaces/msg/KeyValue': (
        [],
        [
            ('key', (T.BASE, ('string', 0))),
            ('value', (T.BASE, ('string', 0))),
        ],
    ),
    'type_description_interfaces/msg/TypeDescription': (
        [],
        [
            (
                'type_description',
                (T.NAME, 'type_description_interfaces/msg/IndividualTypeDescription'),
            ),
            (
                'referenced_type_descriptions',
                (
                    T.SEQUENCE,
                    ((T.NAME, 'type_description_interfaces/msg/IndividualTypeDescription'), 0),
                ),
            ),
        ],
    ),
    'type_description_interfaces/msg/TypeSource': (
        [],
        [
            ('type_name', (T.BASE, ('string', 0))),
            ('encoding', (T.BASE, ('string', 0))),
            ('raw_file_contents', (T.BASE, ('string', 0))),
        ],
    ),
}
