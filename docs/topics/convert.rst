Convert rosbag versions
=======================

The :py:mod:`rosbags.convert` package includes a CLI tool to convert legacy rosbag1 files to rosbag2 and vice versa.

Features
--------

- Reasonably fast, as it converts raw ROS1 messages to raw CDR messages without going though deserialization and serialization
- Tries to match ROS1 message type names to registered ROS2 types
- Automatically registers unknown message types present in the legacy rosbag file for the conversion
- Handles differences of ``std_msgs/msg/Header`` between both ROS versions

Limitations
-----------

- Refuses to convert unindexed rosbag1 files, please reindex files before conversion
- Unindexed MCAP inputs must be in timestamp order
- Direct CDR-to-ROS1 conversion requires little-endian CDR input

Usage
-----

.. code-block:: console

   # Convert "foo.bag", result will be "foo/"
   $ rosbags-convert --src foo.bag --dst foo

   # Convert "bar", result will be "bar.bag"
   $ rosbags-convert --src bar --dst bar.bag

   # Convert "foo.bag", save the result as "bar"
   $ rosbags-convert --src foo.bag --dst /path/to/bar

   # Convert "bar", save the result as "foo.bag"
   $ rosbags-convert --src bar --dst /path/to/foo.bag
