# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Reader Tests."""

from __future__ import annotations

import sqlite3
import struct
from io import BytesIO
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest import mock

import pytest
import zstandard
from ruamel.yaml import YAML

from rosbags.rosbag2 import Reader, ReaderError, Writer
from rosbags.rosbag2.metadata import Metadata

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import BinaryIO

    from _pytest.fixtures import SubRequest

METADATA = """
rosbag2_bagfile_information:
  version: 4
  storage_identifier: sqlite3
  relative_file_paths:
    - db.db3{extension}
  duration:
    nanoseconds: 42
  starting_time:
    nanoseconds_since_epoch: 666
  message_count: 4
  topics_with_message_count:
    - topic_metadata:
        name: /poly
        type: geometry_msgs/msg/Polygon
        serialization_format: cdr
        offered_qos_profiles: ""
      message_count: 1
    - topic_metadata:
        name: /magn
        type: sensor_msgs/msg/MagneticField
        serialization_format: cdr
        offered_qos_profiles: ""
      message_count: 2
    - topic_metadata:
        name: /joint
        type: trajectory_msgs/msg/JointTrajectory
        serialization_format: cdr
        offered_qos_profiles: ""
      message_count: 1
  compression_format: {compression_format}
  compression_mode: {compression_mode}
"""

METADATA_EMPTY = """
rosbag2_bagfile_information:
  version: 8
  storage_identifier: sqlite3
  relative_file_paths:
    - db.db3
  duration:
    nanoseconds: 0
  starting_time:
    nanoseconds_since_epoch: 0
  message_count: 0
  topics_with_message_count: []
  compression_format: ""
  compression_mode: ""
  files:
  - duration:
      nanoseconds: 0
    message_count: 0
    path: db.db3
    starting_time:
      nanoseconds_since_epoch: 0
  custom_data:
    key1: value1
    key2: value2
  ros_distro: rosbags
"""


@pytest.fixture
def empty_bag(tmp_path: Path) -> Path:
    """Manually contruct empty bag."""
    _ = (tmp_path / 'metadata.yaml').write_text(METADATA_EMPTY)
    dbpath = tmp_path / 'db.db3'
    dbh = sqlite3.connect(dbpath)
    _ = dbh.executescript(Writer.SQLITE_SCHEMA)
    return tmp_path


@pytest.fixture(params=['none', 'file', 'message'])
def bag_sqlite3(request: SubRequest, tmp_path: Path) -> Path:
    """Manually contruct sqlite3 bag."""
    param: str = request.param  # pyright: ignore[reportAny]
    _ = (tmp_path / 'metadata.yaml').write_text(
        METADATA.format(
            extension='' if param != 'file' else '.zstd',
            compression_format='""' if param == 'none' else 'zstd',
            compression_mode='""' if param == 'none' else param.upper(),
        ),
    )

    comp = zstandard.ZstdCompressor()

    dbpath = tmp_path / 'db.db3'
    dbh = sqlite3.connect(dbpath)
    _ = dbh.executescript(Writer.SQLITE_SCHEMA)

    cur = dbh.cursor()
    _ = cur.execute(
        'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
        (1, '/poly', 'geometry_msgs/msg/Polygon', 'cdr', '', ''),
    )
    _ = cur.execute(
        'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
        (2, '/magn', 'sensor_msgs/msg/MagneticField', 'cdr', '', ''),
    )
    _ = cur.execute(
        'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
        (3, '/joint', 'trajectory_msgs/msg/JointTrajectory', 'cdr', '', ''),
    )
    _ = cur.execute(
        'INSERT INTO messages VALUES(?, ?, ?, ?)',
        (
            1,
            1,
            666,
            b'poly message' if param != 'message' else comp.compress(b'poly message'),
        ),
    )
    _ = cur.execute(
        'INSERT INTO messages VALUES(?, ?, ?, ?)',
        (
            2,
            2,
            708,
            b'magn message' if param != 'message' else comp.compress(b'magn message'),
        ),
    )
    _ = cur.execute(
        'INSERT INTO messages VALUES(?, ?, ?, ?)',
        (
            3,
            2,
            708,
            b'magn message' if param != 'message' else comp.compress(b'magn message'),
        ),
    )
    _ = cur.execute(
        'INSERT INTO messages VALUES(?, ?, ?, ?)',
        (
            4,
            3,
            708,
            b'joint message' if param != 'message' else comp.compress(b'joint message'),
        ),
    )
    dbh.commit()

    if param == 'file':
        with dbpath.open('rb') as ifh, (tmp_path / 'db.db3.zstd').open('wb') as ofh:
            _ = comp.copy_stream(ifh, ofh)
        dbpath.unlink()

    return tmp_path


