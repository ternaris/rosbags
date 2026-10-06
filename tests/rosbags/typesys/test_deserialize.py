# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deserialization Tests."""

from __future__ import annotations

import struct
from dataclasses import asdict
from typing import cast

import pytest

from rosbags.serde import SerdeError
from rosbags.typesys import Stores, get_types_from_msg, get_typestore
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
    msg_ros1_dct = cast('dict[str, dict[str, str | int]]', asdict(msg_ros1))
    assert msg_ros1_dct['header'].pop('seq') == 0
    assert msg_ros1_dct == asdict(MAGN)

    msg_ros1 = ros1_store.deserialize_ros1(ros2_store.cdr_to_ros1(*MSG_JOINT[:2]), MSG_JOINT[1])
    assert isinstance(msg_ros1, JointTrajectory)
    msg_ros1_dct = asdict(msg_ros1)
    assert msg_ros1_dct['header'].pop('seq') == 0
    assert msg_ros1_dct == asdict(JOINT)


@pytest.mark.parametrize('field', ['string data', 'string[1] data', 'string[] data'])
@pytest.mark.parametrize('size', [0, 100, 2**32 - 1])
@pytest.mark.parametrize('cdr', [False, True])
def test_invalid_string_lengths(field: str, size: int, *, cdr: bool) -> None:
    """Test invalid string lengths are rejected."""
    if not cdr and size == 0:
        return
    store = get_typestore(Stores.EMPTY)
    name = 'x/msg/X'
    store.register(get_types_from_msg(field, name))
    data = (struct.pack('<I', 1) if '[]' in field else b'') + struct.pack('<I', size) + b'A'
    if cdr:
        data = b'\x00\x01\x00\x00' + data
    with pytest.raises(SerdeError, match='string length'):
        _ = store.deserialize_cdr(data, name) if cdr else store.deserialize_ros1(data, name)
    with pytest.raises(SerdeError, match='string length'):
        _ = store.cdr_to_ros1(data, name) if cdr else store.ros1_to_cdr(data, name)


@pytest.mark.parametrize('field', ['uint8[] data', 'string[] data', 'x/Child[] data'])
@pytest.mark.parametrize('cdr', [False, True])
def test_invalid_sequence_counts(field: str, *, cdr: bool) -> None:
    """Test large sequence counts raise error."""
    store = get_typestore(Stores.EMPTY)
    name = 'x/msg/X'
    store.register(
        {**get_types_from_msg(field, name), **get_types_from_msg('uint8 value', 'x/msg/Child')}
    )
    store.max_sequence_length = 100
    data = struct.pack('<I', 2**32 - 1)
    if cdr:
        data = b'\x00\x01\x00\x00' + data
    with pytest.raises(SerdeError, match='sequence length'):
        _ = store.deserialize_cdr(data, name) if cdr else store.deserialize_ros1(data, name)


@pytest.mark.parametrize('header', [b'', b'\x00', b'\x00\x01', b'\x00\x03\x00\x00'])
def test_invalid_cdr_encapsulation(header: bytes) -> None:
    """Test invalid cdr encapsulation throws error."""
    store = get_typestore(Stores.LATEST)
    with pytest.raises(SerdeError, match='encapsulation'):
        _ = store.deserialize_cdr(header, 'std_msgs/msg/Int8')


def test_missing_string_terminator() -> None:
    """Test missing string terminator raises error."""
    store = get_typestore(Stores.LATEST)
    raw = b'\x00\x01\x00\x00' + struct.pack('<I', 2) + b'AB'
    with pytest.raises(SerdeError, match='terminator'):
        _ = store.deserialize_cdr(raw, 'std_msgs/msg/String')
    with pytest.raises(SerdeError, match='terminator'):
        _ = store.cdr_to_ros1(raw, 'std_msgs/msg/String')


@pytest.mark.parametrize('cdr', [False, True])
@pytest.mark.parametrize(
    ('typename', 'payload'),
    [('std_msgs/msg/Int32', b'\x01'), ('std_msgs/msg/String', struct.pack('<I', 2) + b'\xff\x00')],
)
def test_deserialization_errors_cause_serdeerrors(
    typename: str,
    payload: bytes,
    *,
    cdr: bool,
) -> None:
    """Test truncated numbers and invalid UTF-8 retain their error cause."""
    store = get_typestore(Stores.LATEST)
    deserialize = store.deserialize_cdr if cdr else store.deserialize_ros1
    raw = b'\x00\x01\x00\x00' + payload if cdr else payload
    with pytest.raises(SerdeError, match='Could not deserialize') as exc:
        _ = deserialize(raw, typename)
    assert isinstance(exc.value.__cause__, (ValueError, struct.error))


@pytest.mark.parametrize('cdr', [False, True])
def test_deserialization_rejects_trailing_data(*, cdr: bool) -> None:
    """Test deserialization rejects trailing data."""
    store = get_typestore(Stores.LATEST)
    typename = 'std_msgs/msg/Int8'
    if cdr:
        raw = b'\x00\x01\x00\x00\x2a'
        for padding in range(4):
            message = store.deserialize_cdr(raw + bytes(padding), typename)
            assert store.serialize_cdr(message, typename).tobytes() == raw
        with pytest.raises(SerdeError, match='CDR message size mismatch'):
            _ = store.deserialize_cdr(raw + bytes(4), typename)
    else:
        with pytest.raises(SerdeError, match='ROS1 message size mismatch'):
            _ = store.deserialize_ros1(b'\x2a\x00', typename)
