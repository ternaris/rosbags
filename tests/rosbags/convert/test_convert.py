# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbag Converter Tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from unittest.mock import ANY, MagicMock, call, patch

import pytest

from rosbags.convert import ConverterError, convert
from rosbags.convert.converter import (
    LATCH,
    create_connections_converters,
    default_message,
    generate_message_converter,
    migrate_bytes,
    migrate_message,
)
from rosbags.highlevel import AnyReaderError
from rosbags.interfaces import (
    Connection,
    ConnectionExtRosbag1,
    ConnectionExtRosbag2,
    MessageDefinition,
    MessageDefinitionFormat,
    Qos,
)
from rosbags.rosbag1 import (
    Writer as Writer1,
    WriterError as WriterError1,
)
from rosbags.rosbag2 import (
    Writer as Writer2,
    WriterError as WriterError2,
)
from rosbags.typesys.msg import get_types_from_msg
from rosbags.typesys.stores import Stores, get_typestore

if TYPE_CHECKING:
    from pathlib import Path

    from rosbags.typesys.stores.ros1_noetic import (
        sensor_msgs__msg__CameraInfo as CameraInfo1,
        shape_msgs__msg__MeshTriangle as MeshTriangle1,
        std_msgs__msg__Duration as Duration1,
        std_msgs__msg__Int8 as Int8,
        std_msgs__msg__Int8MultiArray as Int8MultiArray1,
        visualization_msgs__msg__InteractiveMarkerUpdate as InteractiveMarkerUpdate1,
        visualization_msgs__msg__Marker as Marker1,
    )
    from rosbags.typesys.stores.ros2_iron import (
        sensor_msgs__msg__CameraInfo as CameraInfo2,
        shape_msgs__msg__MeshTriangle as MeshTriangle2,
        std_msgs__msg__Int16MultiArray as Int16MultiArray2,
        std_msgs__msg__String as String2,
        visualization_msgs__msg__InteractiveMarkerUpdate as InteractiveMarkerUpdate2,
        visualization_msgs__msg__Marker as Marker2,
    )


def test_convert_reader_errors(tmp_path: Path) -> None:
    """Test convert forwards reader errors."""
    with (
        patch('rosbags.convert.converter.AnyReader', side_effect=AnyReaderError('exc')),
        pytest.raises(ConverterError, match='Reading source bag: exc'),
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())


def test_convert_writer_errors(tmp_path: Path) -> None:
    """Test convert forwards writer errors."""
    with (
        patch('rosbags.convert.converter.Writer2', side_effect=WriterError2('exc')),
        pytest.raises(ConverterError, match='Writing destination bag: exc'),
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())

    with (
        patch('rosbags.convert.converter.Writer1', side_effect=WriterError1('exc')),
        pytest.raises(ConverterError, match='Writing destination bag: exc'),
    ):
        convert([], tmp_path / 'foo.bag', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())


def test_convert_reraises_assertions(tmp_path: Path) -> None:
    """Test convert reraises assertion errors."""
    with (
        patch('rosbags.convert.converter.AnyReader', side_effect=AssertionError('exc')),
        pytest.raises(AssertionError, match='exc'),
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())


def test_convert_forwards_exceptions(tmp_path: Path) -> None:
    """Test convert forwards exceptions."""
    with (
        patch('rosbags.convert.converter.AnyReader', side_effect=KeyError('exc')),
        pytest.raises(ConverterError, match="Converting rosbag: KeyError\\('exc'\\)"),
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())


def test_convert_enables_compression(tmp_path: Path) -> None:
    """Test convert forwards exceptions."""
    with (
        patch('rosbags.convert.converter.AnyReader'),
        patch('rosbags.convert.converter.Writer1') as writer,
    ):
        convert([], tmp_path / 'foo.bag', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())
    writer.return_value.set_compression.assert_not_called()

    with (
        patch('rosbags.convert.converter.AnyReader'),
        patch('rosbags.convert.converter.Writer1') as writer,
    ):
        convert([], tmp_path / 'foo.bag', 'sqlite3', 8, 'bz2', 'file', None, None, (), (), (), ())
    writer.return_value.set_compression.assert_called()

    with (
        patch('rosbags.convert.converter.AnyReader'),
        patch('rosbags.convert.converter.Writer2') as writer,
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, None, 'file', None, None, (), (), (), ())
    writer.return_value.set_compression.assert_not_called()

    with (
        patch('rosbags.convert.converter.AnyReader'),
        patch('rosbags.convert.converter.Writer2') as writer,
    ):
        convert([], tmp_path / 'foo', 'sqlite3', 8, 'zstd', 'file', None, None, (), (), (), ())
    writer.return_value.set_compression.assert_called()


