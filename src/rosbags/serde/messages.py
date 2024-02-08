# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Runtime message loader and cache."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype

from .cdr import generate_deserialize_cdr, generate_getsize_cdr, generate_serialize_cdr
from .ros1 import (
    generate_cdr_to_ros1,
    generate_deserialize_ros1,
    generate_getsize_ros1,
    generate_ros1_to_cdr,
    generate_serialize_ros1,
)
from .typing import Descriptor, DescriptorBase, DescriptorSeq, DescriptorType, Field, Msgdef
from .utils import Valtype

if TYPE_CHECKING:
    from rosbags.interfaces.typing import FieldDesc, Typestore


MSGDEFCACHE: dict[Typestore, dict[str, Msgdef[object]]] = {}


class SerdeError(Exception):
    """Serialization and Deserialization Error."""


def get_msgdef(typename: str, typestore: Typestore) -> Msgdef[object]:
    """Retrieve message definition for typename.

    Message definitions are cached globally and generated as needed.

    Args:
        typename: Msgdef type name to load.
        typestore: Type store.

    Returns:
        Message definition.

    """
    if typestore not in MSGDEFCACHE:
        MSGDEFCACHE[typestore] = {}
    cache = MSGDEFCACHE[typestore]

    if typename not in cache:
        entries = typestore.FIELDDEFS[typename][1]

        def fixup(entry: FieldDesc) -> Descriptor:
            if entry[0] == Nodetype.BASE:
                return DescriptorBase(Valtype.BASE, entry[1])
            if entry[0] == Nodetype.NAME:
                return DescriptorType(Valtype.MESSAGE, get_msgdef(entry[1], typestore))
            if entry[0] == Nodetype.ARRAY:
                return DescriptorSeq(Valtype.ARRAY, (fixup(entry[1][0]), entry[1][1]))
            if entry[0] == Nodetype.SEQUENCE:
                return DescriptorSeq(Valtype.SEQUENCE, (fixup(entry[1][0]), entry[1][1]))
            msg = f'Unknown field type {entry[0]!r} encountered.'  # pragma: no cover
            raise SerdeError(msg)  # pragma: no cover

        fields = [Field(name, fixup(desc)) for name, desc in entries]

        getsize_cdr, size_cdr = generate_getsize_cdr(fields)
        getsize_ros1, size_ros1 = generate_getsize_ros1(fields, typename)

        cache[typename] = Msgdef(
            typename,
            fields,
            getattr(typestore, typename.replace('/', '__')),
            size_cdr,
            getsize_cdr,
            generate_serialize_cdr(fields, 'le'),
            generate_serialize_cdr(fields, 'be'),
            generate_deserialize_cdr(fields, 'le'),
            generate_deserialize_cdr(fields, 'be'),
            size_ros1,
            getsize_ros1,
            generate_serialize_ros1(fields, typename),
            generate_deserialize_ros1(fields, typename),
            generate_ros1_to_cdr(fields, typename, copy=False),  # type: ignore[arg-type]
            generate_ros1_to_cdr(fields, typename, copy=True),  # type: ignore[arg-type]
            generate_cdr_to_ros1(fields, typename, copy=False),  # type: ignore[arg-type]
            generate_cdr_to_ros1(fields, typename, copy=True),  # type: ignore[arg-type]
        )
    return cache[typename]
