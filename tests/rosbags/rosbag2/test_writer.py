# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Writer Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import Connection, ConnectionExtRosbag2
from rosbags.rosbag2 import Writer, WriterError
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from pathlib import Path


def test_writer_writes_storage_and_metadata(tmp_path: Path) -> None:
    """Test writer writes storage file and metadata."""
    store = get_typestore(Stores.LATEST)
    path = tmp_path / 'rosbag2'
    with Writer(path) as bag:
        connection = bag.add_connection('/test', 'std_msgs/msg/Int8', typestore=store)
        bag.write(connection, 42, b'\x00')
        bag.write(connection, 666, b'\x01' * 4096)
    assert (path / 'metadata.yaml').exists()
    assert 'RIHS01_' in (path / 'metadata.yaml').read_text()
    assert (path / 'rosbag2.db3').exists()
    size = (path / 'rosbag2.db3').stat().st_size

    path = tmp_path / 'compress_none'
    bag = Writer(path)
    bag.set_compression(bag.CompressionMode.NONE, bag.CompressionFormat.ZSTD)
    with bag:
        connection = bag.add_connection('/test', 'std_msgs/msg/Int8', typestore=store)
        bag.write(connection, 42, b'\x00')
        bag.write(connection, 666, b'\x01' * 4096)
    assert (path / 'metadata.yaml').exists()
    assert (path / 'compress_none.db3').exists()
    assert size == (path / 'compress_none.db3').stat().st_size

    path = tmp_path / 'compress_file'
    bag = Writer(path)
    bag.set_compression(bag.CompressionMode.FILE, bag.CompressionFormat.ZSTD)
    with bag:
        connection = bag.add_connection('/test', 'std_msgs/msg/Int8', typestore=store)
        bag.write(connection, 42, b'\x00')
        bag.write(connection, 666, b'\x01' * 4096)
    assert (path / 'metadata.yaml').exists()
    assert not (path / 'compress_file.db3').exists()
    assert (path / 'compress_file.db3.zstd').exists()

    path = tmp_path / 'compress_message'
    bag = Writer(path)
    bag.set_compression(bag.CompressionMode.MESSAGE, bag.CompressionFormat.ZSTD)
    with bag:
        connection = bag.add_connection('/test', 'std_msgs/msg/Int8', typestore=store)
        bag.write(connection, 42, b'\x00')
        bag.write(connection, 666, b'\x01' * 4096)
    assert (path / 'metadata.yaml').exists()
    assert (path / 'compress_message.db3').exists()
    assert size > (path / 'compress_message.db3').stat().st_size

    path = tmp_path / 'with_custom_data'
    bag = Writer(path)
    bag.open()
    bag.set_custom_data('key1', 'value1')
    with pytest.raises(WriterError, match='non-string value'):
        bag.set_custom_data('key1', 42)  # type: ignore[arg-type]
    bag.close()
    assert b'key1: value1' in (path / 'metadata.yaml').read_bytes()

    path = tmp_path / 'with_external_types'
    bag = Writer(path)
    with bag:
        connection = bag.add_connection(
            '/test',
            'std_msgs/msg/Int8',
            msgdef='msgdef',
            rihs01='RIHS00_hash',
        )
    assert b'RIHS00' in (path / 'metadata.yaml').read_bytes()
    assert b'RIHS01' not in (path / 'metadata.yaml').read_bytes()


def test_failure_cases(tmp_path: Path) -> None:
    """Test writer failure cases."""
    store = get_typestore(Stores.LATEST)

    with pytest.raises(WriterError, match='exists'):
        Writer(tmp_path)

    bag = Writer(tmp_path / 'race')
    (tmp_path / 'race').mkdir()
    with pytest.raises(WriterError, match='exists'):
        bag.open()

    bag = Writer(tmp_path / 'compress_after_open')
    bag.open()
    with pytest.raises(WriterError, match='already open'):
        bag.set_compression(bag.CompressionMode.FILE, bag.CompressionFormat.ZSTD)

    bag = Writer(tmp_path / 'topic')
    with pytest.raises(WriterError, match='was not opened'):
        bag.add_connection('/tf', 'tf2_msgs/msg/TFMessage')

    bag = Writer(tmp_path / 'write')
    with pytest.raises(WriterError, match='was not opened'):
        bag.write(
            Connection(
                1,
                '/tf',
                'tf2_msgs/msg/TFMessage',
                '',
                '',
                0,
                ConnectionExtRosbag2('cdr', ''),
                None,
            ),
            0,
            b'',
        )

    bag = Writer(tmp_path / 'topic')
    bag.open()
    bag.add_connection('/tf', 'tf2_msgs/msg/TFMessage', typestore=store)
    bag.add_connection(
        '/tf',
        'tf2_msgs/msg/TFMessage',
        typestore=store,
        serialization_format='ros1',
    )
    with pytest.raises(WriterError, match='only be added once'):
        bag.add_connection('/tf', 'tf2_msgs/msg/TFMessage', typestore=store)

    bag = Writer(tmp_path / 'notopic')
    bag.open()
    connection = Connection(
        1,
        '/tf',
        'tf_msgs/msg/tf2',
        '',
        '',
        0,
        ConnectionExtRosbag2('cdr', ''),
        None,
    )
    with pytest.raises(WriterError, match='unknown connection'):
        bag.write(connection, 42, b'\x00')


def test_deprecations(tmp_path: Path) -> None:
    """Test writer deprecations."""
    bag = Writer(tmp_path / 'bag')
    with bag, pytest.deprecated_call():
        bag.add_connection('/foo', 'std_msgs/msg/Empty')
