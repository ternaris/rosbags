# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Message Registration Tests."""

import numpy as np
import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_typestore
from rosbags.typesys.msg import get_types_from_msg
from rosbags.typesys.store import Typestore


def test_raw_typestore_is_empty() -> None:
    """Test typestore is empty."""
    store = Typestore()
    assert not store.fielddefs


def test_register_with_new_type() -> None:
    """Test typestore registers new types."""
    store = get_typestore(Stores.LATEST)

    assert 'foo' not in store.fielddefs
    store.register({'foo': ([], [('b', (Nodetype.BASE, ('bool', 0)))])})
    assert 'foo' in store.fielddefs


def test_register_with_same_as_existing_type() -> None:
    """Test typestore accepts identical type."""
    store = get_typestore(Stores.LATEST)

    typename = 'builtin_interfaces/msg/Time'

    assert typename in store.fielddefs
    store.register(
        {
            typename: (
                [],
                [
                    ('sec', (Nodetype.BASE, ('int32', 0))),
                    ('nanosec', (Nodetype.BASE, ('uint32', 0))),
                ],
            )
        }
    )


def test_register_with_different_from_existing_type() -> None:
    """Test typestore rejects different type."""
    store = get_typestore(Stores.LATEST)

    typename = 'builtin_interfaces/msg/Time'

    assert typename in store.fielddefs
    with pytest.raises(TypesysError, match='different definition'):
        store.register(
            {
                typename: (
                    [],
                    [
                        ('sec', (Nodetype.BASE, ('int32', 0))),
                        ('nsec', (Nodetype.BASE, ('uint32', 0))),
                    ],
                )
            }
        )


@pytest.mark.usefixtures('_comparable')
def test_registered_types_support_serde() -> None:
    """Test registered types allow serde operstions."""
    store = get_typestore(Stores.LATEST)

    typename_s_64_64 = 'test_msgs/msg/static_64_64'
    msgdef_s_64_64 = """
    uint64[2] u64
    """

    typename_s_64_16 = 'test_msgs/msg/static_64_16'
    msgdef_s_64_16 = """
    uint64 u64
    uint16 u16
    """

    typename_s_16_64 = 'test_msgs/msg/static_16_64'
    msgdef_s_16_64 = """
    uint16 u16
    uint64 u64
    """

    typename_d_64_64 = 'test_msgs/msg/dynamic_64_64'
    msgdef_d_64_64 = """
    uint64[] u64
    """

    typename_d_64_b_64 = 'test_msgs/msg/dynamic_64_b_64'
    msgdef_d_64_b_64 = """
    uint64 u64
    bool b
    float64 f64
    """

    typename_d_64_s = 'test_msgs/msg/dynamic_64_s'
    msgdef_d_64_s = """
    uint64 u64
    string s
    """

    typename_d_s_64 = 'test_msgs/msg/dynamic_s_64'
    msgdef_d_s_64 = """
    string s
    uint64 u64
    """

    typename_custom = 'test_msgs/msg/custom'
    msgdef_custom = """
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

    store.register(get_types_from_msg(msgdef_s_64_64, typename_s_64_64))
    store.register(get_types_from_msg(msgdef_s_64_16, typename_s_64_16))
    store.register(get_types_from_msg(msgdef_s_16_64, typename_s_16_64))
    store.register(get_types_from_msg(msgdef_d_64_64, typename_d_64_64))
    store.register(get_types_from_msg(msgdef_d_64_b_64, typename_d_64_b_64))
    store.register(get_types_from_msg(msgdef_d_64_s, typename_d_64_s))
    store.register(get_types_from_msg(msgdef_d_s_64, typename_d_s_64))
    store.register(get_types_from_msg(msgdef_custom, typename_custom))

    static_64_64 = store.types[typename_s_64_64]
    static_64_16 = store.types[typename_s_64_16]
    static_16_64 = store.types[typename_s_16_64]
    dynamic_64_64 = store.types[typename_d_64_64]
    dynamic_64_b_64 = store.types[typename_d_64_b_64]
    dynamic_64_s = store.types[typename_d_64_s]
    dynamic_s_64 = store.types[typename_d_s_64]
    custom = store.types[typename_custom]

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

    res = store.deserialize_cdr(store.serialize_cdr(msg, typename_custom), typename_custom)
    assert res == msg

    res = store.deserialize_ros1(store.serialize_ros1(msg, typename_custom), typename_custom)
    assert res == msg
