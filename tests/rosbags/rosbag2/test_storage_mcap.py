# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Mcap Storage Tests."""

from __future__ import annotations

import struct
import sys
from io import BytesIO, StringIO
from itertools import groupby, product
from typing import TYPE_CHECKING, cast

import pytest
from ruamel.yaml import YAML

from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
    Qos,
    QosDurability,
    QosHistory,
    QosLiveliness,
    QosReliability,
    QosTime,
)
from rosbags.rosbag2.enums import CompressionMode
from rosbags.rosbag2.errors import ReaderError
from rosbags.rosbag2.metadata import dump_qos_v9
from rosbags.rosbag2.storage_mcap import McapReader, McapWriter, decompress, read_sized, skip_exact

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

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

LATCH = [
    Qos(
        QosHistory.UNKNOWN,
        0,
        QosReliability.RELIABLE,
        QosDurability.TRANSIENT_LOCAL,
        QosTime(2147483647, 4294967295),
        QosTime(2147483647, 4294967295),
        QosLiveliness.AUTOMATIC,
        QosTime(2147483647, 4294967295),
        avoid_ros_namespace_conventions=False,
    )
]


@pytest.fixture(scope='session')
def qos() -> str:
    """Preserialized QoS metadata for channels."""
    stream = StringIO()
    yaml = YAML(typ='safe')
    yaml.default_flow_style = False
    yaml.dump(
        dump_qos_v9(LATCH),
        stream,
    )
    return stream.getvalue().strip()


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


def test_incomplete_seek() -> None:
    """Test incomplete seek."""

    class BoundedStream(BytesIO):
        """Stream limiting seeks to its existing contents."""

        @override
        def seek(self, offset: int, whence: int = 0) -> int:
            assert whence == 0
            return super().seek(min(offset, len(self.getvalue())))

    with pytest.raises(ReaderError, match='expected 2 bytes, got 1'):
        skip_exact(BoundedStream(b'A'), 2)


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


def test_write_channel(tmp_path: Path, qos: str) -> None:
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
    mcap.add_connection(connection, offered_qos_profiles=qos)
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert len(reader.channels) == 1
    assert not list(reader.messages([]))
    offered_qos_profiles = cast(
        'ConnectionExtRosbag2',
        reader.connections[0].ext,
    ).offered_qos_profiles
    assert offered_qos_profiles == LATCH
    reader.close()


