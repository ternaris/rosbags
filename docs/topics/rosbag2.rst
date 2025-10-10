Rosbag2
=======
The :py:mod:`rosbags.rosbag2` package provides a conformant implementation of rosbag2. It provides read-write access to raw message data saved inside rosbag2 containers, and supports all features present in the C++ reference implementation.

Supported Versions
------------------
All versions up to the current (ROS2 Jazzy) version 9 are supported.

Supported Features
------------------
Rosbag2 is a flexible format that supports plugging different serialization methods, compression formats, and storage containers together. The rosbag2 C++ reference implementation is build around plugins that provide serialization, compression, and storage. This project implements all rosbag2 core plugins that are distributed with the C++ reference implementation.

:Serializers:
    - cdr (without wstring)

:Compressors:
    - zstd

:Storages:
    - sqlite3
    - mcap

Writing rosbag2
---------------
Instances of the :py:class:`Writer <rosbags.rosbag2.Writer>` class can create and write to new rosbag2 files. It is usually used as a context manager. Before the first message of a topic can be written, its topic must first be added to the bag. The following example shows the typical usage pattern:

.. code-block:: python

   from rosbags.rosbag2 import Writer
   from rosbags.typesys import Stores, get_typestore

   # Create a typestore for the desired ROS release and get the string class.
   typestore = get_typestore(Stores.LATEST)
   String = typestore.types['std_msgs/msg/String']

   # Create writer instance and open for writing.
   with Writer('/home/ros/rosbag_2020_03_24') as writer:
       # Add new connection.
       topic = '/chatter'
       msgtype = String.__msgtype__
       connection = writer.add_connection(topic, msgtype, typestore=typestore)

       # Serialize and write message.
       timestamp = 42
       message = String('hello world')
       writer.write(connection, timestamp, typestore.serialize_cdr(message, msgtype))

Reading rosbag2
---------------
Instances of the :py:class:`Reader <rosbags.rosbag2.Reader>` class are used to read rosbag2 metadata and its contents. It is recommended to use the Reader as a context manager. The following example shows the typical usage pattern:

.. note::

   For reading bags, you might want to use the :ref:`highlevel` AnyReader instead, as it provides a simpler and unified API for ROS1 and ROS2 bags.

.. code-block:: python

   from rosbags.rosbag2 import Reader
   from rosbags.typesys import Stores, get_typestore

   # Create a typestore and get the string class.
   typestore = get_typestore(Stores.LATEST)

   # Create reader instance and open for reading.
   with Reader('/home/ros/rosbag_2020_03_24') as reader:
       # Topic and msgtype information is available on .connections list.
       for connection in reader.connections:
           print(connection.topic, connection.msgtype)

       # Iterate over messages.
       for connection, timestamp, rawdata in reader.messages():
           if connection.topic == '/imu_raw/Imu':
               msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
               print(msg.header.frame_id)

       # The .messages() method accepts connection filters.
       connections = [x for x in reader.connections if x.topic == '/imu_raw/Imu']
       for connection, timestamp, rawdata in reader.messages(connections=connections):
           msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
           print(msg.header.frame_id)
