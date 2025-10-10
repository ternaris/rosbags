# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Mcap Storage Tests."""

from __future__ import annotations

import struct
from io import BytesIO
from itertools import groupby, product
from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
)
from rosbags.rosbag2.enums import CompressionMode
from rosbags.rosbag2.errors import ReaderError
from rosbags.rosbag2.storage_mcap import McapReader, McapWriter

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path
    from typing import BinaryIO


def write_record(bio: BinaryIO, opcode: int, records: Iterable[bytes | memoryview]) -> None:
    """Write record."""
    data = b''.join(records)
    _ = bio.write(bytes([opcode]) + struct.pack('<Q', len(data)) + data)


def make_string(text: str) -> bytes:
    """Serialize string."""
    data = text.encode()
    return struct.pack('<I', len(data)) + data


MCAP_HEADER = b'\x89MCAP0\r\n'

SCHEMAS = [
    (
        0x03,
        (
            struct.pack('<H', 1),
            make_string('geometry_msgs/msg/Polygon'),
            make_string('ros2msg'),
            make_string('string foo'),
        ),
    ),
    (
        0x03,
        (
            struct.pack('<H', 2),
            make_string('sensor_msgs/msg/MagneticField'),
            make_string('ros2msg'),
            make_string('string foo'),
        ),
    ),
    (
        0x03,
        (
            struct.pack('<H', 3),
            make_string('trajectory_msgs/msg/JointTrajectory'),
            make_string('ros2msg'),
            make_string('string foo'),
        ),
    ),
]

CHANNELS = [
    (
        0x04,
        (
            struct.pack('<H', 1),
            struct.pack('<H', 1),
            make_string('/poly'),
            make_string('cdr'),
            make_string(''),
        ),
    ),
    (
        0x04,
        (
            struct.pack('<H', 2),
            struct.pack('<H', 2),
            make_string('/magn'),
            make_string('cdr'),
            make_string(''),
        ),
    ),
    (
        0x04,
        (
            struct.pack('<H', 3),
            struct.pack('<H', 3),
            make_string('/joint'),
            make_string('cdr'),
            make_string(''),
        ),
    ),
    (
        0x04,
        (
            struct.pack('<H', 4),
            struct.pack('<H', 0),
            make_string('/schemaless'),
            make_string('cdr'),
            struct.pack('<I', 11 + 28),
            make_string('foo'),
            make_string(''),
            make_string('offered_qos_profiles'),
            make_string(''),
        ),
    ),
]


