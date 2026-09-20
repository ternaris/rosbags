# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""MSG Message Definition Parser Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_types_from_msg, get_typestore
from rosbags.typesys.msg import denormalize_msgtype, normalize_msgtype

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict

NAME = 'test_msgs/msg/Foo'
SEPARATOR = '=' * 80


def parse(msg: str, name: str = NAME) -> Typesdict:
    """Parse a message definition and register it in the empty store.

    Args:
        msg: Message definition text.
        name: Name of the first message.

    Returns:
        Parsed typesdict.

    """
    ret = get_types_from_msg(msg, name)
    get_typestore(Stores.EMPTY).register(ret)
    return ret


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('a/Foo', 'a/msg/Foo'),
        ('a/msg/Foo', 'a/msg/Foo'),
        ('a/action/Foo', 'a/action/Foo'),
    ],
)
def test_normalize_msgtype(name: str, expected: str) -> None:
    """Test message name normalization to ROS2 style."""
    assert normalize_msgtype(name) == expected


def test_denormalize_msgtype() -> None:
    """Test message name denormalization to ROS1 style."""
    assert denormalize_msgtype('a/msg/Foo') == 'a/Foo'


def test_empty_definition() -> None:
    """Test that an empty message definition parses to an empty message."""
    ret = get_types_from_msg('', 'std_msgs/msg/Empty')
    assert ret == {'std_msgs/msg/Empty': ([], [])}


@pytest.mark.parametrize(
    ('typ', 'literal', 'expected'),
    [
        ('bool', 'true', True),
        ('byte', '1', 1),
        ('char', "'a'", 'a'),
        ('int8', '-128', -128),
        ('int16', '-32768', -32768),
        ('int32', '-2147483648', -2147483648),
        ('int64', '-9223372036854775808', -9223372036854775808),
        ('uint8', '255', 255),
        ('uint16', '65535', 65535),
        ('uint32', '4294967295', 4294967295),
        ('uint64', '18446744073709551615', 18446744073709551615),
        ('float32', '1.5', 1.5),
        ('float64', '2.5', 2.5),
        ('string', '"foo"', 'foo'),
    ],
)
def test_constant_types(typ: str, literal: str, expected: object) -> None:
    """Test all base types as constant types."""
    ret = parse(f'{typ} C={literal}')
    assert ret[NAME][0] == [('C', typ, expected)]


@pytest.mark.parametrize(
    ('typ', 'literal', 'expected'),
    [
        # decimal integers
        ('int8', '42', 42),
        ('int8', '+42', 42),
        ('int8', '-42', -42),
        # hexadecimal integers
        ('uint8', '0xff', 255),
        ('uint8', '0XFF', 255),
        ('int8', '-0xff', -255),
        # octal integers
        ('uint8', '0377', 255),
        ('int8', '-0377', -255),
        # binary integers
        ('uint8', '0b1010', 10),
        ('int8', '-0b1010', -10),
        # floats
        ('float32', '1.33', 1.33),
        ('float32', '-1.33', -1.33),
        ('float64', '1.', 1.0),
        ('float64', '.5', 0.5),
        ('float64', '1e5', 1e5),
        ('float64', '-1e-5', -1e-5),
        ('float64', '1.5E+3', 1500.0),
        # booleans
        ('bool', 'true', True),
        ('bool', 'false', False),
        ('bool', 'True', True),
        ('bool', 'TRUE', True),
        ('bool', 'False', False),
        ('bool', 'FALSE', False),
        # strings
        ('string', 'foo bar', 'foo bar'),
        ('string', '   padded   ', 'padded'),
        ('string', '"quoted"', 'quoted'),
        ('string', "'single'", 'single'),
        ('string', '"a\\"b"', 'a\\"b'),
        ('string', '"a\\\\b"', 'a\\\\b'),
    ],
)
def test_constant_values(typ: str, literal: str, expected: object) -> None:
    """Test all constant value literal forms."""
    ret = parse(f'{typ} C={literal}')
    assert ret[NAME][0] == [('C', typ, expected)]


@pytest.mark.parametrize(
    'typ',
    [
        'bool',
        'byte',
        'char',
        'int8',
        'int16',
        'int32',
        'int64',
        'uint8',
        'uint16',
        'uint32',
        'uint64',
        'float32',
        'float64',
        'string',
    ],
)
def test_field_base_types(typ: str) -> None:
    """Test all base types as field types."""
    ret = parse(f'{typ} f')
    assert ret[NAME][1] == [('f', (Nodetype.BASE, (typ, 0)))]


