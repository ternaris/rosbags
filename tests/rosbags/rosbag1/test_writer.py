# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Writer Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from rosbags.rosbag1 import Writer, WriterError
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from pathlib import Path


def test_no_overwrite(tmp_path: Path) -> None:
    """Test writer does not touch existing files."""
    path = tmp_path / 'test.bag'
    _ = path.write_text('foo')
    with pytest.raises(WriterError, match='exists'):
        Writer(path).open()
    path.unlink()

    writer = Writer(path)
    _ = path.write_text('foo')
    with pytest.raises(WriterError, match='exists'):
        writer.open()


def test_empty(tmp_path: Path) -> None:
    """Test empty bag."""
    path = tmp_path / 'test.bag'

    with Writer(path):
        pass
    data = path.read_bytes()
    assert len(data) == 13 + 4096


def test_add_connection(tmp_path: Path) -> None:
    """Test adding of connections."""
    store = get_typestore(Stores.LATEST)

    path = tmp_path / 'test.bag'

    with pytest.raises(WriterError, match='not opened'):
        _ = Writer(path).add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )

    with Writer(path) as writer:
        res = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )
        assert res.id == 0
    data = path.read_bytes()
    assert data.count(b'MESSAGE_DEFINITION') == 2
    assert data.count(b'HASH') == 2
    path.unlink()

    with Writer(path) as writer:
        res = writer.add_connection('/foo', 'std_msgs/msg/Int8', typestore=store)
        assert res.id == 0
    data = path.read_bytes()
    assert data.count(b'int8 data') == 2
    assert data.count(b'27ffa0c9c4b8fb8492252bcad9e5c57b') == 2
    path.unlink()

    with Writer(path) as writer:
        _ = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )
        with pytest.raises(WriterError, match='can only be added once'):
            _ = writer.add_connection(
                '/foo',
                'test_msgs/msg/Test',
                msgdef='MESSAGE_DEFINITION',
                md5sum='HASH',
            )
    path.unlink()

    with Writer(path) as writer:
        res1 = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )
        res2 = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
            callerid='src',
        )
        res3 = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
            latching=1,
        )
        assert (res1.id, res2.id, res3.id) == (0, 1, 2)


def test_write_errors(tmp_path: Path) -> None:
    """Test write errors."""
    path = tmp_path / 'test.bag'

    with pytest.raises(WriterError, match='not opened'):
        Writer(path).write(Mock(), 42, b'DEADBEEF')

    with Writer(path) as writer, pytest.raises(WriterError, match='is no connection'):
        writer.write(Mock(), 42, b'DEADBEEF')
    path.unlink()


