"""Example: Register types from msg files."""

from __future__ import annotations

from pathlib import Path

from rosbags.typesys import Stores, get_types_from_msg, get_typestore


def guess_msgtype(path: Path) -> str:
    """Guess message type name from path."""
    name = path.relative_to(path.parents[2]).with_suffix('')
    if 'msg' not in name.parts:
        name = name.parent / 'msg' / name.name
    return str(name)


typestore = get_typestore(Stores.ROS2_FOXY)
add_types = {}

for pathstr in ['/path/to/custom_msgs/msg/Speed.msg', '/path/to/custom_msgs/msg/Accel.msg']:
    msgpath = Path(pathstr)
    msgdef = msgpath.read_text(encoding='utf-8')
    add_types.update(get_types_from_msg(msgdef, guess_msgtype(msgpath)))

typestore.register(add_types)

Accel = typestore.types['custom_msgs/msg/Accel']
Speed = typestore.types['custom_msgs/msg/Speed']

Accel(42)
Speed(42)
