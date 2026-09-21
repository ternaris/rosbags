# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""IDL Message Definition Parser Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_types_from_idl, get_typestore

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict


IDL_COMPLEX = """
// comment in file
module test_msgs {
  // comment in module
  typedef std_msgs::msg::Bool Bool;

  /**/ /***/ /* block comment */

  /*
   * block comment
   */

  module msg {
    // comment in submodule
    typedef Bool Balias;
    typedef test_msgs::msg::Baz::O Bar;
    typedef double d4[4];

    module Foo_Constants {
        const int32 FOO = 32;
        const int64 BAR = 64;
    };

    @just_key
    @comment(type="text", text="ignore")
    @expr("foo")
    struct Foo {
        // comment in struct
        std_msgs::msg::Header header;
        Balias bool;
        Bar sibling;
        double/* comment in member declaration */x;
        sequence<double> seq1;
        sequence<double, 4> seq2;
        d4 array;
    };

    module Baz {
      struct O {
        octet o;
      };
    };
  };

  struct Bar {
    long i;
  };
};

struct Toplevel {
  short s;
};
"""


def parse(idl: str) -> Typesdict:
    """Parse an IDL definition and register it in a fresh empty store.

    Args:
        idl: IDL definition text.

    Returns:
        Parsed typesdict.

    """
    ret = get_types_from_idl(idl)
    get_typestore(Stores.EMPTY).register(ret)
    return ret


def const_doc(typ: str, literal: str) -> str:
    """Build an IDL document defining a single constant."""
    return f'module m {{ module Foo_Constants {{ const {typ} C = {literal}; }}; struct Foo; }};'


def field_doc(decl: str) -> str:
    """Build an IDL document defining a struct with a single field."""
    return f'module m {{ struct Foo {{ {decl}; }}; }};'


def test_top_level_constants_are_discarded() -> None:
    """Test that top level constants are evaluated but not stored."""
    ret = parse('const int8 A = 7;\nconst int8 B = A * 2;\n')
    assert ret == {}


@pytest.mark.parametrize(
    ('typ', 'literal', 'name', 'value'),
    [
        ('short', '1', 'int16', 1),
        ('long', '2', 'int32', 2),
        ('long long', '3', 'int64', 3),
        ('int8', '4', 'int8', 4),
        ('int16', '5', 'int16', 5),
        ('int32', '6', 'int32', 6),
        ('int64', '7', 'int64', 7),
        ('unsigned short', '8', 'uint16', 8),
        ('unsigned long', '9', 'uint32', 9),
        ('unsigned long long', '10', 'uint64', 10),
        ('uint8', '11', 'uint8', 11),
        ('uint16', '12', 'uint16', 12),
        ('uint32', '13', 'uint32', 13),
        ('uint64', '14', 'uint64', 14),
        ('float', '1.5', 'float32', 1.5),
        ('double', '2.5', 'float64', 2.5),
        ('long double', '3.5', 'float128', 3.5),
        ('char', "'c'", 'char', 'c'),
        ('wchar', "'w'", 'wchar', 'w'),
        ('boolean', 'TRUE', 'bool', True),
        ('octet', '8', 'byte', 8),
        ('string', '"s"', 'string', 's'),
        ('string<128>', '"s"', 'string', 's'),
        ('wstring', '"s"', 'wstring', 's'),
        ('wstring<64>', '"s"', 'wstring', 's'),
    ],
)
def test_constant_types(typ: str, literal: str, name: str, value: object) -> None:
    """Test that all constant types are accepted and normalized."""
    ret = parse(const_doc(typ, literal))
    assert ret['m/Foo'][0] == [('C', name, value)]


