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

from .ros2_eloquent import *

if TYPE_CHECKING:
    from typing import ClassVar

    import numpy as np


FIELDDEFS = FIELDDEFS.copy()
del FIELDDEFS['rcl_interfaces/msg/IntraProcessMessage']
del rcl_interfaces__msg__IntraProcessMessage


@dataclass
class libstatistics_collector__msg__DummyMessage:
    """Class for libstatistics_collector/msg/DummyMessage."""

    header: std_msgs__msg__Header
    __msgtype__: ClassVar[str] = 'libstatistics_collector/msg/DummyMessage'


@dataclass
class rmw_dds_common__msg__Gid:
    """Class for rmw_dds_common/msg/Gid."""

    data: np.ndarray[None, np.dtype[np.uint8]]
    __msgtype__: ClassVar[str] = 'rmw_dds_common/msg/Gid'


@dataclass
class rmw_dds_common__msg__NodeEntitiesInfo:
    """Class for rmw_dds_common/msg/NodeEntitiesInfo."""

    node_namespace: str
    node_name: str
    reader_gid_seq: list[rmw_dds_common__msg__Gid]
    writer_gid_seq: list[rmw_dds_common__msg__Gid]
    __msgtype__: ClassVar[str] = 'rmw_dds_common/msg/NodeEntitiesInfo'


@dataclass
class rmw_dds_common__msg__ParticipantEntitiesInfo:
    """Class for rmw_dds_common/msg/ParticipantEntitiesInfo."""

    gid: rmw_dds_common__msg__Gid
    node_entities_info_seq: list[rmw_dds_common__msg__NodeEntitiesInfo]
    __msgtype__: ClassVar[str] = 'rmw_dds_common/msg/ParticipantEntitiesInfo'


@dataclass
class statistics_msgs__msg__MetricsMessage:
    """Class for statistics_msgs/msg/MetricsMessage."""

    measurement_source_name: str
    metrics_source: str
    unit: str
    window_start: builtin_interfaces__msg__Time
    window_stop: builtin_interfaces__msg__Time
    statistics: list[statistics_msgs__msg__StatisticDataPoint]
    __msgtype__: ClassVar[str] = 'statistics_msgs/msg/MetricsMessage'


@dataclass
class statistics_msgs__msg__StatisticDataPoint:
    """Class for statistics_msgs/msg/StatisticDataPoint."""

    data_type: int
    data: float
    __msgtype__: ClassVar[str] = 'statistics_msgs/msg/StatisticDataPoint'


@dataclass
class statistics_msgs__msg__StatisticDataType:
    """Class for statistics_msgs/msg/StatisticDataType."""

    structure_needs_at_least_one_member: int = 0
    STATISTICS_DATA_TYPE_UNINITIALIZED: ClassVar[int] = 0
    STATISTICS_DATA_TYPE_AVERAGE: ClassVar[int] = 1
    STATISTICS_DATA_TYPE_MINIMUM: ClassVar[int] = 2
    STATISTICS_DATA_TYPE_MAXIMUM: ClassVar[int] = 3
    STATISTICS_DATA_TYPE_STDDEV: ClassVar[int] = 4
    STATISTICS_DATA_TYPE_SAMPLE_COUNT: ClassVar[int] = 5
    __msgtype__: ClassVar[str] = 'statistics_msgs/msg/StatisticDataType'


@dataclass
class visualization_msgs__msg__ImageMarker:  # type: ignore[no-redef]
    """Class for visualization_msgs/msg/ImageMarker."""

    header: std_msgs__msg__Header
    ns: str
    id: int
    type: int
    action: int
    position: geometry_msgs__msg__Point
    scale: float
    outline_color: std_msgs__msg__ColorRGBA
    filled: int
    fill_color: std_msgs__msg__ColorRGBA
    lifetime: builtin_interfaces__msg__Duration
    points: list[geometry_msgs__msg__Point]
    outline_colors: list[std_msgs__msg__ColorRGBA]
    CIRCLE: ClassVar[int] = 0
    LINE_STRIP: ClassVar[int] = 1
    LINE_LIST: ClassVar[int] = 2
    POLYGON: ClassVar[int] = 3
    POINTS: ClassVar[int] = 4
    ADD: ClassVar[int] = 0
    REMOVE: ClassVar[int] = 1
    __msgtype__: ClassVar[str] = 'visualization_msgs/msg/ImageMarker'


