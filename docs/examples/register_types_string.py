"""Example: Register type from definition string."""

from __future__ import annotations

from rosbags.typesys import Stores, get_types_from_msg, get_typestore

# Your custom message definition
STRIDX_MSG = """
string string
uint32 index
"""

typestore = get_typestore(Stores.ROS2_FOXY)
typestore.register(get_types_from_msg(STRIDX_MSG, 'custom_msgs/msg/StrIdx'))

StrIdx = typestore.types['custom_msgs/msg/StrIdx']

message = StrIdx(string='foo', index=42)

# Rawdata that can be passed to rosbag2.Writer.write
rawdata = typestore.serialize_cdr(message, message.__msgtype__)
