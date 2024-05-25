# Copyright 2020 - 2024 Ternarisstorage
# SPDX-License-Identifier: Apache-2.0
"""Mcap storage."""

from __future__ import annotations

import heapq
import struct
from io import BytesIO
from struct import iter_unpack, unpack_from
from typing import TYPE_CHECKING, NamedTuple, cast

import zstandard
from lz4.frame import decompress as lz4_decompress  # type: ignore[import-untyped]

from .errors import ReaderError

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from pathlib import Path
    from typing import BinaryIO

    from rosbags.interfaces import Connection

    Unpack = Callable[[bytes], 'tuple[int]']
    Unpack2 = Callable[[bytes], 'tuple[int, int]']
    Unpack4 = Callable[[bytes], 'tuple[int, int, int, int]']
    Unpack5 = Callable[[bytes], 'tuple[int, int, int, int, int]']


class Schema(NamedTuple):
    """Schema."""

    id: int
    name: str
    encoding: str
    data: str


class Channel(NamedTuple):
    """Channel."""

    id: int
    schema: str
    topic: str
    message_encoding: str
    metadata: bytes  # dict[str, str]


class Chunk(NamedTuple):
    """Chunk."""

    start_time: int
    end_time: int
    size: int
    crc: int
    compression: str
    records: bytes


class ChunkInfo(NamedTuple):
    """Chunk."""

    message_start_time: int
    message_end_time: int
    chunk_start_offset: int
    chunk_length: int
    message_index_offsets: dict[int, int]
    message_index_length: int
    compression: str
    compressed_size: int
    uncompressed_size: int
    channel_count: dict[int, int]


class Statistics(NamedTuple):
    """Statistics."""

    message_count: int
    schema_count: int
    channel_count: int
    attachement_count: int
    metadata_count: int
    chunk_count: int
    start_time: int
    end_time: int
    channel_message_counts: bytes


class Msg(NamedTuple):
    """Message wrapper."""

    timestamp: int
    offset: int
    connection: Connection | None
    data: bytes | None


MAXSIZE: int = 2**63 - 1

deserialize_uint16: Unpack = struct.Struct('<H').unpack
deserialize_uint32: Unpack = struct.Struct('<I').unpack
deserialize_uint64: Unpack = struct.Struct('<Q').unpack

deserialize_qq: Unpack2 = struct.Struct('<QQ').unpack
deserialize_qqqi: Unpack4 = struct.Struct('<QQQI').unpack
deserialize_qqqq: Unpack4 = struct.Struct('<QQQQ').unpack
deserialize_hiqq: Unpack4 = struct.Struct('<HIQQ').unpack
deserialize_qhiqq: Unpack5 = struct.Struct('<QHIQQ').unpack


def read_sized(bio: BinaryIO) -> bytes:
    """Read one record."""
    return bio.read(deserialize_uint64(bio.read(8))[0])


def skip_sized(bio: BinaryIO) -> None:
    """Read one record."""
    _ = bio.seek(deserialize_uint64(bio.read(8))[0], 1)


def read_bytes(bio: BinaryIO) -> bytes:
    """Read string."""
    return bio.read(deserialize_uint32(bio.read(4))[0])


def read_string(bio: BinaryIO) -> str:
    """Read string."""
    return bio.read(deserialize_uint32(bio.read(4))[0]).decode()


DECOMPRESSORS: dict[str, Callable[[bytes, int], bytes]] = {
    '': lambda x, _: x,
    'lz4': lambda x, _: cast('Callable[[bytes], bytes]', lz4_decompress)(x),
    'zstd': zstandard.ZstdDecompressor().decompress,
}


