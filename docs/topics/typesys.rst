Type System
===========

Rosbags incorporates its own pure Python type system, accessible via :py:mod:`rosbags.typesys`. Internally, it utilizes parse trees to represent message definitions. It includes its own parsers for .idl and .msg definitions, facilitating the conversion of message definition files into the internal format. Furthermore, it offers type stores to manage collections of related types. Typesys enables the dynamic addition of custom message types during runtime, eliminating the need for an extra build step.

Type stores
-----------

In both ROS1 and ROS2, message types undergo changes such as additions, modifications, or removals over time. This evolution means that bags created with one ROS1 or ROS2 distribution may not be compatible with another. To address this, rosbags comes equipped with multiple type stores out of the box, ensuring compatibility with both current and previous ROS1 and ROS2 distributions.

A type store serves several key functions:

- It serves as a repository for message definitions.
- It registers new messages and automatically generates efficient serializer/deserializer functions using the :py:mod:`rosbags.serde` module.
- It handles the serialization and deserialization of messages.
- It supports readers and writers, providing features such as message definition hashing.

Getting a store handle
----------------------

To retrieve a type store instance, the typesys module offers the :py:func:`get_typestore() <rosbags.typesys.get_typestore>` function, which can be accessed as follows:

.. code-block:: python

   from rosbags.typesys import Stores, get_typestore

   typestore = get_typestore(Stores.ROS2_FOXY)

The :py:class:`Stores <rosbags.typesys.Stores>` enum is employed to designate the desired type. The built-in type stores comprise:

.. toctree::
   :maxdepth: 1
   :glob:

   typesys-types-*

Deserialization
---------------

Type store instances provide two deserialization functions:

- :py:func:`.deserialize_cdr() <rosbags.typesys.store.Typestore.deserialize_cdr>` to convert CDR messages to Python objects.
- :py:func:`.deserialize_ros1() <rosbags.typesys.store.Typestore.deserialize_ros1>` to convert ROS1 messages to Python objects.

Usage example:

.. code-block:: python

   from rosbags.typesys import Stores, get_typestore

   typestore = get_typestore(Stores.ROS2_HUMBLE)

   # Use CDR for ROS2, endianess is handled automatically.
   msg = typestore.deserialize_cdr(cdr_bytes, 'geometry_msgs/msg/Quaternion')

   # Use the ROS1 format for ROS1.
   msg = typestore.deserialize_ros1(ros1_bytes, 'geometry_msgs/msg/Quaternion')

Serialization
-------------

Type store instances provide two serialization functions:

- :py:func:`.serialize_cdr() <rosbags.typesys.store.Typestore.serialize_cdr>` to convert Python objects to CDR bytes.
- :py:func:`.serialize_ros1() <rosbags.typesys.store.Typestore.serialize_ros1>` to convert Python objects to ROS1 bytes.

.. code-block:: python

   from rosbags.typesys import Stores, get_typestore

   typestore = get_typestore(Stores.ROS2_HUMBLE)

   # Use CDR for ROS2, serialize message with system endianess.
   cdr_bytes = typestore.serialize_cdr(msg, 'geometry_msgs/msg/Quaternion')

   # Use CDR for ROS2, serialize message with explicit endianess.
   cdr_bytes = typestore.serialize_cdr(msg, 'geometry_msgs/msg/Quaternion', little_endian=False)

   # Use ROS1 format for ROS1, this format is little endian only.
   ros1_bytes = typestore.serialize_ros1(msg, 'geometry_msgs/msg/Quaternion')

Message instances
-----------------

The type system generates a data class for each message type, allowing direct read-write access to all mutable fields of a message. However, fields should be mutated with care as no type checking is applied during runtime.

.. note::

   While the type system parses message definitions with array bounds and/or default values, neither bounds nor default values are enforced or assigned to message instances.

Example of creating a message instance:

.. code-block:: python

   from rosbags.typesys import Stores, get_typestore

   typestore = get_typestore(Stores.ROS2_HUMBLE)

   Int32 = typestore.types['std_msgs/msg/Int32']

   int32 = Int32(data=42)

Accessing the data class via the ``.types`` dictionary works for both built-in and custom types. For better IDE and language server integration, it might be preferable to import the data class directly and bypass the type store. However, this should be done cautiously to avoid mixing different type stores.

.. code-block:: python

   from rosbags.typesys.stores.ros2_humble import std_msgs__msg__Int32 as Int32

   int32 = Int32(data=42)

Adding custom types
-------------------

By default, rosbags ships only the core types of a ROS distribution. Users often need to add their own types on top of these.

To add types to a store, message definitions need to be read from either ``.idl`` or ``.msg`` files and converted into parse trees using :py:func:`get_types_from_idl() <rosbags.typesys.get_types_from_idl>` or :py:func:`get_types_from_msg() <rosbags.typesys.get_types_from_msg>`.

Since messages often depend on other messages, they must either be registered one by one in the correct order or all at once. The :py:func:`.register() <rosbags.typesys.store.Typestore.register>` method of a type store takes a dictionary of parse trees with any number of types.

Example:

.. code-block:: python

   from pathlib import Path

   from rosbags.typesys import get_types_from_idl, get_types_from_msg

   # Read definitions to python strings.
   idl_text = Path('foo_msgs/msg/Foo.idl').read_text()
   msg_text = Path('bar_msgs/msg/Bar.msg').read_text()

   # Plain dictionary to hold message definitions.
   add_types = {}

   # Add definitions from one idl file to the dict.
   add_types.update(get_types_from_idl(idl_text))

   # Add definitions from one msg file to the dict.
   add_types.update(get_types_from_msg(msg_text, 'bar_msgs/msg/Bar'))

Once all message definitions are parsed into the ``add_types`` dictionary, they can be added to a type store:

.. code-block:: python

   from rosbags.typesys import Stores, get_typestore

   typestore = get_typestore(Stores.ROS2_HUMBLE)
   typestore.register(add_types)

Now the type store can work with the custom types:

.. code-block:: python

   # Deserialize a custom message.
   msg = typestore.deserialize_cdr(cdr_bytes, 'foo_msgs/msg/Foo')

   # Get the Python data class for the custom type Bar.
   Bar = typestore.types['bar_msgs/msg/Bar']

   # Instantiate a Bar, lets assume it takes x, y, and z.
   bar = Bar(x=1., y=2., z=3.)

   # Serialize custom message.
   cdr_bytes = typestore.serialize_cdr(bar, 'bar_msgs/msg/Bar')