@pytest.fixture(
    params=product(
        ['unindexed', 'indexed'],
        ['plain', 'chunked'],
        ['nostats', 'stats'],
    ),
    ids=lambda x: f'{x[0]}, {x[1]}, {x[2]}',
)
def bag_mcap(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """Assemble mcap file."""
    indexed, chunked, stats = request.param

    path = tmp_path / 'db.mcap'
    bio: BinaryIO
    messages: list[tuple[int, int, int]] = []
    chunks: list[list[bytes]] = []
    with path.open('wb') as realbio:
        bio = realbio
        _ = bio.write(MCAP_HEADER)
        write_record(bio, 0x01, (make_string('ros2'), make_string('test_mcap')))

        if chunked == 'chunked':
            bio = BytesIO()
            messages = []

        write_record(bio, *SCHEMAS[0])
        write_record(bio, *CHANNELS[0])
        messages.append((1, 666, bio.tell()))
        write_record(
            bio,
            0x05,
            (
                struct.pack('<H', 1),
                struct.pack('<I', 1),
                struct.pack('<Q', 666),
                struct.pack('<Q', 666),
                b'poly message',
            ),
        )

        if chunked == 'chunked':
            assert isinstance(bio, BytesIO)
            chunk_start = realbio.tell()
            compression = make_string('')
            uncompressed_size = struct.pack('<Q', len(bio.getbuffer()))
            compressed_size = struct.pack('<Q', len(bio.getbuffer()))
            write_record(
                realbio,
                0x06,
                (
                    struct.pack('<Q', 666),
                    struct.pack('<Q', 666),
                    uncompressed_size,
                    struct.pack('<I', 0),
                    compression,
                    compressed_size,
                    bio.getbuffer(),
                ),
            )
            message_index_offsets: list[tuple[int, int]] = []
            message_index_start = realbio.tell()
            for channel_id, group in groupby(messages, key=lambda x: x[0]):
                message_index_offsets.append((channel_id, realbio.tell()))
                tpls = [y for x in group for y in x[1:]]
                write_record(
                    realbio,
                    0x07,
                    (
                        struct.pack('<H', channel_id),
                        struct.pack('<I', 8 * len(tpls)),
                        struct.pack('<' + 'Q' * len(tpls), *tpls),
                    ),
                )
            chunk = [
                struct.pack('<Q', 666),
                struct.pack('<Q', 666),
                struct.pack('<Q', chunk_start),
                struct.pack('<Q', message_index_start - chunk_start),
                struct.pack('<I', 10 * len(message_index_offsets)),
                *(struct.pack('<HQ', *x) for x in message_index_offsets),
                struct.pack('<Q', realbio.tell() - message_index_start),
                compression,
                compressed_size,
                uncompressed_size,
            ]
            chunks.append(chunk)
            bio = BytesIO()
            messages = []

        write_record(bio, *SCHEMAS[1])
        write_record(bio, *CHANNELS[1])
        messages.append((2, 708, bio.tell()))
        write_record(
            bio,
            0x05,
            (
                struct.pack('<H', 2),
                struct.pack('<I', 1),
                struct.pack('<Q', 708),
                struct.pack('<Q', 708),
                b'magn message',
            ),
        )
        messages.append((2, 708, bio.tell()))
        write_record(
            bio,
            0x05,
            (
                struct.pack('<H', 2),
                struct.pack('<I', 2),
                struct.pack('<Q', 708),
                struct.pack('<Q', 708),
                b'magn message',
            ),
        )

        write_record(bio, *SCHEMAS[2])
        write_record(bio, *CHANNELS[2])
        messages.append((3, 708, bio.tell()))
        write_record(
            bio,
            0x05,
            (
                struct.pack('<H', 3),
                struct.pack('<I', 1),
                struct.pack('<Q', 708),
                struct.pack('<Q', 708),
                b'joint message',
            ),
        )

        write_record(bio, *CHANNELS[3])

        if chunked == 'chunked':
            assert isinstance(bio, BytesIO)
            chunk_start = realbio.tell()
            compression = make_string('')
            uncompressed_size = struct.pack('<Q', len(bio.getbuffer()))
            compressed_size = struct.pack('<Q', len(bio.getbuffer()))
            write_record(
                realbio,
                0x06,
                (
                    struct.pack('<Q', 708),
                    struct.pack('<Q', 708),
                    uncompressed_size,
                    struct.pack('<I', 0),
                    compression,
                    compressed_size,
                    bio.getbuffer(),
                ),
            )
            message_index_offsets = []
            message_index_start = realbio.tell()
            for channel_id, group in groupby(messages, key=lambda x: x[0]):
                message_index_offsets.append((channel_id, realbio.tell()))
                tpls = [y for x in group for y in x[1:]]
                write_record(
                    realbio,
                    0x07,
                    (
                        struct.pack('<H', channel_id),
                        struct.pack('<I', 8 * len(tpls)),
                        struct.pack('<' + 'Q' * len(tpls), *tpls),
                    ),
                )
            chunk = [
                struct.pack('<Q', 708),
                struct.pack('<Q', 708),
                struct.pack('<Q', chunk_start),
                struct.pack('<Q', message_index_start - chunk_start),
                struct.pack('<I', 10 * len(message_index_offsets)),
                *(struct.pack('<HQ', *x) for x in message_index_offsets),
                struct.pack('<Q', realbio.tell() - message_index_start),
                compression,
                compressed_size,
                uncompressed_size,
            ]
            chunks.append(chunk)
            bio = realbio
            messages = []

        if indexed == 'indexed' or stats == 'stats':
            summary_start = bio.tell()
            summary_offset_start = 0

            if indexed == 'indexed':
                for schema in SCHEMAS:
                    write_record(bio, *schema)
                for channel in CHANNELS:
                    write_record(bio, *channel)
                for chunk in chunks:
                    write_record(bio, 0x08, chunk)

                write_record(bio, 0x0A, (b'ignored',))
                write_record(bio, 0x0D, (b'ignored',))
                write_record(bio, 0xFF, (b'ignored',))

            if stats == 'stats':
                write_record(
                    bio,
                    0x0B,
                    (
                        struct.pack('<Q', 4),
                        struct.pack('<H', 3),
                        struct.pack('<I', 4),
                        struct.pack('<I', 0),
                        struct.pack('<I', 0),
                        struct.pack('<I', 2 if chunked == 'chunked' else 0),
                        struct.pack('<Q', 666),
                        struct.pack('<Q', 708),
                        # channel stats
                        struct.pack('<I', 40),
                        struct.pack('<H', 1),
                        struct.pack('<Q', 1),
                        struct.pack('<H', 2),
                        struct.pack('<Q', 2),
                        struct.pack('<H', 3),
                        struct.pack('<Q', 1),
                        struct.pack('<H', 4),
                        struct.pack('<Q', 0),
                    ),
                )
        else:
            summary_start = 0
            summary_offset_start = 0

        write_record(
            bio,
            0x02,
            (
                struct.pack('<Q', summary_start),
                struct.pack('<Q', summary_offset_start),
                struct.pack('<I', 0),
            ),
        )
        _ = bio.write(MCAP_HEADER)

    return path


def test_reader_mcap(bag_mcap: Path) -> None:
    """Test reader mcap reads all messages."""
    reader = McapReader(bag_mcap)
    reader.open()
    metadata = reader.metadata
    assert metadata.duration == 43
    assert metadata.start_time == 666
    assert metadata.end_time == 709
    assert metadata.message_count == 4
    if metadata.compression_mode:
        assert metadata.compression_format == 'zstd'
    assert reader.connections[0].msgcount == 1
    assert reader.connections[1].msgcount == 2
    assert reader.connections[2].msgcount == 1

    assert [x.id for x in reader.connections] == [1, 2, 3, 4]
    assert {x.topic for x in reader.connections} == {'/poly', '/magn', '/joint', '/schemaless'}
    gen = reader.messages(reader.connections)

    connection, timestamp, rawdata = next(gen)
    assert connection.topic == '/poly'
    assert connection.msgtype == 'geometry_msgs/msg/Polygon'
    assert timestamp == 666
    assert rawdata == b'poly message'

    for _ in range(2):
        connection, timestamp, rawdata = next(gen)
        assert connection.topic == '/magn'
        assert connection.msgtype == 'sensor_msgs/msg/MagneticField'
        assert timestamp == 708
        assert rawdata == b'magn message'

    connection, timestamp, rawdata = next(gen)
    assert connection.topic == '/joint'
    assert connection.msgtype == 'trajectory_msgs/msg/JointTrajectory'

    with pytest.raises(StopIteration):
        _ = next(gen)


def test_message_filters_mcap(bag_mcap: Path) -> None:
    """Test reader mcap filters messages."""
    reader = McapReader(bag_mcap)
    reader.open()
    magn_connections = [x for x in reader.connections if x.topic == '/magn']
    gen = reader.messages(connections=magn_connections)
    connection, _, _ = next(gen)
    assert connection.topic == '/magn'
    connection, _, _ = next(gen)
    assert connection.topic == '/magn'
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, start=667)
    connection, _, _ = next(gen)
    assert connection.topic == '/magn'
    connection, _, _ = next(gen)
    assert connection.topic == '/magn'
    connection, _, _ = next(gen)
    assert connection.topic == '/joint'
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, stop=667)
    connection, _, _ = next(gen)
    assert connection.topic == '/poly'
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(connections=magn_connections, stop=667)
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, start=666, stop=666)
    with pytest.raises(StopIteration):
        _ = next(gen)


