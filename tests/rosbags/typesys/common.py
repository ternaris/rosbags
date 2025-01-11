# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Common Test Content."""

import numpy as np

from rosbags.typesys.stores.latest import (
    builtin_interfaces__msg__Time as Time,
    geometry_msgs__msg__Point32 as Point32,
    geometry_msgs__msg__Polygon as Polygon,
    geometry_msgs__msg__Vector3 as Vector3,
    sensor_msgs__msg__MagneticField as MagneticField,
    std_msgs__msg__Header as Header,
    trajectory_msgs__msg__JointTrajectory as JointTrajectory,
)

MSG_POLY = (
    (
        b'\x00\x01\x00\x00'  # header
        b'\x02\x00\x00\x00'  # number of points = 2
        b'\x00\x00\x80\x3f'  # x = 1
        b'\x00\x00\x00\x40'  # y = 2
        b'\x00\x00\x40\x40'  # z = 3
        b'\x00\x00\xa0\x3f'  # x = 1.25
        b'\x00\x00\x10\x40'  # y = 2.25
        b'\x00\x00\x50\x40'  # z = 3.25
    ),
    'geometry_msgs/msg/Polygon',
    True,
)

MSG_MAGN = (
    (
        b'\x00\x01\x00\x00'  # header
        b'\xc4\x02\x00\x00\x00\x01\x00\x00'  # timestamp = 708s 256ns
        b'\x06\x00\x00\x00foo42\x00'  # frameid 'foo42'
        b'\x00\x00\x00\x00\x00\x00'  # padding
        b'\x00\x00\x00\x00\x00\x00\x60\x40'  # x = 128
        b'\x00\x00\x00\x00\x00\x00\x60\x40'  # y = 128
        b'\x00\x00\x00\x00\x00\x00\x60\x40'  # z = 128
        b'\x00\x00\x00\x00\x00\x00\xf0\x3f'  # covariance matrix = 3x3 diag
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    ),
    'sensor_msgs/msg/MagneticField',
    True,
)

MSG_MAGN_BIG = (
    (
        b'\x00\x00\x00\x00'  # header
        b'\x00\x00\x02\xc4\x00\x00\x01\x00'  # timestamp = 708s 256ns
        b'\x00\x00\x00\x06foo42\x00'  # frameid 'foo42'
        b'\x00\x00\x00\x00\x00\x00'  # padding
        b'\x40\x60\x00\x00\x00\x00\x00\x00'  # x = 128
        b'\x40\x60\x00\x00\x00\x00\x00\x00'  # y = 128
        b'\x40\x60\x00\x00\x00\x00\x00\x00'  # z = 128
        b'\x3f\xf0\x00\x00\x00\x00\x00\x00'  # covariance matrix = 3x3 diag
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00'  # garbage
    ),
    'sensor_msgs/msg/MagneticField',
    False,
)

MSG_JOINT = (
    (
        b'\x00\x01\x00\x00'  # header
        b'\xc4\x02\x00\x00\x00\x01\x00\x00'  # timestamp = 708s 256ns
        b'\x04\x00\x00\x00bar\x00'  # frameid 'bar'
        b'\x02\x00\x00\x00'  # number of strings
        b'\x02\x00\x00\x00a\x00'  # string 'a'
        b'\x00\x00'  # padding
        b'\x02\x00\x00\x00b\x00'  # string 'b'
        b'\x00\x00'  # padding
        b'\x00\x00\x00\x00'  # number of points
        b'\x00\x00\x00'  # garbage
    ),
    'trajectory_msgs/msg/JointTrajectory',
    True,
)

POLY = Polygon([Point32(1, 2, 3), Point32(1.25, 2.25, 3.25)])

MAGN = MagneticField(
    Header(Time(708, 256), 'foo42'),
    Vector3(128, 128, 128),
    np.eye(3, dtype=np.float64).reshape(-1),
)

JOINT = JointTrajectory(
    Header(Time(708, 256), 'bar'),
    ['a', 'b'],
    [],
)

MESSAGES = [MSG_POLY, MSG_MAGN, MSG_MAGN_BIG, MSG_JOINT]