@pytest.mark.parametrize(
    ('decl', 'expected'),
    [
        ('Header f', 'std_msgs/msg/Header'),
        ('time f', 'builtin_interfaces/msg/Time'),
        ('duration f', 'builtin_interfaces/msg/Duration'),
        ('Other f', 'test_msgs/msg/Other'),
        ('a/Other f', 'a/msg/Other'),
        ('a/msg/Other f', 'a/msg/Other'),
        ('a/action/Other f', 'a/action/Other'),
    ],
)
def test_field_type_references(decl: str, expected: str) -> None:
    """Test message type reference resolution and normalization."""
    ret = parse(decl)
    assert ret[NAME][1] == [('f', (Nodetype.NAME, expected))]


@pytest.mark.parametrize(
    ('decl', 'expected'),
    [
        ('int32 f', (Nodetype.BASE, ('int32', 0))),
        ('int32[] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 0))),
        ('int32[5] f', (Nodetype.ARRAY, ((Nodetype.BASE, ('int32', 0)), 5))),
        ('int32[<=5] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 5))),
        ('Other f', (Nodetype.NAME, 'test_msgs/msg/Other')),
        ('Other[] f', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'test_msgs/msg/Other'), 0))),
        ('Other[5] f', (Nodetype.ARRAY, ((Nodetype.NAME, 'test_msgs/msg/Other'), 5))),
        ('Other[<=5] f', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'test_msgs/msg/Other'), 5))),
        ('string f', (Nodetype.BASE, ('string', 0))),
        ('string<=10 f', (Nodetype.BASE, ('string', 10))),
        ('string[] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 0)), 0))),
        ('string<=10[] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 10)), 0))),
        ('string[5] f', (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 0)), 5))),
        ('string[<=5] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 0)), 5))),
        ('string<=10[5] f', (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 10)), 5))),
        ('string<=10[<=5] f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('string', 10)), 5))),
    ],
)
def test_field_cardinalities(decl: str, expected: tuple[Nodetype, object]) -> None:
    """Test scalar, sequence and array field types with optional bounds."""
    ret = parse(decl)
    assert ret[NAME][1] == [('f', expected)]


@pytest.mark.parametrize(
    ('decl', 'expected'),
    [
        ('bool b true', (Nodetype.BASE, ('bool', 0))),
        ('uint8 i 42', (Nodetype.BASE, ('uint8', 0))),
        ('float32 y -314.15e-2', (Nodetype.BASE, ('float32', 0))),
        ('string name "John"', (Nodetype.BASE, ('string', 0))),
        ("string name 'Ringo'", (Nodetype.BASE, ('string', 0))),
        ('string name bare value', (Nodetype.BASE, ('string', 0))),
        ('int32[] samples [42]', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 0))),
        ('int32[] samples [1, 2, 3]', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 0))),
        ('int32[] samples [1,2,3]', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 0))),
        ('int32[] samples [ 1 , 2 ]', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int32', 0)), 0))),
    ],
)
def test_field_default_values(decl: str, expected: tuple[Nodetype, object]) -> None:
    """Test that field default values are parsed and discarded."""
    fname = decl.split()[1]
    ret = parse(decl)
    assert ret[NAME][1] == [(fname, expected)]


def test_multiple_definitions() -> None:
    """Test concatenated message definitions separated by separator lines."""
    text = (
        'std_msgs/Header header\n'
        'byte b\n'
        'char c\n'
        'Other[] o\n'
        f'\n{SEPARATOR}\n'
        'MSG: std_msgs/Header\n'
        'time t\n'
        f'\n{SEPARATOR}\n'
        'MSG: test_msgs/Other\n'
        'uint64[3] seq\n'
        'uint32 STATIC = 42\n'
    )
    ret = parse(text)

    assert set(ret) == {'test_msgs/msg/Foo', 'std_msgs/msg/Header', 'test_msgs/msg/Other'}
    fields = ret['test_msgs/msg/Foo'][1]
    assert fields[0] == ('header', (Nodetype.NAME, 'std_msgs/msg/Header'))
    assert fields[1] == ('b', (Nodetype.BASE, ('byte', 0)))
    assert fields[2] == ('c', (Nodetype.BASE, ('char', 0)))
    assert fields[3] == ('o', (Nodetype.SEQUENCE, ((Nodetype.NAME, 'test_msgs/msg/Other'), 0)))
    assert ret['std_msgs/msg/Header'][1] == [('t', (Nodetype.NAME, 'builtin_interfaces/msg/Time'))]
    assert ret['test_msgs/msg/Other'][0] == [('STATIC', 'uint32', 42)]


