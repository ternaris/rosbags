"""Example: Edit message definition.

Between ROS1 and ROS2 the CameraInfo message definition has changed.
The D, K, R, and P field names have been changed from upper case to
lower case. This example shows how to downgrade the messages in a
rosbag1 to the proper message definition.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from rosbags.highlevel.anyreader import AnyReader
from rosbags.rosbag1 import Writer
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

if TYPE_CHECKING:
    from pathlib import Path

    from rosbags.interfaces import ConnectionExtRosbag1
    from rosbags.typesys.stores.ros2_foxy import sensor_msgs__msg__CameraInfo

# Noetic camera info message definition, taken from:
# http://docs.ros.org/en/noetic/api/sensor_msgs/html/msg/CameraInfo.html
CAMERAINFO_DEFINITION = """
std_msgs/Header header
uint32 height
uint32 width
string distortion_model
float64[] D
float64[9] K
float64[9] R
float64[12] P
uint32 binning_x
uint32 binning_y
sensor_msgs/RegionOfInterest roi
"""


def downgrade_camerainfo_to_rosbag1(src: Path, dst: Path) -> None:
    """Edit message definitions in a rosbag1.

    Args:
        src: Rosbag1 source path.
        dst: Destination path.
        topic: Name of topic to remove.

    """
    typename = 'sensor_msgs/msg/CameraInfo'
    typestore = get_typestore(Stores.EMPTY)
    typestore.register(
        get_types_from_msg(CAMERAINFO_DEFINITION, typename),
    )
    CameraInfo = typestore.types[typename]  # noqa: N806

    with AnyReader([src]) as reader, Writer(dst) as writer:
        conn_map = {}

        for conn in reader.connections:
            ext = cast('ConnectionExtRosbag1', conn.ext)

            # Use updated message definition and md5sum for CameraInfo.
            if conn.msgtype == 'sensor_msgs/msg/CameraInfo':
                from_typestore = typestore
            else:
                from_typestore = reader.typestore

            conn_map[conn.id] = writer.add_connection(
                conn.topic,
                conn.msgtype,
                typestore=from_typestore,
                callerid=ext.callerid,
                latching=ext.latching,
            )

        for conn, timestamp, data in reader.messages():
            wconn = conn_map[conn.id]

            if conn.msgtype == 'sensor_msgs/msg/CameraInfo':
                msg = cast('sensor_msgs__msg__CameraInfo', reader.deserialize(data, conn.msgtype))
                converted_msg = CameraInfo(
                    header=msg.header,
                    height=msg.height,
                    width=msg.width,
                    distortion_model=msg.distortion_model,
                    # Map lower case names to upper case.
                    D=msg.d,
                    K=msg.k,
                    R=msg.r,
                    P=msg.p,
                    binning_x=msg.binning_x,
                    binning_y=msg.binning_y,
                    roi=msg.roi,
                )
                outdata: memoryview | bytes = typestore.serialize_ros1(converted_msg, wconn.msgtype)
            else:
                outdata = data

            writer.write(wconn, timestamp, outdata)
