# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag2 reader."""

# pyright: strict, reportUnreachable=false

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Protocol, cast

import zstandard
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from rosbags.interfaces import Connection, ConnectionExtRosbag2, TopicInfo
from rosbags.rosbag2.metadata import parse_qos

from .errors import ReaderError
from .storage_mcap import ReaderMcap
from .storage_sqlite3 import ReaderSqlite3

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


class StorageProtocol(Protocol):
    """Storage Protocol."""

    def __init__(self, paths: Iterable[Path], connections: Iterable[Connection]) -> None:
        """Initialize."""
        raise NotImplementedError  # pragma: no cover

    def open(self) -> None:
        """Open file."""
        raise NotImplementedError  # pragma: no cover

    def close(self) -> None:
        """Close file."""
        raise NotImplementedError  # pragma: no cover

    def get_definitions(self) -> dict[str, tuple[str, str]]:
        """Get message definitions."""
        raise NotImplementedError  # pragma: no cover

    def messages(
        self,
        connections: Iterable[Connection] = (),
        start: int | None = None,
        stop: int | None = None,
    ) -> Generator[tuple[Connection, int, bytes], None, None]:
        """Get messages from file."""
        raise NotImplementedError  # pragma: no cover


class Reader:
    """Reader for rosbag2 files.

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

    STORAGE_PLUGINS: Mapping[str, type[StorageProtocol]] = {
        'mcap': ReaderMcap,
        'sqlite3': ReaderSqlite3,
    }

    def __init__(self, path: Path | str) -> None:
        """Open rosbag and check metadata.

        Args:
            path: Filesystem path to bag.

        Raises:
            ReaderError: Bag not readable or bag metadata.

        """
        path = Path(path)
        yamlpath = path / 'metadata.yaml'
        self.path = path
        try:
            yaml = YAML(typ='safe')
            dct = cast(
                'dict[str, Metadata]',
                yaml.load(yamlpath.read_text()),  # pyright: ignore[reportUnknownMemberType]
            )
        except OSError as err:
            msg = f'Could not read metadata at {yamlpath}: {err}.'
            raise ReaderError(msg) from None
        except YAMLError as exc:
            msg = f'Could not load YAML from {yamlpath}: {exc}'
            raise ReaderError(msg) from None

        try:
            self.metadata: Metadata = dct['rosbag2_bagfile_information']
            if (ver := self.metadata['version']) > 9:
                msg = f'Rosbag2 version {ver} not supported; please report issue.'
                raise ReaderError(msg)
            if (storageid := self.metadata['storage_identifier']) not in self.STORAGE_PLUGINS:
                msg = f'Storage plugin {storageid!r} not supported; please report issue.'
                raise ReaderError(msg)

            self.paths = [path / Path(x).name for x in self.metadata['relative_file_paths']]
            if missing := [x for x in self.paths if not x.exists()]:
                msg = f'Some database files are missing: {[str(x) for x in missing]!r}'
                raise ReaderError(msg)

            self.connections = [
                Connection(
                    id=idx + 1,
                    topic=x['topic_metadata']['name'],
                    msgtype=x['topic_metadata']['type'],
                    msgdef='',
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
                for idx, x in enumerate(self.metadata['topics_with_message_count'])
            ]
            noncdr = {
                fmt
                for x in self.connections
                if isinstance(x.ext, ConnectionExtRosbag2)
                if (fmt := x.ext.serialization_format) != 'cdr'
            }
            if noncdr:
                msg = f'Serialization format {noncdr!r} is not supported.'
                raise ReaderError(msg)

            if self.compression_mode and (cfmt := self.compression_format) != 'zstd':
                msg = f'Compression format {cfmt!r} is not supported.'
                raise ReaderError(msg)

            self.files: list[FileInformation] = self.metadata.get('files', [])[:]
            self.custom_data: dict[str, str] = self.metadata.get('custom_data', {})

            self.tmpdir: TemporaryDirectory[str] | None = None
            self.storage: StorageProtocol | None = None
        except KeyError as exc:
            msg = f'A metadata key is missing {exc!r}.'
            raise ReaderError(msg) from None

    @property
    def duration(self) -> int:
        """Duration in nanoseconds between earliest and latest messages."""
        nsecs: int = self.metadata['duration']['nanoseconds']
        return nsecs + 1 if self.message_count else 0

    @property
    def start_time(self) -> int:
        """Timestamp in nanoseconds of the earliest message."""
        nsecs: int = self.metadata['starting_time']['nanoseconds_since_epoch']
        return nsecs if self.message_count else 2**63 - 1

    @property
    def end_time(self) -> int:
        """Timestamp in nanoseconds after the latest message."""
        return self.start_time + self.duration if self.message_count else 0

    @property
    def message_count(self) -> int:
        """Total message count."""
        return self.metadata['message_count']

    @property
    def compression_format(self) -> str | None:
        """Compression format."""
        return self.metadata.get('compression_format', None) or None

    @property
    def compression_mode(self) -> str | None:
        """Compression mode."""
        mode = self.metadata.get('compression_mode', '').lower()
        return mode if mode != 'none' else None

    @property
    def topics(self) -> dict[str, TopicInfo]:
        """Topic information."""
        return {x.topic: TopicInfo(x.msgtype, x.msgdef, x.msgcount, [x]) for x in self.connections}

    @property
    def ros_distro(self) -> str | None:
        """ROS distribution."""
        return self.metadata.get('ros_distro')

    def open(self) -> None:
        """Open rosbag2."""
        storage_paths: list[Path] = []
        if self.compression_mode == 'file':
            self.tmpdir = TemporaryDirectory()
            tmpdir = self.tmpdir.name
            decomp = zstandard.ZstdDecompressor()
            for path in self.paths:
                storage_file = Path(tmpdir, path.stem)
                with path.open('rb') as infile, storage_file.open('wb') as outfile:
                    _ = decomp.copy_stream(infile, outfile)
                storage_paths.append(storage_file)
        else:
            storage_paths = self.paths[:]

        self.storage = self.STORAGE_PLUGINS[self.metadata['storage_identifier']](
            storage_paths,
            self.connections,
        )
        self.storage.open()
        definitions = self.storage.get_definitions()
        for idx, conn in enumerate(self.connections):
            if desc := definitions.get(conn.msgtype):
                self.connections[idx] = Connection(
                    id=conn.id,
                    topic=conn.topic,
                    msgtype=conn.msgtype,
                    msgdef=desc[1],
                    digest=conn.digest,
                    msgcount=conn.msgcount,
                    ext=conn.ext,
                    owner=conn.owner,
                )

    def close(self) -> None:
        """Close rosbag2."""
        assert self.storage
        self.storage.close()
        self.storage = None
        if self.tmpdir:
            self.tmpdir.cleanup()
            self.tmpdir = None

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
        if not self.storage:
            msg = 'Rosbag is not open.'
            raise ReaderError(msg)

        if self.compression_mode == 'message':
            decomp = zstandard.ZstdDecompressor().decompress
            for connection, timestamp, data in self.storage.messages(connections, start, stop):
                yield connection, timestamp, decomp(data)
        else:
            yield from self.storage.messages(connections, start, stop)

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
