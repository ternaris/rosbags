# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Serialization Tests."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from rosbags.serde import SerdeError
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

from .cdr import serialize
from .common import JOINT, MAGN, MSG_JOINT, MSG_MAGN, MSG_MAGN_BIG, MSG_POLY, POLY


def test_reference_serializer() -> None:
    """Test reference serializer on hand crafted bitstreams."""
    ros2_store = get_typestore(Stores.LATEST)

    assert serialize(POLY, MSG_POLY[1], ros2_store, little_endian=True) == MSG_POLY[0]
    assert serialize(MAGN, MSG_MAGN[1], ros2_store, little_endian=True) == MSG_MAGN[0]
    assert serialize(MAGN, MSG_MAGN[1], ros2_store, little_endian=False) == MSG_MAGN_BIG[0][:-3]
    assert serialize(JOINT, MSG_JOINT[1], ros2_store, little_endian=True) == MSG_JOINT[0][:-3]


def test_cdr_serializer() -> None:
    """Test cdr serializer encodes messages."""
    ros2_store = get_typestore(Stores.LATEST)

    assert ros2_store.serialize_cdr(POLY, MSG_POLY[1]) == MSG_POLY[0]
    assert ros2_store.serialize_cdr(MAGN, MSG_MAGN[1]) == MSG_MAGN[0]
    assert ros2_store.serialize_cdr(MAGN, MSG_MAGN[1], little_endian=False) == MSG_MAGN_BIG[0][:-3]
    assert ros2_store.serialize_cdr(JOINT, MSG_JOINT[1]) == MSG_JOINT[0][:-3]


def test_ros1_serializer() -> None:
    """Test ros1 serializer encodes messages."""
    ros2_store = get_typestore(Stores.LATEST)
    ros1_store = get_typestore(Stores.ROS1_NOETIC)

    poly = ros2_store.cdr_to_ros1(*MSG_POLY[:2])
    magn = ros2_store.cdr_to_ros1(*MSG_MAGN[:2])
    joint = ros2_store.cdr_to_ros1(*MSG_JOINT[:2])

    assert ros1_store.serialize_ros1(POLY, MSG_POLY[1]) == poly
    with patch.object(MAGN.header, 'seq', 0, create=True):
        assert ros1_store.serialize_ros1(MAGN, MSG_MAGN[1]) == magn
    with patch.object(JOINT.header, 'seq', 0, create=True):
        assert ros1_store.serialize_ros1(JOINT, MSG_JOINT[1]) == joint


def test_serializer_errors() -> None:
    """Test seralizer with broken messages."""
    store = get_typestore(Stores.LATEST)

    class Foo:
        """Dummy class."""

        coef = np.array([1, 2, 3, 4], dtype=np.float64)

    msg = Foo()
    _ = store.serialize_cdr(msg, 'shape_msgs/msg/Plane')
    _ = store.serialize_ros1(msg, 'shape_msgs/msg/Plane')

    msg.coef = np.array([1, 2, 3, 4, 4], dtype=np.float64)
    with pytest.raises(SerdeError, match='array length'):
        _ = store.serialize_cdr(msg, 'shape_msgs/msg/Plane')

    with pytest.raises(SerdeError, match='array length'):
        _ = store.serialize_ros1(msg, 'shape_msgs/msg/Plane')


@pytest.mark.usefixtures('_comparable')
def test_padding_is_correct_after_base_array() -> None:
    """Test padding is correctly adjusted after small base arrays."""
    store = get_typestore(Stores.LATEST)

    typename = 'test_msgs/msg/ab_au16'
    msgdef = """
    bool[1] ab
    uint16[2] au16
    """
    cdr_bytestream = b'\x01\x00\x02\x03\x04\x05'
    ros1_bytestream = b'\x01\x02\x03\x04\x05'

    store.register(get_types_from_msg(msgdef, typename))

    ab_au16 = store.types[typename]
    msg = ab_au16(ab=np.array([True], dtype=np.bool_), au16=np.array([770, 1284], np.uint16))

    cdr = store.serialize_cdr(msg, typename)
    assert cdr[4:] == cdr_bytestream
    assert store.deserialize_cdr(cdr, typename) == msg

    assert store.cdr_to_ros1(cdr, typename) == ros1_bytestream
    assert store.ros1_to_cdr(ros1_bytestream, typename) == cdr


@pytest.mark.usefixtures('_comparable')
def test_empty_sequences_do_not_add_padding() -> None:
    """Test empty sequences do not add padding."""
    store = get_typestore(Stores.LATEST)

    typename = 'test_msgs/msg/su64_b'
    msgdef = """
    uint64[] su64
    bool b
    """
    bytestream = b'\x00\x00\x00\x00\x01'

    store.register(get_types_from_msg(msgdef, typename))

    su64_b = store.types[typename]
    msg = su64_b(su64=np.array([], dtype=np.uint64), b=True)

    cdr = store.serialize_cdr(msg, typename)
    assert cdr[4:] == bytestream
    assert store.deserialize_cdr(cdr, typename) == msg

    assert store.cdr_to_ros1(cdr, typename) == bytestream
    assert store.ros1_to_cdr(bytestream, typename) == cdr


