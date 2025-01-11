# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deprecated Interfaces Tests."""

import pytest

from rosbags.serde import (
    cdr_to_ros1,
    deserialize_cdr,
    deserialize_ros1,
    ros1_to_cdr,
    serialize_cdr,
    serialize_ros1,
)
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.latest import std_msgs__msg__Empty as Empty


def test_deprecated_cdr_to_ros1() -> None:
    """Test cdr_to_ros1 warns about deprecation."""
    with pytest.deprecated_call():
        _ = cdr_to_ros1(b'\x00\x01\x00\x00\x00', 'std_msgs/msg/Empty')
        _ = cdr_to_ros1(b'\x00\x01\x00\x00\x00', 'std_msgs/msg/Empty', get_typestore(Stores.LATEST))


def test_deprecated_deserialize_cdr() -> None:
    """Test deserialize_cdr warns about deprecation."""
    with pytest.deprecated_call():
        _ = deserialize_cdr(b'\x00\x01\x00\x00\x00', 'std_msgs/msg/Empty')
        _ = deserialize_cdr(
            b'\x00\x01\x00\x00\x00', 'std_msgs/msg/Empty', get_typestore(Stores.LATEST)
        )


def test_deprecated_deserialize_ros1() -> None:
    """Test deserialize_ros1 warns about deprecation."""
    with pytest.deprecated_call():
        _ = deserialize_ros1(b'', 'std_msgs/msg/Empty')
        _ = deserialize_ros1(b'', 'std_msgs/msg/Empty', get_typestore(Stores.LATEST))


def test_deprecated_ros1_to_cdr() -> None:
    """Test ros1_to_cdr warns about deprecation."""
    with pytest.deprecated_call():
        _ = ros1_to_cdr(b'', 'std_msgs/msg/Empty')
        _ = ros1_to_cdr(b'', 'std_msgs/msg/Empty', get_typestore(Stores.LATEST))


def test_deprecated_serialize_cdr() -> None:
    """Test serialize_cdr warns about deprecation."""
    with pytest.deprecated_call():
        _ = serialize_cdr(Empty(), 'std_msgs/msg/Empty')
        _ = serialize_cdr(Empty(), 'std_msgs/msg/Empty', typestore=get_typestore(Stores.LATEST))


def test_deprecated_serialize_ros1() -> None:
    """Test serialize_ros1 warns about deprecation."""
    with pytest.deprecated_call():
        _ = serialize_ros1(Empty(), 'std_msgs/msg/Empty')
        _ = serialize_ros1(Empty(), 'std_msgs/msg/Empty', typestore=get_typestore(Stores.LATEST))
