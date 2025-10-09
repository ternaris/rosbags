# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Writer/Reader Roundtrip Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.rosbag2 import CompressionFormat, CompressionMode, Reader, Writer, WriterError
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.latest import std_msgs__msg__Float64 as Float64

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize('mode', [*CompressionMode])
def test_roundtrip(mode: CompressionMode, tmp_path: Path) -> None:
    """Test messages stay the same between write and read."""
    store = get_typestore(Stores.LATEST)

    float64 = Float64(1.25)

    path = tmp_path / 'rosbag2'
    wbag = Writer(path, version=Writer.VERSION_LATEST)
    wbag.set_compression(mode, CompressionFormat.ZSTD)
    if mode == CompressionMode.STORAGE:
        with pytest.raises(WriterError, match='storage-side compression'):
            wbag.open()
        return

    with wbag:
        wconnection = wbag.add_connection('/test', float64.__msgtype__, typestore=store)
        wbag.write(wconnection, 42, store.serialize_cdr(float64, float64.__msgtype__))

    rbag = Reader(path)
    with rbag:
        gen = rbag.messages()
        rconnection, _, raw = next(gen)
        assert rconnection.topic == wconnection.topic
        assert rconnection.msgtype == wconnection.msgtype
        assert rconnection.ext == wconnection.ext
        msg = store.deserialize_cdr(raw, rconnection.msgtype)
        assert msg == float64
        with pytest.raises(StopIteration):
            _ = next(gen)
