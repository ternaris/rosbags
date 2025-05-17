# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Mcap Storage Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
)
from rosbags.rosbag2.enums import CompressionMode
from rosbags.rosbag2.storage_mcap import MCAPFile, McapWriter

if TYPE_CHECKING:
    from pathlib import Path


def test_write_empty(tmp_path: Path) -> None:
    """Test schema version is detected."""
    bag = tmp_path / 'bag'
    bag.mkdir()

    mcap = McapWriter(bag, CompressionMode.NONE)
    mcap.close(0, 'metadata')

    reader = MCAPFile(bag / 'bag.mcap')
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

    reader = MCAPFile(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert not reader.channels
    assert not list(reader.messages([]))
    reader.close()


def test_write_channel(tmp_path: Path) -> None:
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
    mcap.add_connection(connection, 'qos')
    mcap.close(0, 'metadata')

    reader = MCAPFile(bag / 'bag.mcap')
    reader.open()
    assert len(reader.schemas) == 1
    assert len(reader.channels) == 1
    assert not list(reader.messages([]))
    reader.close()


def test_write_message(tmp_path: Path) -> None:
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
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'msg1')
    mcap.write(connection, 43, b'msg2')
    mcap.close(0, 'metadata')

    reader = MCAPFile(bag / 'bag.mcap')
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
def test_write_multichunk(tmp_path: Path, compression: str) -> None:
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
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.close(0, 'metadata')

    reader = MCAPFile(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 1
    reader.close()

    (bag / 'bag.mcap').unlink()

    mcap = McapWriter(bag, CompressionMode.NONE)
    mcap.add_msgtype(connection)
    mcap.add_connection(connection, 'qos')
    mcap.write(connection, 42, b'\x00' * 2**20)
    mcap.write(connection, 43, b'msg2')
    mcap.close(0, 'metadata')

    reader = MCAPFile(bag / 'bag.mcap')
    reader.open()
    assert len(reader.chunks) == 2
    reader.close()