def test_metadata() -> None:
    """Test empty metadata conforms to spec."""
    yaml = YAML(typ='safe')
    dct = cast(
        'dict[str, Metadata]',
        yaml.load(METADATA_EMPTY),  # pyright: ignore[reportUnknownMemberType]
    )
    assert dct['rosbag2_bagfile_information'].keys() == Metadata.__annotations__.keys()


def test_empty_bag(empty_bag: Path) -> None:
    """Test metadata of empty bag is correct."""
    with Reader(empty_bag) as reader:
        assert reader.message_count == 0
        assert reader.start_time == 2**63 - 1
        assert reader.end_time == 0
        assert reader.duration == 0
        assert not list(reader.messages())
        assert reader.custom_data['key1'] == 'value1'
        assert reader.custom_data['key2'] == 'value2'
        assert reader.ros_distro == 'rosbags'


def test_reader_sqlite3(bag_sqlite3: Path) -> None:
    """Test reader sqlite3 reads all messages."""
    with Reader(bag_sqlite3) as reader:
        assert reader.duration == 43
        assert reader.start_time == 666
        assert reader.end_time == 709
        assert reader.message_count == 4
        if reader.compression_mode:
            assert reader.compression_format == 'zstd'
        assert [x.id for x in reader.connections] == [1, 2, 3]
        assert [*reader.topics.keys()] == ['/poly', '/magn', '/joint']
        gen = reader.messages()

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


def test_message_filters(bag_sqlite3: Path) -> None:
    """Test reader sqlite3 filters messages."""
    with Reader(bag_sqlite3) as reader:
        magn_connections = [x for x in reader.connections if x.topic == '/magn']
        gen = reader.messages(connections=magn_connections)
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(start=667)
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/joint'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(stop=667)
        connection, _, _ = next(gen)
        assert connection.topic == '/poly'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(connections=magn_connections, stop=667)
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(start=666, stop=666)
        with pytest.raises(StopIteration):
            _ = next(gen)


def test_raises_if_reader_closed(bag_sqlite3: Path) -> None:
    """Test reader raises if methods called on closed."""
    reader = Reader(bag_sqlite3)
    with pytest.raises(ReaderError, match='Rosbag is not open'):
        _ = next(reader.messages())


def test_raises_on_broken_fs_layouts(tmp_path: Path) -> None:
    """Test reader raises if fs layout is broken."""
    with pytest.raises(ReaderError, match='not read metadata'):
        _ = Reader(tmp_path)

    metadata = tmp_path / 'metadata.yaml'

    _ = metadata.write_text('')
    with (
        pytest.raises(ReaderError, match='not read'),
        mock.patch.object(Path, 'read_text', side_effect=PermissionError),
    ):
        _ = Reader(tmp_path)

    _ = metadata.write_text('  invalid:\nthis is not yaml')
    with pytest.raises(ReaderError, match='not load YAML from'):
        _ = Reader(tmp_path)

    _ = metadata.write_text('foo:')
    with pytest.raises(ReaderError, match='key is missing'):
        _ = Reader(tmp_path)

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('version: 4', 'version: 999'),
    )
    with pytest.raises(ReaderError, match='version 999'):
        _ = Reader(tmp_path)

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('sqlite3', 'hdf5'),
    )
    with pytest.raises(ReaderError, match='Storage plugin'):
        _ = Reader(tmp_path)

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ),
    )
    with pytest.raises(ReaderError, match='files are missing'):
        _ = Reader(tmp_path)

    _ = (tmp_path / 'db.db3').write_text('')

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('cdr', 'bson'),
    )
    with pytest.raises(ReaderError, match='Serialization format'):
        _ = Reader(tmp_path)

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='"gz"',
            compression_mode='"file"',
        ),
    )
    with pytest.raises(ReaderError, match='Compression format'):
        _ = Reader(tmp_path)

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ),
    )
    with pytest.raises(ReaderError, match='not open database'), Reader(tmp_path) as reader:
        _ = next(reader.messages())


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
]


