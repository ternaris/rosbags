# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Reference CDR Message Serializer and Deserializer."""

from __future__ import annotations

import sys
from struct import Struct, pack_into, unpack_from
from typing import TYPE_CHECKING, cast

import numpy as np

from rosbags.interfaces import Nodetype
from rosbags.serde import SerdeError
from rosbags.serde.utils import SIZEMAP

if TYPE_CHECKING:
    from typing import TypeAlias

    from numpy.typing import NDArray

    from rosbags.interfaces import Msgdef, Typestore
    from rosbags.interfaces.typing import Basename, FieldDesc
    from rosbags.typesys.store import Msgarg

    Array: TypeAlias = 'list[object] | list[str] | NDArray[np.float64]'
    BasetypeMap: TypeAlias = 'dict[Basename, Struct]'

BASETYPEMAP_LE: BasetypeMap = {
    'bool': Struct('?'),
    'int8': Struct('b'),
    'int16': Struct('<h'),
    'int32': Struct('<i'),
    'int64': Struct('<q'),
    'uint8': Struct('B'),
    'uint16': Struct('<H'),
    'uint32': Struct('<I'),
    'uint64': Struct('<Q'),
    'float32': Struct('<f'),
    'float64': Struct('<d'),
}

BASETYPEMAP_BE: BasetypeMap = {
    'bool': Struct('?'),
    'int8': Struct('b'),
    'int16': Struct('>h'),
    'int32': Struct('>i'),
    'int64': Struct('>q'),
    'uint8': Struct('B'),
    'uint16': Struct('>H'),
    'uint32': Struct('>I'),
    'uint64': Struct('>Q'),
    'float32': Struct('>f'),
    'float64': Struct('>d'),
}


def deserialize_number(
    rawdata: bytes,
    bmap: BasetypeMap,
    pos: int,
    basetype: Basename,
) -> tuple[bool | float | int, int]:
    """Deserialize a single boolean, float, or int.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        basetype: Number type string.

    Returns:
        Deserialized number and new read position.

    """
    dtype, size = bmap[basetype], SIZEMAP[basetype]
    pos = (pos + size - 1) & -size
    return dtype.unpack_from(rawdata, pos)[0], pos + size


def deserialize_string(rawdata: bytes, bmap: BasetypeMap, pos: int) -> tuple[str, int]:
    """Deserialize a string value.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.

    Returns:
        Deserialized string and new read position.

    """
    pos = (pos + 4 - 1) & -4
    length: int = bmap['int32'].unpack_from(rawdata, pos)[0]
    val = bytes(rawdata[pos + 4 : pos + 4 + length - 1])
    return val.decode(), pos + 4 + length


def deserialize_array(
    rawdata: bytes,
    bmap: BasetypeMap,
    pos: int,
    num: int,
    desc: FieldDesc,
    typestore: Typestore,
) -> tuple[Array, int]:
    """Deserialize an array of items of same type.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        num: Number of elements.
        desc: Element type descriptor.
        typestore: Typestore.

    Returns:
        Deserialized array and new read position.

    Raises:
        SerdeError: Unexpected element type.

    """
    if desc[0] == Nodetype.BASE:
        if desc[1][0] == 'string':
            strs: list[str] = []
            while (num := num - 1) >= 0:
                val, pos = deserialize_string(rawdata, bmap, pos)
                strs.append(val)
            return strs, pos

        size = SIZEMAP[desc[1][0]]
        pos = (pos + size - 1) & -size
        ndarr = np.frombuffer(rawdata, dtype=desc[1][0], count=num, offset=pos)
        if (bmap is BASETYPEMAP_LE) != (sys.byteorder == 'little'):
            ndarr = ndarr.byteswap()  # no inplace on readonly array
        return ndarr, pos + num * SIZEMAP[desc[1][0]]

    if desc[0] == Nodetype.NAME:
        msgs: list[object] = []
        while (num := num - 1) >= 0:
            rosmsg, pos = deserialize_message(
                rawdata, bmap, pos, typestore.get_msgdef(desc[1]), typestore
            )
            msgs.append(rosmsg)
        return msgs, pos

    msg = f'Nested arrays {desc!r} are not supported.'
    raise SerdeError(msg)


