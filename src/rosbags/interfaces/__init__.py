# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Shared interfaces."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, NamedTuple, Protocol, TypeAlias, TypeVar

from .typing import Nodetype as _Nodetype

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict

    from .typing import Fielddefs

T = TypeVar('T')

Nodetype = _Nodetype


class ConnectionExtRosbag1(NamedTuple):
    """Rosbag1 specific connection extensions."""

    callerid: str | None
    latching: int | None


class ConnectionExtRosbag2(NamedTuple):
    """Rosbag2 specific connection extensions."""

    serialization_format: str
    offered_qos_profiles: str


class Connection(NamedTuple):
    """Connection information."""

    id: int
    topic: str
    msgtype: str
    msgdef: str
    digest: str
    msgcount: int
    ext: ConnectionExtRosbag1 | ConnectionExtRosbag2
    owner: object


class TopicInfo(NamedTuple):
    """Topic information."""

    msgtype: str | None
    msgdef: str | None
    msgcount: int
    connections: list[Connection]


class Typestore(Protocol):
    """Type storage."""

    fielddefs: Typesdict

    def get_msgdef(self, typename: str) -> Msgdef[object]:
        """Get message definition."""
        raise NotImplementedError  # pragma: no cover


Bitcvt: TypeAlias = Callable[[bytes | memoryview, int, memoryview, int, Typestore], tuple[int, int]]
BitcvtSize: TypeAlias = Callable[[bytes | memoryview, int, None, int, Typestore], tuple[int, int]]

CDRDeser: TypeAlias = Callable[[bytes | memoryview, int, type, Typestore], tuple[T, int]]
CDRSer: TypeAlias = Callable[[memoryview, int, object, Typestore], int]
CDRSerSize: TypeAlias = Callable[[int, object, Typestore], int]


@dataclass(frozen=True)
class Msgdef(Generic[T]):
    """Metadata of a message."""

    name: str
    fields: Fielddefs
    cls: type[object]
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
