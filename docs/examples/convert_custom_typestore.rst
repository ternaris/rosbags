Convert with a Custom Typestore
===============================

When converting ROS bag files, the converter requires access to all relevant message definitions. If the source bag files include all necessary definitions, no further action is needed, the converter will automatically detect and use them. However, if any definitions are missing, you must supply them using a **typestore**.


Creating a Typestore Module
---------------------------

The ``rosbags-convert`` tool supports loading a typestore from a Python module. The easiest way to create a suitable typestore is to start with an existing one and extend it with any additional message types you need.

.. literalinclude:: ./convert_custom_typestore.py

Converting with a Typestore
---------------------------

To use your custom typestore during conversion, pass it to `rosbags-convert` via the `--src-typestore-ref` option.

.. code-block:: shell

   rosbags-convert \
     --src-typestore-ref my_typestores:nmea_typestore \
     --src rosbag_without_types \
     --dst rosbag_with_types

.. note::

   Ensure Python can locate your typestore module. If you encounter ``ModuleNotFoundError``, verify that the directory containing your typestore is included in the ``PYTHONPATH`` environment variable.
