# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag2 errors."""

from __future__ import annotations


class ReaderError(Exception):
    """Reader Error."""

    args: tuple[str]
