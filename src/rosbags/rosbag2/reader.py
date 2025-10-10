# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag2 reader."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Protocol, cast

import zstandard
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
    TopicInfo,
)

from .errors import ReaderError
from .metadata import ReaderMetadata, parse_qos
from .storage_mcap import McapReader
from .storage_sqlite3 import Sqlite3Reader

if TYPE_CHECKING:
    import sys
    from collections.abc import Generator, Iterable, Mapping
    from types import TracebackType
    from typing import Literal

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    from .metadata import FileInformation, Metadata

    class ReaderProtocol(Protocol):
        """Sub Reader Protocol."""

        connections: list[Connection]
        metadata: ReaderMetadata

        def __init__(self, path: Path) -> None:
            """Initialize."""
            raise NotImplementedError  # pragma: no cover

        def open(self) -> None:
            """Open file."""
            raise NotImplementedError  # pragma: no cover

        def close(self) -> None:
            """Close file."""
            raise NotImplementedError  # pragma: no cover

        def messages(
            self,
            connections: Iterable[Connection],
            start: int | None = None,
            stop: int | None = None,
        ) -> Generator[tuple[Connection, int, bytes], None, None]:
            """Get messages from file."""
            raise NotImplementedError  # pragma: no cover


class DirectoryReader:
    """Reader for rosbag2 directories with metadata.yaml file.

    It implements all necessary features to access metadata and message
    streams.

    Version history:

        - Version 1: Initial format.
        - Version 2: Changed field sizes in C++ implementation.
        - Version 3: Added compression.
        - Version 4: Added QoS metadata to topics, changed relative file paths.
        - Version 5: Added per file metadata.
        - Version 6: Added custom_data dict to metadata.
        - Version 7: Added type_description_hash to topic metadata.
        - Version 8: Added ros_distro to metadata.
        - Version 9: Changed QoS metadata serialization and enums.

    """

    STORAGE_PLUGINS: Mapping[str, type[ReaderProtocol]] = {
        'mcap': McapReader,
        'sqlite3': Sqlite3Reader,
    }

    def __init__(self, path: Path) -> None:
        """Open rosbag and check metadata.

        Args:
            path: Filesystem path to bag.

        Raises:
            ReaderError: Bag not readable or bag metadata.

        """
        self.path = path
        if not (path / 'metadata.yaml').exists():
            msg = f'Expected metadata file {str(self.path)!r} does not exist.'
            raise FileNotFoundError(msg)

        self.tmpdir: TemporaryDirectory[str] | None = None
        self.connections: list[Connection] = []
        self.metadata = ReaderMetadata(0, 2**63 - 1, 0, 0, None, None, None, None)
        self.files: list[FileInformation] = []
        self.storages: list[ReaderProtocol] = []

    def open(self) -> None:
        """Open rosbag2."""
        yamlpath = self.path / 'metadata.yaml'
        try:
            yaml = YAML(typ='safe')
            dct = cast(
                'dict[str, Metadata]',
                yaml.load(yamlpath.read_text()),
            )
        except PermissionError:
            raise
        except OSError as err:
            msg = f'Could not read metadata at {yamlpath}: {err}.'
            raise ReaderError(msg) from None
        except YAMLError as exc:
            msg = f'Could not load YAML from {yamlpath}: {exc}'
            raise ReaderError(msg) from None

        try:
            metadata: Metadata = dct['rosbag2_bagfile_information']
            if (ver := metadata['version']) > 9:
                msg = f'Rosbag2 version {ver} not supported; please report issue.'
                raise ReaderError(msg)

            paths = [self.path / Path(x).name for x in metadata['relative_file_paths']]
            if missing := [x for x in paths if not x.exists()]:
                msg = f'Some database files are missing: {[str(x) for x in missing]!r}'
                raise ReaderError(msg)

            if (storageid := metadata['storage_identifier']) not in self.STORAGE_PLUGINS:
                msg = f'Storage plugin {storageid!r} not supported; please report issue.'
                raise ReaderError(msg)

            compression_format = metadata.get('compression_format', None) or None
            mode = metadata.get('compression_mode', '').lower()
            compression_mode = mode if mode != 'none' else None

            if compression_mode and (compression_format) != 'zstd':
                msg = f'Compression format {compression_format!r} is not supported.'
                raise ReaderError(msg)

            self.connections = [
                Connection(
                    id=idx + 1,
                    topic=x['topic_metadata']['name'],
                    msgtype=x['topic_metadata']['type'],
                    msgdef=MessageDefinition(MessageDefinitionFormat.NONE, ''),
                    digest=x['topic_metadata'].get('type_description_hash', ''),
                    msgcount=x['message_count'],
                    ext=ConnectionExtRosbag2(
                        serialization_format=x['topic_metadata']['serialization_format'],
                        offered_qos_profiles=parse_qos(
                            x['topic_metadata'].get('offered_qos_profiles', []),
                        ),
                    ),
                    owner=self,
                )
                for idx, x in enumerate(metadata['topics_with_message_count'])
            ]
            if noncdr := {
                fmt
                for x in self.connections
                if (fmt := cast('ConnectionExtRosbag2', x.ext).serialization_format) != 'cdr'
            }:
                msg = f'Serialization format {noncdr!r} is not supported.'
                raise ReaderError(msg)

            duration = metadata['duration']['nanoseconds']
            start_time = metadata['starting_time']['nanoseconds_since_epoch']
            message_count = metadata['message_count']

        except KeyError as exc:
            msg = f'A metadata key is missing {exc!r}.'
            raise ReaderError(msg) from None

        self.metadata = ReaderMetadata(
            duration=duration + 1 if message_count else 0,
            start_time=start_time if message_count else 2**63 - 1,
            end_time=start_time + duration + 1 if message_count else 0,
            message_count=message_count,
            compression_format=compression_format,
            compression_mode=compression_mode,
            ros_distro=metadata.get('ros_distro'),
            custom=metadata.get('custom_data'),
        )

        self.files = metadata.get('files', [])[:]

        storage_paths: list[Path] = []
        if compression_mode == 'file':
            self.tmpdir = TemporaryDirectory()
            tmpdir = self.tmpdir.name
            decomp = zstandard.ZstdDecompressor()
            for path in paths:
                storage_file = Path(tmpdir, path.stem)
                with path.open('rb') as infile, storage_file.open('wb') as outfile:
                    _ = decomp.copy_stream(infile, outfile)
                storage_paths.append(storage_file)
        else:
            storage_paths = paths[:]

        plugin = self.STORAGE_PLUGINS[metadata['storage_identifier']]
        try:
            for path in storage_paths:
                storage = plugin(path)
                storage.open()
                self.storages.append(storage)
        except:
            self.close()
            raise

        for idx, conn in enumerate(self.connections):
            if msgdef := next(
                (
                    y.msgdef
                    for x in self.storages
                    for y in x.connections
                    if y.msgtype == conn.msgtype and y.msgdef.format != MessageDefinitionFormat.NONE
                ),
                None,
            ):
                self.connections[idx] = conn._replace(msgdef=msgdef)

    def close(self) -> None:
        """Close rosbag2."""
        while self.storages:
            self.storages.pop().close()
        if self.tmpdir:
            self.tmpdir.cleanup()
            self.tmpdir = None

    def messages(
        self,
        connections: Iterable[Connection],
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
            ReaderError: If reader was not opened.

        """
        topics = [x.topic for x in connections]
        for storage in self.storages:
            storage_conns = [x for x in storage.connections if x.topic in topics]
            connmap = {
                x.id: next(y for y in connections if x.topic == y.topic) for x in storage_conns
            }
            if self.metadata.compression_mode == 'message':
                decomp = zstandard.ZstdDecompressor().decompress
                for storage_conn, timestamp, data in storage.messages(storage_conns, start, stop):
                    yield connmap[storage_conn.id], timestamp, decomp(data)
            else:
                for storage_conn, timestamp, data in storage.messages(storage_conns, start, stop):
                    yield connmap[storage_conn.id], timestamp, data


class Reader:
    """Unified Reader.

    It can read from rosbag2 directories or from raw storage files.

    """

    STORAGE_PLUGINS: Mapping[str, type[ReaderProtocol]] = {
        'dir': DirectoryReader,
        '.mcap': McapReader,
        '.db3': Sqlite3Reader,
    }

    def __init__(self, path: str | Path) -> None:
        """Initialize.

        Args:
            path: Filesystem path to bag.

        Raises:
            ReaderError: Path does not exist.

        """
        self.path = Path(path)
        if not self.path.exists():
            msg = f'File {str(self.path)!r} does not exist.'
            raise FileNotFoundError(msg)

        self.is_open = False

        self.storage: ReaderProtocol
        plugin_key = 'dir' if self.path.is_dir() else self.path.suffix
        if plugin := self.STORAGE_PLUGINS.get(plugin_key):
            self.storage = plugin(self.path)
        else:
            msg = f'Unrecognized storage format {self.path.suffix!r}'
            raise ReaderError(msg)

    def _check_open(self) -> None:
        """Ensure reader is open."""
        if not self.is_open:
            msg = 'Rosbag is not open.'
            raise ReaderError(msg)

    @property
    def duration(self) -> int:
        """Duration in nanoseconds between earliest and latest messages."""
        self._check_open()
        return self.storage.metadata.duration

    @property
    def start_time(self) -> int:
        """Timestamp in nanoseconds of the earliest message."""
        self._check_open()
        return self.storage.metadata.start_time

    @property
    def end_time(self) -> int:
        """Timestamp in nanoseconds after the latest message."""
        self._check_open()
        return self.storage.metadata.end_time

    @property
    def message_count(self) -> int:
        """Total message count."""
        self._check_open()
        return self.storage.metadata.message_count

    @property
    def compression_format(self) -> str | None:
        """Compression format."""
        self._check_open()
        return self.storage.metadata.compression_format

    @property
    def compression_mode(self) -> str | None:
        """Compression mode."""
        self._check_open()
        return self.storage.metadata.compression_mode

    @property
    def connections(self) -> list[Connection]:
        """Topic information."""
        self._check_open()
        return self.storage.connections

    @property
    def topics(self) -> dict[str, TopicInfo]:
        """Topic information."""
        self._check_open()
        return {
            x.topic: TopicInfo(x.msgtype, x.msgdef, x.msgcount, [x])
            for x in self.storage.connections
        }

    @property
    def ros_distro(self) -> str | None:
        """ROS distribution."""
        self._check_open()
        return self.storage.metadata.ros_distro

    def open(self) -> None:
        """Open rosbag2."""
        self.storage.open()
        self.is_open = True

    def close(self) -> None:
        """Open rosbag2."""
        self.storage.close()
        self.is_open = False

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
            ReaderError: If reader was not opened.

        """
        self._check_open()
        return self.storage.messages(connections or self.storage.connections, start, stop)

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
