# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""IDL Message Definition Parser Tests."""

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_types_from_idl, get_typestore

IDL_LITERALS_EXPRESSIONS = """
// assign different literals and expressions

const boolean g_bool = TRUE;
const int8 g_int1 = 7;
const int8 g_int2 = 07;
const int8 g_int3 = 0x7;
const double g_float1 = 1.1;
const double g_float2 = 1e10;
const long double g_float3 = -.1e0;
const char g_char = 'c';
const string g_string1 = "";
const string<128> g_string2 = "str" "ing";

module Foo {
    const int64 g_expr1 = ~1;
    const int64 g_expr2 = 2 * 4;
    const int64 g_expr3 = (3);
    const int64 g_expr4 = (g_int1 * 2);
};

"""

IDL_CONST_EXPRS = """
module test_msgs {
  module msg {
    module Foo_Constants {
      const int8 OR = 1 | 2;
      const int8 XOR = 1 ^ 3;
      const int8 AND = 1 & 3;
      const int8 SHIFTL = 1 << 3;
      const int8 SHIFTR = 32 >> 3;
      const int8 ADDP = 1 + 3;
      const int8 ADDM = 1 - 3;
      const int8 MULTM = 2 * 3;
      const int8 MULTR = 8 % 3;
      const int8 MULTD = 8 / 2;
      const int8 UNAM = -8;
      const int8 UNAP = +8;
      const int8 UNAI = ~8;

      const int8 PRECEDENCE = 1 + 2 * 3;
    };
    struct Foo {
      int8 i;
    };
  };
};
"""

IDL = """
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

IDL_STRINGARRAY = """
module test_msgs {
  module msg {
    typedef string string__3[3];
    struct Strings {
        string__3 values;
    };
  };
};
"""

IDL_KEYWORD = """
module test_msgs {
  module msg {
    module Foo_Constants {
        const int32 return = 32;
    };
    struct Foo {
        uint64 yield;
    };
  };
};
"""

IDL_REFRENAME = """
module test_msgs {
  module msg {
    struct Bar {
        int8 i;
    };

    struct Foo {
        Bar bar1;
        msg::Bar bar2;
        ::test_msgs::msg::Bar bar3;

        // Undefined
        Baz baz1;
    };
  };
};
"""

IDL_TYPEDEFS = """
typedef short T1;
module test_msgs {
  module msg {
    typedef long T1;
    struct Foo {
        T1 local;
        ::T1 global;
    };
  };
};
"""

IDL_ENUMS = """
enum COLORS {
  RED,
  GREEN,
  BLUE,
  @value(100)
  BLACK
};
"""


def test_idl_parser_raises_on_bad_definition() -> None:
    """Test idl parser raises on bad definition."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('module test_msgs {}')

    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('typedef long good; bad')


def test_idl_parser_accepts_literals_and_expressions() -> None:
    """Test idl parser accepts literals and expressions."""
    ret = get_types_from_idl(IDL_LITERALS_EXPRESSIONS)
    assert ret == {}


def test_idl_parser_evaluates_expressions() -> None:
    """Test idl parser evluates expressions."""
    ret = get_types_from_idl(IDL_CONST_EXPRS)
    assert ret['test_msgs/msg/Foo'][0] == [
        ('OR', 'int8', 3),
        ('XOR', 'int8', 2),
        ('AND', 'int8', 1),
        ('SHIFTL', 'int8', 8),
        ('SHIFTR', 'int8', 4),
        ('ADDP', 'int8', 4),
        ('ADDM', 'int8', -2),
        ('MULTM', 'int8', 6),
        ('MULTR', 'int8', 2),
        ('MULTD', 'int8', 4),
        ('UNAM', 'int8', -8),
        ('UNAP', 'int8', 8),
        ('UNAI', 'int8', -9),
        ('PRECEDENCE', 'int8', 7),
    ]


def test_idl_parser_raises_on_unresolved_constant() -> None:
    """Test idl parser raises on unresolved constant."""
    with pytest.raises(TypesysError, match="resolve constant 'B'"):
        _ = get_types_from_idl('const int8 A = B;')