def deserialize_message(
    rawdata: bytes,
    bmap: BasetypeMap,
    pos: int,
    msgdef: Msgdef[object],
    typestore: Typestore,
) -> tuple[object, int]:
    """Deserialize a message.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        msgdef: Message definition.
        typestore: Typestore.

    Returns:
        Deserialized message and new read position.

    """
    values: list[object] = []

    for _, desc in msgdef.fields:
        if desc[0] == Nodetype.NAME:
            obj, pos = deserialize_message(
                rawdata, bmap, pos, typestore.get_msgdef(desc[1]), typestore
            )
            values.append(obj)

        elif desc[0] == Nodetype.BASE:
            if desc[1][0] == 'string':
                val, pos = deserialize_string(rawdata, bmap, pos)
                values.append(val)
            else:
                num, pos = deserialize_number(rawdata, bmap, pos, desc[1][0])
                values.append(num)

        elif desc[0] == Nodetype.ARRAY:
            subdesc, length = desc[1]
            arr, pos = deserialize_array(rawdata, bmap, pos, length, subdesc, typestore)
            values.append(arr)

        elif desc[0] == Nodetype.SEQUENCE:
            size, pos = deserialize_number(rawdata, bmap, pos, 'int32')
            arr, pos = deserialize_array(rawdata, bmap, pos, int(size), desc[1][0], typestore)
            values.append(arr)

    return msgdef.cls(*values), pos


def deserialize(rawdata: bytes, typename: str, typestore: Typestore) -> object:
    """Deserialize raw data into a message object.

    Args:
        rawdata: Serialized data.
        typename: Type to deserialize.
        typestore: Typestore,

    Returns:
        Deserialized message object.

    """
    _, little_endian = cast('tuple[int, int]', unpack_from('BB', rawdata, 0))

    msgdef = typestore.get_msgdef(typename)
    obj, _ = deserialize_message(
        rawdata[4:],
        BASETYPEMAP_LE if little_endian else BASETYPEMAP_BE,
        0,
        msgdef,
        typestore,
    )

    return obj


def serialize_number(
    rawdata: memoryview,
    bmap: BasetypeMap,
    pos: int,
    basetype: Basename,
    val: float,
) -> int:
    """Serialize a single boolean, float, or int.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Write position.
        basetype: Number type string.
        val: Value to serialize.

    Returns:
        Next write position.

    """
    dtype, size = bmap[basetype], SIZEMAP[basetype]
    pos = (pos + size - 1) & -size
    dtype.pack_into(rawdata, pos, val)
    return pos + size


def serialize_string(rawdata: memoryview, bmap: BasetypeMap, pos: int, val: str) -> int:
    """Deserialize a string value.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Write position.
        val: Value to serialize.

    Returns:
        Next write position.

    """
    bval = memoryview(val.encode())
    length = len(bval) + 1

    pos = (pos + 4 - 1) & -4
    bmap['int32'].pack_into(rawdata, pos, length)
    rawdata[pos + 4 : pos + 4 + length - 1] = bval
    return pos + 4 + length


def serialize_array(
    rawdata: memoryview,
    bmap: BasetypeMap,
    pos: int,
    desc: FieldDesc,
    val: Array,
    typestore: Typestore,
) -> int:
    """Serialize an array of items of same type.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Write position.
        desc: Element type descriptor.
        val: Value to serialize.
        typestore: Typestore.

    Returns:
        Next write position.

    Raises:
        SerdeError: Unexpected element type.

    """
    if desc[0] == Nodetype.BASE:
        if desc[1][0] == 'string':
            for item in val:
                pos = serialize_string(rawdata, bmap, pos, cast('str', item))
            return pos

        size = SIZEMAP[desc[1][0]]
        pos = (pos + size - 1) & -size
        size *= len(val)
        val = cast('NDArray[np.float64]', val)
        if (bmap is BASETYPEMAP_LE) != (sys.byteorder == 'little'):
            val = val.byteswap()  # no inplace on readonly array
        rawdata[pos : pos + size] = memoryview(val.tobytes())
        return pos + size

    if desc[0] == Nodetype.NAME:
        for item in val:
            pos = serialize_message(
                rawdata, bmap, pos, item, typestore.get_msgdef(desc[1]), typestore
            )
        return pos

    msg = f'Nested arrays {desc!r} are not supported.'
    raise SerdeError(msg)  # pragma: no cover


