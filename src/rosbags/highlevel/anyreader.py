# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Tools for reading all rosbag versions with unified api."""

# pyright: strict, reportUnreachable=false

from __future__ import annotations

import functools
import operator
import warnings
from contextlib import suppress
from heapq import merge
from itertools import groupby
from typing import TYPE_CHECKING

from rosbags.interfaces import TopicInfo
from rosbags.rosbag1 import (
    Reader as Reader1,
    ReaderError as ReaderError1,
)
from rosbags.rosbag2 import (
    Reader as Reader2,
    ReaderError as ReaderError2,
)
from rosbags.typesys import Stores, get_types_from_idl, get_types_from_msg, get_typestore

if TYPE_CHECKING:
    import sys
    from collections.abc import Generator, Iterable, Sequence
    from pathlib import Path
    from types import TracebackType
    from typing import Literal

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    from rosbags.interfaces import Connection
    from rosbags.interfaces.typing import Typesdict
    from rosbags.typesys.store import Typestore


class AnyReaderError(Exception):
    """Reader error."""


ReaderErrors = (ReaderError1, ReaderError2)


class AnyReader:
    """Unified rosbag1 and rosbag2 reader."""

    readers: Sequence[Reader1] | Sequence[Reader2]
    typestore: Typestore

    def __init__(
        self, paths: Sequence[Path], *, default_typestore: Typestore | None = None
    ) -> None:
        """Initialize RosbagReader.

        Opens one or multiple rosbag1 recordings or a single rosbag2 recording.

        Args:
            paths: Paths to multiple rosbag1 files or single rosbag2 directory.
            default_typestore: Typestore to deserialize messages if bag has
                no embedded message definions.

        Raises:
            AnyReaderError: If paths do not exist.

        """
        if not paths:
            msg = 'Must call with at least one path.'
            raise AnyReaderError(msg)

        if missing := [x for x in paths if not x.exists()]:
            msg = f'The following paths are missing: {missing!r}'
            raise AnyReaderError(msg)

        self.paths = paths
        self.is2 = (paths[0] / 'metadata.yaml').exists()
        self.isopen = False
        self.connections: list[Connection] = []
        self.default_typestore = default_typestore
        self.typestore = get_typestore(Stores.EMPTY)

        try:
            if self.is2:
                self.readers = [Reader2(x) for x in paths]
            else:
                self.readers = [Reader1(x) for x in paths]
        except ReaderErrors as err:
            raise AnyReaderError(*err.args) from err

    def _deser_ros1(self, rawdata: bytes, typ: str) -> object:
        """Deserialize ROS1 message."""
        return self.typestore.deserialize_ros1(rawdata, typ)

    def _deser_ros2(self, rawdata: bytes, typ: str) -> object:
        """Deserialize CDR message."""
        return self.typestore.deserialize_cdr(rawdata, typ)

    def deserialize(self, rawdata: bytes, typ: str) -> object:
        """Deserialize message with appropriate helper."""
        return self._deser_ros2(rawdata, typ) if self.is2 else self._deser_ros1(rawdata, typ)

    def open(self) -> None:
        """Open rosbags."""
        assert not self.isopen
        rollback: list[Reader1 | Reader2] = []
        try:
            for reader in self.readers:
                reader.open()
                rollback.append(reader)
        except ReaderErrors as err:
            for reader in rollback:
                with suppress(*ReaderErrors):
                    reader.close()
            raise AnyReaderError(*err.args) from err

        typs: Typesdict = {}
        self.connections = [y for x in self.readers for y in x.connections]
        connections = [x for x in self.connections if x.msgdef]
        if connections:
            sep = '=' * 80 + '\n'
            for connection in connections:
                if connection.msgdef.startswith(f'{sep}IDL: '):
                    for msgdef in connection.msgdef.split(sep)[1:]:
                        hdr, idl = msgdef.split('\n', 1)
                        assert hdr.startswith('IDL: ')
                        typs.update(get_types_from_idl(idl))
                else:
                    typs.update(get_types_from_msg(connection.msgdef, connection.msgtype))

        elif self.default_typestore:
            typs.update(self.default_typestore.fielddefs)
        else:
            warnings.warn(
                (
                    'AnyReader should be instantiated with an explicit typestore when reading '
                    'old Rosbag2 files without embedded message type definions. Using `foxy` '
                    'types as a workaround.'
                ),
                category=DeprecationWarning,
                stacklevel=2,
            )
            typs.update(get_typestore(Stores.ROS2_FOXY).fielddefs)
        self.typestore.register(typs)
        self.isopen = True

    def close(self) -> None:
        """Close rosbag."""
        assert self.isopen
        for reader in self.readers:
            with suppress(*ReaderErrors):
                reader.close()
        self.isopen = False

    def __enter__(self) -> Self:
        """Open rosbags when entering contextmanager."""
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Close rosbags when exiting contextmanager."""
        self.close()
        return False

    @property
    def duration(self) -> int:
        """Duration in nanoseconds between earliest and latest messages."""
        return self.end_time - self.start_time

    @property
    def start_time(self) -> int:
        """Timestamp in nanoseconds of the earliest message."""
        return min(x.start_time for x in self.readers)

    @property
    def end_time(self) -> int:
        """Timestamp in nanoseconds after the latest message."""
        return max(x.end_time for x in self.readers)

    @property
    def message_count(self) -> int:
        """Total message count."""
        return sum(x.message_count for x in self.readers)

    @property
    def topics(self) -> dict[str, TopicInfo]:
        """Topics stored in the rosbags."""
        assert self.isopen

        def summarize(names_infos: Iterable[tuple[str, TopicInfo]]) -> TopicInfo:
            """Summarize topic infos."""
            infos = [x[1] for x in names_infos]
            return TopicInfo(
                msgtypes.pop() if len(msgtypes := {x.msgtype for x in infos}) == 1 else None,
                msgdefs.pop() if len(msgdefs := {x.msgdef for x in infos}) == 1 else None,
                sum(x.msgcount for x in infos),
                functools.reduce(operator.iadd, (x.connections for x in infos), []),
            )

        return {
            name: summarize(infos)
            for name, infos in groupby(
                sorted(
                    (x for reader in self.readers for x in reader.topics.items()),
                    key=lambda x: x[0],
                ),
                key=lambda x: x[0],
            )
        }

    def messages(
        self,
        connections: Iterable[Connection] = (),
        start: int | None = None,
        stop: int | None = None,
    ) -> Generator[tuple[Connection, int, bytes], None, None]:
        """Read messages from bags.

        Args:
            connections: Iterable with connections to filter for. An empty
                iterable disables filtering on connections.
            start: Yield only messages at or after this timestamp (ns).
            stop: Yield only messages before this timestamp (ns).

        Yields:
            Tuples of connection, timestamp (ns), and rawdata.

        """
        assert self.isopen

        def get_owner(connection: Connection) -> Reader1 | Reader2:
            assert isinstance(connection.owner, Reader1 | Reader2)
            return connection.owner

        if connections:
            generators = [
                reader.messages(connections=list(conns), start=start, stop=stop)
                for reader, conns in groupby(
                    sorted(connections, key=lambda x: id(get_owner(x))), key=get_owner
                )
            ]
        else:
            generators = [reader.messages(start=start, stop=stop) for reader in self.readers]
        yield from merge(*generators, key=lambda x: x[1])
