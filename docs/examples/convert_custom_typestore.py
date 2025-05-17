"""Example: Creating a Custom Typestore.

This module defines a global variable ``nmea_typestore``, which extends
the default Jazzy typestore by adding one additional message type.

If this file is saved as ``my_typestores.py``, the fully qualified
reference to the typestore is ``my_typestores:nmea_typestore``.

"""

from __future__ import annotations

from rosbags.typesys import Stores, get_typestore
from rosbags.typesys.msg import get_types_from_msg

NMEA_SENTENCE_MSG = """
std_msgs/msg/Header header
string sentence
"""

nmea_typestore = get_typestore(Stores.ROS2_JAZZY)
nmea_typestore.register(get_types_from_msg(NMEA_SENTENCE_MSG, 'nmea_msgs/msg/Sentence'))