def test_write_message(tmp_path: Path, qos: str) -> None:
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
    mcap.add_connection(connection, offered_qos_profiles=qos)
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
def test_write_multichunk(tmp_path: Path, qos: str, compression: str) -> None:
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
    mcap.add_connection(connection, offered_qos_profiles=qos)
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 1
    reader.close()

    (bag / 'bag.mcap').unlink()

    mcap = McapWriter(bag, CompressionMode.NONE)
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, offered_qos_profiles=qos)
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.write(connection, 43, b'msg2')
    mcap.close(0, 'metadata')

    reader = McapReader(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 2
    reader.close()


def test_unindexed_bag_must_be_ordered(tmp_path: Path) -> None:
    """Test unindexed bags are ordered."""
    path = tmp_path / 'unordered.mcap'
    with path.open('wb') as bio:
        _ = bio.write(MCAP_HEADER)
        write_record(bio, 0x01, [make_string('ros2'), make_string('test')])
        for op, records in [SCHEMAS[0], CHANNELS[0]]:
            write_record(bio, op, records)
        for timestamp in [2, 1]:
            write_record(bio, 0x05, [struct.pack('<HIQQ', 1, 0, timestamp, timestamp), b'X'])
        write_record(bio, 0x0F, [struct.pack('<I', 0)])
        write_record(bio, 0x02, [struct.pack('<QQI', 0, 0, 0)])
        _ = bio.write(MCAP_HEADER)
    reader = McapReader(path)
    reader.open()
    try:
        with pytest.raises(ReaderError, match='timestamp order'):
            _ = list(reader.messages(reader.connections))
    finally:
        reader.close()


@pytest.mark.parametrize('data', [b'', struct.pack('<Q', 100) + b'A', struct.pack('<Q', 2**32 - 1)])
def test_reader_detects_truncated_records(data: bytes) -> None:
    """Test reader detects truncated records."""
    with pytest.raises(ReaderError, match='Truncated record'):
        _ = read_sized(BytesIO(data))


def test_reader_validates_chunk_size_and_checksum() -> None:
    """Test reader validates declared chunk size and checksum."""
    with pytest.raises(ReaderError, match='size mismatch'):
        _ = decompress(b'A', '', 2, 0)
    with pytest.raises(ReaderError, match='checksum mismatch'):
        _ = decompress(b'A', '', 1, 1)
    with pytest.raises(ReaderError, match='compression'):
        _ = decompress(b'A', 'unknown', 1, 0)


@pytest.mark.parametrize(('opcode', 'summary'), [(3, 0), (2, 1), (2, 2**63)])
def test_reader_rejects_invalid_footer(tmp_path: Path, opcode: int, summary: int) -> None:
    """Test reader rejects invalid footer."""
    path = tmp_path / 'invalid.mcap'
    with path.open('wb') as bio:
        _ = bio.write(MCAP_HEADER)
        write_record(bio, 0x01, [make_string('ros2'), make_string('test')])
        write_record(bio, opcode, [struct.pack('<QQI', summary, 0, 0)])
        _ = bio.write(MCAP_HEADER)
    reader = McapReader(path)
    with pytest.raises(ReaderError, match=r'Invalid MCAP footer|Invalid MCAP summary offset'):
        reader.open()
    assert reader.bio is None


@pytest.mark.parametrize(
    ('scan', 'record'),
    [
        ('metadata', 'message'),
        ('metadata', 'nested'),
        ('messages', 'message'),
        ('messages', 'nested'),
        ('messages', 'short_chunk'),
        ('messages', 'boundary'),
    ],
)
def test_reader_rejects_invalid_records(tmp_path: Path, scan: str, record: str) -> None:
    """Test reader rejects invalid records."""
    bio = BytesIO()
    if record == 'message':
        _ = bio.write(b'\x05' + struct.pack('<QHIQQ', 21, 1, 0, 1, 1))
        match = 'Invalid message record length'
    elif record == 'short_chunk':
        _ = bio.write(b'\x06' + struct.pack('<Q', 39))
        match = 'Invalid chunk record length'
    elif record == 'boundary':
        write_record(
            bio, 0x06, [struct.pack('<QQQI', 1, 1, 1, 0), make_string(''), struct.pack('<Q', 1)]
        )
        match = 'Compressed data exceeds'
    else:
        nested = b'\x06' + struct.pack('<Q', 40) + bytes(40)
        write_record(
            bio,
            0x06,
            [
                struct.pack('<QQQI', 1, 1, len(nested), 0),
                make_string(''),
                struct.pack('<Q', len(nested)),
                nested,
            ],
        )
        match = 'Nested MCAP chunks|Invalid chunk record length'
    reader = McapReader(tmp_path / 'unused.mcap')
    reader.bio = bio
    reader.data_end = len(bio.getvalue())
    try:
        if scan == 'metadata':
            with pytest.raises(ReaderError, match=match):
                reader.meta_scan()
        else:
            with pytest.raises(ReaderError, match=match):
                _ = list(reader.messages_scan([]))
    finally:
        reader.close()


def test_summary_channels_are_deduplicated(tmp_path: Path) -> None:
    """Test repeated summary channels produce a single connection."""
    bio = BytesIO()
    for opcode, records in [SCHEMAS[0], CHANNELS[0], CHANNELS[0]]:
        write_record(bio, opcode, records)
    write_record(bio, 0x0E, [])
    reader = McapReader(tmp_path / 'unused.mcap')
    reader.bio = bio
    try:
        reader.read_index()
        assert len(reader.connections) == 1
        assert reader.connections[0].id == 1
    finally:
        reader.close()