@dataclass
class visualization_msgs__msg__Marker:  # type: ignore[no-redef]
    """Class for visualization_msgs/msg/Marker."""

    header: std_msgs__msg__Header
    ns: str
    id: int
    type: int
    action: int
    pose: geometry_msgs__msg__Pose
    scale: geometry_msgs__msg__Vector3
    color: std_msgs__msg__ColorRGBA
    lifetime: builtin_interfaces__msg__Duration
    frame_locked: bool
    points: list[geometry_msgs__msg__Point]
    colors: list[std_msgs__msg__ColorRGBA]
    text: str
    mesh_resource: str
    mesh_use_embedded_materials: bool
    ARROW: ClassVar[int] = 0
    CUBE: ClassVar[int] = 1
    SPHERE: ClassVar[int] = 2
    CYLINDER: ClassVar[int] = 3
    LINE_STRIP: ClassVar[int] = 4
    LINE_LIST: ClassVar[int] = 5
    CUBE_LIST: ClassVar[int] = 6
    SPHERE_LIST: ClassVar[int] = 7
    POINTS: ClassVar[int] = 8
    TEXT_VIEW_FACING: ClassVar[int] = 9
    MESH_RESOURCE: ClassVar[int] = 10
    TRIANGLE_LIST: ClassVar[int] = 11
    ADD: ClassVar[int] = 0
    MODIFY: ClassVar[int] = 0
    DELETE: ClassVar[int] = 2
    DELETEALL: ClassVar[int] = 3
    __msgtype__: ClassVar[str] = 'visualization_msgs/msg/Marker'


