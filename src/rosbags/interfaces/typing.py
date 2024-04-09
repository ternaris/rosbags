# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags typing."""

from collections.abc import Callable
from typing import Literal, Protocol, TypeAlias, TypeVar

from . import Nodetype

T = TypeVar('T')

Basename: TypeAlias = Literal[
    'bool',
    'byte',
    'char',
    'int8',
    'int16',
    'int32',
    'int64',
    'uint8',
    'uint16',
    'uint32',
    'uint64',
    'float32',
    'float64',
    'float128',
    'string',
]
Basetype: TypeAlias = tuple[Basename, int]

BaseDesc: TypeAlias = tuple[Literal[Nodetype.BASE], Basetype]
NameDesc: TypeAlias = tuple[Literal[Nodetype.NAME], str]
FieldDesc: TypeAlias = (
    BaseDesc
    | NameDesc
    | tuple[Literal[Nodetype.ARRAY, Nodetype.SEQUENCE], tuple[BaseDesc | NameDesc, int]]
)

ConstValue: TypeAlias = str | bool | int | float

Constdefs: TypeAlias = list[tuple[str, Basename, ConstValue]]
Fielddefs: TypeAlias = list[tuple[str, FieldDesc]]
Typesdict: TypeAlias = dict[str, tuple[Constdefs, Fielddefs]]


class Typestore(Protocol):
    """Type storage."""

    FIELDDEFS: Typesdict


Bitcvt = Callable[[bytes, int, bytes, int, Typestore], tuple[int, int]]
BitcvtSize = Callable[[bytes, int, None, int, Typestore], tuple[int, int]]

CDRDeser = Callable[[bytes, int, type, Typestore], tuple[T, int]]
CDRSer = Callable[[bytes, int, object, Typestore], int]
CDRSerSize = Callable[[int, object, Typestore], int]
