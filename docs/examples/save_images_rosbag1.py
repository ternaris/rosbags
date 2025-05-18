"""Example: Save images as rosbag1."""

from __future__ import annotations

import numpy as np

from rosbags.rosbag1 import Writer
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.stores.ros1_noetic import (
    builtin_interfaces__msg__Time as Time,
    sensor_msgs__msg__CompressedImage as CompressedImage,
    std_msgs__msg__Header as Header,
)

TOPIC = '/camera'
FRAMEID = 'map'

# Contains filenames and their timestamps
IMAGES = [('homer.jpg', 42), ('marge.jpg', 43)]


def save_images() -> None:
    """Iterate over IMAGES and save to output bag."""
    typestore = get_typestore(Stores.ROS1_NOETIC)
    with Writer('output.bag') as writer:
        conn = writer.add_connection(TOPIC, CompressedImage.__msgtype__, typestore=typestore)

        for idx, (path, timestamp) in enumerate(IMAGES):
            msg = CompressedImage(
                Header(
                    seq=idx,
                    stamp=Time(sec=int(timestamp // 10**9), nanosec=int(timestamp % 10**9)),
                    frame_id=FRAMEID,
                ),
                format='jpeg',  # could also be 'png'
                data=np.fromfile(path, dtype=np.uint8),
            )

            writer.write(
                conn,
                timestamp,
                typestore.serialize_ros1(msg, CompressedImage.__msgtype__),
            )
