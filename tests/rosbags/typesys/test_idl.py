# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""IDL Message Definition Parser Tests."""

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import Stores, TypesysError, get_types_from_idl, get_typestore

IDL_LITERALS_EXPRESSIONS = """
// assign different literals and expressions

#ifndef FOO
#define FOO

#include <global>
#include "local"

const bool g_bool = TRUE;
const int8 g_int1 = 7;
const int8 g_int2 = 07;
const int8 g_int3 = 0x7;
const float64 g_float1 = 1.1;
const float64 g_float2 = 1e10;
const char g_char = 'c';
const string g_string1 = "";
const string<128> g_string2 = "str" "ing";

module Foo {
    const int64 g_expr1 = ~1;
    const int64 g_expr2 = 2 * 4;
};

#endif
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
    typedef test_msgs::msg::Bar Bar;
    typedef double d4[4];

    module Foo_Constants {
        const int32 FOO = 32;
        const int64 BAR = 64;
    };

    @comment(type="text", text="ignore")
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

    module Bar {
      #define i
    };
  };

  struct Bar {
    int i;
  };
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


def test_idl_parser_raises_on_bad_definition() -> None:
    """Test idl parser raises on bad definition."""
    with pytest.raises(TypesysError, match='Could not parse'):
        _ = get_types_from_idl('module test_msgs {}')


def test_idl_parser_accepts_literals_and_expressions() -> None:
    """Test idl parser accepts literals and expressions."""
    ret = get_types_from_idl(IDL_LITERALS_EXPRESSIONS)
    assert ret == {}


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
    assert fields[2][1][1] == 'test_msgs/msg/Bar'
    assert fields[3][1][0] == int(Nodetype.BASE)
    assert fields[4][1][0] == int(Nodetype.SEQUENCE)
    assert fields[5][1][0] == int(Nodetype.SEQUENCE)
    assert fields[6][1][0] == int(Nodetype.ARRAY)

    assert 'test_msgs/Bar' in ret
    consts, fields = ret['test_msgs/Bar']
    assert consts == []
    assert len(fields) == 1
    assert fields[0][0] == 'i'
    assert fields[0][1][1] == ('int', 0)


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
