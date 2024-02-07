"""Example: Register types from msg files."""

from pathlib import Path

from rosbags.typesys import get_types_from_msg, register_types


def guess_msgtype(path: Path) -> str:
    """Guess message type name from path."""
    name = path.relative_to(path.parents[2]).with_suffix('')
    if 'msg' not in name.parts:
        name = name.parent / 'msg' / name.name
    return str(name)


add_types = {}

for pathstr in ['/path/to/custom_msgs/msg/Speed.msg', '/path/to/custom_msgs/msg/Accel.msg']:
    msgpath = Path(pathstr)
    msgdef = msgpath.read_text(encoding='utf-8')
    add_types.update(get_types_from_msg(msgdef, guess_msgtype(msgpath)))

register_types(add_types)

# Type import works only after the register_types call,
# the classname is derived from the msgtype names above.

from rosbags.typesys.types import (  # type: ignore[attr-defined]  # noqa: E402
    custom_msgs__msg__Accel as Accel,
    custom_msgs__msg__Speed as Speed,
)

Accel(42)
Speed(42)
