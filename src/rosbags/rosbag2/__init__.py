# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags support for rosbag2 files.

Readers and writers provide access to metadata and raw message content saved
in the rosbag2 format.

"""

from .errors import ReaderError
from .reader import Reader
from .writer import Writer, WriterError

__all__ = [
    'Reader',
    'ReaderError',
    'Writer',
    'WriterError',
]
