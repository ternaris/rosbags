# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Shared interfaces."""

from __future__ import annotations

from typing import NamedTuple


class ConnectionExtRosbag1(NamedTuple):
    """Rosbag1 specific connection extensions."""

    callerid: str | None
    latching: int | None


class ConnectionExtRosbag2(NamedTuple):
    """Rosbag2 specific connection extensions."""

    serialization_format: str
    offered_qos_profiles: str


class Connection(NamedTuple):
    """Connection information."""

    id: int
    topic: str
    msgtype: str
    msgdef: str
    digest: str
    msgcount: int
    ext: ConnectionExtRosbag1 | ConnectionExtRosbag2
    owner: object


class TopicInfo(NamedTuple):
    """Topic information."""

    msgtype: str | None
    msgdef: str | None
    msgcount: int
    connections: list[Connection]
