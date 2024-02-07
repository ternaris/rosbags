"""Save multiple images in rosbag2."""

import numpy as np

from rosbags.rosbag2 import Writer
from rosbags.serde import serialize_cdr
from rosbags.typesys.types import (
    builtin_interfaces__msg__Time as Time,
    sensor_msgs__msg__CompressedImage as CompressedImage,
    std_msgs__msg__Header as Header,
)

TOPIC = '/camera'
FRAMEID = 'map'

# Contains filenames and their timestamps
IMAGES = [
    ('homer.jpg', 42),
    ('marge.jpg', 43),
]


def save_images() -> None:
    """Iterate over IMAGES and save to output bag."""
    with Writer('output') as writer:
        conn = writer.add_connection(TOPIC, CompressedImage.__msgtype__)

        for path, timestamp in IMAGES:
            message = CompressedImage(
                Header(
                    stamp=Time(
                        sec=int(timestamp // 10**9),
                        nanosec=int(timestamp % 10**9),
                    ),
                    frame_id=FRAMEID,
                ),
                format='jpeg',  # could also be 'png'
                data=np.fromfile(path, dtype=np.uint8),
            )

            writer.write(
                conn,
                timestamp,
                serialize_cdr(message, message.__msgtype__),
            )