@pytest.fixture(
    params=['unindexed', 'partially_indexed', 'indexed', 'chunked_unindexed', 'chunked_indexed'],
)
def bag_mcap(request: SubRequest, tmp_path: Path) -> Path:
    """Manually contruct mcap bag."""
    param: str = request.param  # pyright: ignore[reportAny]
    _ = (tmp_path / 'metadata.yaml').write_text(
        METADATA.format(
            extension='.mcap',
            compression_format='""',
            compression_mode='""',
        ).replace('sqlite3', 'mcap'),
    )

    path = tmp_path / 'db.db3.mcap'
    bio: BinaryIO
    messages: list[tuple[int, int, int]] = []
    chunks: list[list[bytes]] = []
    with path.open('wb') as realbio:
        bio = realbio
        _ = bio.write(MCAP_HEADER)
        write_record(bio, 0x01, (make_string('ros2'), make_string('test_mcap')))

        if param.startswith('chunked'):
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

        if param.startswith('chunked'):
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

        if param.startswith('chunked'):
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

        if param in {'indexed', 'partially_indexed', 'chunked_indexed'}:
            summary_start = bio.tell()
            for schema in SCHEMAS:
                write_record(bio, *schema)
            if param != 'partially_indexed':
                for channel in CHANNELS:
                    write_record(bio, *channel)
            if param == 'chunked_indexed':
                for chunk in chunks:
                    write_record(bio, 0x08, chunk)

            summary_offset_start = 0
            write_record(bio, 0x0A, (b'ignored',))
            write_record(
                bio,
                0x0B,
                (
                    struct.pack('<Q', 4),
                    struct.pack('<H', 3),
                    struct.pack('<I', 3),
                    struct.pack('<I', 0),
                    struct.pack('<I', 0),
                    struct.pack('<I', 0 if param == 'indexed' else 1),
                    struct.pack('<Q', 666),
                    struct.pack('<Q', 708),
                    struct.pack('<I', 0),
                ),
            )
            write_record(bio, 0x0D, (b'ignored',))
            write_record(bio, 0xFF, (b'ignored',))
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

    return tmp_path


def test_reader_mcap(bag_mcap: Path) -> None:
    """Test reader mcap reads all messages."""
    with Reader(bag_mcap) as reader:
        assert reader.duration == 43
        assert reader.start_time == 666
        assert reader.end_time == 709
        assert reader.message_count == 4
        if reader.compression_mode:
            assert reader.compression_format == 'zstd'
        assert [x.id for x in reader.connections] == [1, 2, 3]
        assert [*reader.topics.keys()] == ['/poly', '/magn', '/joint']
        gen = reader.messages()

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
    with Reader(bag_mcap) as reader:
        magn_connections = [x for x in reader.connections if x.topic == '/magn']
        gen = reader.messages(connections=magn_connections)
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(start=667)
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/magn'
        connection, _, _ = next(gen)
        assert connection.topic == '/joint'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(stop=667)
        connection, _, _ = next(gen)
        assert connection.topic == '/poly'
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(connections=magn_connections, stop=667)
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(start=666, stop=666)
        with pytest.raises(StopIteration):
            _ = next(gen)


def test_bag_mcap_files(tmp_path: Path) -> None:
    """Test reader raises if mcap files are bad."""
    _ = (tmp_path / 'metadata.yaml').write_text(
        METADATA.format(
            extension='.mcap',
            compression_format='""',
            compression_mode='""',
        ).replace('sqlite3', 'mcap'),
    )

    path = tmp_path / 'db.db3.mcap'
    path.touch()
    reader = Reader(tmp_path)
    path.unlink()
    with pytest.raises(ReaderError, match='Could not open'):
        reader.open()

    path.touch()
    with pytest.raises(ReaderError, match='seems to be empty'):
        Reader(tmp_path).open()

    _ = path.write_bytes(b'xxxxxxxx')
    with pytest.raises(ReaderError, match='magic is invalid'):
        Reader(tmp_path).open()

    _ = path.write_bytes(b'\x89MCAP0\r\n\xff')
    with pytest.raises(ReaderError, match='Unexpected record'):
        Reader(tmp_path).open()

    with path.open('wb') as bio:
        _ = bio.write(b'\x89MCAP0\r\n')
        write_record(bio, 0x01, (make_string('ros1'), make_string('test_mcap')))
    with pytest.raises(ReaderError, match='Profile is not'):
        Reader(tmp_path).open()

    with path.open('wb') as bio:
        _ = bio.write(b'\x89MCAP0\r\n')
        write_record(bio, 0x01, (make_string('ros2'), make_string('test_mcap')))
    with pytest.raises(ReaderError, match='File end magic is invalid'):
        Reader(tmp_path).open()