def test_write_simple(tmp_path: Path) -> None:
    """Test writing of messages."""
    path = tmp_path / 'test.bag'

    with Writer(path) as writer:
        conn_foo = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )
        conn_latching = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
            latching=1,
        )
        conn_bar = writer.add_connection(
            '/bar',
            'test_msgs/msg/Bar',
            msgdef='OTHER_DEFINITION',
            md5sum='HASH',
            callerid='src',
        )
        _ = writer.add_connection(
            '/baz',
            'test_msgs/msg/Baz',
            msgdef='NEVER_WRITTEN',
            md5sum='HASH',
        )

        writer.write(conn_foo, 42, b'DEADBEEF')
        writer.write(conn_latching, 42, b'DEADBEEF')
        writer.write(conn_bar, 43, b'SECRET')
        writer.write(conn_bar, 43, b'SUBSEQUENT')

    res = path.read_bytes()
    assert res.count(b'op=\x05') == 1
    assert res.count(b'op=\x06') == 1
    assert res.count(b'MESSAGE_DEFINITION') == 4
    assert res.count(b'latching=1') == 2
    assert res.count(b'OTHER_DEFINITION') == 2
    assert res.count(b'callerid=src') == 2
    assert res.count(b'NEVER_WRITTEN') == 2
    assert res.count(b'DEADBEEF') == 2
    assert res.count(b'SECRET') == 1
    assert res.count(b'SUBSEQUENT') == 1
    path.unlink()

    with Writer(path) as writer:
        writer.chunk_threshold = 256
        conn_foo = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
        )
        conn_latching = writer.add_connection(
            '/foo',
            'test_msgs/msg/Test',
            msgdef='MESSAGE_DEFINITION',
            md5sum='HASH',
            latching=1,
        )
        conn_bar = writer.add_connection(
            '/bar',
            'test_msgs/msg/Bar',
            msgdef='OTHER_DEFINITION',
            md5sum='HASH',
            callerid='src',
        )
        _ = writer.add_connection(
            '/baz', 'test_msgs/msg/Baz', msgdef='NEVER_WRITTEN', md5sum='HASH'
        )

        writer.write(conn_foo, 42, b'DEADBEEF')
        writer.write(conn_latching, 42, b'DEADBEEF')
        writer.write(conn_bar, 43, b'SECRET')
        writer.write(conn_bar, 43, b'SUBSEQUENT')

    res = path.read_bytes()
    assert res.count(b'op=\x05') == 2
    assert res.count(b'op=\x06') == 2
    assert res.count(b'MESSAGE_DEFINITION') == 4
    assert res.count(b'latching=1') == 2
    assert res.count(b'OTHER_DEFINITION') == 2
    assert res.count(b'callerid=src') == 2
    assert res.count(b'NEVER_WRITTEN') == 2
    assert res.count(b'DEADBEEF') == 2
    assert res.count(b'SECRET') == 1
    assert res.count(b'SUBSEQUENT') == 1
    path.unlink()


def test_compression_errors(tmp_path: Path) -> None:
    """Test compression modes."""
    path = tmp_path / 'test.bag'
    with Writer(path) as writer, pytest.raises(WriterError, match='already open'):
        writer.set_compression(writer.CompressionFormat.BZ2)


@pytest.mark.parametrize('fmt', [None, Writer.CompressionFormat.BZ2, Writer.CompressionFormat.LZ4])
def test_compression_modes(tmp_path: Path, fmt: Writer.CompressionFormat | None) -> None:
    """Test compression modes."""
    store = get_typestore(Stores.LATEST)
    path = tmp_path / 'test.bag'
    writer = Writer(path)
    if fmt:
        writer.set_compression(fmt)
    with writer:
        conn = writer.add_connection('/foo', 'std_msgs/msg/Int8', typestore=store)
        writer.write(conn, 42, b'\x42')
    data = path.read_bytes()
    assert data.count(f'compression={fmt.name.lower() if fmt else "none"}'.encode()) == 1


@pytest.mark.parametrize('fmt', [None, Writer.CompressionFormat.BZ2, Writer.CompressionFormat.LZ4])
def test_chunksize_is_correct(tmp_path: Path, fmt: Writer.CompressionFormat | None) -> None:
    """Test chunksize is correct."""
    store = get_typestore(Stores.LATEST)
    path = tmp_path / 'test1.bag'
    writer = Writer(path)
    if fmt:
        writer.set_compression(fmt)
    with writer:
        conn = writer.add_connection('/foo', 'std_msgs/msg/Int8', typestore=store)
        writer.write(conn, 42, b'\x42')
    data = path.read_bytes()
    assert b'size=\xca\x00\x00\x00' in data

    path = tmp_path / 'test2.bag'
    writer = Writer(path)
    if fmt:
        writer.set_compression(fmt)
    with writer:
        conn = writer.add_connection('/foo', 'std_msgs/msg/Int8', typestore=store)
        writer.write(conn, 42, b'\x42')
        writer.write(conn, 43, b'\x43')
    data = path.read_bytes()
    assert b'size=\xf9\x00\x00\x00' in data


def test_deprecations(tmp_path: Path) -> None:
    """Test writer deprecations."""
    bag = Writer(tmp_path / 'bag')
    with bag, pytest.deprecated_call():
        _ = bag.add_connection('/foo', 'std_msgs/msg/Empty')
