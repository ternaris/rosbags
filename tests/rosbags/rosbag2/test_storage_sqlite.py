# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Sqlite3 Storage Tests."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from rosbags.rosbag2.errors import ReaderError
from rosbags.rosbag2.storage_sqlite3 import Sqlite3Reader

if TYPE_CHECKING:
    from pathlib import Path

SQLITE_SCHEMA_V1 = """
CREATE TABLE topics(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  serialization_format TEXT NOT NULL
);
CREATE TABLE messages(
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  timestamp INTEGER NOT NULL,
  data BLOB NOT NULL
);
CREATE INDEX timestamp_idx ON messages (timestamp ASC);
"""

SQLITE_SCHEMA_V2 = """
CREATE TABLE topics(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  serialization_format TEXT NOT NULL,
  offered_qos_profiles TEXT NOT NULL
);
CREATE TABLE messages(
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  timestamp INTEGER NOT NULL,
  data BLOB NOT NULL
);
CREATE INDEX timestamp_idx ON messages (timestamp ASC);
"""

SQLITE_SCHEMA_V3 = """
CREATE TABLE schema(
  schema_version INTEGER PRIMARY KEY,
  ros_distro TEXT NOT NULL
);
CREATE TABLE metadata(
  id INTEGER PRIMARY KEY,
  metadata_version INTEGER NOT NULL,
  metadata TEXT NOT NULL
);
CREATE TABLE topics(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  serialization_format TEXT NOT NULL,
  offered_qos_profiles TEXT NOT NULL
);
CREATE TABLE messages(
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  timestamp INTEGER NOT NULL,
  data BLOB NOT NULL
);
CREATE INDEX timestamp_idx ON messages (timestamp ASC);
INSERT INTO schema(schema_version, ros_distro) VALUES (3, 'rosbags');
"""

SQLITE_SCHEMA_V4 = """
CREATE TABLE schema(
  schema_version INTEGER PRIMARY KEY,
  ros_distro TEXT NOT NULL
);
CREATE TABLE metadata(
  id INTEGER PRIMARY KEY,
  metadata_version INTEGER NOT NULL,
  metadata TEXT NOT NULL
);
CREATE TABLE topics(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  serialization_format TEXT NOT NULL,
  offered_qos_profiles TEXT NOT NULL,
  type_description_hash TEXT NOT NULL
);
CREATE TABLE message_definitions(
  id INTEGER PRIMARY KEY,
  topic_type TEXT NOT NULL,
  encoding TEXT NOT NULL,
  encoded_message_definition TEXT NOT NULL,
  type_description_hash TEXT NOT NULL
);
CREATE TABLE messages(
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  timestamp INTEGER NOT NULL,
  data BLOB NOT NULL
);
CREATE INDEX timestamp_idx ON messages (timestamp ASC);
INSERT INTO schema(schema_version, ros_distro) VALUES (4, 'rosbags');
"""


@pytest.fixture
def database(tmp_path: Path) -> Path:
    """Create empty database."""
    path = tmp_path / 'db.db3'
    con = sqlite3.connect(path)
    con.close()

    return path


@pytest.fixture(
    params=[
        (1, SQLITE_SCHEMA_V1),
        (2, SQLITE_SCHEMA_V2),
        (3, SQLITE_SCHEMA_V3),
        (4, SQLITE_SCHEMA_V4),
    ],
)
def schema(request: pytest.FixtureRequest, tmp_path: Path) -> int:
    """Create empty database."""
    version: int
    version, sql = request.param

    path = tmp_path / 'db.db3'
    con = sqlite3.connect(path)
    with con:
        _ = con.executescript(sql)
    con.close()

    return version


@pytest.fixture
def add_connections(database: Path, schema: int) -> None:
    """Add connections to database."""
    con = sqlite3.connect(database)
    with con:
        if schema >= 4:
            _ = con.execute(
                (
                    'INSERT INTO message_definitions(topic_type, encoding,'
                    ' encoded_message_definition, type_description_hash) VALUES (?, ?, ?, ?);'
                ),
                (
                    'std_msgs/msg/Empty',
                    'ros2msg',
                    '',
                    'RIHS01_20b625256f32d5dbc0d04fee44f43c41e51c70d3502f84b4a08e7a9c26a96312',
                ),
            )
            _ = con.execute(
                (
                    'INSERT INTO topics('
                    'name, type, serialization_format, offered_qos_profiles, type_description_hash'
                    ') VALUES (?, ?, ?, ?, ?), (?, ?, ?, ?, ?)'
                ),
                ('t1', 'm1', 'cdr', '', 'h1', 't2', 'm2', 'cdr', '', 'h2'),
            )
    con.close()


@pytest.fixture
def add_messages(database: Path) -> None:
    """Add messages to database."""
    con = sqlite3.connect(database)
    with con:
        _ = con.execute(
            ('INSERT INTO messages(topic_id, timestamp, data)VALUES (?, ?, ?), (?, ?, ?);'),
            (1, 42, b'', 1, 666, b''),
        )
    con.close()


def test_open_raises_on_missing_tables(database: Path) -> None:
    """Test open raises on missing tables."""
    reader = Sqlite3Reader(database)
    with pytest.raises(ReaderError, match='missing tables'):
        reader.open()


