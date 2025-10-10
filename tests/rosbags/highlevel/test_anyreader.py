# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""AnyReader Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import pytest

from rosbags.highlevel import AnyReader, AnyReaderError
from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
)
from rosbags.rosbag1 import Writer as Writer1
from rosbags.rosbag2 import Writer as Writer2
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from rosbags.rosbag1 import Reader as Reader1
    from rosbags.typesys.stores.ros1_noetic import std_msgs__msg__Int8 as Int8

HEADER = b'\x00\x01\x00\x00'


class MockReader:
    """Mock reader simulating empty typestore."""

    def __init__(self, paths: list[Path]) -> None:
        """Initialize mock."""
        _ = paths
        self.connections = [
            Connection(
                1,
                '/foo',
                'test_msg/msg/Foo',
                MessageDefinition(MessageDefinitionFormat.NONE, ''),
                '',
                0,
                ConnectionExtRosbag2('', []),
                self,
            ),
        ]

    def open(self) -> None:
        """Unused."""


@pytest.fixture
def bags1(tmp_path: Path) -> list[Path]:
    """Test data fixture."""
    paths = [
        tmp_path / 'ros1_1.bag',
        tmp_path / 'ros1_2.bag',
        tmp_path / 'ros1_3.bag',
        tmp_path / 'bad.bag',
    ]
    store = get_typestore(Stores.LATEST)
    with Writer1(paths[0]) as writer:
        topic1 = writer.add_connection('/topic1', 'std_msgs/msg/Int8', typestore=store)
        topic2 = writer.add_connection('/topic2', 'std_msgs/msg/Int16', typestore=store)
        writer.write(topic1, 1, b'\x01')
        writer.write(topic2, 2, b'\x02\x00')
        writer.write(topic1, 9, b'\x09')
    with Writer1(paths[1]) as writer:
        topic1 = writer.add_connection('/topic1', 'std_msgs/msg/Int8', typestore=store)
        writer.write(topic1, 5, b'\x05')
    with Writer1(paths[2]) as writer:
        topic2 = writer.add_connection('/topic2', 'std_msgs/msg/Int16', typestore=store)
        writer.write(topic2, 15, b'\x15\x00')

    paths[3].touch()

    return paths


@pytest.fixture
def bags2(tmp_path: Path) -> list[Path]:
    """Test data fixture."""
    paths = [
        tmp_path / 'ros2_1',
        tmp_path / 'ros2_2',
        tmp_path / 'bad',
    ]
    store = get_typestore(Stores.LATEST)
    with Writer2(paths[0], version=Writer2.VERSION_LATEST) as writer:
        topic1 = writer.add_connection('/topic1', 'std_msgs/msg/Int8', typestore=store)
        topic2 = writer.add_connection('/topic2', 'std_msgs/msg/Int16', typestore=store)
        writer.write(topic1, 1, HEADER + b'\x01')
        writer.write(topic2, 2, HEADER + b'\x02\x00')
        writer.write(topic1, 9, HEADER + b'\x09')
        writer.write(topic1, 5, HEADER + b'\x05')
        writer.write(topic2, 15, HEADER + b'\x15\x00')

    store = get_typestore(Stores.LATEST)
    with Writer2(paths[1], version=Writer2.VERSION_LATEST) as writer:
        topic3 = writer.add_connection('/topic3', 'std_msgs/msg/Int32', typestore=store)
        writer.write(topic3, 4, HEADER + b'\x01\x00\x00\x00')

    paths[2].mkdir()
    _ = (paths[2] / 'metadata.yaml').write_text('x:')

    return paths


def test_anyreader1(bags1: Sequence[Path]) -> None:
    """Test AnyReader on rosbag1."""
    with pytest.raises(AnyReaderError, match='at least one'):
        _ = AnyReader([])

    with pytest.raises(FileNotFoundError, match='missing'):
        _ = AnyReader([bags1[0] / 'badname'])

    reader = AnyReader(bags1)
    with pytest.raises(AssertionError):
        assert reader.topics

    with pytest.raises(AssertionError):
        _ = next(reader.messages())

    reader = AnyReader(bags1)
    with pytest.raises(AnyReaderError, match='seems to be empty'):
        reader.open()
    assert all(not x.bio for x in cast('list[Reader1]', reader.readers))

    with AnyReader(bags1[:3]) as reader:
        assert reader.duration == 15
        assert reader.start_time == 1
        assert reader.end_time == 16
        assert reader.message_count == 5
        assert list(reader.topics.keys()) == ['/topic1', '/topic2']
        assert len(reader.topics['/topic1'].connections) == 2
        assert reader.topics['/topic1'].msgcount == 3
        assert len(reader.topics['/topic2'].connections) == 2
        assert reader.topics['/topic2'].msgcount == 2

        gen = reader.messages()

        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (1, b'\x01')

        msg: Int8
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 1
        nxt = next(gen)
        assert nxt[0].topic == '/topic2'
        assert nxt[1:] == (2, b'\x02\x00')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 2
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (5, b'\x05')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 5
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (9, b'\x09')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 9
        nxt = next(gen)
        assert nxt[0].topic == '/topic2'
        assert nxt[1:] == (15, b'\x15\x00')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 21
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(connections=reader.topics['/topic1'].connections)
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        with pytest.raises(StopIteration):
            _ = next(gen)


