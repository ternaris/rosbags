# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Concrete store implementations."""

from enum import Enum
from importlib import import_module

from rosbags.typesys.store import Typestore


class Stores(Enum):
    """All builtin stores."""

    EMPTY = 'empty'
    """Only builtin messages (Duration, Time)."""
    LATEST = 'latest'
    """Alias for lastest ROS2 LTS."""
    ROS1_NOETIC = 'ros1_noetic'
    """Noetic Ninjemys."""
    ROS2_DASHING = 'ros2_dashing'
    """Dashing Diademata."""
    ROS2_ELOQUENT = 'ros2_eloquent'
    """Eloquent Elusor."""
    ROS2_FOXY = 'ros2_foxy'
    """Foxy Fitzroy."""
    ROS2_GALACTIC = 'ros2_galactic'
    """Galactic Geochelone."""
    ROS2_HUMBLE = 'ros2_humble'
    """Humble Hawksbill."""
    ROS2_IRON = 'ros2_iron'
    """Iron Irwini."""


def get_typestore(name: Stores) -> Typestore:
    """Get typestore by name."""
    if name == Stores.LATEST:
        name = Stores.ROS2_FOXY

    mod = import_module(f'.{name.value}', __name__)
    return Typestore(mod)