@pytest.mark.parametrize(
    ('typ', 'literal', 'name', 'value'),
    [
        # decimal integers
        ('int8', '42', 'int8', 42),
        ('int8', '+42', 'int8', 42),
        ('int8', '-42', 'int8', -42),
        # hexadecimal integers
        ('uint8', '0xff', 'uint8', 255),
        ('uint8', '0XFF', 'uint8', 255),
        ('int8', '-0xff', 'int8', -255),
        # octal integers
        ('uint8', '0377', 'uint8', 255),
        ('int8', '-0377', 'int8', -255),
        # floats
        ('double', '1.33', 'float64', 1.33),
        ('double', '-1.33', 'float64', -1.33),
        ('double', '1.', 'float64', 1.0),
        ('double', '.5', 'float64', 0.5),
        ('double', '1e5', 'float64', 1e5),
        ('double', '-1e-5', 'float64', -1e-5),
        ('double', '1.5E+3', 'float64', 1500.0),
        ('double', '+.5e-2', 'float64', 0.005),
        # characters
        ('char', "'c'", 'char', 'c'),
        ('char', "'9'", 'char', '9'),
        ('char', "'_'", 'char', '_'),
        # booleans
        ('boolean', 'TRUE', 'bool', True),
        ('boolean', 'FALSE', 'bool', False),
        # strings
        ('string', '""', 'string', ''),
        ('string', '"a b"', 'string', 'a b'),
        ('string', '"str" "ing"', 'string', 'string'),
        ('string', '"a\\"b"', 'string', 'a\\"b'),
    ],
)
def test_constant_values(typ: str, literal: str, name: str, value: object) -> None:
    """Test all constant value literal forms."""
    ret = parse(const_doc(typ, literal))
    assert ret['m/Foo'][0] == [('C', name, value)]


@pytest.mark.parametrize(
    ('typ', 'name', 'expr', 'value'),
    [
        # unary operators
        ('int64', 'int64', '~1', -2),
        ('int64', 'int64', '-1', -1),
        ('int64', 'int64', '+1', 1),
        ('int64', 'int64', '1 - -2', 3),
        ('int64', 'int64', '-(1 + 2)', -3),
        # bitwise operators
        ('int64', 'int64', '1 | 2', 3),
        ('int64', 'int64', '1 ^ 3', 2),
        ('int64', 'int64', '1 & 3', 1),
        ('int64', 'int64', '1 << 3', 8),
        ('int64', 'int64', '32 >> 3', 4),
        # arithmetic operators
        ('int64', 'int64', '1 + 3', 4),
        ('int64', 'int64', '1 - 3', -2),
        ('int64', 'int64', '2 * 3', 6),
        ('int64', 'int64', '8 % 3', 2),
        ('int64', 'int64', '8 / 2', 4),
        ('int64', 'int64', '7 / 2', 3),
        ('int64', 'int64', '10 % 3 / 2', 0),
        ('int64', 'int64', '100 / 10 / 2', 20),
        ('double', 'float64', '1.5 + 2.5', 4.0),
        ('double', 'float64', '3.0 - 0.5', 2.5),
        ('double', 'float64', '2.5 * 2.0', 5.0),
        ('double', 'float64', '7.0 / 2.0', 3.5),
        ('double', 'float64', '-1.5', -1.5),
        ('double', 'float64', '+2.5', 2.5),
        # precedence and associativity
        ('int64', 'int64', '1 + 2 * 3', 7),
        ('int64', 'int64', '1 << 2 + 3', 32),
        ('int64', 'int64', '1 + 2 << 3', 24),
        ('int64', 'int64', '1 | 2 ^ 3 & 4', 3),
        ('int64', 'int64', '~1 + 2', 0),
        # parentheses
        ('int64', 'int64', '(1 + 2) * 3', 9),
        ('int64', 'int64', '~(1 + 2)', -4),
        ('int64', 'int64', '(3)', 3),
        ('int64', 'int64', '1+2', 3),
        # literals in expressions
        ('int64', 'int64', '0x10 + 07', 23),
    ],
)
def test_expression_evaluation(typ: str, name: str, expr: str, value: object) -> None:
    """Test evaluation of all const expression forms."""
    ret = parse(const_doc(typ, expr))
    assert ret['m/Foo'][0] == [('C', name, value)]


@pytest.mark.parametrize(
    ('text', 'name', 'expected'),
    [
        pytest.param(
            'module m { '
            '  module Foo_Constants {'
            '    const int8 A = 7; '
            '    const int8 B = A + 1;'
            '  };'
            '  struct Foo;'
            '};',
            'm/Foo',
            [('A', 'int8', 7), ('B', 'int8', 8)],
            id='same module',
        ),
        pytest.param(
            'module a {'
            '  const int8 A = 7;'
            '  module b {'
            '    module Foo_Constants { '
            '      const int8 C = A;'
            '    };'
            '    struct Foo;'
            '  };'
            '};',
            'a/b/Foo',
            [('C', 'int8', 7)],
            id='parent scope',
        ),
        pytest.param(
            'module m {'
            '  const int8 A = 7;'
            '  module Foo_Constants {'
            '    const int8 C = A;'
            '  };'
            '  struct Foo;'
            '};',
            'm/Foo',
            [('C', 'int8', 7)],
            id='outer module',
        ),
    ],
)
def test_constant_references(text: str, name: str, expected: list[tuple[str, str, int]]) -> None:
    """Test that constant references resolve through parent scopes."""
    ret = parse(text)
    assert ret[name][0] == expected


