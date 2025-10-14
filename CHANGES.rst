.. _changes:

Changes
=======

0.11.0 - 2025-10-15
-------------------

- Advertise Python 3.14 compatibility
- Support standalone storage files in ``rosbag2.Reader`` `#78`_ `#121`_ `#124`_
- Remove deprecated APIs and behavior
- Increase ``rosbags-convert`` default rosbag2 target format version to 9
- Improve handling of nested types in the IDL parser

.. _#78: https://gitlab.com/ternaris/rosbags/issues/78
.. _#121: https://gitlab.com/ternaris/rosbags/issues/121
.. _#124: https://gitlab.com/ternaris/rosbags/issues/124


0.10.11 - 2025-08-02
--------------------

- Write mcap statistics record `#120`_

.. _#120: https://gitlab.com/ternaris/rosbags/issues/120


0.10.10 - 2025-05-18
--------------------

- Add kilted typestore
- Allow empty schema definitions in MCAP files
- Read MCAP chunks with message_start_time 0 `#112`_
- Document conversion with custom typestore `#116`_
- Do not convert filesystem related exceptions `#117`_
- Use explicit dtypes in tests `#118`_

.. _#112: https://gitlab.com/ternaris/rosbags/issues/112
.. _#116: https://gitlab.com/ternaris/rosbags/issues/116
.. _#117: https://gitlab.com/ternaris/rosbags/issues/117
.. _#118: https://gitlab.com/ternaris/rosbags/issues/118


0.10.9 - 2025-03-11
-------------------

- Properly represent the Empty message type `#109`_
- Add MCAP writer, support conversion to rosbag2 with MCAP storage `#97`_

.. _#97: https://gitlab.com/ternaris/rosbags/issues/97
.. _#109: https://gitlab.com/ternaris/rosbags/issues/109


0.10.8 - 2025-02-26
-------------------

- Add missing jazzy store to enum `#108`_
- Fix rosbag1 reader example and point to AnyReader `#110`_
- Allow msg Header field type in any position `#111`_

.. _#108: https://gitlab.com/ternaris/rosbags/issues/108
.. _#110: https://gitlab.com/ternaris/rosbags/issues/110
.. _#111: https://gitlab.com/ternaris/rosbags/issues/111


0.10.7 - 2025-01-11
-------------------

- Advertise Python 3.13 compatibility
- Switch to uv


0.10.6 - 2024-10-29
-------------------

- Fall back to noetic store in deprecated rosbag1 writer code path `#102`_

.. _#102: https://gitlab.com/ternaris/rosbags/issues/102


0.10.5 - 2024-10-21
-------------------

- Support compression in rosbags-convert `#94`_
- Require minimum typing_extensions version `#100`_
- Improve parsing of float literals `#101`_

.. _#94: https://gitlab.com/ternaris/rosbags/issues/94
.. _#100: https://gitlab.com/ternaris/rosbags/issues/100
.. _#101: https://gitlab.com/ternaris/rosbags/issues/101


0.10.4 - 2024-06-30
-------------------

- Add jazzy typestore.
- Fix dumping of QoS metadata `#93`_
- Fix automatic message type renaming in rosbags convert.

.. _#93: https://gitlab.com/ternaris/rosbags/issues/93


0.10.3 - 2024-06-07
-------------------

- Improve rosbags-convert help strings
- Support rosbag2 up to version 9 `#92`_

.. _#92: https://gitlab.com/ternaris/rosbags/issues/92


0.10.2 - 2024-05-25
-------------------

- Improve type hints


0.10.1 - 2024-05-10
-------------------

- Avoid name collisions with relative typenames `#85`_

.. _#85: https://gitlab.com/ternaris/rosbags/issues/85


0.10.0 - 2024-04-09
-------------------

- Increase minimum required Python version to 3.10
- Add reading multiple ROS2 bags to AnyReader
- Add merging of bags to rosbags-convert
- Add message type definition migration to rosbags-convert


0.9.23 - 2024-04-01
-------------------

- Remove IDL octet support as it is not used in ROS, fixes `#81`_

.. _#81: https://gitlab.com/ternaris/rosbags/issues/81


0.9.22 - 2024-03-06
-------------------

- Fix header definition handling in rosbag converter `#74`_

.. _#74: https://gitlab.com/ternaris/rosbags/issues/74


0.9.21 - 2024-03-04
-------------------

- Fix Python 3.9 and 3.10 compatibility `#73`_

.. _#73: https://gitlab.com/ternaris/rosbags/issues/73


0.9.20 - 2024-02-29
-------------------

- Deprecate APIs working on global types
- Support explicit typestores for message handling
- Ship core types from current and historic ROS distributions
- Fix CDR alignment after base arrays `#72`_

.. _#72: https://gitlab.com/ternaris/rosbags/issues/72


0.9.19 - 2023-12-23
-------------------

- Fix msgdef encoding detection in AnyReader


0.9.18 - 2023-12-22
-------------------

- Improve rosbag2 message digest handling


0.9.17 - 2023-12-21
-------------------

- Improve type hint detection in class generator
- Support concatenated IDL messages from bag
- Add rosbag2 messages to default typesys `#63`_
- Account for base types that decrease alignment `#66`_

.. _#63: https://gitlab.com/ternaris/rosbags/issues/63
.. _#66: https://gitlab.com/ternaris/rosbags/issues/66


