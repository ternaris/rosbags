# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Writer/Reader Roundtrip Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.rosbag1 import Reader, Writer
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.ros1_noetic import std_msgs__msg__Float64 as Float64

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize('fmt', [None, *Writer.CompressionFormat])
def test_roundtrip(tmp_path: Path, fmt: Writer.CompressionFormat | None) -> None:
    """Test messages stay the same between write and read."""
    store = get_typestore(Stores.ROS1_NOETIC)

    float64 = Float64(1.25)

    path = tmp_path / 'test.bag'
    wbag = Writer(path)
    if fmt:
        wbag.set_compression(fmt)
    with wbag:
        wconnection = wbag.add_connection('/test', float64.__msgtype__, typestore=store)
        wbag.write(wconnection, 42, store.serialize_ros1(float64, float64.__msgtype__))

    rbag = Reader(path)
    with rbag:
        gen = rbag.messages()
        rconnection, _, raw = next(gen)
        assert rconnection.topic == wconnection.topic
        # Should implement: assert rconnection.msgtype == wconnection.msgtype
        assert rconnection.ext == wconnection.ext
        msg = store.deserialize_ros1(raw, rconnection.msgtype)
        assert msg == float64
        with pytest.raises(StopIteration):
            _ = next(gen)
