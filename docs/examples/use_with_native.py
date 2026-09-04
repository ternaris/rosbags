"""Example: Message instance conversion."""

from __future__ import annotations

import importlib
from dataclasses import fields
from typing import TYPE_CHECKING, TypeVar

import numpy as np

if TYPE_CHECKING:
    from dataclasses import Field
    from typing import ClassVar, Protocol

    class MessageInstance(Protocol):
        """Rosbags deserialized message instance."""

        __msgtype__: ClassVar[str]
        __dataclass_fields__: ClassVar[dict[str, Field[object]]]


T = TypeVar('T')

NATIVE_CLASSES: dict[str, type] = {}


def to_native(msg: MessageInstance) -> object:
    """Convert rosbags message to native message.

    Args:
        msg: Rosbags message.

    Returns:
        Native message.

    """
    msgtype: str = msg.__msgtype__
    if msgtype not in NATIVE_CLASSES:
        pkg, name = msgtype.rsplit('/', 1)
        NATIVE_CLASSES[msgtype] = getattr(importlib.import_module(pkg.replace('/', '.')), name)

    kwargs = {}
    for field in fields(msg):
        assert isinstance(field.type, str)
        if 'ClassVar' in field.type:
            continue
        value = getattr(msg, field.name)
        if '__msg__' in field.type:
            value = to_native(value)
        elif isinstance(value, list):
            value = [to_native(x) for x in value]
        elif isinstance(value, np.ndarray):
            value = value.tolist()
        kwargs[field.name] = value

    return NATIVE_CLASSES[msgtype](**kwargs)


if __name__ == '__main__':
    from rosbags.typesys.stores.ros2_foxy import (
        builtin_interfaces__msg__Time,
        sensor_msgs__msg__Image,
        std_msgs__msg__Header,
    )

    image = sensor_msgs__msg__Image(
        std_msgs__msg__Header(builtin_interfaces__msg__Time(42, 666), '/frame'),
        4,
        4,
        'rgb8',
        False,  # noqa: FBT003
        4 * 3,
        np.zeros(4 * 4 * 3, dtype=np.uint8),
    )

    native_image = to_native(image)
    # native_image can now be passed to the ROS stack