def test_convert_connection_filtering(tmp_path: Path) -> None:
    """Test convert filters connections."""
    with (
        patch('rosbags.convert.converter.AnyReader') as reader,
        patch('rosbags.convert.converter.Writer2'),
        patch('rosbags.convert.converter.create_connections_converters') as ccc,
    ):
        reader.return_value.__enter__.return_value.connections = []
        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), (), (), ())
    ccc.assert_not_called()

    with (
        patch('rosbags.convert.converter.AnyReader') as reader,
        patch('rosbags.convert.converter.Writer2'),
        patch(
            'rosbags.convert.converter.create_connections_converters',
            side_effect=AnyReaderError,
        ) as ccc,
    ):
        conn = MagicMock()
        conn.topic = 'foo'
        conn.msgtype = 'bar'
        reader.return_value.__enter__.return_value.connections = [conn]
        with pytest.raises(ConverterError):
            convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), (), (), ())
        ccc.reset_mock()

        with pytest.raises(ConverterError):
            convert(
                [], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), ('foo'), (), ('unknown')
            )
        ccc.reset_mock()

        with pytest.raises(ConverterError):
            convert(
                [], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), ('unknown'), (), ('bar')
            )
        ccc.reset_mock()

        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, ('foo'), (), (), ())
        ccc.assert_not_called()

        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), (), ('bar'), ())
        ccc.assert_not_called()

        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), ('unknown'), (), ())
        ccc.assert_not_called()

        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), (), (), ('unknown'))
        ccc.assert_not_called()


def test_convert_applies_transforms(tmp_path: Path) -> None:
    """Test convert applies transforms."""
    with (
        patch('rosbags.convert.converter.AnyReader') as reader,
        patch('rosbags.convert.converter.Writer2') as writer,
        patch(
            'rosbags.convert.converter.create_connections_converters',
        ) as ccc,
    ):
        conn = MagicMock()
        conn.id = 42
        conn.topic = 'foo'
        conn.msgtype = 'bar'
        conn.owner = 'own'
        rctx = reader.return_value.__enter__.return_value
        rctx.connections = [conn]
        rctx.messages.return_value = [(conn, 1, 2)]
        ccc.return_value = [
            {(42, 'own'): 666},
            {'bar': lambda x: x * 2},
        ]

        convert([], tmp_path, 'sqlite3', 8, None, 'file', None, None, (), (), (), ())

        writer.return_value.write.assert_called_with(666, 1, 4)


def test_connection_params_are_converted() -> None:
    """Test connection params are converted."""
    connections = [
        Connection(
            1,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1(None, latching=1),
            None,
        ),
        Connection(
            2,
            '/t2',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('caller', latching=0),
            None,
        ),
    ]

    reader = MagicMock()
    reader.is2 = False
    reader.typestore = get_typestore(Stores.ROS1_NOETIC)

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_has_calls(
        [
            call(
                '/t1',
                'std_msgs/msg/Int8',
                typestore=ANY,
                callerid=None,
                latching=1,
            ),
            call(
                '/t2',
                'std_msgs/msg/Int8',
                typestore=ANY,
                callerid='caller',
                latching=0,
            ),
        ]
    )

    writer = MagicMock(spec=Writer2)
    writer.connections = []
    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_has_calls(
        [
            call(
                '/t1',
                'std_msgs/msg/Int8',
                typestore=ANY,
                serialization_format='cdr',
                offered_qos_profiles=LATCH,
            ),
            call(
                '/t2',
                'std_msgs/msg/Int8',
                typestore=ANY,
                serialization_format='cdr',
                offered_qos_profiles=[],
            ),
        ]
    )

    connections = [
        Connection(
            1,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag2('cdr', LATCH),
            None,
        ),
        Connection(
            2,
            '/t2',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag2('cdr', []),
            None,
        ),
    ]

    reader = MagicMock()
    reader.is2 = True
    reader.typestore = get_typestore(Stores.ROS2_FOXY)

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_has_calls(
        [
            call(
                '/t1',
                'std_msgs/msg/Int8',
                typestore=ANY,
                callerid=None,
                latching=1,
            ),
            call(
                '/t2',
                'std_msgs/msg/Int8',
                typestore=ANY,
                callerid=None,
                latching=0,
            ),
        ]
    )

    writer = MagicMock(spec=Writer2)
    writer.connections = []
    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_has_calls(
        [
            call(
                '/t1',
                'std_msgs/msg/Int8',
                typestore=ANY,
                serialization_format='cdr',
                offered_qos_profiles=LATCH,
            ),
            call(
                '/t2',
                'std_msgs/msg/Int8',
                typestore=ANY,
                serialization_format='cdr',
                offered_qos_profiles=[],
            ),
        ]
    )


