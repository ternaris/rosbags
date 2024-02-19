# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Serializer and deserializer tests."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pytest

from rosbags.serde import (
    SerdeError,
)
from rosbags.typesys import Stores, get_types_from_msg, get_typestore
from rosbags.typesys.stores.ros1_noetic import (
    geometry_msgs__msg__Polygon as Polygon1,
    sensor_msgs__msg__MagneticField as MagneticField1,
)
from rosbags.typesys.stores.ros2_humble import (
    geometry_msgs__msg__Polygon as Polygon,
    sensor_msgs__msg__MagneticField as MagneticField,
)

from .cdr import deserialize, serialize

if TYPE_CHECKING:
    import sys
    from typing import Generator

    if sys.version_info >= (3, 10):
        from typing import ParamSpec
    else:
        from typing_extensions import ParamSpec

    P = ParamSpec('P')

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

MESSAGES = [MSG_POLY, MSG_MAGN, MSG_MAGN_BIG, MSG_JOINT]

STATIC_64_64 = """
uint64[2] u64
"""

STATIC_64_16 = """
uint64 u64
uint16 u16
"""

STATIC_16_64 = """
uint16 u16
uint64 u64
"""

DYNAMIC_64_64 = """
uint64[] u64
"""

DYNAMIC_64_B_64 = """
uint64 u64
bool b
float64 f64
"""

DYNAMIC_64_S = """
uint64 u64
string s
"""

DYNAMIC_S_64 = """
string s
uint64 u64
"""

CUSTOM = """
string base_str
float32 base_f32
test_msgs/msg/static_64_64 msg_s66
test_msgs/msg/static_64_16 msg_s61
test_msgs/msg/static_16_64 msg_s16
test_msgs/msg/dynamic_64_64 msg_d66
test_msgs/msg/dynamic_64_b_64 msg_d6b6
test_msgs/msg/dynamic_64_s msg_d6s
test_msgs/msg/dynamic_s_64 msg_ds6

string[2] arr_base_str
float32[2] arr_base_f32
test_msgs/msg/static_64_64[2] arr_msg_s66
test_msgs/msg/static_64_16[2] arr_msg_s61
test_msgs/msg/static_16_64[2] arr_msg_s16
test_msgs/msg/dynamic_64_64[2] arr_msg_d66
test_msgs/msg/dynamic_64_b_64[2] arr_msg_d6b6
test_msgs/msg/dynamic_64_s[2] arr_msg_d6s
test_msgs/msg/dynamic_s_64[2] arr_msg_ds6

string[] seq_base_str
float32[] seq_base_f32
test_msgs/msg/static_64_64[] seq_msg_s66
test_msgs/msg/static_64_16[] seq_msg_s61
test_msgs/msg/static_16_64[] seq_msg_s16
test_msgs/msg/dynamic_64_64[] seq_msg_d66
test_msgs/msg/dynamic_64_b_64[] seq_msg_d6b6
test_msgs/msg/dynamic_64_s[] seq_msg_d6s
test_msgs/msg/dynamic_s_64[] seq_msg_ds6
"""

SU64_B = """
uint64[] su64
bool b
"""

SU64_U64 = """
uint64[] su64
uint64 u64
"""

SMSG_U64 = """
su64_u64[] seq
uint64 u64
"""

EMPTY_MSG = """
uint8 JUST_SOME_CONSTANT = 1
"""

EMPTY_UNALIGNED_HOLDER = """
int32 pre
test_msgs/msg/Empty empty
int64 post
"""

EMPTY_ALIGNED_HOLDER = """
int64 pre
test_msgs/msg/Empty empty
int64 post
"""


@pytest.fixture()
def _comparable() -> Generator[None, None, None]:
    """Make messages containing numpy arrays comparable.

    Notes:
        This solution is necessary as numpy.ndarray is not directly patchable.

    """
    frombuffer = np.frombuffer

    class CNDArray:
        """Comparable ndarray."""

        def __init__(self, child: np.ndarray[int, np.dtype[np.uint8]]) -> None:
            self.child = child

        def __eq__(self, other: object) -> bool:
            if isinstance(other, CNDArray):
                other = other.child
            assert isinstance(other, np.ndarray)
            return bool(np.equal(self.child, other).all())

        def byteswap(self) -> CNDArray:
            return CNDArray(self.child.byteswap())

        def __deepcopy__(self, _: dict[str, object]) -> CNDArray:
            return self

        def __getattr__(self, name: str) -> object:
            return getattr(self.child, name)

    def wrap_frombuffer(mem: bytes, dtype: str, count: int, offset: int) -> CNDArray:
        return CNDArray(frombuffer(mem, dtype=dtype, count=count, offset=offset))

    with patch.object(np, 'frombuffer', wrap_frombuffer):
        yield