@pytest.mark.parametrize(
    ('typ', 'expected'),
    [
        ('short', 'int16'),
        ('long', 'int32'),
        ('long long', 'int64'),
        ('int8', 'int8'),
        ('int16', 'int16'),
        ('int32', 'int32'),
        ('int64', 'int64'),
        ('unsigned short', 'uint16'),
        ('unsigned long', 'uint32'),
        ('unsigned long long', 'uint64'),
        ('uint8', 'uint8'),
        ('uint16', 'uint16'),
        ('uint32', 'uint32'),
        ('uint64', 'uint64'),
        ('float', 'float32'),
        ('double', 'float64'),
        ('long double', 'float128'),
        ('char', 'char'),
        ('wchar', 'wchar'),
        ('boolean', 'bool'),
        ('octet', 'byte'),
        ('string', 'string'),
        ('wstring', 'wstring'),
    ],
)
def test_field_base_types(typ: str, expected: str) -> None:
    """Test all base types as field types."""
    ret = parse(field_doc(f'{typ} f'))
    assert ret['m/Foo'][1] == [('f', (Nodetype.BASE, (expected, 0)))]


@pytest.mark.parametrize(
    ('decl', 'expected'),
    [
        pytest.param('m::Other f', 'm/Other', id='module scoped'),
        pytest.param('::m::Other f', 'm/Other', id='absolutely scoped'),
        pytest.param('a::b::Other f', 'a/b/Other', id='nested scoped'),
        pytest.param('std_msgs::msg::Header f', 'std_msgs/msg/Header', id='package scoped'),
    ],
)
def test_field_type_references(decl: str, expected: str) -> None:
    """Test scoped type reference resolution."""
    ret = parse(field_doc(decl))
    assert ret['m/Foo'][1] == [('f', (Nodetype.NAME, expected))]


@pytest.mark.parametrize(
    ('decl', 'expected'),
    [
        pytest.param(
            'string<128> f',
            (Nodetype.BASE, ('string', 128)),
            id='bounded string',
        ),
        pytest.param(
            'wstring<64> f',
            (Nodetype.BASE, ('wstring', 64)),
            id='bounded wstring',
        ),
        pytest.param(
            'sequence<int8> f',
            (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int8', 0)), 0)),
            id='unbounded sequence',
        ),
        pytest.param(
            'sequence<int8, 4> f',
            (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int8', 0)), 4)),
            id='bounded sequence',
        ),
        pytest.param(
            'sequence<int8, 2 * 3> f',
            (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int8', 0)), 6)),
            id='sequence with expression bound',
        ),
        pytest.param(
            'sequence<Other> f',
            (Nodetype.SEQUENCE, ((Nodetype.NAME, 'm/Other'), 0)),
            id='sequence of named type',
        ),
        pytest.param(
            'sequence<Other, 2> f',
            (Nodetype.SEQUENCE, ((Nodetype.NAME, 'm/Other'), 2)),
            id='bounded sequence of named type',
        ),
        pytest.param(
            'int8 f[3]',
            (Nodetype.ARRAY, ((Nodetype.BASE, ('int8', 0)), 3)),
            id='array',
        ),
        pytest.param(
            'int8 f[2 + 1]',
            (Nodetype.ARRAY, ((Nodetype.BASE, ('int8', 0)), 3)),
            id='array with expression bound',
        ),
        pytest.param(
            'string<16> f[3]',
            (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 16)), 3)),
            id='array of bounded string',
        ),
        pytest.param(
            'Other f[2]',
            (Nodetype.ARRAY, ((Nodetype.NAME, 'm/Other'), 2)),
            id='array of named type',
        ),
    ],
)
def test_field_cardinalities(decl: str, expected: tuple[Nodetype, object]) -> None:
    """Test scalar, sequence and array field types with optional bounds."""
    ret = parse(field_doc(decl))
    assert ret['m/Foo'][1] == [('f', expected)]


