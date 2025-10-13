# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Metadata Tests."""

from __future__ import annotations

from typing import cast

from ruamel.yaml import YAML

from rosbags.interfaces import (
    Qos,
    QosDurability,
    QosHistory,
    QosLiveliness,
    QosReliability,
    QosTime,
)
from rosbags.rosbag2.metadata import dump_qos_v8, dump_qos_v9, parse_qos

REF = [
    Qos(
        QosHistory.UNKNOWN,
        0,
        QosReliability.RELIABLE,
        QosDurability.VOLATILE,
        QosTime(9223372036, 854775807),
        QosTime(9223372036, 854775807),
        QosLiveliness.AUTOMATIC,
        QosTime(9223372036, 854775807),
        avoid_ros_namespace_conventions=False,
    )
]

REF_UNKNOWN = [
    Qos(
        QosHistory.UNKNOWN,
        0,
        QosReliability.UNKNOWN,
        QosDurability.UNKNOWN,
        QosTime(9223372036, 854775807),
        QosTime(9223372036, 854775807),
        QosLiveliness.UNKNOWN,
        QosTime(9223372036, 854775807),
        avoid_ros_namespace_conventions=False,
    )
]

QOS_V8_EMPTY = 'offered_qos_profiles: ""'
QOS_V8 = (
    r'offered_qos_profiles: "- history: 3\n  depth: 0\n  reliability: 1\n  durability: 2\n  '
    r'deadline:\n    sec: 9223372036\n    nsec: 854775807\n  lifespan:\n    sec: 9223372036\n    '
    r'nsec: 854775807\n  liveliness: 1\n  liveliness_lease_duration:\n    sec: 9223372036\n    '
    r'nsec: 854775807\n  avoid_ros_namespace_conventions: false"'
)

QOS_V8_BADENTRIES = (
    r'offered_qos_profiles: "- history: 42\n  depth: 0\n  reliability: 42\n  durability: 42\n  '
    r'deadline:\n    sec: 9223372036\n    nsec: 854775807\n  lifespan:\n    sec: 9223372036\n    '
    r'nsec: 854775807\n  liveliness: 42\n  liveliness_lease_duration:\n    sec: 9223372036\n    '
    r'nsec: 854775807\n  avoid_ros_namespace_conventions: false"'
)


QOS_V9_EMPTY = 'offered_qos_profiles: []'
QOS_V9 = """
offered_qos_profiles:
  - history: unknown
    depth: 0
    reliability: reliable
    durability: volatile
    deadline:
      sec: 9223372036
      nsec: 854775807
    lifespan:
      sec: 9223372036
      nsec: 854775807
    liveliness: automatic
    liveliness_lease_duration:
      sec: 9223372036
      nsec: 854775807
    avoid_ros_namespace_conventions: false
"""


def test_qos_parsing() -> None:
    """Test qos values are parsed correctly."""
    yaml = YAML(typ='safe')
    dct = cast(
        'dict[str, str]',
        yaml.load(QOS_V8_EMPTY),
    )
    assert parse_qos(dct['offered_qos_profiles']) == []

    dct = cast(
        'dict[str, str]',
        yaml.load(QOS_V8),
    )
    assert parse_qos(dct['offered_qos_profiles']) == REF

    dct = cast(
        'dict[str, str]',
        yaml.load(QOS_V9_EMPTY),
    )
    assert parse_qos(dct['offered_qos_profiles']) == []

    dct = cast(
        'dict[str, str]',
        yaml.load(QOS_V9),
    )
    assert parse_qos(dct['offered_qos_profiles']) == REF


def test_qos_v8_out_of_range() -> None:
    """Test qos v8 out of range enums are mapped to unknown."""
    yaml = YAML(typ='safe')
    dct = cast(
        'dict[str, str]',
        yaml.load(QOS_V8_BADENTRIES),
    )
    assert parse_qos(dct['offered_qos_profiles']) == REF_UNKNOWN


def test_qos_roundtrip() -> None:
    """Test qos values stay the same after roundtrip."""
    assert parse_qos(dump_qos_v8([])) == []
    assert parse_qos(dump_qos_v8(REF)) == REF
    assert parse_qos(dump_qos_v9([])) == []
    assert parse_qos(dump_qos_v9(REF)) == REF
