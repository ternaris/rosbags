# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Python types used in this package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, Union

if TYPE_CHECKING:
    from typing import Callable, Literal

    from rosbags.interfaces.typing import Basetype, Typestore

    from .utils import Valtype

    Bitcvt = Callable[[bytes, int, bytes, int, Typestore], 'tuple[int, int]']
    BitcvtSize = Callable[[bytes, int, None, int, Typestore], 'tuple[int, int]']

    CDRDeser = Callable[[bytes, int, type, Typestore], 'tuple[T, int]']
    CDRSer = Callable[[bytes, int, object, Typestore], int]
    CDRSerSize = Callable[[int, object, Typestore], int]

T = TypeVar('T')


class DescriptorBase(NamedTuple):
    """Value type descriptor."""

    valtype: Literal[Valtype.BASE]
    args: Basetype


class DescriptorType(NamedTuple):
    """Value type descriptor."""

    valtype: Literal[Valtype.MESSAGE]
    args: Msgdef[object]


class DescriptorSeq(NamedTuple):
    """Value type descriptor."""

    valtype: Literal[Valtype.SEQUENCE, Valtype.ARRAY]
    args: tuple[Descriptor, int]


Descriptor = Union[DescriptorBase, DescriptorType, DescriptorSeq]


class Field(NamedTuple):
    """Metadata of a field."""

    name: str
    descriptor: Descriptor


class Msgdef(NamedTuple, Generic[T]):
    """Metadata of a message."""

    name: str
    fields: list[Field]
    cls: type
    size_cdr: int
    getsize_cdr: CDRSerSize
    serialize_cdr_le: CDRSer
    serialize_cdr_be: CDRSer
    deserialize_cdr_le: CDRDeser[T]
    deserialize_cdr_be: CDRDeser[T]
    size_ros1: int
    getsize_ros1: CDRSerSize
    serialize_ros1: CDRSer
    deserialize_ros1: CDRDeser[T]
    getsize_ros1_to_cdr: BitcvtSize
    ros1_to_cdr: Bitcvt
    getsize_cdr_to_ros1: BitcvtSize
    cdr_to_ros1: Bitcvt
