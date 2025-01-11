# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""MSG Message Definition Parser Tests."""

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_types_from_msg, get_typestore

MSG = """
# comment

bool b=true
int32 global=42
float32 f=1.33
string str= foo bar\t

std_msgs/Header header
std_msgs/msg/Bool bool
test_msgs/Bar sibling
float64 base
float64[] seq1
float64[] seq2
float64[4] array
"""

MSG_BOUNDS = """
int32[] unbounded_integer_array
int32[5] five_integers_array
int32[<=5] up_to_five_integers_array

string string_of_unbounded_size
string<=10 up_to_ten_characters_string

string[<=5] up_to_five_unbounded_strings
string<=10[] unbounded_array_of_string_up_to_ten_characters_each
string<=10[<=5] up_to_five_strings_up_to_ten_characters_each
"""

MSG_DEFAULTS = """
bool b false
uint8 i 42
uint8 o 0377
uint8 h 0xff
float32 y -314.15e-2
string name1 "John"
string name2 'Ringo'
int32[] samples [-200, -100, 0, 100, 200]
"""

MULTI_MSG = """
std_msgs/Header header
byte b
char c
Other[] o

================================================================================
MSG: std_msgs/Header
time time

================================================================================
MSG: test_msgs/Other
uint64[3] Header
uint32 static = 42
"""

CSTRING_CONFUSION_MSG = """
std_msgs/Header header
string s

================================================================================
MSG: std_msgs/Header
time time
"""

RELSIBLING_MSG = """
Header header
Other other
"""

KEYWORD_MSG = """
bool return=true
uint64 yield
"""

NAME_COLLISION_MSG = """
std_msgs/Int s_int
Int c_int

================================================================================
MSG: collision_msgs/Int
int16 value
================================================================================
MSG: std_msgs/Int
int8 data
"""

WITH_LITERALS_MSG = """
float32 both 0.0
float32 integer_only 0.
float32 fraction_only .0
float32 scientific_pos 1e1
float32 scientific_neg 1e-1
"""


