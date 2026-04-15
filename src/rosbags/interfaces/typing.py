# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags typing."""

import sys
from enum import IntEnum, auto
from typing import Any, BinaryIO, Literal, Protocol, TypeAlias, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

T = TypeVar('T')


class Nodetype(IntEnum):
    """Parse tree node types.

    The first four match the Valtypes of final message definitions.
    """

    BASE = auto()
    NAME = auto()
    ARRAY = auto()
    SEQUENCE = auto()


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


class StatResult(Protocol):  # pragma: no cover
    """Start result protocol."""

    @property
    def st_size(self) -> int:
        """Proxy."""
        raise NotImplementedError


class RPath(Protocol):  # pragma: no cover
    """Reader path protocol."""

    def exists(self) -> bool:
        """Proxy."""
        raise NotImplementedError

    def is_dir(self) -> bool:
        """Proxy."""
        raise NotImplementedError

    def open(  # type: ignore[explicit-any]
        self,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> BinaryIO:
        """Proxy."""
        raise NotImplementedError

    def read_text(
        self,
        encoding: str | None = None,
    ) -> str:
        """Proxy."""
        raise NotImplementedError

    def stat(self, *, follow_symlinks: bool = True) -> StatResult:
        """Proxy."""
        raise NotImplementedError

    def __truediv__(self, key: str | Self) -> Self:
        """Proxy."""
        raise NotImplementedError

    @property
    def stem(self) -> str:
        """Proxy."""
        raise NotImplementedError

    @property
    def suffix(self) -> str:
        """Proxy."""
        raise NotImplementedError
