# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag1 to Rosbag2 Converter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.interfaces import Connection, ConnectionExtRosbag1, ConnectionExtRosbag2
from rosbags.rosbag1 import (
    Reader as Reader1,
    ReaderError as ReaderError1,
    Writer as Writer1,
    WriterError as WriterError1,
)
from rosbags.rosbag2 import (
    Reader as Reader2,
    ReaderError as ReaderError2,
    Writer as Writer2,
    WriterError as WriterError2,
)
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence


LATCH = """
- history: 3
  depth: 0
  reliability: 1
  durability: 1
  deadline:
    sec: 2147483647
    nsec: 4294967295
  lifespan:
    sec: 2147483647
    nsec: 4294967295
  liveliness: 1
  liveliness_lease_duration:
    sec: 2147483647
    nsec: 4294967295
  avoid_ros_namespace_conventions: false
""".strip()


class ConverterError(Exception):
    """Converter Error."""


def upgrade_connection(rconn: Connection) -> Connection:
    """Convert rosbag1 connection to rosbag2 connection.

    Args:
        rconn: Rosbag1 connection.

    Returns:
        Rosbag2 connection.

    """
    assert isinstance(rconn.ext, ConnectionExtRosbag1)
    return Connection(
        rconn.id,
        rconn.topic,
        rconn.msgtype,
        '',
        '',
        0,
        ConnectionExtRosbag2('cdr', LATCH if rconn.ext.latching else ''),
        None,
    )


def downgrade_connection(rconn: Connection) -> Connection:
    """Convert rosbag2 connection to rosbag1 connection.

    Args:
        rconn: Rosbag2 connection.
        typestore: Typestore.

    Returns:
        Rosbag1 connection.

    """
    assert isinstance(rconn.ext, ConnectionExtRosbag2)
    return Connection(
        rconn.id,
        rconn.topic,
        rconn.msgtype,
        '',
        '',
        -1,
        ConnectionExtRosbag1(None, int('durability: 1' in rconn.ext.offered_qos_profiles)),
        None,
    )


def convert_1to2(
    src: Path,
    dst: Path,
    exclude_topics: Sequence[str],
    include_topics: Sequence[str],
) -> None:
    """Convert Rosbag1 to Rosbag2.

    Args:
        src: Rosbag1 path.
        dst: Rosbag2 path.
        exclude_topics: Topics to exclude from conversion, even if included explicitly.
        include_topics: Topics to include in conversion, instead of all.

    Raises:
        ConverterError: If all connections are excluded.

    """
    store = get_typestore(Stores.EMPTY)
    foxy_store = get_typestore(Stores.ROS2_FOXY)
    store.register({'std_msgs/msg/Header': foxy_store.FIELDDEFS['std_msgs/msg/Header']})

    with Reader1(src) as reader, Writer2(dst) as writer:
        connmap: dict[int, Connection] = {}
        connections = [
            x
            for x in reader.connections
            if x.topic not in exclude_topics and (not include_topics or x.topic in include_topics)
        ]
        if not connections:
            msg = 'No connections left for conversion.'
            raise ConverterError(msg)
        for rconn in connections:
            candidate = upgrade_connection(rconn)
            assert isinstance(candidate.ext, ConnectionExtRosbag2)
            for conn in writer.connections:
                assert isinstance(conn.ext, ConnectionExtRosbag2)
                if (
                    conn.topic == candidate.topic
                    and conn.msgtype == candidate.msgtype
                    and conn.ext == candidate.ext
                ):
                    break
            else:
                typs = get_types_from_msg(rconn.msgdef, rconn.msgtype)
                typs.pop('std_msgs/msg/Header', None)
                store.register(typs)
                conn = writer.add_connection(
                    candidate.topic,
                    candidate.msgtype,
                    typestore=store,
                    serialization_format=candidate.ext.serialization_format,
                    offered_qos_profiles=candidate.ext.offered_qos_profiles,
                )
            connmap[rconn.id] = conn

        for rconn, timestamp, data in reader.messages(connections=connections):
            cdrdata = store.ros1_to_cdr(data, rconn.msgtype)
            writer.write(connmap[rconn.id], timestamp, cdrdata)


def convert_2to1(
    src: Path,
    dst: Path,
    exclude_topics: Sequence[str],
    include_topics: Sequence[str],
) -> None:
    """Convert Rosbag2 to Rosbag1.

    Args:
        src: Rosbag2 path.
        dst: Rosbag1 path.
        exclude_topics: Topics to exclude from conversion, even if included explicitly.
        include_topics: Topics to include in conversion, instead of all.

    Raises:
        ConverterError: If all connections are excluded.

    """
    store = get_typestore(Stores.ROS2_FOXY)
    # Use same store as reader, but with ROS1 Header message definition.
    ros1_store = get_typestore(Stores.ROS2_FOXY)
    noetic_store = get_typestore(Stores.ROS1_NOETIC)
    ros1_store.FIELDDEFS.pop('std_msgs/msg/Header')
    ros1_store.register({'std_msgs/msg/Header': noetic_store.FIELDDEFS['std_msgs/msg/Header']})

    with Reader2(src) as reader, Writer1(dst) as writer:
        connmap: dict[int, Connection] = {}
        connections = [
            x
            for x in reader.connections
            if x.topic not in exclude_topics and (not include_topics or x.topic in include_topics)
        ]
        if not connections:
            msg = 'No connections left for conversion.'
            raise ConverterError(msg)
        for rconn in connections:
            candidate = downgrade_connection(rconn)
            assert isinstance(candidate.ext, ConnectionExtRosbag1)
            for conn in writer.connections:
                assert isinstance(conn.ext, ConnectionExtRosbag1)
                if (
                    conn.topic == candidate.topic
                    and conn.msgtype == candidate.msgtype
                    and conn.ext.latching == candidate.ext.latching
                ):
                    break
            else:
                conn = writer.add_connection(
                    candidate.topic,
                    candidate.msgtype,
                    typestore=ros1_store,
                    callerid=candidate.ext.callerid,
                    latching=candidate.ext.latching,
                )
            connmap[rconn.id] = conn

        for rconn, timestamp, data in reader.messages(connections=connections):
            ros1data = store.cdr_to_ros1(data, rconn.msgtype)
            writer.write(connmap[rconn.id], timestamp, ros1data)


def convert(
    src: Path,
    dst: Path | None,
    exclude_topics: Sequence[str] = (),
    include_topics: Sequence[str] = (),
) -> None:
    """Convert between Rosbag1 and Rosbag2.

    Args:
        src: Source rosbag.
        dst: Destination rosbag.
        exclude_topics: Topics to exclude from conversion, even if included explicitly.
        include_topics: Topics to include in conversion, instead of all.

    Raises:
        ConverterError: An error occured during reading, writing, or
            converting.

    """
    upgrade = src.suffix == '.bag'
    dst = dst if dst else src.with_suffix('' if upgrade else '.bag')
    if dst.exists():
        msg = f'Output path {str(dst)!r} exists already.'
        raise ConverterError(msg)
    func = convert_1to2 if upgrade else convert_2to1

    try:
        func(src, dst, exclude_topics, include_topics)
    except (ReaderError1, ReaderError2) as err:
        msg = f'Reading source bag: {err}'
        raise ConverterError(msg) from err
    except (WriterError1, WriterError2) as err:
        msg = f'Writing destination bag: {err}'
        raise ConverterError(msg) from err
    except Exception as err:  # noqa: BLE001
        msg = f'Converting rosbag: {err!r}'
        raise ConverterError(msg) from err