@pytest.mark.parametrize('message', MESSAGES)
def test_serde(message: tuple[bytes, str, bool]) -> None:
    """Test serialization deserialization roundtrip."""
    rawdata, typ, is_little = message
    store = get_typestore(Stores.LATEST)
    ros1_store = get_typestore(Stores.ROS1_NOETIC)

    serdeser = store.serialize_cdr(
        store.deserialize_cdr(rawdata, typ), typ, little_endian=is_little
    )
    assert serdeser == serialize(
        deserialize(rawdata, typ, store),
        typ,
        store,
        little_endian=is_little,
    )
    assert serdeser == rawdata[: len(serdeser)]
    assert len(rawdata) - len(serdeser) < 4
    assert all(x == 0 for x in rawdata[len(serdeser) :])

    if rawdata[1] == 1:
        rawdata = store.cdr_to_ros1(rawdata, typ)
        serdeser = ros1_store.serialize_ros1(ros1_store.deserialize_ros1(rawdata, typ), typ)
        assert serdeser == rawdata


@pytest.mark.usefixtures('_comparable')
def test_deserializer() -> None:
    """Test deserializer."""
    store = get_typestore(Stores.LATEST)
    ros1_store = get_typestore(Stores.ROS1_NOETIC)
    msg = store.deserialize_cdr(*MSG_POLY[:2])
    assert isinstance(msg, Polygon)

    assert msg == deserialize(*MSG_POLY[:2], store)
    assert isinstance(msg, Polygon)
    assert len(msg.points) == 2
    assert msg.points[0].x == 1
    assert msg.points[0].y == 2
    assert msg.points[0].z == 3
    assert msg.points[1].x == 1.25
    assert msg.points[1].y == 2.25
    assert msg.points[1].z == 3.25
    msg_ros1 = ros1_store.deserialize_ros1(store.cdr_to_ros1(*MSG_POLY[:2]), MSG_POLY[1])
    assert isinstance(msg_ros1, Polygon1)
    assert asdict(msg_ros1) == asdict(msg)

    msg = store.deserialize_cdr(*MSG_MAGN[:2])
    assert msg == deserialize(*MSG_MAGN[:2], store)
    assert isinstance(msg, MagneticField)
    assert 'MagneticField' in repr(msg)
    assert msg.header.stamp.sec == 708
    assert msg.header.stamp.nanosec == 256
    assert msg.header.frame_id == 'foo42'
    field = msg.magnetic_field
    assert (field.x, field.y, field.z) == (128.0, 128.0, 128.0)
    diag = np.diag(msg.magnetic_field_covariance.reshape(3, 3))
    assert (diag == [1.0, 1.0, 1.0]).all()
    msg_ros1 = ros1_store.deserialize_ros1(store.cdr_to_ros1(*MSG_MAGN[:2]), MSG_MAGN[1])
    assert isinstance(msg_ros1, MagneticField1)
    msg_ros1_dct = asdict(msg_ros1)
    assert msg_ros1_dct['header'].pop('seq') == 0
    assert msg_ros1_dct == asdict(msg)

    msg_big = store.deserialize_cdr(*MSG_MAGN_BIG[:2])
    assert msg_big == deserialize(*MSG_MAGN_BIG[:2], store)
    assert isinstance(msg_big, MagneticField)
    assert msg.magnetic_field == msg_big.magnetic_field