def test_destination_typestore_gets_created() -> None:
    """Test destination typestore gets created."""
    connections = [
        Connection(
            1,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('', latching=True),
            None,
        ),
    ]

    typestore1 = get_typestore(Stores.ROS1_NOETIC)
    typestore2 = get_typestore(Stores.ROS2_FOXY)

    reader = MagicMock()
    reader.is2 = False
    reader.typestore = typestore1

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_called_with(
        '/t1',
        'std_msgs/msg/Int8',
        typestore=typestore1,
        callerid='',
        latching=True,
    )

    reader = MagicMock()
    reader.is2 = True
    reader.typestore = typestore2

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_called_with(
        '/t1',
        'std_msgs/msg/Int8',
        typestore=ANY,
        callerid='',
        latching=True,
    )
    assert writer.add_connection.call_args.kwargs['typestore'] != typestore2

    reader = MagicMock()
    reader.is2 = False
    reader.typestore = typestore1

    writer = MagicMock(spec=Writer2)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_called_with(
        '/t1',
        'std_msgs/msg/Int8',
        typestore=ANY,
        serialization_format='cdr',
        offered_qos_profiles=LATCH,
    )
    assert writer.add_connection.call_args.kwargs['typestore'] != typestore1

    reader = MagicMock()
    reader.is2 = True
    reader.typestore = typestore2

    writer = MagicMock(spec=Writer2)
    writer.connections = []

    _ = create_connections_converters(connections, None, reader, writer)
    writer.add_connection.assert_called_with(
        '/t1',
        'std_msgs/msg/Int8',
        typestore=typestore2,
        serialization_format='cdr',
        offered_qos_profiles=LATCH,
    )

    reader = MagicMock()
    reader.is2 = False
    reader.typestore = typestore1

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    empty = get_typestore(Stores.EMPTY)
    _ = create_connections_converters(connections, empty, reader, writer)
    writer.add_connection.assert_called_with(
        '/t1',
        'std_msgs/msg/Int8',
        typestore=empty,
        callerid='',
        latching=True,
    )
    assert 'std_msgs/msg/Int8' in empty.types


