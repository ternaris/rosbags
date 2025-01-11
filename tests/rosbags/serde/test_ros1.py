# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""ROS1 Generator Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype
from rosbags.serde.ros1 import (
    generate_cdr_to_ros1,
    generate_deserialize_ros1,
    generate_getsize_ros1,
    generate_ros1_to_cdr,
    generate_serialize_ros1,
)
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Fielddefs

ALL_COMBINATIONS: Fielddefs = [
    ('structure_needs_at_least_one_member', (Nodetype.BASE, ('uint8', 0))),
    ('fmsg', (Nodetype.NAME, 'f_size')),
    ('vmsg', (Nodetype.NAME, 'v_size')),
    ('u64', (Nodetype.BASE, ('uint64', 0))),
    ('str', (Nodetype.BASE, ('string', 0))),
    ('a_fmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'f_size'), 2))),
    ('a_vmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'v_size'), 2))),
    ('a_u64', (Nodetype.ARRAY, ((Nodetype.BASE, ('uint64', 0)), 2))),
    ('a_str', (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 0)), 2))),
    ('s_fmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'f_size'), 2))),
    ('s_vmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'v_size'), 2))),
    ('s_u64', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint64', 0)), 2))),
    ('s_str', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 0)), 2))),
]


def test_ros1_generator() -> None:
    """Test ros1 code generators do not throw."""
    store = get_typestore(Stores.EMPTY)
    store.register(
        {
            'f_size': ([], [('u64', (Nodetype.BASE, ('uint64', 0)))]),
            'v_size': ([], [('s_u8', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint8', 0)), 0)))]),
        }
    )
    _ = generate_getsize_ros1(ALL_COMBINATIONS, store)
    _ = generate_deserialize_ros1(ALL_COMBINATIONS, store)
    _ = generate_serialize_ros1(ALL_COMBINATIONS, store)

    for typename, copy in zip(('foo', 'std_msgs/msg/Header'), (True, False), strict=True):
        _ = generate_cdr_to_ros1(ALL_COMBINATIONS, typename, store, copy=copy)
        _ = generate_ros1_to_cdr(ALL_COMBINATIONS, typename, store, copy=copy)