def test_msg_parser_raises_on_bad_definition() -> None:
    """Test msg parser raises on bad definition."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_msg('invalid', 'test_msgs/msg/Foo')


def test_msg_parser_accepts_empty_definition() -> None:
    """Test msg parser accepts empty message definition."""
    ret = get_types_from_msg('', 'std_msgs/msg/Empty')
    assert ret == {'std_msgs/msg/Empty': ([], [])}


def test_msg_parser_accepts_single_msg() -> None:
    """Test msg parser accepts single message."""
    ret = get_types_from_msg(MSG, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert 'test_msgs/msg/Foo' in ret
    consts, fields = ret['test_msgs/msg/Foo']
    assert consts == [
        ('b', 'bool', True),
        ('global_', 'int32', 42),
        ('f', 'float32', 1.33),
        ('str', 'string', 'foo bar'),
    ]
    assert fields[0][0] == 'header'
    assert fields[0][1][1] == 'std_msgs/msg/Header'
    assert fields[1][0] == 'bool'
    assert fields[1][1][1] == 'std_msgs/msg/Bool'
    assert fields[2][0] == 'sibling'
    assert fields[2][1][1] == 'test_msgs/msg/Bar'
    assert fields[3][1][0] == int(Nodetype.BASE)
    assert fields[4][1][0] == int(Nodetype.SEQUENCE)
    assert fields[5][1][0] == int(Nodetype.SEQUENCE)
    assert fields[6][1][0] == int(Nodetype.ARRAY)


def test_msg_parser_processes_bounds() -> None:
    """Test msg parser processes string and sequence bounds."""
    ret = get_types_from_msg(MSG_BOUNDS, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret == {
        'test_msgs/msg/Foo': (
            [],
            [
                ('unbounded_integer_array', (4, ((1, ('int32', 0)), 0))),
                ('five_integers_array', (3, ((1, ('int32', 0)), 5))),
                ('up_to_five_integers_array', (4, ((1, ('int32', 0)), 5))),
                ('string_of_unbounded_size', (1, ('string', 0))),
                ('up_to_ten_characters_string', (1, ('string', 10))),
                ('up_to_five_unbounded_strings', (4, ((1, ('string', 0)), 5))),
                (
                    'unbounded_array_of_string_up_to_ten_characters_each',
                    (4, ((1, ('string', 10)), 0)),
                ),
                ('up_to_five_strings_up_to_ten_characters_each', (4, ((1, ('string', 10)), 5))),
            ],
        ),
    }


def test_msg_parser_accepts_field_defaults() -> None:
    """Test msg parser accepts field defaults."""
    ret = get_types_from_msg(MSG_DEFAULTS, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret == {
        'test_msgs/msg/Foo': (
            [],
            [
                ('b', (1, ('bool', 0))),
                ('i', (1, ('uint8', 0))),
                ('o', (1, ('uint8', 0))),
                ('h', (1, ('uint8', 0))),
                ('y', (1, ('float32', 0))),
                ('name1', (1, ('string', 0))),
                ('name2', (1, ('string', 0))),
                ('samples', (4, ((1, ('int32', 0)), 0))),
            ],
        ),
    }


def test_msg_parser_accepts_multiple_definitions() -> None:
    """Test msg parser accepts concatenated definitions."""
    ret = get_types_from_msg(MULTI_MSG, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert len(ret) == 3
    assert 'test_msgs/msg/Foo' in ret
    assert 'std_msgs/msg/Header' in ret
    assert 'test_msgs/msg/Other' in ret
    fields = ret['test_msgs/msg/Foo'][1]
    assert fields[0][1][1] == 'std_msgs/msg/Header'
    assert fields[1][1][1] == ('byte', 0)
    assert fields[2][1][1] == ('char', 0)
    consts = ret['test_msgs/msg/Other'][0]
    assert consts == [('static', 'uint32', 42)]


def test_msg_parser_does_not_confuse_string_constants() -> None:
    """Test msg parser does not confuse message separator with const string."""
    ret = get_types_from_msg(CSTRING_CONFUSION_MSG, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert len(ret) == 2
    assert 'test_msgs/msg/Foo' in ret
    assert 'std_msgs/msg/Header' in ret
    consts, fields = ret['test_msgs/msg/Foo']
    assert consts == []
    assert fields[0][1][1] == 'std_msgs/msg/Header'
    assert fields[1][1][1] == ('string', 0)


def test_msg_parser_resolves_relative_siblings() -> None:
    """Test msg parser resolves relative siblings."""
    ret = get_types_from_msg(RELSIBLING_MSG, 'test_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret['test_msgs/msg/Foo'][1][0][1][1] == 'std_msgs/msg/Header'
    assert ret['test_msgs/msg/Foo'][1][1][1][1] == 'test_msgs/msg/Other'

    ret = get_types_from_msg(RELSIBLING_MSG, 'rel_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret['rel_msgs/msg/Foo'][1][0][1][1] == 'std_msgs/msg/Header'
    assert ret['rel_msgs/msg/Foo'][1][1][1][1] == 'rel_msgs/msg/Other'


def test_msg_parser_avoids_python_keyword_collisions() -> None:
    """Test msg parser renames message fields to avoid python keyword collisions."""
    ret = get_types_from_msg(KEYWORD_MSG, 'keyword_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret['keyword_msgs/msg/Foo'][0][0][0] == 'return_'
    assert ret['keyword_msgs/msg/Foo'][1][0][0] == 'yield_'


def test_msg_parser_handles_name_collisions() -> None:
    """Test msg parser handles identical type names in different namespaces."""
    ret = get_types_from_msg(NAME_COLLISION_MSG, 'collision_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert ret['collision_msgs/msg/Foo'][1][0][1][1] == 'std_msgs/msg/Int'
    assert ret['collision_msgs/msg/Foo'][1][1][1][1] == 'collision_msgs/msg/Int'


def test_literal_notations() -> None:
    """Test msg parser handles different literal notations."""
    ret = get_types_from_msg(WITH_LITERALS_MSG, 'literals_msgs/msg/Foo')
    get_typestore(Stores.EMPTY).register(ret)

    assert len(ret['literals_msgs/msg/Foo'][1]) == 5