def test_connection_deduplication() -> None:
    """Test connections get deduplicated."""
    connections = [
        Connection(
            1,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('', latching=True),
            None,
        ),
        Connection(
            2,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('', latching=True),
            None,
        ),
        Connection(
            3,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('', latching=False),
            None,
        ),
        Connection(
            4,
            '/t1',
            'std_msgs/msg/Int8',
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1('foo', latching=False),
            None,
        ),
    ]

    typestore = get_typestore(Stores.ROS1_NOETIC)
    reader = MagicMock()
    reader.is2 = False
    reader.typestore = typestore

    writer = MagicMock(spec=Writer1)
    writer.connections = []

    def add_connection1(
        name: str, typ: str, *, typestore: object, callerid: str, latching: bool
    ) -> Connection:
        _ = typestore
        res = Connection(
            len(writer.connections),
            name,
            typ,
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag1(callerid, latching),
            None,
        )
        writer.connections.append(res)
        return res

    writer.add_connection = add_connection1

    res = create_connections_converters(connections, typestore, reader, writer)
    assert res[0] == {
        (1, None): writer.connections[0],
        (2, None): writer.connections[0],
        (3, None): writer.connections[1],
        (4, None): writer.connections[2],
    }
    assert len(res[1]) == 1

    reader = MagicMock()
    reader.is2 = False
    reader.typestore = typestore

    writer = MagicMock(spec=Writer2)
    writer.connections = []

    def add_connection2(
        name: str,
        typ: str,
        *,
        typestore: object,
        serialization_format: str,
        offered_qos_profiles: list[Qos],
    ) -> Connection:
        _ = typestore
        res = Connection(
            len(writer.connections),
            name,
            typ,
            MessageDefinition(MessageDefinitionFormat.NONE, ''),
            '',
            0,
            ConnectionExtRosbag2(serialization_format, offered_qos_profiles),
            None,
        )
        writer.connections.append(res)
        return res

    writer.add_connection = add_connection2

    res = create_connections_converters(connections, typestore, reader, writer)
    assert res[0] == {
        (1, None): writer.connections[0],
        (2, None): writer.connections[0],
        (3, None): writer.connections[1],
        (4, None): writer.connections[1],
    }
    assert len(res[1]) == 1


def test_message_converter() -> None:
    """Test message converter."""
    srcts = get_typestore(Stores.ROS1_NOETIC)
    dstts = get_typestore(Stores.ROS2_IRON)

    conv = generate_message_converter(
        srcts,
        dstts,
        'builtin_interfaces/msg/Time',
        'builtin_interfaces/msg/Time',
        {},
        src_is2=False,
        dst_is2=False,
    )
    assert conv(b'42').tobytes() == b'42'

    conv = generate_message_converter(
        srcts,
        dstts,
        'builtin_interfaces/msg/Time',
        'builtin_interfaces/msg/Time',
        {},
        src_is2=True,
        dst_is2=True,
    )
    assert conv(b'42').tobytes() == b'42'

    conv = generate_message_converter(
        srcts,
        dstts,
        'std_msgs/msg/Header',
        'std_msgs/msg/Header',
        {},
        src_is2=False,
        dst_is2=False,
    )
    assert conv(b'42').tobytes() == b'42'

    conv = generate_message_converter(
        srcts,
        srcts,  # same typestore
        'visualization_msgs/msg/MarkerArray',
        'visualization_msgs/msg/MarkerArray',
        {},
        src_is2=False,
        dst_is2=False,
    )
    assert conv(b'42').tobytes() == b'42'

    with patch.object(dstts, 'ros1_to_cdr', return_value=memoryview(b'mock')) as func:
        conv = generate_message_converter(
            srcts,
            dstts,
            'builtin_interfaces/msg/Time',
            'builtin_interfaces/msg/Time',
            {},
            src_is2=False,
            dst_is2=True,
        )
        assert conv(b'42').tobytes() == b'mock'
        func.assert_called_with(b'42', typename='builtin_interfaces/msg/Time')

    with patch.object(srcts, 'cdr_to_ros1', return_value=memoryview(b'mock')) as func:
        conv = generate_message_converter(
            srcts,
            dstts,
            'builtin_interfaces/msg/Time',
            'builtin_interfaces/msg/Time',
            {},
            src_is2=True,
            dst_is2=False,
        )
        assert conv(b'42').tobytes() == b'mock'
        func.assert_called_with(b'42', typename='builtin_interfaces/msg/Time')

    with patch('rosbags.convert.converter.migrate_bytes', return_value=memoryview(b'mock')) as func:
        conv = generate_message_converter(
            srcts,
            dstts,
            'visualization_msgs/msg/MarkerArray',
            'visualization_msgs/msg/MarkerArray',
            {},
            src_is2=False,
            dst_is2=False,
        )
        assert conv(b'42').tobytes() == b'mock'
        func.assert_called()

    with patch('rosbags.convert.converter.migrate_bytes', return_value=memoryview(b'mock')) as func:
        conv = generate_message_converter(
            srcts,
            dstts,
            'std_msgs/msg/Int8',
            'std_msgs/msg/Int16',
            {},
            src_is2=False,
            dst_is2=False,
        )
        assert conv(b'42').tobytes() == b'mock'
        func.assert_called()