def serialize_message(
    rawdata: memoryview,
    bmap: BasetypeMap,
    pos: int,
    message: object,
    msgdef: Msgdef[object],
    typestore: Typestore,
) -> int:
    """Serialize a message.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Write position.
        message: Message object.
        msgdef: Message definition.
        typestore: Typestore.

    Returns:
        Next write position.

    """
    for fieldname, desc in msgdef.fields:
        val: Msgarg = getattr(message, fieldname)
        if desc[0] == Nodetype.NAME:
            pos = serialize_message(
                rawdata, bmap, pos, val, typestore.get_msgdef(desc[1]), typestore
            )

        elif desc[0] == Nodetype.BASE:
            if desc[1][0] == 'string':
                assert isinstance(val, str)
                pos = serialize_string(rawdata, bmap, pos, val)
            else:
                assert isinstance(val, int | float)
                pos = serialize_number(rawdata, bmap, pos, desc[1][0], val)

        elif desc[0] == Nodetype.ARRAY:
            assert isinstance(val, list | np.ndarray)
            lval: list[str] = cast('list[str]', val)
            pos = serialize_array(rawdata, bmap, pos, desc[1][0], lval, typestore)

        elif desc[0] == Nodetype.SEQUENCE:
            assert isinstance(val, list | np.ndarray)
            lval = cast('list[str]', val)
            size = len(lval)
            pos = serialize_number(rawdata, bmap, pos, 'int32', size)
            pos = serialize_array(rawdata, bmap, pos, desc[1][0], lval, typestore)

    return pos


def get_array_size(desc: FieldDesc, val: Array, size: int, typestore: Typestore) -> int:
    """Calculate size of an array.

    Args:
        desc: Element type descriptor.
        val: Array to calculate size of.
        size: Current size of message.
        typestore: Typestore.

    Returns:
        Size of val in bytes.

    Raises:
        SerdeError: Unexpected element type.

    """
    if desc[0] == Nodetype.BASE:
        if desc[1][0] == 'string':
            for item in val:
                size = (size + 4 - 1) & -4
                assert isinstance(item, str)
                size += 4 + len(item) + 1
            return size

        isize = SIZEMAP[desc[1][0]]
        size = (size + isize - 1) & -isize
        return size + isize * len(val)

    if desc[0] == Nodetype.NAME:
        for item in val:
            size = get_size(item, typestore.get_msgdef(desc[1]), typestore, size)
        return size

    msg = f'Nested arrays {desc!r} are not supported.'
    raise SerdeError(msg)  # pragma: no cover


def get_size(message: object, msgdef: Msgdef[object], typestore: Typestore, size: int = 0) -> int:
    """Calculate size of serialzied message.

    Args:
        message: Message object.
        msgdef: Message definition.
        typestore: Typestore.
        size: Current size of message.

    Returns:
        Size of message in bytes.

    Raises:
        SerdeError: Unexpected array length in message.

    """
    for fieldname, desc in msgdef.fields:
        val: Msgarg = getattr(message, fieldname)
        if desc[0] == Nodetype.NAME:
            size = get_size(val, typestore.get_msgdef(desc[1]), typestore, size)

        elif desc[0] == Nodetype.BASE:
            if desc[1][0] == 'string':
                assert isinstance(val, str)
                size = (size + 4 - 1) & -4
                size += 4 + len(val.encode()) + 1
            else:
                isize = SIZEMAP[desc[1][0]]
                size = (size + isize - 1) & -isize
                size += isize

        elif desc[0] == Nodetype.ARRAY:
            subdesc, length = desc[1]
            assert isinstance(val, list | np.ndarray)
            lval: list[str] = cast('list[str]', val)
            if len(lval) != length:
                msg = f'Unexpected array length: {len(lval)} != {length}.'
                raise SerdeError(msg)
            size = get_array_size(subdesc, lval, size, typestore)

        elif desc[0] == Nodetype.SEQUENCE:
            assert isinstance(val, list | np.ndarray)
            lval = cast('list[str]', val)
            size = (size + 4 - 1) & -4
            size += 4
            size = get_array_size(desc[1][0], lval, size, typestore)

    return size


def serialize(
    message: object,
    typename: str,
    typestore: Typestore,
    *,
    little_endian: bool = sys.byteorder == 'little',
) -> memoryview:
    """Serialize message object to bytes.

    Args:
        message: Message object.
        typename: Type to serialize.
        little_endian: Should use little endianess.
        typestore: Typestore.

    Returns:
        Serialized bytes.

    """
    msgdef = typestore.get_msgdef(typename)
    size = 4 + get_size(message, msgdef, typestore)
    rawdata = memoryview(bytearray(size))

    pack_into('BB', rawdata, 0, 0, little_endian)
    pos = serialize_message(
        rawdata[4:],
        BASETYPEMAP_LE if little_endian else BASETYPEMAP_BE,
        0,
        message,
        msgdef,
        typestore,
    )
    assert pos + 4 == size
    return rawdata.toreadonly()