def test_bag_mcap_files(tmp_path: Path) -> None:
    """Test reader raises if mcap files are bad."""
    path = tmp_path / 'db.db3.mcap'

    with pytest.raises(ReaderError, match='Could not open'):
        McapReader(path).open()

    path.touch()
    with pytest.raises(ReaderError, match='seems to be empty'):
        McapReader(path).open()

    _ = path.write_bytes(b'xxxxxxxx')
    with pytest.raises(ReaderError, match='magic is invalid'):
        McapReader(path).open()

    _ = path.write_bytes(b'\x89MCAP0\r\n\xff')
    with pytest.raises(ReaderError, match='Unexpected record'):
        McapReader(path).open()

    with path.open('wb') as bio:
        _ = bio.write(b'\x89MCAP0\r\n')
        write_record(bio, 0x01, (make_string('ros1'), make_string('test_mcap')))
    with pytest.raises(ReaderError, match='Profile is not'):
        McapReader(path).open()

    with path.open('wb') as bio:
        _ = bio.write(b'\x89MCAP0\r\n')
        write_record(bio, 0x01, (make_string('ros2'), make_string('test_mcap')))
    with pytest.raises(ReaderError, match='File end magic is invalid'):
        McapReader(path).open()


def test_write_empty(tmp_path: Path) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode.NONE)
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert not reader.schemas
    assert not reader.channels