@pytest.mark.usefixtures('_comparable')
def test_serializer() -> None:
    """Test serializer."""
    store = get_typestore(Stores.LATEST)

    class Foo:
        """Dummy class."""

        data = 7

    msg = Foo()
    ret = store.serialize_cdr(msg, 'std_msgs/msg/Int8', little_endian=True)
    assert ret == serialize(msg, 'std_msgs/msg/Int8', store, little_endian=True)
    assert ret == b'\x00\x01\x00\x00\x07'

    ret = store.serialize_cdr(msg, 'std_msgs/msg/Int8', little_endian=False)
    assert ret == serialize(msg, 'std_msgs/msg/Int8', store, little_endian=False)
    assert ret == b'\x00\x00\x00\x00\x07'

    ret = store.serialize_cdr(msg, 'std_msgs/msg/Int16', little_endian=True)
    assert ret == serialize(msg, 'std_msgs/msg/Int16', store, little_endian=True)
    assert ret == b'\x00\x01\x00\x00\x07\x00'

    ret = store.serialize_cdr(msg, 'std_msgs/msg/Int16', little_endian=False)
    assert ret == serialize(msg, 'std_msgs/msg/Int16', store, little_endian=False)
    assert ret == b'\x00\x00\x00\x00\x00\x07'


@pytest.mark.usefixtures('_comparable')
def test_serializer_errors() -> None:
    """Test seralizer with broken messages."""
    store = get_typestore(Stores.LATEST)

    class Foo:
        """Dummy class."""

        coef: np.ndarray[int, np.dtype[np.uint8]] = np.array([1, 2, 3, 4])

    msg = Foo()
    ret = store.serialize_cdr(msg, 'shape_msgs/msg/Plane', little_endian=True)
    assert ret == serialize(msg, 'shape_msgs/msg/Plane', store, little_endian=True)

    msg.coef = np.array([1, 2, 3, 4, 4])
    with pytest.raises(SerdeError, match='array length'):
        store.serialize_cdr(msg, 'shape_msgs/msg/Plane', little_endian=True)


@pytest.mark.usefixtures('_comparable')
def test_custom_type() -> None:
    """Test custom type."""
    store = get_typestore(Stores.LATEST)

    cname = 'test_msgs/msg/custom'
    store.register(dict(get_types_from_msg(STATIC_64_64, 'test_msgs/msg/static_64_64')))
    store.register(dict(get_types_from_msg(STATIC_64_16, 'test_msgs/msg/static_64_16')))
    store.register(dict(get_types_from_msg(STATIC_16_64, 'test_msgs/msg/static_16_64')))
    store.register(dict(get_types_from_msg(DYNAMIC_64_64, 'test_msgs/msg/dynamic_64_64')))
    store.register(dict(get_types_from_msg(DYNAMIC_64_B_64, 'test_msgs/msg/dynamic_64_b_64')))
    store.register(dict(get_types_from_msg(DYNAMIC_64_S, 'test_msgs/msg/dynamic_64_s')))
    store.register(dict(get_types_from_msg(DYNAMIC_S_64, 'test_msgs/msg/dynamic_s_64')))
    store.register(dict(get_types_from_msg(CUSTOM, cname)))

    static_64_64 = store.get_msgdef('test_msgs/msg/static_64_64').cls
    static_64_16 = store.get_msgdef('test_msgs/msg/static_64_16').cls
    static_16_64 = store.get_msgdef('test_msgs/msg/static_16_64').cls
    dynamic_64_64 = store.get_msgdef('test_msgs/msg/dynamic_64_64').cls
    dynamic_64_b_64 = store.get_msgdef('test_msgs/msg/dynamic_64_b_64').cls
    dynamic_64_s = store.get_msgdef('test_msgs/msg/dynamic_64_s').cls
    dynamic_s_64 = store.get_msgdef('test_msgs/msg/dynamic_s_64').cls
    custom = store.get_msgdef('test_msgs/msg/custom').cls

    msg = custom(
        'str',
        1.5,
        static_64_64(np.array([64, 64], dtype=np.uint64)),
        static_64_16(64, 16),
        static_16_64(16, 64),
        dynamic_64_64(np.array([33, 33], dtype=np.uint64)),
        dynamic_64_b_64(64, b=True, f64=1.25),
        dynamic_64_s(64, 's'),
        dynamic_s_64('s', 64),
        # arrays
        ['str_1', ''],
        np.array([1.5, 0.75], dtype=np.float32),
        [
            static_64_64(np.array([64, 64], dtype=np.uint64)),
            static_64_64(np.array([64, 64], dtype=np.uint64)),
        ],
        [static_64_16(64, 16), static_64_16(64, 16)],
        [static_16_64(16, 64), static_16_64(16, 64)],
        [
            dynamic_64_64(np.array([33, 33], dtype=np.uint64)),
            dynamic_64_64(np.array([33, 33], dtype=np.uint64)),
        ],
        [dynamic_64_b_64(64, b=True, f64=1.25), dynamic_64_b_64(64, b=True, f64=1.25)],
        [dynamic_64_s(64, 's'), dynamic_64_s(64, 's')],
        [dynamic_s_64('s', 64), dynamic_s_64('s', 64)],
        # sequences
        ['str_1', ''],
        np.array([1.5, 0.75], dtype=np.float32),
        [
            static_64_64(np.array([64, 64], dtype=np.uint64)),
            static_64_64(np.array([64, 64], dtype=np.uint64)),
        ],
        [static_64_16(64, 16), static_64_16(64, 16)],
        [static_16_64(16, 64), static_16_64(16, 64)],
        [
            dynamic_64_64(np.array([33, 33], dtype=np.uint64)),
            dynamic_64_64(np.array([33, 33], dtype=np.uint64)),
        ],
        [dynamic_64_b_64(64, b=True, f64=1.25), dynamic_64_b_64(64, b=True, f64=1.25)],
        [dynamic_64_s(64, 's'), dynamic_64_s(64, 's')],
        [dynamic_s_64('s', 64), dynamic_s_64('s', 64)],
    )

    res = store.deserialize_cdr(store.serialize_cdr(msg, cname), cname)
    assert res == deserialize(serialize(msg, cname, store), cname, store)
    assert res == msg

    res = store.deserialize_ros1(store.serialize_ros1(msg, cname), cname)
    assert res == msg


