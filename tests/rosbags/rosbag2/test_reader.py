# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Reader Tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest
import zstandard
from ruamel.yaml import YAML

from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
)
from rosbags.rosbag2 import Reader, ReaderError
from rosbags.rosbag2.metadata import Metadata
from rosbags.rosbag2.reader import DirectoryReader

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


METADATA = """
rosbag2_bagfile_information:
  version: 4
  storage_identifier: mock
  relative_file_paths:
    - db0.dat{extension}
    - db1.dat{extension}
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
  storage_identifier: mock
  relative_file_paths:
    - db0.dat
    - db1.dat
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
    path: db0.dat
    starting_time:
      nanoseconds_since_epoch: 0
  - duration:
      nanoseconds: 0
    message_count: 0
    path: db1.dat
    starting_time:
      nanoseconds_since_epoch: 0
  custom_data:
    key1: value1
    key2: value2
  ros_distro: rosbags
"""


@pytest.fixture(autouse=True)
def mock_storage() -> Generator[MagicMock, None, None]:
    """Inject fake storage plugin."""
    mock_storage = MagicMock(name='MockStorage')

    with patch.dict(
        'rosbags.rosbag2.reader.DirectoryReader.STORAGE_PLUGINS', {'mock': mock_storage}
    ):
        yield mock_storage


@pytest.fixture
def empty_bag(tmp_path: Path) -> Path:
    """Manually construct empty bag."""
    _ = (tmp_path / 'metadata.yaml').write_text(METADATA_EMPTY)
    (tmp_path / 'db0.dat').touch()
    (tmp_path / 'db1.dat').touch()
    return tmp_path


@pytest.fixture
def nonempty_bag(tmp_path: Path) -> Path:
    """Manually construct empty bag."""
    _ = (tmp_path / 'metadata.yaml').write_text(
        METADATA.format(extension='', compression_format='""', compression_mode='""'),
    )
    (tmp_path / 'db0.dat').touch()
    (tmp_path / 'db1.dat').touch()
    return tmp_path


@pytest.fixture(params=['none', 'file', 'message'])
def bag_with_compression(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    mock_storage: MagicMock,
) -> Path:
    """Manually construct bag with compression."""
    param: str = request.param
    _ = (tmp_path / 'metadata.yaml').write_text(
        METADATA.format(
            extension='' if param != 'file' else '.zstd',
            compression_format='""' if param == 'none' else 'zstd',
            compression_mode='""' if param == 'none' else param.upper(),
        ),
    )

    comp = zstandard.ZstdCompressor()
    textcomp = comp.compress if request.param == 'message' else lambda x: bytes(x)

    db0 = tmp_path / 'db0.dat'
    db0.write_bytes(b'mockdata0')

    db1 = tmp_path / 'db1.dat'
    db1.write_bytes(b'mockdata1')

    if param == 'file':
        for item in [db0, db1]:
            with item.open('rb') as ifh, item.with_suffix('.dat.zstd').open('wb') as ofh:
                _ = comp.copy_stream(ifh, ofh)
                item.unlink()

    defargs = (
        MessageDefinition(MessageDefinitionFormat.NONE, ''),
        '',
        0,
        ConnectionExtRosbag2('cdr', []),
        None,
    )

    class MockStorage:
        """Mock Storage."""

        def __init__(self, path: Path) -> None:
            """Initialize."""
            self.index = int(path.stem[-1])
            self.path = path
            self.connections = (
                [
                    Connection(201, '/poly', 'geometry_msgs/msg/Polygon', *defargs),
                    Connection(101, '/magn', 'sensor_msgs/msg/MagneticField', *defargs),
                    Connection(301, '/joint', 'trajectory_msgs/msg/JointTrajectory', *defargs),
                ]
                if self.index
                else []
            )

        def open(self) -> None:
            """Open storage."""
            assert self.path.read_bytes().startswith(f'mockdata{self.index}'.encode())

        def close(self) -> None:
            """Close storage."""

        def messages(
            self,
            connections: Iterable[Connection],
            start: int | None = None,
            stop: int | None = None,
        ) -> Generator[tuple[Connection, int, bytes], None, None]:
            """Messages."""
            if not self.index:
                return

            cids = [x.id for x in connections]
            start = start or 0
            stop = stop or 1000

            for cid, timestamp, data in (
                (201, 666, textcomp(b'poly message')),
                (101, 708, textcomp(b'magn message')),
                (101, 708, textcomp(b'magn message')),
                (301, 708, textcomp(b'joint message')),
            ):
                if cid in cids and start <= timestamp < stop:
                    yield next(x for x in self.connections if x.id == cid), timestamp, data

    mock_storage.side_effect = MockStorage

    return tmp_path