@pytest.mark.parametrize(
    ('text', 'name', 'expected'),
    [
        pytest.param(
            'module m { struct Foo { int8 a, b, c[3]; }; };',
            'm/Foo',
            [
                ('a', (Nodetype.BASE, ('int8', 0))),
                ('b', (Nodetype.BASE, ('int8', 0))),
                ('c', (Nodetype.ARRAY, ((Nodetype.BASE, ('int8', 0)), 3))),
            ],
            id='struct members',
        ),
        pytest.param(
            'module m { typedef int8 A, B, C[3]; struct Foo { A a; B b; C c; }; };',
            'm/Foo',
            [
                ('a', (Nodetype.BASE, ('int8', 0))),
                ('b', (Nodetype.BASE, ('int8', 0))),
                ('c', (Nodetype.ARRAY, ((Nodetype.BASE, ('int8', 0)), 3))),
            ],
            id='typedefs',
        ),
    ],
)
def test_multiple_declarators(
    text: str,
    name: str,
    expected: list[tuple[str, tuple[Nodetype, object]]],
) -> None:
    """Test declarations with multiple declarators."""
    ret = parse(text)
    assert ret[name][1] == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        pytest.param(
            'module m { typedef long T; struct Foo { T f; }; };',
            [('f', (Nodetype.BASE, ('int32', 0)))],
            id='base type',
        ),
        pytest.param(
            'module m { typedef double d4[4]; struct Foo { d4 f; }; };',
            [('f', (Nodetype.ARRAY, ((Nodetype.BASE, ('float64', 0)), 4)))],
            id='array',
        ),
        pytest.param(
            'module m { typedef string string__3[3]; struct Foo { string__3 s; }; };',
            [('s', (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 0)), 3)))],
            id='string array',
        ),
        pytest.param(
            'module m { typedef sequence<int8, 4> S; struct Foo { S f; }; };',
            [('f', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('int8', 0)), 4)))],
            id='sequence',
        ),
        pytest.param(
            'module m { typedef double D, E[2]; struct Foo { D d; E e; }; };',
            [
                ('d', (Nodetype.BASE, ('float64', 0))),
                ('e', (Nodetype.ARRAY, ((Nodetype.BASE, ('float64', 0)), 2))),
            ],
            id='multiple declarators',
        ),
    ],
)
def test_typedefs(text: str, expected: list[tuple[str, tuple[Nodetype, object]]]) -> None:
    """Test that typedefs are expanded at the use site."""
    ret = parse(text)
    assert ret['m/Foo'][1] == expected


def test_typedef_shadowing() -> None:
    """Test that local typedefs shadow global ones and absolute references work."""
    ret = parse(
        'typedef short T1;'
        'module test_msgs {'
        '  module msg {'
        '    typedef long T1;'
        '    struct Foo {'
        '        T1 local;'
        '        ::T1 global;'
        '    };'
        '  };'
        '};'
    )
    assert ret['test_msgs/msg/Foo'][1] == [
        ('local', (Nodetype.BASE, ('int32', 0))),
        ('global_', (Nodetype.BASE, ('int16', 0))),
    ]


@pytest.mark.parametrize('kw', ['return', 'yield', 'global'])
def test_python_keyword_renaming(kw: str) -> None:
    """Test that names colliding with python keywords get renamed."""
    ret = parse(
        f'module m {{ module Foo_Constants {{ const int32 {kw} = 32; }};'
        f' struct Foo {{ uint64 {kw}; }}; }};'
    )
    assert ret['m/Foo'][0] == [(kw + '_', 'int32', 32)]
    assert ret['m/Foo'][1] == [(kw + '_', (Nodetype.BASE, ('uint64', 0)))]


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        pytest.param(
            'module m { struct Foo { int8 i; }; enum COLORS { RED, GREEN, BLUE }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='plain',
        ),
        pytest.param(
            'module m { struct Foo { int8 i; }; enum COLORS { RED, @value(100) BLACK }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='annotated enumerator',
        ),
        pytest.param(
            'module m { struct Foo { int8 i; }; enum COLORS { RED, @value(2 * 10) BLACK }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='expression value',
        ),
        pytest.param(
            '@doc("x") module m { enum COLORS { RED }; };',
            {},
            id='annotated enum',
        ),
        pytest.param(
            'enum COLORS {\n  RED,\n  GREEN,\n  BLUE,\n  @value(100)\n  BLACK\n};',
            {},
            id='multiline top level',
        ),
    ],
)
def test_enums_are_discarded(text: str, expected: Typesdict) -> None:
    """Test that enums are parsed but not stored."""
    assert parse(text) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        pytest.param(
            '@just_key @comment(type="text", text="ignore") @expr("foo")'
            ' module m { struct Foo { @doc int8 i; }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='module struct and field',
        ),
        pytest.param(
            '@c("x") module m { module Foo_Constants { const int8 C = 1; }; struct Foo; };',
            {'m/Foo': ([('C', 'int8', 1)], [])},
            id='const',
        ),
        pytest.param(
            'module m { struct Foo { @k(1) int8 i; }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='single positional param',
        ),
        pytest.param(
            'module m { struct Foo { @k(a=1, b="s", c=3.5, d=2 * 10) int8 i; }; };',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='named params',
        ),
        pytest.param(
            'module m {\n@verbatim (language="comment", text=\n " Oriented bounding box")'
            '\nstruct Foo { int8 i; };\n};',
            {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])},
            id='multiline',
        ),
    ],
)
def test_annotations_are_ignored(text: str, expected: Typesdict) -> None:
    """Test that annotations are parsed but not stored."""
    assert parse(text) == expected


