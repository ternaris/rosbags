.. _highlevel:

Highlevel APIs
==============
The :py:mod:`rosbags.highlevel` package provides classes that abstract the complexity of ROS types, serialization and message access into single easy-to-use interfaces.

All in one reader
-----------------
Instances of the :py:class:`AnyReader <rosbags.highlevel.AnyReader>` class give unified access to a list of either ROS1 or ROS2 bag files, but not a mixture of both, and will replay messages in correct timestamp order as if the messages came from a single bag.

The reader also directly exposes appropriate deserialization methods and automatically registers all message type definitions into blank, internal type store.

.. code-block:: python

   from pathlib import Path

   from rosbags.highlevel import AnyReader

   # Create reader instance and open for reading.
   with AnyReader([Path('/home/ros/rosbag_2024_01_26')]) as reader:
       connections = [x for x in reader.connections if x.topic == '/imu_raw/Imu']
       for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)
            print(msg.header.frame_id)

For legacy ROS2 bag files that lack message definitions, you need to create and provide a typestore manually.

.. code-block:: python

   from pathlib import Path

   from rosbags.highlevel import AnyReader
   from rosbags.typesys import Stores, get_typestore

   # Explicitly create a type store for legacy ROS2 bags without message definitions.
   typestore = get_typestore(Stores.ROS2_FOXY)

   # Create reader instance and open for reading.
   with AnyReader([Path('/home/ros/rosbag_2020_03_24')], default_typestore=typestore) as reader:
       connections = [x for x in reader.connections if x.topic == '/imu_raw/Imu']
       for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)
            print(msg.header.frame_id)
