# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Sqlite3 storage."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, cast

from rosbags.interfaces import MessageDefinition, MessageDefinitionFormat
from rosbags.rosbag2.enums import CompressionMode
from rosbags.typesys.msg import get_types_from_msg
from rosbags.typesys.store import Typestore

from .errors import ReaderError, WriterError

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from pathlib import Path

    from rosbags.interfaces import Connection, ConnectionExtRosbag2


class Sqlite3Reader:
    """Sqlite3 storage reader."""

    def __init__(self, paths: Iterable[Path], connections: Iterable[Connection]) -> None:
        """Set up storage reader.

        Args:
            paths: Paths of storage files.
            connections: List of connections.
            store: Typestore.

        """
        self.paths = paths
        self.dbconns: list[sqlite3.Connection] = []
        self.schema = 0
        self.msgtypes: list[dict[str, str]] = []
        self.connections = connections

    def open(self) -> None:
        """Open rosbag2."""
        for path in self.paths:
            conn = sqlite3.connect(f'file:{path}?immutable=1', uri=True)
            conn.row_factory = lambda _, x: x  # pyright: ignore[reportUnknownLambdaType]
            cur = conn.cursor()
            _ = cur.execute(
                (
                    'SELECT count(*) FROM sqlite_master '
                    'WHERE type="table" AND name IN ("messages", "topics")'
                ),
            )
            if cur.fetchone()[0] != 2:
                msg = f'Cannot open database {path} or database missing tables.'
                raise ReaderError(msg)

            self.dbconns.append(conn)

        cur = self.dbconns[-1].cursor()
        if cur.execute('PRAGMA table_info(schema)').fetchall():
            schema: int
            (schema,) = cur.execute('SELECT schema_version FROM schema').fetchone()
        elif any(
            x[1] == 'offered_qos_profiles'
            for x in cast('Iterable[tuple[str, str]]', cur.execute('PRAGMA table_info(topics)'))
        ):
            schema = 2
        else:
            schema = 1

        if schema >= 4:
            msgtypes: list[dict[str, str]] = [
                {
                    'name': x[0],
                    'encoding': x[1],
                    'msgdef': x[2],
                    'digest': x[3],
                }
                for x in cast(
                    'Iterable[tuple[str, str, str, str]]',
                    cur.execute(
                        (
                            'SELECT topic_type, encoding, encoded_message_definition,'
                            ' type_description_hash FROM message_definitions ORDER BY id'
                        ),
                    ),
                )
            ]
            for typ in msgtypes:
                assert typ['encoding'] == 'ros2msg'
                types = get_types_from_msg(typ['msgdef'], typ['name'])

                store = Typestore()
                store.register(types)

                assert typ['digest'] == store.hash_rihs01(
                    typ['name'],
                ), f'Failed to parse {typ["name"]}'
        else:
            msgtypes = []

        self.schema = schema
        self.msgtypes = msgtypes

    def close(self) -> None:
        """Close rosbag2."""
        assert self.dbconns
        for dbconn in self.dbconns:
            dbconn.close()
        self.dbconns.clear()

    def get_definitions(self) -> dict[str, MessageDefinition]:
        """Get message definitions."""
        if not self.dbconns:
            msg = 'Rosbag has not been opened.'
            raise ReaderError(msg)
        fmtmap = {
            'ros2msg': MessageDefinitionFormat.MSG,
            'ros2idl': MessageDefinitionFormat.IDL,
        }
        return {
            x['name']: MessageDefinition(fmtmap[x['encoding']], x['msgdef']) for x in self.msgtypes
        }

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

        Raises:
            ReaderError: Bag not open.

        """
        if not self.dbconns:
            msg = 'Rosbag has not been opened.'
            raise ReaderError(msg)

        query = [
            'SELECT topics.id,messages.timestamp,messages.data',
            'FROM messages JOIN topics ON messages.topic_id=topics.id',
        ]
        args: list[Iterable[str] | int] = []
        clause = 'WHERE'

        if connections:
            topics = {x.topic for x in connections}
            query.append(f'{clause} topics.name IN ({",".join("?" for _ in topics)})')
            args += topics
            clause = 'AND'

        if start is not None:
            query.append(f'{clause} messages.timestamp >= ?')
            args.append(start)
            clause = 'AND'

        if stop is not None:
            query.append(f'{clause} messages.timestamp < ?')
            args.append(stop)
            clause = 'AND'

        query.append('ORDER BY timestamp')
        querystr = ' '.join(query)

        for conn in self.dbconns:
            topics_ids = cast(
                'list[tuple[str, int]]',
                list(conn.execute('SELECT name,id FROM topics')),
            )
            connmap = {  # pragma: no branch
                cid: conn
                for conn in (connections or self.connections)
                if (cid := next((cid for name, cid in topics_ids if name == conn.topic), None))
            }

            cur = cast('Iterable[tuple[int, int, bytes]]', conn.execute(querystr, args))

            for cid, timestamp, data in cur:
                yield connmap[cid], timestamp, data


class Sqlite3Writer:
    """Sqlite3 Storage Writer."""

    SQLITE_SCHEMA = """
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

    def __init__(self, path: Path, compression: CompressionMode) -> None:
        """Initialize sqlite3 storage."""
        if compression == CompressionMode.STORAGE:
            msg = 'SQLITE3 writer does not support storage-side compression.'
            raise WriterError(msg)

        self.path = path / f'{path.name}.db3'
        self.conn = sqlite3.connect(f'file:{self.path}', uri=True)
        _ = self.conn.executescript(self.SQLITE_SCHEMA)
        self.cursor = self.conn.cursor()

    def add_msgtype(self, connection: Connection) -> None:
        """Add a msgtype.

        Args:
            connection: Connection.

        """
        _ = self.cursor.execute(
            (
                'INSERT INTO message_definitions (topic_type, encoding,'
                ' encoded_message_definition, type_description_hash) VALUES(?, ?, ?, ?)'
            ),
            (
                connection.msgtype,
                'ros2msg' if connection.msgdef.format == MessageDefinitionFormat.MSG else 'ros2idl',
                connection.msgdef.data,
                connection.digest,
            ),
        )

    def add_connection(self, connection: Connection, offered_qos_profiles: str) -> None:
        """Add a connection.

        Args:
            connection: Connection.
            offered_qos_profiles: Serialized QoS profiles.

        """
        _ = self.cursor.execute(
            'INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)',
            (
                connection.id,
                connection.topic,
                connection.msgtype,
                cast('ConnectionExtRosbag2', connection.ext).serialization_format,
                offered_qos_profiles,
                connection.digest,
            ),
        )

    def write(self, connection: Connection, timestamp: int, data: bytes | memoryview) -> None:
        """Write message to rosbag2.

        Args:
            connection: Connection to write message to.
            timestamp: Message timestamp (ns).
            data: Serialized message data.

        """
        _ = self.cursor.execute(
            'INSERT INTO messages (topic_id, timestamp, data) VALUES(?, ?, ?)',
            (connection.id, timestamp, data),
        )

    def close(self, version: int, metadata: str) -> None:
        """Close rosbag2 after writing.

        Closes open database transactions and writes metadata.yaml.

        """
        self.cursor.execute(
            'INSERT INTO metadata(metadata_version, metadata) VALUES(?, ?)',
            (version, metadata),
        )

        self.conn.commit()
        _ = self.conn.execute('PRAGMA optimize')
        self.conn.close()