def msgsrc(
    chunk: ChunkInfo,
    channel_map: dict[int, Connection],
    start: int,
    stop: int,
    bio: BinaryIO,
) -> Generator[Msg, None, None]:
    """Yield messages from chunk in time order."""
    yield Msg(chunk.message_start_time, 0, None, None)

    _ = bio.seek(chunk.chunk_start_offset + 9 + 40 + len(chunk.compression))
    compressed_data = bio.read(chunk.compressed_size)
    subio = BytesIO(DECOMPRESSORS[chunk.compression](compressed_data, chunk.uncompressed_size))

    messages: list[Msg] = []
    while (offset := subio.tell()) < chunk.uncompressed_size:
        op_ = ord(subio.read(1))
        if op_ == 0x05:
            recio = BytesIO(read_sized(subio))
            channel_id, _, log_time, _ = deserialize_hiqq(recio.read(22))
            if start <= log_time < stop and channel_id in channel_map:
                messages.append(
                    Msg(
                        log_time,
                        chunk.chunk_start_offset + offset,
                        channel_map[channel_id],
                        recio.read(),
                    ),
                )
        else:
            skip_sized(subio)

    yield from sorted(messages, key=lambda x: x.timestamp)


class MCAPFile:
    """Mcap format reader."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path
        self.bio: BinaryIO | None = None
        self.data_start = 0
        self.data_end = 0
        self.schemas: dict[int, Schema] = {}
        self.channels: dict[int, Channel] = {}
        self.chunks: list[ChunkInfo] = []
        self.statistics: Statistics | None = None

    def open(self) -> None:
        """Open MCAP."""
        try:
            self.bio = self.path.open('rb')
        except OSError as err:
            msg = f'Could not open file {str(self.path)!r}: {err.strerror}.'
            raise ReaderError(msg) from err

        magic = self.bio.read(8)
        if not magic:
            msg = f'File {str(self.path)!r} seems to be empty.'
            raise ReaderError(msg)

        if magic != b'\x89MCAP0\r\n':
            msg = 'File magic is invalid.'
            raise ReaderError(msg)

        op_ = ord(self.bio.read(1))
        if op_ != 0x01:
            msg = 'Unexpected record.'
            raise ReaderError(msg)

        recio = BytesIO(read_sized(self.bio))
        profile = read_string(recio)
        if profile != 'ros2':
            msg = 'Profile is not ros2.'
            raise ReaderError(msg)
        self.data_start = self.bio.tell()

        _ = self.bio.seek(-37, 2)
        footer_start = self.bio.tell()
        data = self.bio.read()
        magic = data[-8:]
        if magic != b'\x89MCAP0\r\n':
            msg = 'File end magic is invalid.'
            raise ReaderError(msg)

        assert len(data) == 37
        assert data[0:9] == b'\x02\x14\x00\x00\x00\x00\x00\x00\x00', data[0:9]

        (summary_start,) = deserialize_uint64(data[9:17])
        if summary_start:
            self.data_end = summary_start
            self.read_index()
        else:
            self.data_end = footer_start

    def read_index(self) -> None:
        """Read index from file."""
        bio = self.bio
        assert bio

        schemas = self.schemas
        channels = self.channels
        chunks = self.chunks

        _ = bio.seek(self.data_end)
        while True:
            op_ = ord(bio.read(1))

            if op_ in {0x02, 0x0E}:
                break

            if op_ == 0x03:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schemas[key] = Schema(key, read_string(bio), read_string(bio), read_string(bio))

            elif op_ == 0x04:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schema_name = schemas[deserialize_uint16(bio.read(2))[0]].name
                channels[key] = Channel(
                    key,
                    schema_name,
                    read_string(bio),
                    read_string(bio),
                    read_bytes(bio),
                )

            elif op_ == 0x08:
                _ = bio.seek(8, 1)
                chunk = ChunkInfo(
                    *deserialize_qqqq(bio.read(32)),
                    {
                        x[0]: x[1]
                        for x in cast(
                            'Iterable[tuple[int, int]]',
                            iter_unpack('<HQ', bio.read(deserialize_uint32(bio.read(4))[0])),
                        )
                    },
                    *deserialize_uint64(bio.read(8)),
                    read_string(bio),
                    *deserialize_qq(bio.read(16)),
                    {},
                )
                offset_channel = sorted((v, k) for k, v in chunk.message_index_offsets.items())
                offsets = [
                    *[x[0] for x in offset_channel],
                    chunk.chunk_start_offset + chunk.chunk_length + chunk.message_index_length,
                ]
                chunk.channel_count.update(
                    {
                        x[1]: count // 16
                        for x, y, z in zip(offset_channel, offsets[1:], offsets, strict=False)
                        if (count := y - z - 15)
                    },
                )
                chunks.append(chunk)

            elif op_ == 0x0A:
                skip_sized(bio)

            elif op_ == 0x0B:
                _ = bio.seek(8, 1)
                self.statistics = Statistics(
                    *cast(
                        'tuple[int, int, int, int, int, int, int ,int]',
                        unpack_from('<QHIIIIQQ', bio.read(42), 0),
                    ),
                    read_bytes(bio),
                )

            elif op_ == 0x0D:
                skip_sized(bio)

            else:
                skip_sized(bio)

    def close(self) -> None:
        """Close MCAP."""
        assert self.bio
        self.bio.close()
        self.bio = None

    def meta_scan(self) -> None:
        """Generate metadata by scanning through file."""
        assert self.bio
        bio = self.bio
        bio_size = self.data_end
        _ = bio.seek(self.data_start)

        schemas = self.schemas
        channels = self.channels

        while bio.tell() < bio_size:
            op_ = ord(bio.read(1))

            if op_ == 0x03:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schemas[key] = Schema(key, read_string(bio), read_string(bio), read_string(bio))
            elif op_ == 0x04:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schema_name = schemas[unpack_from('<H', bio.read(2))[0]].name
                channels[key] = Channel(
                    key,
                    schema_name,
                    read_string(bio),
                    read_string(bio),
                    read_bytes(bio),
                )
            elif op_ == 0x06:
                _ = bio.seek(8, 1)
                _, _, uncompressed_size, _ = deserialize_qqqi(bio.read(28))
                compression = read_string(bio)
                (compressed_size,) = deserialize_uint64(bio.read(8))
                bio = BytesIO(
                    DECOMPRESSORS[compression](bio.read(compressed_size), uncompressed_size),
                )
                bio_size = uncompressed_size
            else:
                skip_sized(bio)

            if bio.tell() == bio_size and bio != self.bio:
                bio = self.bio
                bio_size = self.data_end

    def get_schema_definitions(self) -> dict[str, tuple[str, str]]:
        """Get schema definition."""
        if not self.schemas:
            self.meta_scan()
        return {schema.name: (schema.encoding[4:], schema.data) for schema in self.schemas.values()}

    def messages_scan(
        self,
        connections: Iterable[Connection],
        start: int | None = None,
        stop: int | None = None,
    ) -> Generator[tuple[Connection, int, bytes], None, None]:
        """Read messages by scanning whole bag."""
        assert self.bio
        bio = self.bio
        bio_size = self.data_end
        _ = bio.seek(self.data_start)

        schemas = self.schemas.copy()
        channels = self.channels.copy()

        if channels:
            read_meta = False
            channel_map = {  # pragma: no branch
                cid: conn
                for conn in connections
                if (
                    cid := next(
                        (
                            cid
                            for cid, x in self.channels.items()
                            if x.schema == conn.msgtype and x.topic == conn.topic
                        ),
                        None,
                    )
                )
            }
        else:
            read_meta = True
            channel_map = {}

        if start is None:
            start = 0
        if stop is None:
            stop = MAXSIZE

        while bio.tell() < bio_size:
            op_ = ord(bio.read(1))

            if op_ == 0x03 and read_meta:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schemas[key] = Schema(key, read_string(bio), read_string(bio), read_string(bio))
            elif op_ == 0x04 and read_meta:
                _ = bio.seek(8, 1)
                (key,) = deserialize_uint16(bio.read(2))
                schema_name = schemas[unpack_from('<H', bio.read(2))[0]].name
                channels[key] = Channel(
                    key,
                    schema_name,
                    read_string(bio),
                    read_string(bio),
                    read_bytes(bio),
                )
                conn = next(
                    (
                        x
                        for x in connections
                        if x.topic == channels[key].topic and x.msgtype == schema_name
                    ),
                    None,
                )
                if conn:
                    channel_map[key] = conn
            elif op_ == 0x05:
                size, channel_id, _, timestamp, _ = deserialize_qhiqq(bio.read(30))
                data = bio.read(size - 22)
                if start <= timestamp < stop and channel_id in channel_map:
                    yield channel_map[channel_id], timestamp, data
            elif op_ == 0x06:
                (size,) = deserialize_uint64(bio.read(8))
                start_time, end_time, uncompressed_size, _ = deserialize_qqqi(bio.read(28))
                if read_meta or (start < end_time and start_time < stop):
                    compression = read_string(bio)
                    (compressed_size,) = deserialize_uint64(bio.read(8))
                    bio = BytesIO(
                        DECOMPRESSORS[compression](bio.read(compressed_size), uncompressed_size),
                    )
                    bio_size = uncompressed_size
                else:
                    _ = bio.seek(size - 28, 1)
            else:
                skip_sized(bio)

            if bio.tell() == bio_size and bio != self.bio:
                bio = self.bio
                bio_size = self.data_end

    def messages(
        self,
        connections: Iterable[Connection],
        start: int | None = None,
        stop: int | None = None,
    ) -> Generator[tuple[Connection, int, bytes], None, None]:
        """Read messages from bag.

        Args:
            connections: Iterable with connections to filter for.
            start: Yield only messages at or after this timestamp (ns).
            stop: Yield only messages before this timestamp (ns).

        Yields:
            tuples of connection, timestamp (ns), and rawdata.

        """
        assert self.bio

        if not self.chunks:
            yield from self.messages_scan(connections, start, stop)
            return

        channel_map = {  # pragma: no branch
            cid: conn
            for conn in connections
            if (
                cid := next(
                    (
                        cid
                        for cid, x in self.channels.items()
                        if x.schema == conn.msgtype and x.topic == conn.topic
                    ),
                    None,
                )
            )
        }

        chunks = [
            msgsrc(
                x,
                channel_map,
                start or x.message_start_time,
                stop or x.message_end_time + 1,
                self.bio,
            )
            for x in self.chunks
            if x.message_start_time != 0
            and (start is None or start < x.message_end_time)
            and (stop is None or x.message_start_time < stop)
            and (any(x.channel_count.get(cid, 0) for cid in channel_map))
        ]

        for timestamp, offset, connection, data in heapq.merge(*chunks):
            if not offset:
                continue
            assert connection
            assert data
            yield connection, timestamp, data


class ReaderMcap:
    """Mcap storage reader."""

    def __init__(self, paths: Iterable[Path], connections: Iterable[Connection]) -> None:
        """Set up storage reader.

        Args:
            paths: Paths of storage files.
            connections: List of connections.

        """
        self.paths = paths
        self.readers: list[MCAPFile] = []
        self.connections = connections

    def open(self) -> None:
        """Open rosbag2."""
        self.readers = [MCAPFile(x) for x in self.paths]
        for reader in self.readers:
            reader.open()

    def close(self) -> None:
        """Close rosbag2."""
        assert self.readers
        for reader in self.readers:
            reader.close()
        self.readers = []

    def get_definitions(self) -> dict[str, tuple[str, str]]:
        """Get message definitions."""
        res: dict[str, tuple[str, str]] = {}
        for reader in self.readers:
            res.update(reader.get_schema_definitions())
        return res

    def messages(
        self,
        connections: Iterable[Connection] = (),
        start: int | None = None,
        stop: int | None = None,
    ) -> Generator[tuple[Connection, int, bytes], None, None]:
        """Read messages from bag.

        Args:
            connections: Iterable with connections to filter for. An empty
                iterable disables filtering on connections.
            start: Yield only messages at or after this timestamp (ns).
            stop: Yield only messages before this timestamp (ns).

        Yields:
            tuples of connection, timestamp (ns), and rawdata.

        """
        connections = list(connections) or list(self.connections)

        for reader in self.readers:
            yield from reader.messages(connections, start, stop)