def test_comments_and_whitespace() -> None:
    """Test line comments, block comments and tabs in various positions."""
    text = (
        '// leading comment\n'
        'module m {\n'
        '\t/* block\n'
        '\t * comment */\n'
        '\tstruct Foo {\n'
        '\t\tint8\ti; // trailing comment\n'
        '\t};\n'
        '};'
    )
    ret = parse(text)
    assert ret == {'m/Foo': ([], [('i', (Nodetype.BASE, ('int8', 0)))])}


def test_complex_document() -> None:
    """Test a document with comments, annotations, typedefs and constants."""
    ret = parse(IDL_COMPLEX)

    assert set(ret) == {'Toplevel', 'test_msgs/Bar', 'test_msgs/msg/Baz/O', 'test_msgs/msg/Foo'}

    consts, fields = ret['test_msgs/msg/Foo']
    assert consts == [('FOO', 'int32', 32), ('BAR', 'int64', 64)]
    assert fields == [
        ('header', (Nodetype.NAME, 'std_msgs/msg/Header')),
        ('bool', (Nodetype.NAME, 'std_msgs/msg/Bool')),
        ('sibling', (Nodetype.NAME, 'test_msgs/msg/Baz/O')),
        ('x', (Nodetype.BASE, ('float64', 0))),
        ('seq1', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('float64', 0)), 0))),
        ('seq2', (Nodetype.SEQUENCE, ((Nodetype.BASE, ('float64', 0)), 4))),
        ('array', (Nodetype.ARRAY, ((Nodetype.BASE, ('float64', 0)), 4))),
    ]

    assert ret['test_msgs/msg/Baz/O'] == ([], [('o', (Nodetype.BASE, ('byte', 0)))])
    assert ret['test_msgs/Bar'] == ([], [('i', (Nodetype.BASE, ('int32', 0)))])
    assert ret['Toplevel'] == ([], [('s', (Nodetype.BASE, ('int16', 0)))])


def test_type_resolution_prefers_declarations() -> None:
    """Test that unqualified names resolve to declared siblings first."""
    ret = parse(
        'module test_msgs {'
        '  module msg {'
        '    struct Bar {'
        '        int8 i;'
        '    };'
        '    struct Foo {'
        '        Bar bar1;'
        '        msg::Bar bar2;'
        '        ::test_msgs::msg::Bar bar3;'
        '        Baz baz1;'
        '    };'
        '  };'
        '};'
    )
    assert ret['test_msgs/msg/Foo'][1] == [
        ('bar1', (Nodetype.NAME, 'test_msgs/msg/Bar')),
        ('bar2', (Nodetype.NAME, 'test_msgs/msg/Bar')),
        ('bar3', (Nodetype.NAME, 'test_msgs/msg/Bar')),
        ('baz1', (Nodetype.NAME, 'test_msgs/msg/Baz')),
    ]


