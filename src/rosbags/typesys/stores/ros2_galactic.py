# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
#
# THIS FILE IS GENERATED, DO NOT EDIT
"""Message type definitions."""

# ruff: noqa: E501,F401,F403,F405,F821,N801,N814,TCH004

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype as T

from .ros2_foxy import *

if TYPE_CHECKING:
    from typing import ClassVar

    import numpy as np


@dataclass
class rcl_interfaces__msg__ParameterDescriptor:  # type: ignore[no-redef]
    """Class for rcl_interfaces/msg/ParameterDescriptor."""

    name: str
    type: int
    description: str
    additional_constraints: str
    read_only: bool
    dynamic_typing: bool
    floating_point_range: list[rcl_interfaces__msg__FloatingPointRange]
    integer_range: list[rcl_interfaces__msg__IntegerRange]
    __msgtype__: ClassVar[str] = 'rcl_interfaces/msg/ParameterDescriptor'


FIELDDEFS = {
    **FIELDDEFS,
    'rcl_interfaces/msg/ParameterDescriptor': (
        [],
        [
            ('name', (T.BASE, ('string', 0))),
            ('type', (T.BASE, ('uint8', 0))),
            ('description', (T.BASE, ('string', 0))),
            ('additional_constraints', (T.BASE, ('string', 0))),
            ('read_only', (T.BASE, ('bool', 0))),
            ('dynamic_typing', (T.BASE, ('bool', 0))),
            (
                'floating_point_range',
                (T.SEQUENCE, ((T.NAME, 'rcl_interfaces/msg/FloatingPointRange'), 1)),
            ),
            ('integer_range', (T.SEQUENCE, ((T.NAME, 'rcl_interfaces/msg/IntegerRange'), 1))),
        ],
    ),
}
