# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deserialization Tests."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.ros1_noetic import (
    geometry_msgs__msg__Polygon as Polygon,
    sensor_msgs__msg__MagneticField as MagneticField,
    trajectory_msgs__msg__JointTrajectory as JointTrajectory,
)

from .cdr import deserialize
from .common import JOINT, MAGN, MSG_JOINT, MSG_MAGN, MSG_MAGN_BIG, MSG_POLY, POLY


@pytest.mark.usefixtures('_comparable')
def test_reference_deserializer() -> None:
    """Test reference deserializer on hand crafted bitstreams."""
    ros2_store = get_typestore(Stores.LATEST)

    assert deserialize(*MSG_POLY[:2], ros2_store) == POLY
    assert deserialize(*MSG_MAGN[:2], ros2_store) == MAGN
    assert deserialize(*MSG_MAGN_BIG[:2], ros2_store) == MAGN
    assert deserialize(*MSG_JOINT[:2], ros2_store) == JOINT


@pytest.mark.usefixtures('_comparable')
def test_cdr_deserializer() -> None:
    """Test cdr deserializer decodes messages."""
    ros2_store = get_typestore(Stores.LATEST)

    assert ros2_store.deserialize_cdr(*MSG_POLY[:2]) == POLY
    assert ros2_store.deserialize_cdr(*MSG_MAGN[:2]) == MAGN
    assert ros2_store.deserialize_cdr(*MSG_MAGN_BIG[:2]) == MAGN
    assert ros2_store.deserialize_cdr(*MSG_JOINT[:2]) == JOINT


@pytest.mark.usefixtures('_comparable')
def test_ros1_deserializer() -> None:
    """Test ros1 deserializer decodes messages."""
    ros2_store = get_typestore(Stores.LATEST)
    ros1_store = get_typestore(Stores.ROS1_NOETIC)

    msg_ros1 = ros1_store.deserialize_ros1(ros2_store.cdr_to_ros1(*MSG_POLY[:2]), MSG_POLY[1])
    assert isinstance(msg_ros1, Polygon)
    assert asdict(msg_ros1) == asdict(POLY)

    msg_ros1 = ros1_store.deserialize_ros1(ros2_store.cdr_to_ros1(*MSG_MAGN[:2]), MSG_MAGN[1])
    assert isinstance(msg_ros1, MagneticField)
    msg_ros1_dct: dict[str, dict[str, str | int]] = asdict(msg_ros1)
    assert msg_ros1_dct['header'].pop('seq') == 0
    assert msg_ros1_dct == asdict(MAGN)

    msg_ros1 = ros1_store.deserialize_ros1(ros2_store.cdr_to_ros1(*MSG_JOINT[:2]), MSG_JOINT[1])
    assert isinstance(msg_ros1, JointTrajectory)
    msg_ros1_dct = asdict(msg_ros1)
    assert msg_ros1_dct['header'].pop('seq') == 0
    assert msg_ros1_dct == asdict(JOINT)