def test_ros1_to_cdr() -> None:
    """Test ROS1 to CDR conversion."""
    store = get_typestore(Stores.LATEST)

    msgtype = 'test_msgs/msg/static_16_64'
    store.register(dict(get_types_from_msg(STATIC_16_64, msgtype)))
    msg_ros = b'\x01\x00' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = (
        b'\x00\x01\x00\x00'
        b'\x01\x00'
        b'\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x02'
    )
    assert store.ros1_to_cdr(msg_ros, msgtype) == msg_cdr
    assert store.serialize_cdr(store.deserialize_ros1(msg_ros, msgtype), msgtype) == msg_cdr

    msgtype = 'test_msgs/msg/dynamic_s_64'
    store.register(dict(get_types_from_msg(DYNAMIC_S_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00X' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = (
        b'\x00\x01\x00\x00' b'\x02\x00\x00\x00X\x00' b'\x00\x00' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    )
    assert store.ros1_to_cdr(msg_ros, msgtype) == msg_cdr
    assert store.serialize_cdr(store.deserialize_ros1(msg_ros, msgtype), msgtype) == msg_cdr


def test_cdr_to_ros1() -> None:
    """Test CDR to ROS1 conversion."""
    store = get_typestore(Stores.LATEST)

    msgtype = 'test_msgs/msg/static_16_64'
    store.register(dict(get_types_from_msg(STATIC_16_64, msgtype)))
    msg_ros = b'\x01\x00' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = (
        b'\x00\x01\x00\x00'
        b'\x01\x00'
        b'\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x02'
    )
    assert store.cdr_to_ros1(msg_cdr, msgtype) == msg_ros
    assert store.serialize_ros1(store.deserialize_cdr(msg_cdr, msgtype), msgtype) == msg_ros

    msgtype = 'test_msgs/msg/dynamic_s_64'
    store.register(dict(get_types_from_msg(DYNAMIC_S_64, msgtype)))
    msg_ros = b'\x01\x00\x00\x00X' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    msg_cdr = (
        b'\x00\x01\x00\x00' b'\x02\x00\x00\x00X\x00' b'\x00\x00' b'\x00\x00\x00\x00\x00\x00\x00\x02'
    )
    assert store.cdr_to_ros1(msg_cdr, msgtype) == msg_ros
    assert store.serialize_ros1(store.deserialize_cdr(msg_cdr, msgtype), msgtype) == msg_ros

    Header = store.types['std_msgs/msg/Header']  # noqa: N806
    Time = store.types['builtin_interfaces/msg/Time']  # noqa: N806

    header = Header(stamp=Time(42, 666), frame_id='frame')
    msg_ros = store.cdr_to_ros1(
        store.serialize_cdr(header, 'std_msgs/msg/Header'), 'std_msgs/msg/Header'
    )
    assert msg_ros == b'\x00\x00\x00\x00*\x00\x00\x00\x9a\x02\x00\x00\x05\x00\x00\x00frame'


@pytest.mark.usefixtures('_comparable')
def test_padding_empty_sequence() -> None:
    """Test empty sequences do not add item padding."""
    store = get_typestore(Stores.LATEST)

    store.register(dict(get_types_from_msg(SU64_B, 'test_msgs/msg/su64_b')))

    su64_b = store.get_msgdef('test_msgs/msg/su64_b').cls
    msg = su64_b(np.array([], dtype=np.uint64), b=True)

    cdr = store.serialize_cdr(msg, msg.__msgtype__)
    assert cdr[4:] == b'\x00\x00\x00\x00\x01'

    ros1 = store.cdr_to_ros1(cdr, msg.__msgtype__)
    assert ros1 == cdr[4:]

    assert store.ros1_to_cdr(ros1, msg.__msgtype__) == cdr

    assert store.deserialize_cdr(cdr, msg.__msgtype__) == msg


@pytest.mark.usefixtures('_comparable')
def test_align_after_empty_sequence() -> None:
    """Test alignment after empty sequences."""
    store = get_typestore(Stores.LATEST)

    store.register(dict(get_types_from_msg(SU64_U64, 'test_msgs/msg/su64_u64')))
    store.register(dict(get_types_from_msg(SMSG_U64, 'test_msgs/msg/smsg_u64')))

    su64_u64 = store.get_msgdef('test_msgs/msg/su64_u64').cls
    smsg_u64 = store.get_msgdef('test_msgs/msg/smsg_u64').cls
    msg1 = su64_u64(np.array([], dtype=np.uint64), 42)
    msg2 = smsg_u64([], 42)

    cdr = store.serialize_cdr(msg1, msg1.__msgtype__)
    assert cdr[4:] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00'
    assert store.serialize_cdr(msg2, msg2.__msgtype__) == cdr

    ros1 = store.cdr_to_ros1(cdr, msg1.__msgtype__)
    assert ros1 == b'\x00\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00'
    assert store.cdr_to_ros1(cdr, msg2.__msgtype__) == ros1

    assert store.ros1_to_cdr(ros1, msg1.__msgtype__) == cdr

    assert store.deserialize_cdr(cdr, msg1.__msgtype__) == msg1
    assert store.deserialize_cdr(cdr, msg2.__msgtype__) == msg2


def test_empty_message_handling() -> None:
    """Test empty message handling."""
    store = get_typestore(Stores.LATEST)

    store.register(dict(get_types_from_msg(EMPTY_MSG, 'test_msgs/msg/Empty')))
    store.register(
        dict(get_types_from_msg(EMPTY_UNALIGNED_HOLDER, 'test_msgs/msg/UnalignedHolder')),
    )
    store.register(dict(get_types_from_msg(EMPTY_ALIGNED_HOLDER, 'test_msgs/msg/AlignedHolder')))

    empty = store.get_msgdef('test_msgs/msg/Empty').cls
    unaligned_holder = store.get_msgdef('test_msgs/msg/UnalignedHolder').cls
    aligned_holder = store.get_msgdef('test_msgs/msg/AlignedHolder').cls

    unaligned_msg = unaligned_holder(-1, empty(), -1)
    aligned_msg = aligned_holder(-1, empty(), -1)

    unaligned_cdr_bytes = (
        b'\x00\x01\x00\x00'
        b'\xff\xff\xff\xff'
        b'\x00\x00\x00\x00'
        b'\xff\xff\xff\xff\xff\xff\xff\xff'
    )
    aligned_cdr_bytes = (
        b'\x00\x01\x00\x00'
        b'\xff\xff\xff\xff\xff\xff\xff\xff'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\xff\xff\xff\xff\xff\xff\xff\xff'
    )
    unaligned_ros1_bytes = b'\xff\xff\xff\xff' b'\xff\xff\xff\xff\xff\xff\xff\xff'
    aligned_ros1_bytes = b'\xff\xff\xff\xff\xff\xff\xff\xff' b'\xff\xff\xff\xff\xff\xff\xff\xff'

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