@pytest.mark.usefixtures('_comparable')
def test_empty_sequences_have_correct_postalignment() -> None:
    """Test alignment after empty sequences is correct."""
    store = get_typestore(Stores.LATEST)

    typename_su64_u64 = 'test_msgs/msg/su64_u64'
    msgdef_su64_u64 = """
    uint64[] su64
    uint64 u64
    """

    typename_smsg_u64 = 'test_msgs/msg/smsg_u64'
    msgdef_smsg_u64 = """
    su64_u64[] seq
    uint64 u64
    """

    cdr_bytes = (
        b'\x00\x00\x00\x00'  # sequence length = 0
        b'\x00\x00\x00\x00'  # padding
        b'\x2a\x00\x00\x00\x00\x00\x00\x00'  # u64 = 42
    )

    ros1_bytes = (
        b'\x00\x00\x00\x00'  # sequence length = 0
        b'\x2a\x00\x00\x00\x00\x00\x00\x00'  # u64 = 42
    )

    store.register(get_types_from_msg(msgdef_su64_u64, typename_su64_u64))
    store.register(get_types_from_msg(msgdef_smsg_u64, typename_smsg_u64))

    msg1 = store.types[typename_su64_u64](np.array([], dtype=np.uint64), 42)
    msg2 = store.types[typename_smsg_u64]([], 42)

    cdr = store.serialize_cdr(msg1, msg1.__msgtype__)
    assert store.serialize_cdr(msg2, msg2.__msgtype__) == cdr
    assert cdr[4:] == cdr_bytes

    assert store.deserialize_cdr(cdr, msg1.__msgtype__) == msg1
    assert store.deserialize_cdr(cdr, msg2.__msgtype__) == msg2

    ros1 = store.cdr_to_ros1(cdr, msg1.__msgtype__)
    assert store.cdr_to_ros1(cdr, msg2.__msgtype__) == ros1
    assert ros1 == ros1_bytes

    assert store.ros1_to_cdr(ros1, msg1.__msgtype__) == cdr
    assert store.ros1_to_cdr(ros1, msg2.__msgtype__) == cdr


def test_empty_message_handling() -> None:
    """Test empty message handling."""
    store = get_typestore(Stores.LATEST)

    typename_empty = 'test_msgs/msg/Empty'
    msgdef_empty = """
    uint8 JUST_SOME_CONSTANT = 1
    """

    typename_unaligned = 'test_msgs/msg/UnalignedHolder'
    msgdef_unaligned = """
    int32 pre
    test_msgs/msg/Empty empty
    int64 post
    """

    typename_aligned = 'test_msgs/msg/AlignedHolder'
    msgdef_aligned = """
    int64 pre
    test_msgs/msg/Empty empty
    int64 post
    """

    store.register(get_types_from_msg(msgdef_empty, typename_empty))
    store.register(get_types_from_msg(msgdef_unaligned, typename_unaligned))
    store.register(get_types_from_msg(msgdef_aligned, typename_aligned))

    empty = store.types[typename_empty]
    unaligned_holder = store.types[typename_unaligned]
    aligned_holder = store.types[typename_aligned]

    unaligned_msg = unaligned_holder(-1, empty(), -1)
    aligned_msg = aligned_holder(-1, empty(), -1)

    unaligned_cdr_bytes = (
        b'\x00\x01\x00\x00'  # cdr header
        b'\xff\xff\xff\xff'  # pre = -1
        b'\x00'  # empty message
        b'\x00\x00\x00'  # padding
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # post = -1
    )
    aligned_cdr_bytes = (
        b'\x00\x01\x00\x00'  # cdr header
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # pre = -1
        b'\x00'  # empty message
        b'\x00\x00\x00\x00\x00\x00\x00'  # padding
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # post = -1
    )
    unaligned_ros1_bytes = (
        b'\xff\xff\xff\xff'  # pre = -1
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # post = -1
    )
    aligned_ros1_bytes = (
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # pre = -1
        b'\xff\xff\xff\xff\xff\xff\xff\xff'  # post = -1
    )

    assert store.serialize_cdr(unaligned_msg, unaligned_msg.__msgtype__) == unaligned_cdr_bytes
    assert store.serialize_cdr(aligned_msg, aligned_msg.__msgtype__) == aligned_cdr_bytes
    assert store.serialize_ros1(unaligned_msg, unaligned_msg.__msgtype__) == unaligned_ros1_bytes
    assert store.serialize_ros1(aligned_msg, aligned_msg.__msgtype__) == aligned_ros1_bytes

    assert store.deserialize_cdr(unaligned_cdr_bytes, unaligned_msg.__msgtype__) == unaligned_msg
    assert store.deserialize_cdr(aligned_cdr_bytes, aligned_msg.__msgtype__) == aligned_msg
    assert store.deserialize_ros1(unaligned_ros1_bytes, unaligned_msg.__msgtype__) == unaligned_msg
    assert store.deserialize_ros1(aligned_ros1_bytes, aligned_msg.__msgtype__) == aligned_msg

    assert store.cdr_to_ros1(unaligned_cdr_bytes, unaligned_msg.__msgtype__) == unaligned_ros1_bytes
    assert store.cdr_to_ros1(aligned_cdr_bytes, aligned_msg.__msgtype__) == aligned_ros1_bytes
    assert store.ros1_to_cdr(unaligned_ros1_bytes, unaligned_msg.__msgtype__) == unaligned_cdr_bytes
    assert store.ros1_to_cdr(aligned_ros1_bytes, aligned_msg.__msgtype__) == aligned_cdr_bytes