def test_write_schema(tmp_path: Path) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode.NONE)
    connection = Connection(
        1,
        'topic',
        'msgtype',
        MessageDefinition(MessageDefinitionFormat.MSG, 'msgdef'),
        'digest',
        0,
        ConnectionExtRosbag2('cdr', []),
        None,
    )
    mcap.add_msgtype(connection)
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert not reader.channels
    assert not list(reader.messages([]))
    reader.close()


def test_write_channel(tmp_path: Path) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode.NONE)
    connection = Connection(
        1,
        'topic',
        'msgtype',
        MessageDefinition(MessageDefinitionFormat.MSG, 'msgdef'),
        'digest',
        0,
        ConnectionExtRosbag2('cdr', []),
        None,
    )
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, 'qos')
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert len(reader.channels) == 1
    assert not list(reader.messages([]))
    reader.close()


def test_write_message(tmp_path: Path) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode.NONE)
    connection = Connection(
        1,
        'topic',
        'msgtype',
        MessageDefinition(MessageDefinitionFormat.MSG, 'msgdef'),
        'digest',
        0,
        ConnectionExtRosbag2('cdr', []),
        None,
    )
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'msg1')
    mcap.write(connection, 43, b'msg2')
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert len(reader.channels) == 1
    assert list(reader.messages([connection])) == [
        (connection, 42, b'msg1'),
        (connection, 43, b'msg2'),
    ]
    assert len(reader.chunks) == 1
    reader.close()


@pytest.mark.parametrize('compression', ['none', 'storage'])
def test_write_multichunk(tmp_path: Path, compression: str) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode[compression.upper()])
    connection = Connection(
        1,
        'topic',
        'msgtype',
        MessageDefinition(MessageDefinitionFormat.MSG, 'msgdef'),
        'digest',
        0,
        ConnectionExtRosbag2('cdr', []),
        None,
    )
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 1
    reader.close()

    (bag / 'bag.mcap').unlink()

    mcap = McapWriter(bag, CompressionMode.NONE)
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.write(connection, 43, b'msg2')
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 2
    reader.close()