def test_migrate_bytes() -> None:
    """Test byte level conversion."""
    srcts = get_typestore(Stores.ROS1_NOETIC)
    dstts = get_typestore(Stores.ROS2_IRON)

    res = migrate_bytes(
        srcts,
        dstts,
        'std_msgs/msg/Int8',
        'std_msgs/msg/Int8',
        {},
        b'\x01',
        src_is2=False,
        dst_is2=False,
    )
    assert res.tobytes() == b'\x01'

    res = migrate_bytes(
        srcts,
        dstts,
        'std_msgs/msg/Int8',
        'std_msgs/msg/Int8',
        {},
        res,
        src_is2=False,
        dst_is2=True,
    )
    assert res.tobytes() == b'\x00\x01\x00\x00\x01'

    res = migrate_bytes(
        srcts,
        dstts,
        'std_msgs/msg/Int8',
        'std_msgs/msg/Int8',
        {},
        res,
        src_is2=True,
        dst_is2=True,
    )
    assert res.tobytes() == b'\x00\x01\x00\x00\x01'

    res = migrate_bytes(
        srcts,
        dstts,
        'std_msgs/msg/Int8',
        'std_msgs/msg/Int8',
        {},
        res,
        src_is2=True,
        dst_is2=False,
    )
    assert res.tobytes() == b'\x01'


