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

from .ros2_galactic import *

if TYPE_CHECKING:
    from typing import ClassVar

    import numpy as np


FIELDDEFS = FIELDDEFS.copy()
del FIELDDEFS['libstatistics_collector/msg/DummyMessage']
del libstatistics_collector__msg__DummyMessage


@dataclass
class rosbag2_interfaces__msg__ReadSplitEvent:
    """Class for rosbag2_interfaces/msg/ReadSplitEvent."""

    closed_file: str
    opened_file: str
    __msgtype__: ClassVar[str] = 'rosbag2_interfaces/msg/ReadSplitEvent'


@dataclass
class rosbag2_interfaces__msg__WriteSplitEvent:
    """Class for rosbag2_interfaces/msg/WriteSplitEvent."""

    closed_file: str
    opened_file: str
    __msgtype__: ClassVar[str] = 'rosbag2_interfaces/msg/WriteSplitEvent'


@dataclass
class shape_msgs__msg__SolidPrimitive:  # type: ignore[no-redef]
    """Class for shape_msgs/msg/SolidPrimitive."""

    type: int
    dimensions: np.ndarray[None, np.dtype[np.float64]]
    polygon: geometry_msgs__msg__Polygon
    BOX: ClassVar[int] = 1
    SPHERE: ClassVar[int] = 2
    CYLINDER: ClassVar[int] = 3
    CONE: ClassVar[int] = 4
    PRISM: ClassVar[int] = 5
    BOX_X: ClassVar[int] = 0
    BOX_Y: ClassVar[int] = 1
    BOX_Z: ClassVar[int] = 2
    SPHERE_RADIUS: ClassVar[int] = 0
    CYLINDER_HEIGHT: ClassVar[int] = 0
    CYLINDER_RADIUS: ClassVar[int] = 1
    CONE_HEIGHT: ClassVar[int] = 0
    CONE_RADIUS: ClassVar[int] = 1
    PRISM_HEIGHT: ClassVar[int] = 0
    __msgtype__: ClassVar[str] = 'shape_msgs/msg/SolidPrimitive'


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
    texture_resource: str
    texture: sensor_msgs__msg__CompressedImage
    uv_coordinates: list[visualization_msgs__msg__UVCoordinate]
    text: str
    mesh_resource: str
    mesh_file: visualization_msgs__msg__MeshFile
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


@dataclass
class visualization_msgs__msg__MeshFile:
    """Class for visualization_msgs/msg/MeshFile."""

    filename: str
    data: np.ndarray[None, np.dtype[np.uint8]]
    __msgtype__: ClassVar[str] = 'visualization_msgs/msg/MeshFile'


@dataclass
class visualization_msgs__msg__UVCoordinate:
    """Class for visualization_msgs/msg/UVCoordinate."""

    u: float
    v: float
    __msgtype__: ClassVar[str] = 'visualization_msgs/msg/UVCoordinate'


FIELDDEFS = {
    **FIELDDEFS,
    'rosbag2_interfaces/msg/ReadSplitEvent': (
        [],
        [
            ('closed_file', (T.BASE, ('string', 0))),
            ('opened_file', (T.BASE, ('string', 0))),
        ],
    ),
    'rosbag2_interfaces/msg/WriteSplitEvent': (
        [],
        [
            ('closed_file', (T.BASE, ('string', 0))),
            ('opened_file', (T.BASE, ('string', 0))),
        ],
    ),
    'shape_msgs/msg/SolidPrimitive': (
        [
            ('BOX', 'uint8', 1),
            ('SPHERE', 'uint8', 2),
            ('CYLINDER', 'uint8', 3),
            ('CONE', 'uint8', 4),
            ('PRISM', 'uint8', 5),
            ('BOX_X', 'uint8', 0),
            ('BOX_Y', 'uint8', 1),
            ('BOX_Z', 'uint8', 2),
            ('SPHERE_RADIUS', 'uint8', 0),
            ('CYLINDER_HEIGHT', 'uint8', 0),
            ('CYLINDER_RADIUS', 'uint8', 1),
            ('CONE_HEIGHT', 'uint8', 0),
            ('CONE_RADIUS', 'uint8', 1),
            ('PRISM_HEIGHT', 'uint8', 0),
        ],
        [
            ('type', (T.BASE, ('uint8', 0))),
            ('dimensions', (T.SEQUENCE, ((T.BASE, ('float64', 0)), 3))),
            ('polygon', (T.NAME, 'geometry_msgs/msg/Polygon')),
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
            ('texture_resource', (T.BASE, ('string', 0))),
            ('texture', (T.NAME, 'sensor_msgs/msg/CompressedImage')),
            ('uv_coordinates', (T.SEQUENCE, ((T.NAME, 'visualization_msgs/msg/UVCoordinate'), 0))),
            ('text', (T.BASE, ('string', 0))),
            ('mesh_resource', (T.BASE, ('string', 0))),
            ('mesh_file', (T.NAME, 'visualization_msgs/msg/MeshFile')),
            ('mesh_use_embedded_materials', (T.BASE, ('bool', 0))),
        ],
    ),
    'visualization_msgs/msg/MeshFile': (
        [],
        [
            ('filename', (T.BASE, ('string', 0))),
            ('data', (T.SEQUENCE, ((T.BASE, ('uint8', 0)), 0))),
        ],
    ),
    'visualization_msgs/msg/UVCoordinate': (
        [],
        [
            ('u', (T.BASE, ('float32', 0))),
            ('v', (T.BASE, ('float32', 0))),
        ],
    ),
}