def test_empty_metadata_conforms_to_spec() -> None:
    """Test empty metadata conforms to spec."""
    yaml = YAML(typ='safe')
    dct = cast(
        'dict[str, Metadata]',
        yaml.load(METADATA_EMPTY),
    )
    assert dct['rosbag2_bagfile_information'].keys() == Metadata.__annotations__.keys()


def test_directory_reader_raises_on_broken_fs_layouts(tmp_path: Path) -> None:
    """Test directory reader raises on broken filesystem layouts."""
    with pytest.raises(FileNotFoundError, match=r'metadata file .* does not exist'):
        DirectoryReader(tmp_path)

    metadata = tmp_path / 'metadata.yaml'
    metadata.touch()

    with (
        pytest.raises(PermissionError),
        patch.object(Path, 'read_text', side_effect=PermissionError),
    ):
        DirectoryReader(tmp_path).open()

    with (
        pytest.raises(ReaderError, match='not read'),
        patch.object(Path, 'read_text', side_effect=IsADirectoryError),
    ):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text('  invalid:\nthis is not yaml')
    with pytest.raises(ReaderError, match='not load YAML from'):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text('foo:')
    with pytest.raises(ReaderError, match='key is missing'):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text(METADATA_EMPTY)
    with pytest.raises(ReaderError, match='files are missing'):
        DirectoryReader(tmp_path).open()


def test_directory_reader_raises_on_unsupported_features(tmp_path: Path) -> None:
    """Test directory reader raises if fs layout is broken."""
    metadata = tmp_path / 'metadata.yaml'
    (tmp_path / 'db0.dat').touch()
    (tmp_path / 'db1.dat').touch()

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('version: 4', 'version: 999'),
    )
    with pytest.raises(ReaderError, match='version 999'):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('mock', 'hdf5'),
    )
    with pytest.raises(ReaderError, match='Storage plugin'):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='""',
            compression_mode='""',
        ).replace('cdr', 'bson'),
    )
    with pytest.raises(ReaderError, match='Serialization format'):
        DirectoryReader(tmp_path).open()

    _ = metadata.write_text(
        METADATA.format(
            extension='',
            compression_format='"gz"',
            compression_mode='"file"',
        ),
    )
    with pytest.raises(ReaderError, match='Compression format'):
        DirectoryReader(tmp_path).open()


def test_directory_reader_raises_on_storage_open_exception(
    empty_bag: Path,
    mock_storage: MagicMock,
) -> None:
    """Test directory reader raises on storage open exception."""

    class OpenError(Exception): ...

    first = MagicMock()
    second = MagicMock()
    second.open.side_effect = OpenError
    mock_storage.side_effect = [first, second]

    with pytest.raises(OpenError):
        DirectoryReader(empty_bag).open()

    first.open.assert_called_once()
    first.close.assert_called_once()
    second.open.assert_called_once()
    second.close.assert_not_called()


