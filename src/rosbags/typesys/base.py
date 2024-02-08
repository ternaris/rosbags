# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Types and helpers used by message definition converters."""

from __future__ import annotations

import json
import keyword
from hashlib import sha256
from itertools import starmap
from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype

if TYPE_CHECKING:
    from typing import TypedDict

    from rosbags.interfaces.typing import FieldDesc, Typesdict, Typestore

    from .peg import Visitor

    class FieldType(TypedDict):
        """Field type."""

        type_id: int
        capacity: int
        string_capacity: int
        nested_type_name: str

    class Field(TypedDict):
        """Field."""

        name: str
        type: FieldType

    class Struct(TypedDict):
        """Struct."""

        type_name: str
        fields: list[Field]


class TypesysError(Exception):
    """Parser error."""


def normalize_fieldname(name: str) -> str:
    """Normalize field name.

    Avoid collisions with Python keywords.

    Args:
        name: Field name.

    Returns:
        Normalized name.

    """
    if keyword.iskeyword(name):
        return f'{name}_'
    return name


def parse_message_definition(visitor: Visitor, text: str) -> Typesdict:
    """Parse message definition.

    Args:
        visitor: Visitor instance to use.
        text: Message definition.

    Returns:
        Parsetree of message.

    Raises:
        TypesysError: Message parsing failed.

    """
    try:
        rule = visitor.RULES['specification']
        pos = rule.skip_ws(text, 0)
        npos, trees = rule.parse(text, pos)
        assert npos == len(text), f'Could not parse: {text!r}'
        return visitor.visit(trees)  # type: ignore[return-value]
    except Exception as err:  # noqa: BLE001
        msg = f'Could not parse: {text!r}'
        raise TypesysError(msg) from err


TIDMAP = {
    'int8': 2,
    'uint8': 3,
    'int16': 4,
    'uint16': 5,
    'int32': 6,
    'uint32': 7,
    'int64': 8,
    'uint64': 9,
    'float32': 10,
    'float64': 11,
    'float128': 12,
    'char': 13,
    # Unsupported 'wchar': 14,
    'bool': 15,
    'octet': 16,
    'string': 17,
    # Unsupported 'wstring': 18,
    # Unsupported 'fixed_string': 19,
    # Unsupported 'fixed_wstring': 20,
    'bounded_string': 21,
    # Unsupported 'bounded_wstring': 22,
}


def hash_rihs01(typ: str, typestore: Typestore) -> str:
    """Hash message definition.

    Args:
        typ: Message type name.
        typestore: Message type store.

    Returns:
        Hash value.

    """

    def get_field(name: str, desc: FieldDesc) -> Field:
        increment = 0
        capacity = 0
        string_capacity = 0
        subtype = ''
        if desc[0] == Nodetype.ARRAY:
            increment = 48
            capacity = desc[1][1]
            typ, rest = desc[1][0]
        elif desc[0] == Nodetype.SEQUENCE:
            count = desc[1][1]
            if count:
                increment = 96
                capacity = count
            else:
                increment = 144
            typ, rest = desc[1][0]
        else:
            typ, rest = desc

        if typ == Nodetype.NAME:
            tid = increment + 1
            assert isinstance(rest, str)
            subtype = rest
            get_struct(subtype)
        elif rest[0] == 'string' and rest[1]:
            assert isinstance(rest[1], int)
            string_capacity = rest[1]
            tid = increment + TIDMAP['bounded_string']
        else:
            assert isinstance(rest[0], str)
            tid = increment + TIDMAP[rest[0]]

        return {
            'name': name,
            'type': {
                'type_id': tid,
                'capacity': capacity,
                'string_capacity': string_capacity,
                'nested_type_name': subtype,
            },
        }

    struct_cache: dict[str, Struct] = {}

    def get_struct(typ: str) -> Struct:
        if typ not in struct_cache:
            struct_cache[typ] = {
                'type_name': typ,
                'fields': list(
                    starmap(
                        get_field,
                        typestore.FIELDDEFS[typ][1]
                        or [('structure_needs_at_least_one_member', (Nodetype.BASE, ('uint8', 0)))],
                    )
                ),
            }
        return struct_cache[typ]

    dct = {
        'type_description': get_struct(typ),
        'referenced_type_descriptions': [y for x, y in sorted(struct_cache.items()) if x != typ],
    }

    digest = sha256(json.dumps(dct).encode()).hexdigest()
    return f'RIHS01_{digest}'