def test_separator_lookalike() -> None:
    """Test that a string value of '=' characters is not confused with the separator."""
    text = f'string S={SEPARATOR}\n\n{SEPARATOR}\nMSG: std_msgs/Header\ntime t\n'
    ret = parse(text)

    assert set(ret) == {'test_msgs/msg/Foo', 'std_msgs/msg/Header'}
    assert ret[NAME][0] == [('S', 'string', SEPARATOR)]


def test_type_resolution_is_lexical() -> None:
    """Test that unqualified type names resolve relative to the owning message."""
    text = (
        'std_msgs/Int s_int\n'
        'Int c_int\n'
        f'\n{SEPARATOR}\n'
        'MSG: collision_msgs/Int\n'
        'int16 value\n'
        f'{SEPARATOR}\n'
        'MSG: std_msgs/Int\n'
        'int8 data\n'
    )
    ret = parse(text, 'collision_msgs/msg/Foo')

    fields = ret['collision_msgs/msg/Foo'][1]
    assert fields[0][1][1] == 'std_msgs/msg/Int'
    assert fields[1][1][1] == 'collision_msgs/msg/Int'


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('yield', 'yield_'),
        ('class', 'class_'),
        ('if', 'if_'),
        ('name', 'name'),
    ],
)
def test_python_keyword_renaming(name: str, expected: str) -> None:
    """Test that field names colliding with python keywords get renamed."""
    ret = parse(f'uint64 {name}')
    assert ret[NAME][1] == [(expected, (Nodetype.BASE, ('uint64', 0)))]


def test_annotations_are_ignored() -> None:
    """Test that annotations are parsed but not stored."""
    ret = parse('@optional\nint8 i1\n@optional int8 i2\n')
    assert ret[NAME][1] == [
        ('i1', (Nodetype.BASE, ('int8', 0))),
        ('i2', (Nodetype.BASE, ('int8', 0))),
    ]


def test_comments_and_whitespace() -> None:
    """Test comments, blank lines and tabs in various positions."""
    ret = parse(
        '# leading comment\n\nint32 I=42 # trailing comment\n\t# indented comment\nint8\ti\n\n'
    )
    assert ret == {
        NAME: (
            [('I', 'int32', 42)],
            [('i', (Nodetype.BASE, ('int8', 0)))],
        )
    }


def test_missing_trailing_newline() -> None:
    """Test that the last line does not need a trailing newline."""
    ret = parse('int8 i')
    assert ret == {NAME: ([], [('i', (Nodetype.BASE, ('int8', 0)))])}


@pytest.mark.parametrize(
    ('text', 'name'),
    [
        pytest.param('int8 i', 'bad name', id='bad message name'),
        pytest.param('int8 i', '', id='empty message name'),
        pytest.param('invalid', NAME, id='unknown line'),
        pytest.param('int8 i\ntrailing', NAME, id='trailing garbage'),
        pytest.param(
            f'int8 i\n{SEPARATOR[:-1]}\nMSG: a/msg/B\nint8 j\n',
            NAME,
            id='short separator',
        ),
        pytest.param(f'int8 i\n{SEPARATOR}\n', NAME, id='dangling separator'),
        pytest.param('std_msgs/Header H=5', NAME, id='constant with message type'),
        pytest.param('int32 i=42', NAME, id='lowercase constant name'),
        pytest.param('int32 foo_', NAME, id='trailing _ field name'),
        pytest.param('string S=', NAME, id='constant without value'),
        pytest.param('int32', NAME, id='field without name'),
        pytest.param('int32[abc] f', NAME, id='invalid array size'),
    ],
)
def test_syntax_errors(text: str, name: str) -> None:
    """Test that invalid message definitions raise a TypesysError."""
    with pytest.raises(TypesysError, match='Could not parse'):
        get_types_from_msg(text, name)
