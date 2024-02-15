# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deprecated functions."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from .stores import Stores, get_typestore

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict

    from .store import Typestore


depmsg = """
Global type registration has been replaced with explicit typestores.

Perform all type registration and subsequent serialization and
deserialization on typestore instances:

from rosbags.typesys import Stores, get_typestore

typestore = get_typestore(Stores.ROS2_FOXY)
typestore.register(types)
""".strip()

store = get_typestore(Stores.ROS2_FOXY)


def register_types(typs: Typesdict, typestore: Typestore | None = None) -> None:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    typestore = typestore or store
    return typestore.register(typs)
