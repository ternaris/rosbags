# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags message serialization and deserialization.

Serializers and deserializers convert between python messages objects and
the common rosbag serialization formats. Computationally cheap functions
convert directly between different serialization formats.

"""

from .deprecated import (
    cdr_to_ros1,
    deserialize_cdr,
    deserialize_ros1,
    ros1_to_cdr,
    serialize_cdr,
    serialize_ros1,
)
from .errors import SerdeError

__all__ = [
    'SerdeError',
    'cdr_to_ros1',
    'deserialize_cdr',
    'deserialize_ros1',
    'ros1_to_cdr',
    'serialize_cdr',
    'serialize_ros1',
]