def test_migrate_message() -> None:
    """Test message level conversion."""
    srcts = get_typestore(Stores.ROS1_NOETIC)
    dstts = get_typestore(Stores.ROS2_IRON)
    cache1: dict[str, object] = {}

    msg = cast('Marker1', default_message(srcts, 'visualization_msgs/msg/Marker'))
    res = cast(
        'Marker2',
        migrate_message(
            srcts,
            dstts,
            'visualization_msgs/msg/Marker',
            'visualization_msgs/msg/Marker',
            cache1,
            msg,
        ),
    )
    assert res.texture_resource == ''
    assert isinstance(res.texture, dstts.types['sensor_msgs/msg/CompressedImage'])
    assert res.uv_coordinates == []
    assert isinstance(res.mesh_file, dstts.types['visualization_msgs/msg/MeshFile'])

    cache2: dict[str, object] = {}
    assert (
        migrate_message(
            dstts,
            srcts,
            'visualization_msgs/msg/Marker',
            'visualization_msgs/msg/Marker',
            cache2,
            res,
        )
        == msg
    )

    msg2 = cast(
        'InteractiveMarkerUpdate1',
        default_message(
            srcts,
            'visualization_msgs/msg/InteractiveMarkerUpdate',
        ),
    )
    msg2.erases.append('foo')
    res2 = cast(
        'InteractiveMarkerUpdate2',
        migrate_message(
            srcts,
            dstts,
            'visualization_msgs/msg/InteractiveMarkerUpdate',
            'visualization_msgs/msg/InteractiveMarkerUpdate',
            cache1,
            msg2,
        ),
    )
    assert res2.erases == ['foo']

    # Type change.
    msg3 = cast(
        'Int8',
        default_message(
            srcts,
            'std_msgs/msg/Int8',
        ),
    )
    msg3.data = 42
    res3 = cast(
        'String2',
        migrate_message(
            srcts,
            dstts,
            'std_msgs/msg/Int8',
            'std_msgs/msg/String',
            cache1,
            msg3,
        ),
    )
    assert res3.data == ''

    # Dtype change.
    msg4 = cast(
        'Int8MultiArray1',
        default_message(
            srcts,
            'std_msgs/msg/Int8MultiArray',
        ),
    )
    msg4.data.resize(4, refcheck=False)
    res4 = cast(
        'Int16MultiArray2',
        migrate_message(
            srcts,
            dstts,
            'std_msgs/msg/Int8MultiArray',
            'std_msgs/msg/Int16MultiArray',
            cache1,
            msg4,
        ),
    )
    assert len(res4.data) == 4
    assert res4.data.dtype.name == 'int16'

    msg5 = cast(
        'Int8',
        default_message(
            srcts,
            'std_msgs/msg/Int8',
        ),
    )
    msg5.data = 42
    res5 = cast(
        'Duration1',
        migrate_message(
            dstts,
            srcts,
            'std_msgs/msg/Int8',
            'std_msgs/msg/Duration',
            cache2,
            msg5,
        ),
    )
    assert res5.data.sec == 0

    msg6 = cast(
        'CameraInfo1',
        default_message(
            srcts,
            'sensor_msgs/msg/CameraInfo',
        ),
    )
    msg6.K[:] = 10
    res6 = cast(
        'CameraInfo2',
        migrate_message(
            srcts,
            dstts,
            'sensor_msgs/msg/CameraInfo',
            'sensor_msgs/msg/CameraInfo',
            cache1,
            msg6,
        ),
    )
    assert (res6.k == 10).all()

    msg7 = cast(
        'MeshTriangle1',
        default_message(
            srcts,
            'shape_msgs/msg/MeshTriangle',
        ),
    )
    msg7.vertex_indices.resize(10, refcheck=False)
    res7 = cast(
        'MeshTriangle2',
        migrate_message(
            srcts,
            dstts,
            'shape_msgs/msg/MeshTriangle',
            'shape_msgs/msg/MeshTriangle',
            cache1,
            msg7,
        ),
    )
    assert len(res7.vertex_indices) == 3

    msg7 = cast(
        'MeshTriangle1',
        default_message(
            srcts,
            'shape_msgs/msg/MeshTriangle',
        ),
    )
    msg7.vertex_indices.resize(1, refcheck=False)
    res7 = cast(
        'MeshTriangle2',
        migrate_message(
            srcts,
            dstts,
            'shape_msgs/msg/MeshTriangle',
            'shape_msgs/msg/MeshTriangle',
            cache1,
            msg7,
        ),
    )
    assert len(res7.vertex_indices) == 3

    @dataclass
    class Strarr:
        data: list[Int8]

    @dataclass
    class Addrem:
        value: int

    typs = get_types_from_msg('string[4] data', 'x/msg/strarr')
    srcts.register(typs)
    typs = get_types_from_msg('string[2] data', 'x/msg/strarr')
    dstts.register(typs)
    msg8 = cast(
        'Strarr',
        default_message(
            srcts,
            'x/msg/strarr',
        ),
    )
    assert len(msg8.data) == 4
    res8 = cast(
        'Strarr',
        migrate_message(
            srcts,
            dstts,
            'x/msg/strarr',
            'x/msg/strarr',
            cache1,
            msg8,
        ),
    )
    assert len(res8.data) == 2

    msg8 = cast(
        'Strarr',
        default_message(
            dstts,
            'x/msg/strarr',
        ),
    )
    assert len(msg8.data) == 2
    res8 = cast(
        'Strarr',
        migrate_message(
            dstts,
            srcts,
            'x/msg/strarr',
            'x/msg/strarr',
            cache1,
            msg8,
        ),
    )
    assert len(res8.data) == 4

    typs = get_types_from_msg('std_msgs/msg/Int8[2] data', 'x/msg/msgarr')
    dstts.register(typs)
    msg9 = cast(
        'Strarr',
        default_message(
            srcts,
            'x/msg/strarr',
        ),
    )
    assert len(msg9.data) == 4
    res9 = cast(
        'Strarr',
        migrate_message(
            srcts,
            dstts,
            'x/msg/strarr',
            'x/msg/msgarr',
            cache1,
            msg9,
        ),
    )
    msg5 = cast(
        'Int8',
        default_message(
            dstts,
            'std_msgs/msg/Int8',
        ),
    )
    assert res9.data == [msg5, msg5]

    typs = get_types_from_msg('uint8 value', 'x/msg/addrem')
    dstts.register(typs)
    msg10 = cast(
        'Int8',
        default_message(
            srcts,
            'std_msgs/msg/Int8',
        ),
    )
    msg10.data = 42
    res10 = cast(
        'Addrem',
        migrate_message(
            srcts,
            dstts,
            'std_msgs/msg/Int8',
            'x/msg/addrem',
            cache1,
            msg10,
        ),
    )
    assert res10.value == 0
