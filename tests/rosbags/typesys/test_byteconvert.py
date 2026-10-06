# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Byte Stream Conversion Tests."""

from __future__ import annotations

import struct

import pytest

from rosbags.serde import SerdeError
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


@pytest.mark.parametrize('cdr', [False, True])
def test_struct_errors_cause_serdeerrors(*, cdr: bool) -> None:
    """Test struct.error is converted to SerdeError."""
    store = get_typestore(Stores.LATEST)
    convert = store.cdr_to_ros1 if cdr else store.ros1_to_cdr
    raw = b'\x00\x01\x00\x00\x01' if cdr else b'\x01'
    with pytest.raises(SerdeError, match='Could not convert') as exc:
        _ = convert(raw, 'std_msgs/msg/String')
    assert isinstance(exc.value.__cause__, struct.error)


@pytest.mark.parametrize('cdr', [False, True])
def test_conversion_rejects_trailing_data(*, cdr: bool) -> None:
    """Test conversion rejects trailing data."""
    store = get_typestore(Stores.LATEST)
    typename = 'std_msgs/msg/Int8'
    if cdr:
        raw = b'\x00\x01\x00\x00\x2a'
        for padding in range(4):
            assert store.cdr_to_ros1(raw + bytes(padding), typename).tobytes() == b'\x2a'
        with pytest.raises(SerdeError, match='CDR message size mismatch'):
            _ = store.cdr_to_ros1(raw + bytes(4), typename)
    else:
        with pytest.raises(SerdeError, match='ROS1 message size mismatch'):
            _ = store.ros1_to_cdr(b'\x2a\x00', typename)


@pytest.mark.parametrize(
    'header',
    [b'', b'\x00', b'\x00\x01', b'\x00\x00\x00\x00', b'\x00\x03\x00\x00'],
)
def test_conversion_rejects_invalid_cdr_header(header: bytes) -> None:
    """Test conversion rejects invalid cdr header."""
    with pytest.raises(SerdeError, match='little-endian CDR encapsulation'):
        _ = get_typestore(Stores.LATEST).cdr_to_ros1(header, 'std_msgs/msg/Int8')
