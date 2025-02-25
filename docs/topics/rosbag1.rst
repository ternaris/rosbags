Rosbag1
=======

The :py:mod:`rosbags.rosbag1` package provides fast read-only access to raw messages stored in the legacy bag format. The rosbag1 support is built for a ROS2 world and some APIs and values perform normalizations to mimic ROS2 behavior and make messages originating from rosbag1 and rosbag2 behave identically. Most notably message types are internally renamed to match their ROS2 counterparts.

Writing rosbag1
---------------
Instances of the :py:class:`Writer <rosbags.rosbag1.Writer>` class can create and write to new rosbag1 files. It is usually used as a context manager. Before the first message of a topic can be written, its topic must first be added to the bag. The following example shows the typical usage pattern:

.. code-block:: python

   from rosbags.rosbag1 import Writer
   from rosbags.typesys import Stores, get_typestore

   # Create a typestore for the desired ROS release and get the string class.
   typestore = get_typestore(Stores.ROS1_NOETIC)
   String = typestore.types['std_msgs/msg/String']

   # Create writer instance and open for writing.
   with Writer('/home/ros/rosbag_2020_03_24.bag') as writer:
       # Add new connection.
       topic = '/chatter'
       msgtype = String.__msgtype__
       connection = writer.add_connection(topic, msgtype, typestore=typestore)

       # Serialize and write message.
       timestamp = 42
       message = String('hello world')
       writer.write(connection, timestamp, typestore.serialize_ros1(message, msgtype))

Reading rosbag1
---------------
Instances of the :py:class:`Reader <rosbags.rosbag2.Reader>` class are typically used as context managers and provide access to bag metadata and contents after the bag has been opened. The following example shows the typical usage pattern:

.. note::

   For reading bags, you might want to use the :ref:`highlevel` AnyReader instead, as it provides a simpler and unified API for ROS1 and ROS2 bags.

.. code-block:: python

   from rosbags.rosbag1 import Reader
   from rosbags.typesys import Stores, get_typestore

   # Create a typestore for the matching ROS release.
   typestore = get_typestore(Stores.ROS1_NOETIC)

   # Create reader instance and open for reading.
   with Reader('/home/ros/rosbag_2020_03_24') as reader:
       # Topic and msgtype information is available on .connections list.
       for connection in reader.connections:
           print(connection.topic, connection.msgtype)

       # Iterate over messages.
       for connection, timestamp, rawdata in reader.messages():
           if connection.topic == '/imu_raw/Imu':
               msg = typestore.deserialize_ros1(rawdata, connection.msgtype)
               print(msg.header.frame_id)

       # The .messages() method accepts connection filters.
       connections = [x for x in reader.connections if x.topic == '/imu_raw/Imu']
       for connection, timestamp, rawdata in reader.messages(connections=connections):
           msg = typestore.deserialize_ros1(rawdata, connection.msgtype)
           print(msg.header.frame_id)