def test_anyreader2(bags2: list[Path]) -> None:
    """Test AnyReader on rosbag2."""
    with pytest.raises(AnyReaderError, match='key is missing'):
        AnyReader([bags2[2]]).open()

    typestore = get_typestore(Stores.LATEST)
    with AnyReader(bags2[:2], default_typestore=typestore) as reader:
        assert reader.duration == 15
        assert reader.start_time == 1
        assert reader.end_time == 16
        assert reader.message_count == 6
        assert list(reader.topics.keys()) == ['/topic1', '/topic2', '/topic3']
        assert len(reader.topics['/topic1'].connections) == 1
        assert reader.topics['/topic1'].msgcount == 3
        assert len(reader.topics['/topic2'].connections) == 1
        assert reader.topics['/topic2'].msgcount == 2
        assert len(reader.topics['/topic3'].connections) == 1
        assert reader.topics['/topic3'].msgcount == 1

        gen = reader.messages()

        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (1, HEADER + b'\x01')

        msg: Int8
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 1
        nxt = next(gen)
        assert nxt[0].topic == '/topic2'
        assert nxt[1:] == (2, HEADER + b'\x02\x00')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 2
        nxt = next(gen)
        assert nxt[0].topic == '/topic3'
        assert nxt[1:] == (4, HEADER + b'\x01\x00\x00\x00')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 1
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (5, HEADER + b'\x05')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 5
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        assert nxt[1:] == (9, HEADER + b'\x09')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 9
        nxt = next(gen)
        assert nxt[0].topic == '/topic2'
        assert nxt[1:] == (15, HEADER + b'\x15\x00')
        msg = cast('Int8', reader.deserialize(nxt[2], nxt[0].msgtype))
        assert msg.data == 21
        with pytest.raises(StopIteration):
            _ = next(gen)

        gen = reader.messages(connections=reader.topics['/topic1'].connections)
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        nxt = next(gen)
        assert nxt[0].topic == '/topic1'
        with pytest.raises(StopIteration):
            _ = next(gen)


def test_anyreader2_autoregister(bags2: list[Path]) -> None:
    """Test AnyReader on rosbag2."""

    class MockReader:
        """Mock reader."""

        def __init__(self, paths: list[Path]) -> None:
            """Initialize mock."""
            _ = paths
            self.connections = [
                Connection(
                    1,
                    '/foo',
                    'test_msg/msg/Foo',
                    MessageDefinition(MessageDefinitionFormat.MSG, 'string foo'),
                    'msg',
                    0,
                    ConnectionExtRosbag2('', []),
                    self,
                ),
                Connection(
                    2,
                    '/bar',
                    'test_msg/msg/Bar',
                    MessageDefinition(
                        MessageDefinitionFormat.MSG,
                        f'{"=" * 80}\nIDL: test_msg/msg/Bar\n'
                        'module test_msgs { module msg { struct Bar {string bar;}; }; };',
                    ),
                    'idl',
                    0,
                    ConnectionExtRosbag2('', []),
                    self,
                ),
                Connection(
                    3,
                    '/baz',
                    'test_msg/msg/Baz',
                    MessageDefinition(MessageDefinitionFormat.NONE, ''),
                    '',
                    0,
                    ConnectionExtRosbag2('', []),
                    self,
                ),
            ]

        def open(self) -> None:
            """Unused."""

    with (
        patch('rosbags.highlevel.anyreader.Reader2', MockReader),
        patch('rosbags.typesys.store.Typestore.register') as mock_register_types,
    ):
        AnyReader([bags2[0]]).open()
    mock_register_types.assert_called_once()
    assert mock_register_types.call_args[0][0] == {
        'test_msg/msg/Foo': ([], [('foo', (1, ('string', 0)))]),
        'test_msgs/msg/Bar': ([], [('bar', (1, ('string', 0)))]),
    }


def test_anyreader_raises_on_unknown_files(tmp_path: Path) -> None:
    """Test AnyReader raises on unknown files."""
    paths = [tmp_path / 'unknown', tmp_path / 'test.mcap']
    for path in paths:
        path.touch()

    with pytest.raises(AnyReaderError, match='Unrecognized storage format'):
        AnyReader(paths)


def test_anyreader_does_not_require_typestore_on_empty_bag(tmp_path: Path) -> None:
    """Test AnyReader does not require typestore on an empty bag."""
    path = tmp_path / 'test.bag'
    with Writer1(path):
        pass

    with AnyReader([path]) as reader:
        assert reader.connections == []


def test_anyreader_uses_default_typestore(bags2: list[Path]) -> None:
    """Test AnyReader uses default typestore."""
    with patch('rosbags.highlevel.anyreader.Reader2', MockReader):
        AnyReader([bags2[0]], default_typestore=get_typestore(Stores.EMPTY)).open()


def test_anyreader_raises_on_missing_typestore(bags2: list[Path]) -> None:
    """Test AnyReader raises on missing typestore."""
    with (
        patch('rosbags.highlevel.anyreader.Reader2', MockReader),
        pytest.raises(AnyReaderError, match='Bag contains no type definitions'),
    ):
        AnyReader([bags2[0]]).open()
