# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Message Definition Hashing Tests."""

import pytest

from rosbags.typesys import Stores, TypesysError, get_types_from_msg, get_typestore

MSG_HASH = """
byte[4] array
byte[] sequence
byte[<=4] bounded_sequence
char[4] chars
string str
string[4] array_of_str
string<=8 bounded_str
string<=8[4] array_of_bounded_str
string<=8[] sequence_of_bounded_str
string<=8[<=4] bounded_sequence_of_bounded_str
"""


def test_generate_msgdef() -> None:
    """Test typestore generates message definitions from parse trees."""
    store = get_typestore(Stores.ROS1_NOETIC)

    res = store.generate_msgdef('std_msgs/msg/Empty')
    assert res == ('', 'd41d8cd98f00b204e9800998ecf8427e')

    res = store.generate_msgdef('std_msgs/msg/Header')
    assert res == ('uint32 seq\ntime stamp\nstring frame_id\n', '2176decaecbce78abc3b96ef049fabed')

    res = store.generate_msgdef('geometry_msgs/msg/PointStamped')
    assert res[0].split(f'{"=" * 80}\n') == [
        'std_msgs/Header header\ngeometry_msgs/Point point\n',
        'MSG: std_msgs/Header\nuint32 seq\ntime stamp\nstring frame_id\n',
        'MSG: geometry_msgs/Point\nfloat64 x\nfloat64 y\nfloat64 z\n',
    ]

    res = store.generate_msgdef('geometry_msgs/msg/Twist')
    assert res[0].split(f'{"=" * 80}\n') == [
        'geometry_msgs/Vector3 linear\ngeometry_msgs/Vector3 angular\n',
        'MSG: geometry_msgs/Vector3\nfloat64 x\nfloat64 y\nfloat64 z\n',
    ]

    res = store.generate_msgdef('shape_msgs/msg/Mesh')
    assert res[0].split(f'{"=" * 80}\n') == [
        'shape_msgs/MeshTriangle[] triangles\ngeometry_msgs/Point[] vertices\n',
        'MSG: shape_msgs/MeshTriangle\nuint32[3] vertex_indices\n',
        'MSG: geometry_msgs/Point\nfloat64 x\nfloat64 y\nfloat64 z\n',
    ]

    res = store.generate_msgdef('shape_msgs/msg/Plane')
    assert res[0] == 'float64[4] coef\n'

    res = store.generate_msgdef('sensor_msgs/msg/MultiEchoLaserScan')
    assert len(res[0].split('=' * 80)) == 3

    store.register(get_types_from_msg('time[3] times\nuint8 foo=42', 'foo_msgs/Timelist'))
    res = store.generate_msgdef('foo_msgs/msg/Timelist')
    assert res[0] == 'uint8 foo=42\ntime[3] times\n'

    with pytest.raises(TypesysError, match='is unknown'):
        _ = store.generate_msgdef('foo_msgs/msg/Badname')


def test_ros1md5() -> None:
    """Test typestore hashes with MD5."""
    store = get_typestore(Stores.LATEST)

    _, digest = store.generate_msgdef('std_msgs/msg/Byte')
    assert digest == 'ad736a2e8818154c487bb80fe42ce43b'

    _, digest = store.generate_msgdef('std_msgs/msg/ByteMultiArray')
    assert digest == '70ea476cbcfd65ac2f68f3cda1e891fe'

    store.register(get_types_from_msg(MSG_HASH, 'test_msgs/msg/Hash'))
    _, digest = store.generate_msgdef('test_msgs/msg/Hash')
    assert digest == 'ba5c64f27c2f554bc2975575c3ce3c20'


def test_rihs01() -> None:
    """Test typestore hashes with RIHS01."""
    store = get_typestore(Stores.LATEST)

    assert (
        store.hash_rihs01('std_msgs/msg/Byte')
        == 'RIHS01_41e1a3345f73fe93ede006da826a6ee274af23dd4653976ff249b0f44e3e798f'
    )

    assert (
        store.hash_rihs01('std_msgs/msg/ByteMultiArray')
        == 'RIHS01_972fec7f50ab3c1d06783c228e79e8a9a509021708c511c059926261ada901d4'
    )

    assert (
        store.hash_rihs01('geometry_msgs/msg/Accel')
        == 'RIHS01_dc448243ded9b1fcbcca24aba0c22f013dae06c354ba2d849571c0a2a3f57ca0'
    )

    store.register(get_types_from_msg(MSG_HASH, 'test_msgs/msg/Hash'))
    assert (
        store.hash_rihs01('test_msgs/msg/Hash')
        == 'RIHS01_6f444494cb202f5c8dc6f92c98f4c60b926f1b24a3dc1cabfa7fbd35c72e246a'
    )