0.9.16 - 2023-08-11
-------------------

- Support rosbag2 up to version 8 `#59`_
- Implement RIHS01 hashing of types
- Fix chunk size bug in rosbag1 writer `#58`_
- Fix handling of empty messages `#56`_
- Allow empty bags, chunks, and connections
- Avoid field name collisions with python keywords `#51`_
- Improve msg/idl type matching
- Improve some examples

.. _#51: https://gitlab.com/ternaris/rosbags/issues/51
.. _#56: https://gitlab.com/ternaris/rosbags/issues/56
.. _#58: https://gitlab.com/ternaris/rosbags/issues/58
.. _#59: https://gitlab.com/ternaris/rosbags/issues/59


0.9.15 - 2023-03-02
-------------------
- Refactor rosbag2 Reader for multiple storage backends
- Improve parsing of IDL files
- Handle bags containing only connection records
- Add AnyReader to documentation
- Add initial MCAP reader for rosbag2 `#33`_

.. _#33: https://gitlab.com/ternaris/rosbags/issues/33


0.9.14 - 2023-01-12
-------------------
- Fix reader example in README `#40`_
- Flush decompressed files rosbag2.Reader
- Advertise Python 3.11 compatibility

.. _#40: https://gitlab.com/ternaris/rosbags/issues/40


0.9.13 - 2022-09-23
-------------------
- Fix parsing of comments in message definitions `#31`_
- Fix parsing of members starting with ``string`` in message definitions `#35`_
- Change lz4 compression level to 0 `#36`_
- Add include filters to rosbag conversion `#38`_
- Implement direct ros1 (de)serialization

.. _#31: https://gitlab.com/ternaris/rosbags/issues/31
.. _#35: https://gitlab.com/ternaris/rosbags/issues/35
.. _#36: https://gitlab.com/ternaris/rosbags/issues/36
.. _#38: https://gitlab.com/ternaris/rosbags/issues/38


0.9.12 - 2022-07-27
-------------------
- Add support for rosbag2 version 6 metadata `#30`_
- Enable rosbags-convert to exclude topics `#25`_

.. _#30: https://gitlab.com/ternaris/rosbags/issues/30
.. _#25: https://gitlab.com/ternaris/rosbags/issues/25


0.9.11 - 2022-05-17
-------------------
- Report start_time and end_time on empty bags


0.9.10 - 2022-05-04
-------------------
- Add support for multiple type stores
- Document which types are supported out of the box `#21`_
- Unify Connection and TopicInfo objects across rosbag1 and rosbag2
- Add experimental all-in-one reader for rosbag1, split rosbag1, and rosbag2
- Convert reader and writer .connection attribute from dict to list
- Add support for rosbag2 version 5 metadata `#18`_
- Speed up opening of rosbag1 files
- Fix serialization of empty message sequences `#23`_

.. _#18: https://gitlab.com/ternaris/rosbags/issues/18
.. _#21: https://gitlab.com/ternaris/rosbags/issues/21
.. _#23: https://gitlab.com/ternaris/rosbags/issues/23


0.9.9 - 2022-01-10
------------------
- Fix documentation code samples `#15`_
- Fix handling of padding after empty sequences `#14`_
- Support conversion from rosbag2 to rosbag1 `#11`_

.. _#11: https://gitlab.com/ternaris/rosbags/issues/11
.. _#14: https://gitlab.com/ternaris/rosbags/issues/14
.. _#15: https://gitlab.com/ternaris/rosbags/issues/15


0.9.8 - 2021-11-25
------------------
- Support bool and float constants in msg files


0.9.7 - 2021-11-09
------------------
- Fix parsing of const fields with string value `#9`_
- Parse empty msg definitions
- Make packages PEP561 compliant
- Parse msg bounded fields and default values `#12`_

.. _#9: https://gitlab.com/ternaris/rosbags/issues/9
.. _#12: https://gitlab.com/ternaris/rosbags/issues/12

0.9.6 - 2021-10-04
------------------
- Do not match msg separator as constant value


0.9.5 - 2021-10-04
------------------
- Add string constant support to msg parser


0.9.4 - 2021-09-15
------------------
- Make reader1 API match reader2
- Fix connection mapping for reader2 messages `#1`_, `#8`_

.. _#1: https://gitlab.com/ternaris/rosbags/issues/1
.. _#8: https://gitlab.com/ternaris/rosbags/issues/8

0.9.3 - 2021-08-06
------------------

- Add const fields to type classes
- Add CDR to ROS1 bytestream conversion
- Add ROS1 message definition generator
- Use connection oriented APIs in readers and writers
- Add rosbag1 writer


0.9.2 - 2021-07-08
------------------

- Support relative type references in msg files


0.9.1 - 2021-07-05
------------------

- Use half-open intervals for time ranges
- Create appropriate QoS profiles for latched topics in converted bags
- Fix return value tuple order of messages() in documentation `#2`_
- Add type hints to message classes
- Remove non-default ROS2 message types
- Support multi-line comments in idl files
- Fix parsing of msg files on non-POSIX platforms `#4`_

.. _#2: https://gitlab.com/ternaris/rosbags/issues/2
.. _#4: https://gitlab.com/ternaris/rosbags/issues/4


0.9.0 - 2021-05-16
------------------

- Initial Release
