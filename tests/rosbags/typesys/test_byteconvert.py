# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Byte Stream Conversion Tests."""

from __future__ import annotations

from rosbags.typesys import Stores, get_types_from_msg, get_typestore

STATIC_16_64 = """
uint16 u16
uint64 u64
"""

DYNAMIC_S_64 = """
string s
uint64 u64
"""


def test_ros1_to_cdr() -> None:
    """Test ROS1 to CDR conversion."""
    store = get_typestore(Stores.LATEST)

    msgtype = 'test_msgs/msg/static_16_64'
    store.register(dict(get_types_from_msg(STATIC_16_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = b'\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    assert store.ros1_to_cdr(msg_ros, msgtype) == msg_cdr
    assert store.serialize_cdr(store.deserialize_ros1(msg_ros, msgtype), msgtype) == msg_cdr

    msgtype = 'test_msgs/msg/dynamic_s_64'
    store.register(dict(get_types_from_msg(DYNAMIC_S_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00X\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = b'\x00\x01\x00\x00\x02\x00\x00\x00X\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    assert store.ros1_to_cdr(msg_ros, msgtype) == msg_cdr
    assert store.serialize_cdr(store.deserialize_ros1(msg_ros, msgtype), msgtype) == msg_cdr


def test_cdr_to_ros1() -> None:
    """Test CDR to ROS1 conversion."""
    store = get_typestore(Stores.LATEST)

    msgtype = 'test_msgs/msg/static_16_64'
    store.register(dict(get_types_from_msg(STATIC_16_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = b'\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    assert store.cdr_to_ros1(msg_cdr, msgtype) == msg_ros
    assert store.serialize_ros1(store.deserialize_cdr(msg_cdr, msgtype), msgtype) == msg_ros

    msgtype = 'test_msgs/msg/dynamic_s_64'
    store.register(dict(get_types_from_msg(DYNAMIC_S_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00X\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = b'\x00\x01\x00\x00\x02\x00\x00\x00X\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
    assert store.cdr_to_ros1(msg_cdr, msgtype) == msg_ros
    assert store.serialize_ros1(store.deserialize_cdr(msg_cdr, msgtype), msgtype) == msg_ros

    Header = store.types['std_msgs/msg/Header']  # noqa: N806
    Time = store.types['builtin_interfaces/msg/Time']  # noqa: N806

    header = Header(stamp=Time(42, 666), frame_id='frame')
    msg_ros = store.cdr_to_ros1(
        store.serialize_cdr(header, 'std_msgs/msg/Header'), 'std_msgs/msg/Header'
    ).tobytes()
    assert msg_ros == b'\x00\x00\x00\x00*\x00\x00\x00\x9a\x02\x00\x00\x05\x00\x00\x00frame'