FIELDDEFS = {
    **FIELDDEFS,
    'libstatistics_collector/msg/DummyMessage': (
        [],
        [
            ('header', (T.NAME, 'std_msgs/msg/Header')),
        ],
    ),
    'rmw_dds_common/msg/Gid': (
        [],
        [
            ('data', (T.ARRAY, ((T.BASE, ('char', 0)), 24))),
        ],
    ),
    'rmw_dds_common/msg/NodeEntitiesInfo': (
        [],
        [
            ('node_namespace', (T.BASE, ('string', 256))),
            ('node_name', (T.BASE, ('string', 256))),
            ('reader_gid_seq', (T.SEQUENCE, ((T.NAME, 'rmw_dds_common/msg/Gid'), 0))),
            ('writer_gid_seq', (T.SEQUENCE, ((T.NAME, 'rmw_dds_common/msg/Gid'), 0))),
        ],
    ),
    'rmw_dds_common/msg/ParticipantEntitiesInfo': (
        [],
        [
            ('gid', (T.NAME, 'rmw_dds_common/msg/Gid')),
            (
                'node_entities_info_seq',
                (T.SEQUENCE, ((T.NAME, 'rmw_dds_common/msg/NodeEntitiesInfo'), 0)),
            ),
        ],
    ),
    'statistics_msgs/msg/MetricsMessage': (
        [],
        [
            ('measurement_source_name', (T.BASE, ('string', 0))),
            ('metrics_source', (T.BASE, ('string', 0))),
            ('unit', (T.BASE, ('string', 0))),
            ('window_start', (T.NAME, 'builtin_interfaces/msg/Time')),
            ('window_stop', (T.NAME, 'builtin_interfaces/msg/Time')),
            ('statistics', (T.SEQUENCE, ((T.NAME, 'statistics_msgs/msg/StatisticDataPoint'), 0))),
        ],
    ),
    'statistics_msgs/msg/StatisticDataPoint': (
        [],
        [
            ('data_type', (T.BASE, ('uint8', 0))),
            ('data', (T.BASE, ('float64', 0))),
        ],
    ),
    'statistics_msgs/msg/StatisticDataType': (
        [
            ('STATISTICS_DATA_TYPE_UNINITIALIZED', 'uint8', 0),
            ('STATISTICS_DATA_TYPE_AVERAGE', 'uint8', 1),
            ('STATISTICS_DATA_TYPE_MINIMUM', 'uint8', 2),
            ('STATISTICS_DATA_TYPE_MAXIMUM', 'uint8', 3),
            ('STATISTICS_DATA_TYPE_STDDEV', 'uint8', 4),
            ('STATISTICS_DATA_TYPE_SAMPLE_COUNT', 'uint8', 5),
        ],
        [
            ('structure_needs_at_least_one_member', (T.BASE, ('uint8', 0))),
        ],
    ),
    'visualization_msgs/msg/ImageMarker': (
        [
            ('CIRCLE', 'int32', 0),
            ('LINE_STRIP', 'int32', 1),
            ('LINE_LIST', 'int32', 2),
            ('POLYGON', 'int32', 3),
            ('POINTS', 'int32', 4),
            ('ADD', 'int32', 0),
            ('REMOVE', 'int32', 1),
        ],
        [
            ('header', (T.NAME, 'std_msgs/msg/Header')),
            ('ns', (T.BASE, ('string', 0))),
            ('id', (T.BASE, ('int32', 0))),
            ('type', (T.BASE, ('int32', 0))),
            ('action', (T.BASE, ('int32', 0))),
            ('position', (T.NAME, 'geometry_msgs/msg/Point')),
            ('scale', (T.BASE, ('float32', 0))),
            ('outline_color', (T.NAME, 'std_msgs/msg/ColorRGBA')),
            ('filled', (T.BASE, ('uint8', 0))),
            ('fill_color', (T.NAME, 'std_msgs/msg/ColorRGBA')),
            ('lifetime', (T.NAME, 'builtin_interfaces/msg/Duration')),
            ('points', (T.SEQUENCE, ((T.NAME, 'geometry_msgs/msg/Point'), 0))),
            ('outline_colors', (T.SEQUENCE, ((T.NAME, 'std_msgs/msg/ColorRGBA'), 0))),
        ],
    ),
    'visualization_msgs/msg/Marker': (
        [
            ('ARROW', 'int32', 0),
            ('CUBE', 'int32', 1),
            ('SPHERE', 'int32', 2),
            ('CYLINDER', 'int32', 3),
            ('LINE_STRIP', 'int32', 4),
            ('LINE_LIST', 'int32', 5),
            ('CUBE_LIST', 'int32', 6),
            ('SPHERE_LIST', 'int32', 7),
            ('POINTS', 'int32', 8),
            ('TEXT_VIEW_FACING', 'int32', 9),
            ('MESH_RESOURCE', 'int32', 10),
            ('TRIANGLE_LIST', 'int32', 11),
            ('ADD', 'int32', 0),
            ('MODIFY', 'int32', 0),
            ('DELETE', 'int32', 2),
            ('DELETEALL', 'int32', 3),
        ],
        [
            ('header', (T.NAME, 'std_msgs/msg/Header')),
            ('ns', (T.BASE, ('string', 0))),
            ('id', (T.BASE, ('int32', 0))),
            ('type', (T.BASE, ('int32', 0))),
            ('action', (T.BASE, ('int32', 0))),
            ('pose', (T.NAME, 'geometry_msgs/msg/Pose')),
            ('scale', (T.NAME, 'geometry_msgs/msg/Vector3')),
            ('color', (T.NAME, 'std_msgs/msg/ColorRGBA')),
            ('lifetime', (T.NAME, 'builtin_interfaces/msg/Duration')),
            ('frame_locked', (T.BASE, ('bool', 0))),
            ('points', (T.SEQUENCE, ((T.NAME, 'geometry_msgs/msg/Point'), 0))),
            ('colors', (T.SEQUENCE, ((T.NAME, 'std_msgs/msg/ColorRGBA'), 0))),
            ('text', (T.BASE, ('string', 0))),
            ('mesh_resource', (T.BASE, ('string', 0))),
            ('mesh_use_embedded_materials', (T.BASE, ('bool', 0))),
        ],
    ),
}