def test_detects_schema_version(database: Path, schema: int) -> None:
    """Test schema version is detected."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert reader.schema == schema
    reader.close()


@pytest.mark.usefixtures('schema')
@pytest.mark.parametrize('schema', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_empty_database_has_correct_metadata(database: Path) -> None:
    """Test empty database has correct metadata."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert reader.metadata.duration == 0
    assert reader.metadata.start_time == 2**63 - 1
    assert reader.metadata.end_time == 0
    assert reader.metadata.message_count == 0
    assert reader.connections == []
    reader.close()


@pytest.mark.usefixtures('schema', 'add_connections')
@pytest.mark.parametrize('schema', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_database_with_empty_connections_has_correct_metadata(database: Path) -> None:
    """Test database with empty connections has correct metadata."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert reader.metadata.duration == 0
    assert reader.metadata.start_time == 2**63 - 1
    assert reader.metadata.end_time == 0
    assert reader.metadata.message_count == 0
    assert len(reader.connections) == 2
    assert reader.connections[0].msgcount == 0
    assert reader.connections[1].msgcount == 0
    reader.close()


@pytest.mark.usefixtures('schema', 'add_connections', 'add_messages')
@pytest.mark.parametrize('schema', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_database_with_messages_has_correct_metadata(database: Path) -> None:
    """Test database with messages has correct metadata."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert reader.metadata.duration == 667 - 42
    assert reader.metadata.start_time == 42
    assert reader.metadata.end_time == 667
    assert reader.metadata.message_count == 2
    assert len(reader.connections) == 2
    assert reader.connections[0].msgcount == 2
    assert reader.connections[1].msgcount == 0
    reader.close()


@pytest.mark.usefixtures('add_connections')
def test_type_definitions_are_read(database: Path, schema: int) -> None:
    """Test type definitions are read."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert (schema < 4) ^ bool(reader.msgtypes)
    reader.close()


@pytest.mark.parametrize('database', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_messages_raises_on_closed_reader(database: Path) -> None:
    """Test messages raises on closed reader."""
    reader = Sqlite3Reader(database)
    with pytest.raises(AssertionError):
        _ = next(reader.messages([]))


@pytest.mark.usefixtures('schema', 'add_connections', 'add_messages')
@pytest.mark.parametrize('schema', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_messages_yields_data(database: Path) -> None:
    """Test database with messages has correct metadata."""
    reader = Sqlite3Reader(database)
    reader.open()
    assert list(reader.messages(())) == []
    assert list(reader.messages(reader.connections, start=1000)) == []
    assert list(reader.messages(reader.connections, stop=40)) == []
    assert list(reader.messages(reader.connections, stop=100)) == [(reader.connections[0], 42, b'')]
    reader.close()


@pytest.mark.usefixtures(
    'schema',
)
@pytest.mark.parametrize('schema', [(4, SQLITE_SCHEMA_V4)], indirect=True)
def test_messages_fiters(database: Path) -> None:
    """Test message filters."""
    con = sqlite3.connect(database)

    with con:
        _ = con.execute(
            'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
            (1, '/poly', 'geometry_msgs/msg/Polygon', 'cdr', '', ''),
        )
        _ = con.execute(
            'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
            (2, '/magn', 'sensor_msgs/msg/MagneticField', 'cdr', '', ''),
        )
        _ = con.execute(
            'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
            (3, '/joint', 'trajectory_msgs/msg/JointTrajectory', 'cdr', '', ''),
        )
        _ = con.execute(
            'INSERT INTO messages VALUES(?, ?, ?, ?)',
            (1, 1, 666, b'poly message'),
        )
        _ = con.execute(
            'INSERT INTO messages VALUES(?, ?, ?, ?)',
            (2, 2, 708, b'magn message'),
        )
        _ = con.execute(
            'INSERT INTO messages VALUES(?, ?, ?, ?)',
            (3, 2, 708, b'magn message'),
        )
        _ = con.execute(
            'INSERT INTO messages VALUES(?, ?, ?, ?)',
            (4, 3, 708, b'joint message'),
        )
    con.close()

    reader = Sqlite3Reader(database)
    reader.open()
    metadata = reader.metadata
    assert metadata.duration == 43
    assert metadata.start_time == 666
    assert metadata.end_time == 709
    assert metadata.message_count == 4
    assert [x.id for x in reader.connections] == [1, 2, 3]

    gen = reader.messages(reader.connections)

    cmap = {x.topic: x for x in reader.connections}
    assert next(gen) == (cmap['/poly'], 666, b'poly message')
    assert next(gen) == (cmap['/magn'], 708, b'magn message')
    assert next(gen) == (cmap['/magn'], 708, b'magn message')
    assert next(gen) == (cmap['/joint'], 708, b'joint message')

    with pytest.raises(StopIteration):
        _ = next(gen)

    magn_connections = [x for x in reader.connections if x.topic == '/magn']
    gen = reader.messages(connections=magn_connections)
    assert next(gen)[0] == cmap['/magn']
    assert next(gen)[0] == cmap['/magn']
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, start=667)
    assert next(gen)[0] == cmap['/magn']
    assert next(gen)[0] == cmap['/magn']
    assert next(gen)[0] == cmap['/joint']
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, stop=667)
    assert next(gen)[0] == cmap['/poly']
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(connections=magn_connections, stop=667)
    with pytest.raises(StopIteration):
        _ = next(gen)

    gen = reader.messages(reader.connections, start=666, stop=666)
    with pytest.raises(StopIteration):
        _ = next(gen)

    reader.close()
