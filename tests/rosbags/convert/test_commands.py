# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag Converter Tests."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

from rosbags.convert import ConverterError
from rosbags.convert.commands import command
from rosbags.typesys.stores import Stores, get_typestore
from rosbags.typesys.stores.ros1_noetic import FIELDDEFS as NOETIC_FIELDDEFS
from rosbags.typesys.stores.ros2_foxy import FIELDDEFS as FOXY_FIELDDEFS

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

NOTYPESTORE = ()
NOTYPESTORE_REF = f'{sys.modules[__name__].__name__}.NOTYPESTORE'
TYPESTORE = get_typestore(Stores.ROS1_NOETIC)
TYPESTORE_REF = f'{sys.modules[__name__].__name__}.TYPESTORE'
TYPESTORE_REFALT = f'{sys.modules[__name__].__name__}:TYPESTORE'


def test_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test cli wrapper."""
    bag1 = tmp_path / 'ros1.bag'
    _ = bag1.write_text('')
    bag2 = tmp_path / 'subdir'
    bag2.mkdir()
    out = tmp_path / 'out.bag'
    out2 = tmp_path / 'out'

    assert command([tmp_path / 'noexist'], out) == 1
    assert 'are missing' in capsys.readouterr().out

    assert command([bag1], bag2) == 1
    assert 'exists already' in capsys.readouterr().out

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out)
    cvrt.assert_called_once()
    assert cvrt.call_args.args[3] == 9

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, compress='none')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[4:6] == (None, 'file')

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, compress='bz2')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[4:6] == ('bz2', 'file')

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, compress='lz4')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[4:6] == ('lz4', 'file')

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out2, compress='zstd')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[4:6] == ('zstd', 'file')

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out2, compress='zstd', compress_mode='message')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[4:6] == ('zstd', 'message')

    assert command([bag1, bag2], out, compress='zstd') == 1
    assert 'Invalid compression' in capsys.readouterr().out

    assert command([bag1, bag2], out2, compress='bz2') == 1
    assert 'Invalid compression' in capsys.readouterr().out

    assert command([bag1, bag2], out, compress_mode='message') == 1
    assert 'Invalid compression' in capsys.readouterr().out

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out)
    cvrt.assert_called_once()
    assert cvrt.call_args.args[6].fielddefs == FOXY_FIELDDEFS

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, src_typestore='ros1_noetic')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[6].fielddefs == NOETIC_FIELDDEFS

    with patch('rosbags.convert.commands.convert') as cvrt:
        assert command([bag1, bag2], out, src_typestore_ref=NOTYPESTORE_REF) == 1
    cvrt.assert_not_called()

    for ref in (TYPESTORE_REF, TYPESTORE_REFALT):
        with patch('rosbags.convert.commands.convert') as cvrt:
            _ = command([bag1, bag2], out, src_typestore_ref=ref)
        cvrt.assert_called_once()
        assert cvrt.call_args.args[6].fielddefs == NOETIC_FIELDDEFS

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out)
    cvrt.assert_called_once()
    assert cvrt.call_args.args[7] is None

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, dst_typestore='ros1_noetic')
    cvrt.assert_called_once()
    assert cvrt.call_args.args[7].fielddefs == NOETIC_FIELDDEFS

    with patch('rosbags.convert.commands.convert') as cvrt:
        assert command([bag1, bag2], out, dst_typestore_ref=NOTYPESTORE_REF) == 1
    cvrt.assert_not_called()

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, dst_typestore_ref=TYPESTORE_REF)
    cvrt.assert_called_once()
    assert cvrt.call_args.args[7].fielddefs == NOETIC_FIELDDEFS

    with patch('rosbags.convert.commands.convert') as cvrt:
        _ = command([bag1, bag2], out, dst_typestore_ref=TYPESTORE_REF)
    cvrt.assert_called_once()
    assert cvrt.call_args.args[7].fielddefs == NOETIC_FIELDDEFS

    with patch('rosbags.convert.commands.convert', side_effect=ConverterError('exc')):
        assert command([bag1, bag2], out) == 1
    assert 'ERROR: exc' in capsys.readouterr().out

    with patch('rosbags.convert.commands.convert'):
        assert command([bag1, bag2], out) == 0
