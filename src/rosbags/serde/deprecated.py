# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deprecated functions."""

from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rosbags.typesys.store import Typestore


depmsg = """
Global serialization/deserialization functions have been replaced with
explicit typestores.

If you are deserializing messages from an AnyReader instance, simply
use its `.deserialize(data, typename)` method.

Otherwise instantiate a type store and use its methods:

from rosbags.typesys import Stores, get_typestore

typestore = get_typestore(Stores.ROS2_FOXY)
typestore.deserialize_cdr(data, typename)
""".strip()


def deserialize_cdr(
    rawdata: bytes | memoryview,
    typename: str,
    typestore: Typestore | None = None,
) -> object:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.deserialize_cdr(rawdata, typename)


def serialize_cdr(
    message: object,
    typename: str,
    *,
    little_endian: bool = sys.byteorder == 'little',
    typestore: Typestore | None = None,
) -> memoryview:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.serialize_cdr(message, typename, little_endian=little_endian)


def deserialize_ros1(
    rawdata: bytes | memoryview,
    typename: str,
    typestore: Typestore | None = None,
) -> object:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.deserialize_ros1(rawdata, typename)


def serialize_ros1(
    message: object,
    typename: str,
    typestore: Typestore | None = None,
) -> memoryview:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.serialize_ros1(message, typename)


def ros1_to_cdr(
    raw: bytes | memoryview,
    typename: str,
    typestore: Typestore | None = None,
) -> memoryview:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.ros1_to_cdr(raw, typename)


def cdr_to_ros1(
    raw: bytes | memoryview,
    typename: str,
    typestore: Typestore | None = None,
) -> memoryview:
    """DEPRECATED."""  # noqa: D401
    warnings.warn(depmsg, category=DeprecationWarning, stacklevel=2)
    if not typestore:
        from rosbags.typesys.deprecated import store

        typestore = store

    return typestore.cdr_to_ros1(raw, typename)
