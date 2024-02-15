"""Example: Register rosbag1 types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

if TYPE_CHECKING:
    from pathlib import Path


def process_bag(src: Path) -> None:
    """Register contained messages types before processing bag.

    Args:
        src: Bag to process.

    """
    typestore = get_typestore(Stores.EMPTY)
    with Reader(src) as reader:
        typs = {}
        for conn in reader.connections:
            typs.update(get_types_from_msg(conn.msgdef, conn.msgtype))
        typestore.register(typs)

        # Now all message types used in the bag are registered
        # for conn, timestamp, data in reader.messages():
        #     ...
