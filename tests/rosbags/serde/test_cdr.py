# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""CDR Generator Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype
from rosbags.serde.cdr import generate_deserialize_cdr, generate_getsize_cdr, generate_serialize_cdr
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Fielddefs

ALL_COMBINATIONS: Fielddefs = [
    ('fmsg', (Nodetype.NAME, 'f_size')),
    ('gmsg', (Nodetype.NAME, 'paf_size')),
    ('vmsg', (Nodetype.NAME, 'v_size')),
    ('wmsg', (Nodetype.NAME, 'pav_size')),
    ('u64', (Nodetype.BASE, ('uint64', 0))),
    ('u8', (Nodetype.BASE, ('uint8', 0))),
    ('str', (Nodetype.BASE, ('string', 0))),
    ('a_fmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'f_size'), 2))),
    ('a_gmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'paf_size'), 2))),
    ('a_vmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'v_size'), 2))),
    ('a_wmsg', (Nodetype.ARRAY, ((Nodetype.NAME, 'pav_size'), 2))),
    ('a_u64', (Nodetype.ARRAY, ((Nodetype.BASE, ('uint64', 0)), 2))),
    ('a_u8', (Nodetype.ARRAY, ((Nodetype.BASE, ('uint8', 0)), 2))),
    ('a_str', (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 0)), 2))),
    ('s_fmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'f_size'), 2))),
    ('s_gmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'paf_size'), 2))),
    ('s_vmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'v_size'), 2))),
    ('s_wmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'pav_size'), 2))),
    ('s_xmsg', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'psv_size'), 2))),
    ('s_u64', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint64', 0)), 2))),
    ('s_u8', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint8', 0)), 2))),
    ('s_str', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 0)), 2))),
]


def test_cdr_generator() -> None:
    """Test cdr code generators do not throw."""
    store = get_typestore(Stores.EMPTY)
    store.register(
        {
            'f_size': (
                [],
                [
                    ('u64', (Nodetype.BASE, ('uint64', 0))),
                ],
            ),
            'paf_size': (
                [],
                [
                    ('u64', (Nodetype.BASE, ('uint64', 0))),
                    ('u8', (Nodetype.BASE, ('uint8', 0))),
                ],
            ),
            'v_size': (
                [],
                [
                    ('str', (Nodetype.BASE, ('string', 0))),
                ],
            ),
            'pav_size': (
                [],
                [
                    ('s_u64', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint64', 0)), 0))),
                ],
            ),
            'psv_size': (
                [],
                [
                    ('u64', (Nodetype.BASE, ('uint64', 0))),
                    ('s_u64', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('uint64', 0)), 0))),
                    ('a_u64', (Nodetype.ARRAY, ((Nodetype.BASE, ('uint64', 0)), 2))),
                ],
            ),
        }
    )
    _ = generate_getsize_cdr(ALL_COMBINATIONS, store)
    for endianess in ('le', 'be'):
        _ = generate_deserialize_cdr(ALL_COMBINATIONS, store, endianess)
        _ = generate_serialize_cdr(ALL_COMBINATIONS, store, endianess)
