# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Test full data roundtrip."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.rosbag1 import Reader, Writer
from rosbags.typesys import Stores, get_typestore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize('fmt', [None, Writer.CompressionFormat.BZ2, Writer.CompressionFormat.LZ4])
def test_roundtrip(tmp_path: Path, fmt: Writer.CompressionFormat | None) -> None:
    """Test full data roundtrip."""
    store = get_typestore(Stores.LATEST)

    class Foo:
        """Dummy class."""

        data = 1.25

    path = tmp_path / 'test.bag'
    wbag = Writer(path)
    if fmt:
        wbag.set_compression(fmt)
    with wbag:
        msgtype = 'std_msgs/msg/Float64'
        conn = wbag.add_connection('/test', msgtype, typestore=store)
        wbag.write(conn, 42, store.cdr_to_ros1(store.serialize_cdr(Foo, msgtype), msgtype))

    rbag = Reader(path)
    with rbag:
        gen = rbag.messages()
        connection, _, raw = next(gen)
        msg = store.deserialize_cdr(store.ros1_to_cdr(raw, connection.msgtype), connection.msgtype)
        assert getattr(msg, 'data', None) == Foo.data
        with pytest.raises(StopIteration):
            next(gen)