@pytest.mark.parametrize(
    ('text', 'match'),
    [
        pytest.param('', 'Could not parse', id='empty definition'),
        pytest.param('module test_msgs {}', 'Could not parse', id='empty module'),
        pytest.param('typedef long good; bad', 'Could not parse', id='leftover input'),
        pytest.param('struct Foo { int8 i; }', 'Could not parse', id='missing semicolon'),
        pytest.param('struct Foo { int8 arr[]; };', 'Could not parse', id='empty array bound'),
        pytest.param('#include "x.idl"', 'Could not parse', id='preprocessor line'),
        pytest.param(
            'module test_msgs { const _Foo foo = 8; };',
            'Could not parse',
            id='invalid const type',
        ),
        pytest.param(
            'module test_msgs { const int8 foo = !8; };',
            'Could not parse',
            id='unknown operator',
        ),
        pytest.param('typedef _Foo foo;', 'Could not parse', id='invalid typedef type'),
        pytest.param('typedef Foo _foo;', 'Could not parse', id='invalid typedef name'),
        pytest.param('enum COLORS { _RED };', 'Could not parse', id='invalid enumerator'),
        pytest.param('enum COLORS { @value( RED };', 'Could not parse', id='unclosed annotation'),
        pytest.param(
            'enum COLORS { @value() RED };',
            'Could not parse',
            id='empty annotation params',
        ),
        pytest.param(
            'module m { struct Foo { @k(1, 2) int8 i; }; };',
            'Could not parse',
            id='positional annotation params',
        ),
        pytest.param(const_doc('int8', '0b101'), 'Could not parse', id='binary literal'),
        pytest.param('const int8 A = B;', "resolve constant 'B'", id='unresolved constant'),
        pytest.param(
            'const int8 A = 7; const int8 C = ::A;',
            "resolve constant '/A'",
            id='global constant reference',
        ),
        pytest.param(
            'module a { const int8 A = 7; };'
            ' module b { module Foo_Constants { const int8 C = A; }; struct Foo; };',
            "resolve constant 'A'",
            id='sibling constant not visible',
        ),
        pytest.param(
            const_doc('boolean', 'true'),
            "resolve constant 'true'",
            id='lowercase boolean',
        ),
        pytest.param(const_doc('double', '1 + 2.0'), 'Cannot mix types', id='mixed int and float'),
        pytest.param(const_doc('int8', 'TRUE | 1'), 'Cannot mix types', id='mixed bool and int'),
        pytest.param(const_doc('int8', '8 / 0'), 'Division by zero', id='division by zero'),
        pytest.param(const_doc('int8', '8 % 0'), 'Modulo by zero', id='modulo by zero'),
        pytest.param(const_doc('int64', '1 << -1'), 'negative count', id='negative shift'),
        pytest.param(
            const_doc('string', '-"a"'),
            "Cannot apply operator '-'",
            id='unary minus on string',
        ),
        pytest.param(
            const_doc('double', '~1.5'),
            "Cannot apply operator '~'",
            id='bitwise invert on float',
        ),
        pytest.param(
            const_doc('string', '"a" + "b"'),
            "Cannot apply operator '\\+'",
            id='string concatenation',
        ),
        pytest.param(
            const_doc('double', '5.0 % 2.0'),
            "Cannot apply operator '%'",
            id='modulo on float',
        ),
        pytest.param(
            'module m { struct Foo { int8 i; }; module Foo_Constants { const Foo C = 8; }; };',
            'Cannot evaluate constant of non-base type',
            id='constant of struct type',
        ),
        pytest.param(
            'struct Foo { int8 f[3][2]; };',
            'Multidimensional arrays',
            id='multidimensional array',
        ),
        pytest.param(
            'module m { typedef double d4[4]; struct S { d4 f[2]; }; };',
            'Multidimensional arrays',
            id='array of array typedef',
        ),
        pytest.param(
            'module m { typedef double F[3][4]; };',
            'Multidimensional arrays',
            id='multidimensional array typedef',
        ),
        pytest.param(
            'struct Foo { string<1.5> f; };',
            'String bound must be an integer',
            id='float string bound',
        ),
        pytest.param(
            'struct Foo { int8 f[1.5]; };',
            'Array or sequence bound must be an integer',
            id='float array bound',
        ),
        pytest.param(
            'struct Foo { sequence<int8, 1.5> f; };',
            'Array or sequence bound must be an integer',
            id='float sequence bound',
        ),
    ],
)
def test_syntax_errors(text: str, match: str) -> None:
    """Test that invalid IDL definitions raise a TypesysError."""
    with pytest.raises(TypesysError, match=match):
        _ = get_types_from_idl(text)