def test_idl_parser_accepts_complex_document() -> None:
    """Test idl parser accepts definition with comments, typedefs, and annotations."""
    ret = get_types_from_idl(IDL)
    get_typestore(Stores.EMPTY).register(ret)

    assert 'test_msgs/msg/Foo' in ret
    consts, fields = ret['test_msgs/msg/Foo']
    assert consts == [('FOO', 'int32', 32), ('BAR', 'int64', 64)]
    assert fields[0][0] == 'header'
    assert fields[0][1][1] == 'std_msgs/msg/Header'
    assert fields[1][0] == 'bool'
    assert fields[1][1][1] == 'std_msgs/msg/Bool'
    assert fields[2][0] == 'sibling'
    assert fields[2][1][1] == 'test_msgs/msg/Baz/O'
    assert fields[3][1][0] == int(Nodetype.BASE)
    assert fields[4][1][0] == int(Nodetype.SEQUENCE)
    assert fields[5][1][0] == int(Nodetype.SEQUENCE)
    assert fields[6][1][0] == int(Nodetype.ARRAY)

    assert 'test_msgs/Bar' in ret
    consts, fields = ret['test_msgs/Bar']
    assert consts == []
    assert len(fields) == 1
    assert fields[0][0] == 'i'
    assert fields[0][1][1] == ('int32', 0)

    assert 'Toplevel' in ret
    consts, fields = ret['Toplevel']
    assert consts == []
    assert len(fields) == 1
    assert fields[0][0] == 's'
    assert fields[0][1][1] == ('int16', 0)


def test_idl_parser_accepts_string_arrays() -> None:
    """Test idl parser accepts string arrays."""
    ret = get_types_from_idl(IDL_STRINGARRAY)
    get_typestore(Stores.EMPTY).register(ret)

    consts, fields = ret['test_msgs/msg/Strings']
    assert consts == []
    assert len(fields) == 1
    assert fields[0][0] == 'values'
    assert fields[0][1] == (Nodetype.ARRAY, ((Nodetype.BASE, ('string', 0)), 3))


def test_idl_parser_avoids_python_keyword_collisions() -> None:
    """Test idl parser renames message fields to avoid python keyword collisions."""
    ret = get_types_from_idl(IDL_KEYWORD)
    get_typestore(Stores.EMPTY).register(ret)

    consts, fields = ret['test_msgs/msg/Foo']
    assert consts[0][0] == 'return_'
    assert fields[0][0] == 'yield_'


def test_idl_parser_renames_relative_references() -> None:
    """Test idl parser renames relative type references."""
    ret = get_types_from_idl(IDL_REFRENAME)
    get_typestore(Stores.EMPTY).register(ret)

    _, fields = ret['test_msgs/msg/Foo']
    assert fields[0][0] == 'bar1'
    assert fields[0][1] == (Nodetype.NAME, 'test_msgs/msg/Bar')
    assert fields[1][0] == 'bar2'
    assert fields[1][1] == (Nodetype.NAME, 'test_msgs/msg/Bar')
    assert fields[2][0] == 'bar3'
    assert fields[2][1] == (Nodetype.NAME, 'test_msgs/msg/Bar')
    assert fields[3][0] == 'baz1'
    assert fields[3][1] == (Nodetype.NAME, 'test_msgs/msg/Baz')


def test_idl_typedefs() -> None:
    """Test idl parser resolves typedefs."""
    ret = get_types_from_idl(IDL_TYPEDEFS)
    get_typestore(Stores.EMPTY).register(ret)

    _, fields = ret['test_msgs/msg/Foo']
    assert fields[0][0] == 'local'
    assert fields[0][1] == (Nodetype.BASE, ('int32', 0))
    assert fields[1][0] == 'global_'
    assert fields[1][1] == (Nodetype.BASE, ('int16', 0))


def test_idl_parser_refuses_bad_const_types() -> None:
    """Test idl parser refuses bad const types."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('module test_msgs { const _Foo foo = 8; };')


def test_idl_parser_refuses_bad_expressions() -> None:
    """Test idl parser refuses bad const types."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('module test_msgs { const int8 foo = !8; };')


def test_idl_parser_refuses_missing_array_size() -> None:
    """Test idl parser refuses missing array size."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('struct Foo { int8 arr[]; };')


def test_idl_parser_refuses_bad_enumerator() -> None:
    """Test idl parser refuses bad enumerators."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('enum COLORS { _RED };')


def test_idl_parser_parses_enums() -> None:
    """Test idl parser parses enums."""
    res = get_types_from_idl(IDL_ENUMS)
    assert res == {}


def test_idl_parser_refuses_bad_type_declarator() -> None:
    """Test idl parser refuses bad type declarator."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('typedef _Foo foo;')


def test_idl_parser_refuses_bad_declarators() -> None:
    """Test idl parser refuses bad declarators."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('typedef Foo _foo;')


def test_idl_parser_refuses_bad_annotation_params() -> None:
    """Test idl parser refuses bad annotation params."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('enum COLORS { @value( RED };')

    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('enum COLORS { @value() RED };')
