# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""DEPRECATED."""

from __future__ import annotations

import warnings

from rosbags.typesys.stores.ros2_foxy import *  # noqa: F403

message = """
Importing from 'rosbags.typesys.types' is deprecated.
Use a specific type store instead, for example:
from rosbags.typesys.stores.ros2_foxy import std_msgs__msg__Header
"""

warnings.warn(message, category=DeprecationWarning, stacklevel=2)
