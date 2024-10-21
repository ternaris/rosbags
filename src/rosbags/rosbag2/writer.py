# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag2 writer."""

# pyright: strict, reportUnreachable=false

from __future__ import annotations

import sqlite3
import warnings
from enum import IntEnum, auto
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import zstandard
from ruamel.yaml import YAML

from rosbags.interfaces import Connection, ConnectionExtRosbag2, Qos
from rosbags.rosbag2.metadata import dump_qos_v8, dump_qos_v9, parse_qos
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    import sys
    from collections.abc import Sequence
    from types import TracebackType
    from typing import Literal

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    from rosbags.typesys.store import Typestore

    from .metadata import Metadata


class WriterError(Exception):
    """Writer Error."""


class Writer:
    """Rosbag2 writer.

    This class implements writing of rosbag2 files in version 8. It should be
    used as a contextmanager.

    """

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

    class CompressionMode(IntEnum):
        """Compession modes."""

        NONE = auto()
        FILE = auto()
        MESSAGE = auto()

    class CompressionFormat(IntEnum):
        """Compession formats."""

        ZSTD = auto()

    VERSION_LATEST: Literal[9] = 9

    def __init__(self, path: Path | str, *, version: Literal[8, 9] | None = None) -> None:
        """Initialize writer.

        Args:
            path: Filesystem path to bag.
            version: Rosbag2 file format version.

        Raises:
            WriterError: Target path exisits already, Writer can only create new rosbags.

        """
        path = Path(path)
        self.path = path
        if path.exists():
            msg = f'{path} exists already, not overwriting.'
            raise WriterError(msg)
        self.metapath = path / 'metadata.yaml'
        self.dbpath = path / f'{path.name}.db3'
        self.compression_mode = ''
        self.compression_format = ''
        self.compressor: zstandard.ZstdCompressor | None = None
        self.connections: list[Connection] = []
        self.counts: dict[int, int] = {}
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.custom_data: dict[str, str] = {}
        self.added_types: list[str] = []
        if not version:
            warnings.warn(
                'Writer should be called with an explicit version number (8 or 9).',
                category=DeprecationWarning,
                stacklevel=2,
            )
            version = 8
        self.version = version

    def set_compression(self, mode: Writer.CompressionMode, fmt: Writer.CompressionFormat) -> None:
        """Enable compression on bag.

        This function has to be called before opening.

        Args:
            mode: Compression mode to use, either 'file' or 'message'.
            fmt: Compressor to use, currently only 'zstd'.

        Raises:
            WriterError: Bag already open.

        """
        if self.conn:
            msg = f'Cannot set compression, bag {self.path} already open.'
            raise WriterError(msg)
        if mode == self.CompressionMode.NONE:
            return
        self.compression_mode = mode.name.lower()
        self.compression_format = fmt.name.lower()
        self.compressor = zstandard.ZstdCompressor()

    def set_custom_data(self, key: str, value: str) -> None:
        """Set key value pair in custom_data.

        Args:
            key: Key to set.
            value: Value to set.

        Raises:
            WriterError: If value has incorrect type.

        """
        if not isinstance(value, str):  # pyright:ignore[reportUnnecessaryIsInstance]
            msg = f'Cannot set non-string value {value!r} in custom_data.'
            raise WriterError(msg)
        self.custom_data[key] = value

    def open(self) -> None:
        """Open rosbag2 for writing.

        Create base directory and open database connection.

        """
        try:
            self.path.mkdir(mode=0o755, parents=True)
        except FileExistsError:
            msg = f'{self.path} exists already, not overwriting.'
            raise WriterError(msg) from None

        self.conn = sqlite3.connect(f'file:{self.dbpath}', uri=True)
        _ = self.conn.executescript(self.SQLITE_SCHEMA)
        self.cursor = self.conn.cursor()

    def add_connection(
        self,
        topic: str,
        msgtype: str,
        *,
        typestore: Typestore | None = None,
        msgdef: str | None = None,
        rihs01: str | None = None,
        serialization_format: str = 'cdr',
        offered_qos_profiles: Sequence[Qos] | str = (),
    ) -> Connection:
        """Add a connection.

        This function can only be called after opening a bag.

        Args:
            topic: Topic name.
            msgtype: Message type.
            typestore: Typestore.
            msgdef: Message definiton.
            rihs01: Message hash.
            serialization_format: Serialization format.
            offered_qos_profiles: QOS Profile.

        Returns:
            Connection object.

        Raises:
            WriterError: Bag not open or topic previously registered.

        """
        if not self.cursor:
            msg = 'Bag was not opened.'
            raise WriterError(msg)

        if msgdef is None or rihs01 is None:
            if not typestore:
                warnings.warn(
                    'Writer.add_connection should be called with typestore or msgdef/rihs01 pair.',
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                typestore = get_typestore(Stores.ROS2_FOXY)
            msgdef, _ = typestore.generate_msgdef(msgtype, ros_version=2)
            rihs01 = typestore.hash_rihs01(msgtype)
        assert msgdef is not None
        assert rihs01

        if msgtype not in self.added_types:
            _ = self.cursor.execute(
                (
                    'INSERT INTO message_definitions (topic_type, encoding,'
                    ' encoded_message_definition, type_description_hash) VALUES(?, ?, ?, ?)'
                ),
                (msgtype, 'ros2msg', msgdef, rihs01),
            )
            self.added_types.append(msgtype)

        if isinstance(offered_qos_profiles, str):
            warnings.warn(
                'Writer.add_connection should be called with instantiated QoS profiles.',
                category=DeprecationWarning,
                stacklevel=2,
            )
            qos_profiles = parse_qos(offered_qos_profiles)
        else:
            qos_profiles = list(offered_qos_profiles)

        connection = Connection(
            id=len(self.connections) + 1,
            topic=topic,
            msgtype=msgtype,
            msgdef=msgdef,
            digest=rihs01,
            msgcount=0,
            ext=ConnectionExtRosbag2(
                serialization_format=serialization_format,
                offered_qos_profiles=qos_profiles,
            ),
            owner=self,
        )
        for conn in self.connections:
            if (
                conn.topic == connection.topic
                and conn.msgtype == connection.msgtype
                and conn.ext == connection.ext
            ):
                msg = f'Connection can only be added once: {connection!r}.'
                raise WriterError(msg)

        self.connections.append(connection)
        self.counts[connection.id] = 0

        dump_qos = dump_qos_v9 if self.version >= 9 else dump_qos_v8
        dumped = dump_qos(qos_profiles)
        if not isinstance(dumped, str):
            stream = StringIO()
            yaml = YAML(typ='safe')
            yaml.default_flow_style = False
            yaml.dump(dumped, stream)  # pyright: ignore[reportUnknownMemberType]
            dumped = stream.getvalue().strip()

        meta = (
            connection.id,
            topic,
            msgtype,
            serialization_format,
            dumped,
            rihs01,
        )
        _ = self.cursor.execute('INSERT INTO topics VALUES(?, ?, ?, ?, ?, ?)', meta)
        return connection

    def write(self, connection: Connection, timestamp: int, data: bytes | memoryview) -> None:
        """Write message to rosbag2.

        Args:
            connection: Connection to write message to.
            timestamp: Message timestamp (ns).
            data: Serialized message data.

        Raises:
            WriterError: Bag not open or topic not registered.

        """
        if not self.cursor:
            msg = 'Bag was not opened.'
            raise WriterError(msg)
        if connection not in self.connections:
            msg = f'Tried to write to unknown connection {connection!r}.'
            raise WriterError(msg)

        if self.compression_mode == 'message':
            assert self.compressor
            data = self.compressor.compress(data)

        _ = self.cursor.execute(
            'INSERT INTO messages (topic_id, timestamp, data) VALUES(?, ?, ?)',
            (connection.id, timestamp, data),
        )
        self.counts[connection.id] += 1

    def close(self) -> None:
        """Close rosbag2 after writing.

        Closes open database transactions and writes metadata.yaml.

        """
        assert self.cursor
        assert self.conn
        self.cursor.close()
        self.cursor = None

        duration: int
        start: int
        count: int
        duration, start, count = self.conn.execute(
            'SELECT max(timestamp) - min(timestamp), min(timestamp), count(*) FROM messages',
        ).fetchone()

        dump_qos = dump_qos_v9 if self.version >= 9 else dump_qos_v8

        metadata: dict[str, Metadata] = {
            'rosbag2_bagfile_information': {
                'version': self.version,
                'storage_identifier': 'sqlite3',
                'relative_file_paths': [self.dbpath.name],
                'duration': {'nanoseconds': duration},
                'starting_time': {'nanoseconds_since_epoch': start},
                'message_count': count,
                'topics_with_message_count': [
                    {
                        'topic_metadata': {
                            'name': x.topic,
                            'type': x.msgtype,
                            'serialization_format': x.ext.serialization_format,
                            'offered_qos_profiles': dump_qos(x.ext.offered_qos_profiles),
                            'type_description_hash': x.digest,
                        },
                        'message_count': self.counts[x.id],
                    }
                    for x in self.connections
                    if isinstance(x.ext, ConnectionExtRosbag2)
                ],
                'compression_format': self.compression_format,
                'compression_mode': self.compression_mode,
                'files': [
                    {
                        'path': self.dbpath.name,
                        'starting_time': {'nanoseconds_since_epoch': start},
                        'duration': {'nanoseconds': duration},
                        'message_count': count,
                    },
                ],
                'custom_data': self.custom_data,
                'ros_distro': 'rosbags',
            },
        }

        metastr = StringIO()
        yaml = YAML(typ='safe')
        yaml.default_flow_style = False
        yaml.dump(metadata['rosbag2_bagfile_information'], metastr)  # pyright: ignore[reportUnknownMemberType]

        self.conn.execute(
            'INSERT INTO metadata(metadata_version, metadata) VALUES(?, ?)',
            (self.version, metastr.getvalue().strip()),
        )

        self.conn.commit()
        _ = self.conn.execute('PRAGMA optimize')
        self.conn.close()

        if self.compression_mode == 'file':
            assert self.compressor
            src = self.dbpath
            self.dbpath = src.with_suffix(f'.db3.{self.compression_format}')
            with src.open('rb') as infile, self.dbpath.open('wb') as outfile:
                _ = self.compressor.copy_stream(infile, outfile)
            src.unlink()
            metadata['rosbag2_bagfile_information']['relative_file_paths'] = [self.dbpath.name]
            metadata['rosbag2_bagfile_information']['files'][0]['path'] = self.dbpath.name

        metastr = StringIO()
        yaml.dump(metadata, metastr)  # pyright: ignore[reportUnknownMemberType]
        self.metapath.write_text(metastr.getvalue(), 'utf8')

    def __enter__(self) -> Self:
        """Open rosbag2 when entering contextmanager."""
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Close rosbag2 when exiting contextmanager."""
        self.close()
        return False