def test_directory_reader_has_correct_metadata_on_empty_bag(
    empty_bag: Path, mock_storage: MagicMock
) -> None:
    """Test directory reader has correct metadata on empty bag."""
    storage = MagicMock()
    mock_storage.return_value = storage

    reader = DirectoryReader(empty_bag)
    reader.open()
    metadata = reader.metadata
    assert metadata.message_count == 0
    assert metadata.start_time == 2**63 - 1
    assert metadata.end_time == 0
    assert metadata.duration == 0
    assert metadata.custom
    assert metadata.custom['key1'] == 'value1'
    assert metadata.custom['key2'] == 'value2'
    assert metadata.ros_distro == 'rosbags'


def test_directory_reader_has_correct_metadata_on_nonempty_bag(
    nonempty_bag: Path, mock_storage: MagicMock
) -> None:
    """Test directory reader has correct metadata on empty bag."""
    storage = MagicMock()
    mock_storage.return_value = storage

    reader = DirectoryReader(nonempty_bag)
    reader.open()
    metadata = reader.metadata
    assert metadata.message_count == 4
    assert metadata.start_time == 666
    assert metadata.end_time == 709
    assert metadata.duration == 43
    assert not metadata.custom
    assert not metadata.ros_distro


def test_directory_reader_integrates_msgdefs_into_connections(
    nonempty_bag: Path,
    mock_storage: MagicMock,
) -> None:
    """Test directory reader integrates msgdefs into connections."""
    storage = MagicMock()
    storage.connections = [
        Connection(
            1,
            '/poly',
            'geometry_msgs/msg/Polygon',
            MessageDefinition(MessageDefinitionFormat.MSG, 'uint8 foo'),
            '',
            0,
            ConnectionExtRosbag2('cdr', []),
            None,
        )
    ]
    mock_storage.return_value = storage

    reader = DirectoryReader(nonempty_bag)
    reader.open()
    assert reader.connections[0].msgdef.data == 'uint8 foo'


def test_reader_raises_on_missing_path(tmp_path: Path) -> None:
    """Test reader raises on missing path."""
    with pytest.raises(FileNotFoundError):
        _ = Reader(tmp_path / 'missing')


def test_reader_selects_plugins(tmp_path: Path) -> None:
    """Test reader raises on missing path."""
    mockdir = MagicMock()
    mockdb3 = MagicMock()
    with patch.dict(
        'rosbags.rosbag2.reader.Reader.STORAGE_PLUGINS', {'dir': mockdir, '.db3': mockdb3}
    ):
        _ = Reader(tmp_path)
        mockdir.assert_called_once_with(tmp_path)
        mockdb3.assert_not_called()
        mockdir.reset_mock()

        dbpath = tmp_path / 'foo.db3'
        dbpath.touch()
        _ = Reader(dbpath)
        mockdir.assert_not_called()
        mockdb3.assert_called_once_with(dbpath)

        dbpath = tmp_path / 'unknown.plug'
        dbpath.touch()
        with pytest.raises(ReaderError, match='Unrecognized storage format'):
            _ = Reader(dbpath)


def test_reader_passes_messages_to_plugins(bag_with_compression: Path) -> None:
    """Test reader passes messages to plugins."""
    with Reader(bag_with_compression) as reader:
        gen = reader.messages()

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


def test_reader_raises_if_closed(nonempty_bag: Path) -> None:
    """Test reader raises if methods called while closed."""
    reader = Reader(nonempty_bag)

    def check() -> None:
        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.duration

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.start_time

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.end_time

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.message_count

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.compression_format

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.compression_mode

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.connections

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.topics

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = reader.ros_distro

        with pytest.raises(ReaderError, match='Rosbag is not open'):
            _ = next(reader.messages())

    check()

    with reader:
        _ = reader.duration
        _ = reader.start_time
        _ = reader.end_time
        _ = reader.message_count
        _ = reader.compression_format
        _ = reader.compression_mode
        _ = reader.connections
        _ = reader.topics
        _ = reader.ros_distro
        with pytest.raises(StopIteration):
            _ = next(reader.messages())

    check()
