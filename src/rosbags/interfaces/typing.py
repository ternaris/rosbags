# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags typing."""

import sys
from typing import Callable, Dict, List, Literal, Protocol, Tuple, TypeVar, Union

from . import Nodetype

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

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
Basetype: TypeAlias = Tuple[Basename, int]

BaseDesc: TypeAlias = Tuple[Literal[Nodetype.BASE], Basetype]
NameDesc: TypeAlias = Tuple[Literal[Nodetype.NAME], str]
FieldDesc: TypeAlias = Union[
    BaseDesc,
    NameDesc,
    Tuple[Literal[Nodetype.ARRAY, Nodetype.SEQUENCE], Tuple[Union[BaseDesc, NameDesc], int]],
]

ConstValue: TypeAlias = Union[str, bool, int, float]

Constdefs: TypeAlias = List[Tuple[str, Basename, ConstValue]]
Fielddefs: TypeAlias = List[Tuple[str, FieldDesc]]
Typesdict: TypeAlias = Dict[str, Tuple[Constdefs, Fielddefs]]


class Typestore(Protocol):
    """Type storage."""

    FIELDDEFS: Typesdict


Bitcvt = Callable[[bytes, int, bytes, int, Typestore], Tuple[int, int]]
BitcvtSize = Callable[[bytes, int, None, int, Typestore], Tuple[int, int]]

CDRDeser = Callable[[bytes, int, type, Typestore], Tuple[T, int]]
CDRSer = Callable[[bytes, int, object, Typestore], int]
CDRSerSize = Callable[[int, object, Typestore], int]
