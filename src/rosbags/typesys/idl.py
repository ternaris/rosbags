# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""IDL Parser.

Grammar, parse tree visitor and conversion functions for message definitions in
`IDL`_ format.

.. _IDL: https://www.omg.org/spec/IDL/About-IDL/

"""

from __future__ import annotations

import re
from enum import IntEnum, auto
from typing import TYPE_CHECKING, cast

from rosbags.interfaces import Nodetype

from .base import normalize_fieldname, parse_message_definition
from .peg import Visitor, parse_grammar

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Literal, TypeAlias

    from rosbags.interfaces.typing import (
        BaseDesc,
        Basename,
        Basetype,
        ConstValue,
        Fielddefs,
        FieldDesc,
        NameDesc,
        Typesdict,
    )

    L: TypeAlias = 'tuple[Literal["LITERAL"], str]'

    LitNode: TypeAlias = 'tuple[Literal[Node.LITERAL], ConstValue]'

    Adec: TypeAlias = 'tuple[Literal[Node.ADECLARATOR], NameDesc, LitNode]'
    Anno: TypeAlias = 'tuple[Literal[Node.ANNOTATION], str, list[tuple[NameDesc, LitNode]]]'
    Const: TypeAlias = 'tuple[Literal[Node.CONST], tuple[Basetype, str, ConstValue]]'
    Expr: TypeAlias = 'LitNode | NameDesc | ExprUnary | ExprBinary'
    ExprBinary: TypeAlias = 'tuple[Literal[Node.EXPRESSION_BINARY], str, int, int]'
    ExprUnary: TypeAlias = 'tuple[Literal[Node.EXPRESSION_UNARY], str, int]'
    Module: TypeAlias = 'tuple[Literal[Node.MODULE], list[Const], list[Struct]]'
    Struct: TypeAlias = 'tuple[Literal[Node.STRUCT], str, Fielddefs]'

GRAMMAR_IDL = r"""
specification
  = definition+

definition
  = macro
  / include
  / module_dcl ';'
  / const_dcl ';'
  / type_dcl ';'

macro
  = ifndef
  / define
  / endif

ifndef
  = '#ifndef' r'[a-zA-Z0-9_]+'

define
  = '#define' r'[a-zA-Z0-9_]+'

endif
  = '#endif'

include
  = '#include' include_filename

include_filename
  = '<' r'[^>]+' '>'
  / '"' r'[^"]+' '"'

module_dcl
  = annotation* 'module' identifier '{' definition+ '}'

const_dcl
  = 'const' const_type identifier '=' expression

type_dcl
  = typedef_dcl
  / constr_type_dcl

typedef_dcl
  = 'typedef' type_declarator

type_declarator
  = ( template_type_spec
    / simple_type_spec
    / constr_type_dcl
    ) any_declarators

simple_type_spec
  = base_type_spec
  / scoped_name

template_type_spec
  = sequence_type
  / string_type

sequence_type
  = 'sequence' '<' type_spec ',' expression '>'
  / 'sequence' '<' type_spec '>'

type_spec
  = template_type_spec
  / simple_type_spec

any_declarators
  = any_declarator (',' any_declarator)*

any_declarator
  = array_declarator
  / simple_declarator

constr_type_dcl
  = struct_dcl

struct_dcl
  = struct_def

struct_def
  = annotation* 'struct' identifier '{' member+ '}'

member
  = annotation* type_spec declarators ';'

declarators
  = declarator (',' declarator)*

declarator
  = simple_declarator

simple_declarator
  = identifier

array_declarator
  = identifier fixed_array_size+

fixed_array_size
  = '[' expression ']'

annotation
  = '@' scoped_name ('(' annotation_params ')')?

annotation_params
  = annotation_param (',' annotation_param)*
  / expression

annotation_param
  = identifier '=' expression

const_type
  = base_type_spec
  / string_type
  / scoped_name

base_type_spec
  = float_type
  / integer_type
  / char_type
  / boolean_type

integer_type
  = r'u?int(64|32|16|8)\b'
  / r'(unsigned\s+)?((long\s+)?long|int|short)\b'

float_type
  = r'(long.double|double|float)\b'

char_type
  = r'char\b'

boolean_type
  = r'boolean\b'

string_type
  = 'string' '<' expression '>'
  / r'string\b'

scoped_name
  = identifier '::' scoped_name
  / ':' scoped_name
  / identifier

identifier
  = r'[a-zA-Z_][a-zA-Z_0-9]*'

expression
  = primary_expr binary_operator primary_expr
  / primary_expr
  / unary_operator primary_expr

primary_expr
  = literal
  / scoped_name
  / '(' expression ')'

binary_operator
  = '|'
  / '^'
  / '&'
  / '<<'
  / '>>'
  / '+'
  / '-'
  / '*'
  / '/'
  / '%'

unary_operator
  = '+'
  / '-'
  / '~'

literal
  = boolean_literal
  / float_literal
  / integer_literal
  / character_literal
  / string_literals

boolean_literal
  = 'TRUE'
  / 'FALSE'

integer_literal
  = hexadecimal_literal
  / octal_literal
  / decimal_literal

decimal_literal
  = r'[-+]?[1-9][0-9]+'
  / r'[-+]?[0-9]'

octal_literal
  = r'[-+]?0[0-7]+'

hexadecimal_literal
  = r'[-+]?0[xX][a-fA-F0-9]+'

float_literal
  = r'[-+]?[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?'
  / r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)'

character_literal
  = '\'' r'[a-zA-Z0-9_]' '\''

string_literals
  = string_literal+

string_literal
  = '"' r'(\\"|[^"])*' '"'
"""


class Node(IntEnum):
    """Parse tree node types."""

    LITERAL = auto()
    MODULE = auto()
    CONST = auto()
    STRUCT = auto()
    ADECLARATOR = auto()
    ANNOTATION = auto()
    EXPRESSION_BINARY = auto()
    EXPRESSION_UNARY = auto()


class VisitorIDL(Visitor):
    """IDL file visitor."""

    RULES = parse_grammar(
        GRAMMAR_IDL,
        re.compile(r'(\s|/[*]([^*]|[*](?!/))*[*]/|//[^\n]*$)+', re.MULTILINE | re.DOTALL),
    )

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self.typedefs: dict[str | Basetype, FieldDesc] = {}

    def visit_specification(
        self,
        children: tuple[tuple[tuple[Node, list[Const], list[Struct]], L] | None],
    ) -> Typesdict:
        """Process start symbol, return only children of modules."""
        structs: dict[str, Fielddefs] = {}
        consts: dict[str, list[tuple[str, Basename, ConstValue]]] = {}
        for item in children:
            if item is None or item[0][0] != Node.MODULE:
                continue
            for csubitem in item[0][1]:
                assert csubitem[0] == Node.CONST
                if '_Constants/' in csubitem[1][1]:
                    structname, varname = csubitem[1][1].split('_Constants/')
                    if structname not in consts:
                        consts[structname] = []
                    consts[structname].append(
                        (
                            normalize_fieldname(varname),
                            csubitem[1][0][0],
                            csubitem[1][2],
                        ),
                    )

            for ssubitem in item[0][2]:
                assert ssubitem[0] == Node.STRUCT
                structs[ssubitem[1]] = ssubitem[2]
                if ssubitem[1] not in consts:
                    consts[ssubitem[1]] = []
        return {k: (consts[k], v) for k, v in structs.items()}

    def visit_macro(self, _: L | tuple[L, str]) -> None:
        """Process macro, suppress output."""

    def visit_include(self, _: tuple[L, tuple[L, str, L]]) -> None:
        """Process include, suppress output."""

    def visit_module_dcl(
        self,
        children: tuple[
            tuple[Anno, ...],
            L,
            NameDesc,
            L,
            tuple[tuple[Const | Struct | Module | None, L] | None, ...],
            L,
        ],
    ) -> Module:
        """Process module declaration."""
        assert len(children) == 6
        assert children[2][0] == Nodetype.NAME
        name = children[2][1]

        definitions = children[4]
        consts: list[Const] = []
        structs: list[Struct] = []
        for item in definitions:
            if item is None:
                continue
            assert item[1] == ('LITERAL', ';')
            if item[0] is None:
                continue
            subitem = item[0]
            if subitem[0] == Node.CONST:
                consts.append(subitem)
            elif subitem[0] == Node.STRUCT:
                structs.append(subitem)
            else:
                assert subitem[0] == Node.MODULE
                consts += subitem[1]
                structs += subitem[2]

        consts = [(ityp, (typ, f'{name}/{subname}', val)) for ityp, (typ, subname, val) in consts]
        structs = [(typ, f'{name}/{subname}', rest) for typ, subname, rest in structs]

        return Node.MODULE, consts, structs

    def visit_const_dcl(self, children: tuple[L, BaseDesc, NameDesc, L, LitNode]) -> Const:
        """Process const declaration."""
        return Node.CONST, (children[1][1], children[2][1], children[4][1])

    def visit_type_dcl(self, children: Struct | None) -> Struct | None:
        """Process type, pass structs, suppress otherwise."""
        if not children:
            return None
        assert children[0] == Node.STRUCT
        return children

    def visit_typedef_dcl(
        self,
        children: tuple[L, tuple[NameDesc | BaseDesc, tuple[NameDesc | Adec, ...]]],
    ) -> None:
        """Process type declarator, register type mapping in instance typedef dictionary."""
        assert len(children) == 2
        dclchildren = children[1]
        assert len(dclchildren) == 2
        base = self.typedefs.get(dclchildren[0][1], dclchildren[0])
        for declarator in dclchildren[1]:
            if declarator[0] == Node.ADECLARATOR:
                alias = declarator[1][1]
                typ, name = base
                assert isinstance(typ, Nodetype)
                assert isinstance(name, str | tuple)
                count = cast('Adec', declarator)[2][1]
                assert isinstance(count, int)
                value = cast('FieldDesc', (Nodetype.ARRAY, ((typ, name), count)))
            else:
                alias = cast('NameDesc', declarator)[1]
                value = base
            self.typedefs[alias] = value

    def visit_sequence_type(
        self,
        children: tuple[L, L, BaseDesc, L] | tuple[L, L, BaseDesc, L, LitNode, L],
    ) -> tuple[Nodetype, tuple[BaseDesc, int]]:
        """Process sequence type specification."""
        if len(children) == 6:
            typ, count = children[4]
            assert typ == Node.LITERAL
            assert isinstance(count, int)
            return Nodetype.SEQUENCE, (children[2], count)
        return Nodetype.SEQUENCE, (children[2], 0)

    def create_struct_field(
        self,
        parts: tuple[
            FieldDesc,
            tuple[NameDesc, ...],
        ],
    ) -> Generator[tuple[str, FieldDesc], None, None]:
        """Create struct field and expand typedefs."""
        typename, params = parts

        while typename[0] == Nodetype.NAME and typename[1] in self.typedefs:
            typename = self.typedefs[typename[1]]

        yield from ((normalize_fieldname(x[1]), typename) for x in params if x)

    def visit_struct_dcl(
        self,
        children: tuple[
            tuple[Anno, ...],
            L,
            NameDesc,
            L,
            list[tuple[tuple[Anno, ...], FieldDesc, tuple[NameDesc, ...], L]],
            L,
        ],
    ) -> Struct:
        """Process struct declaration."""
        fields = [y for x in children[4] for y in self.create_struct_field(x[1:3])]
        return Node.STRUCT, children[2][1], fields

    def visit_declarators(
        self,
        children: tuple[NameDesc, tuple[tuple[L, NameDesc], ...]],
    ) -> tuple[NameDesc, ...]:
        """Process declarators."""
        return children[0], *(x[1] for x in children[1])

    def visit_any_declarators(
        self,
        children: tuple[
            NameDesc | Adec,
            tuple[tuple[L, NameDesc | Adec], ...],
        ],
    ) -> tuple[NameDesc | Adec, ...]:
        """Process any declarators."""
        return children[0], *(x[1] for x in children[1])

    def visit_array_declarator(
        self,
        children: tuple[NameDesc, tuple[tuple[L, LitNode, L]]],
    ) -> Adec:
        """Process array declarator."""
        return Node.ADECLARATOR, children[0], children[1][0][1]

    def visit_annotation(
        self,
        children: tuple[
            L,
            NameDesc,
            tuple[
                tuple[
                    L,
                    tuple[
                        tuple[NameDesc, L, LitNode],
                        tuple[tuple[L, tuple[NameDesc, L, LitNode]], ...],
                    ],
                    L,
                ],
            ],
        ],
    ) -> Anno:
        """Process annotation."""
        assert len(children) == 3
        assert children[1][0] == Nodetype.NAME
        params = children[2][0][1]
        flat = [params[0], *[x[1:][0] for x in params[1]]]
        assert all(len(x) == 3 for x in flat)
        retparams = [(x[0], x[2]) for x in flat]
        return Node.ANNOTATION, children[1][1], retparams

    def visit_base_type_spec(self, children: str) -> BaseDesc:
        """Process base type specifier."""
        oname = children
        name = {
            'boolean': 'bool',
            'long double': 'float128',
            'double': 'float64',
            'float': 'float32',
        }.get(oname, oname)
        return Nodetype.BASE, (cast('Basename', name), 0)

    def visit_string_type(self, children: str | tuple[L, L, LitNode, L]) -> BaseDesc:
        """Prrocess string type specifier."""
        if isinstance(children, str):
            return Nodetype.BASE, ('string', 0)

        assert len(children) == 4
        assert isinstance(children[0], tuple)
        assert isinstance(children[2][1], int)
        return Nodetype.BASE, ('string', children[2][1])

    def visit_scoped_name(self, children: NameDesc | tuple[NameDesc, L, NameDesc]) -> NameDesc:
        """Process scoped name."""
        if len(children) == 2:
            return children
        assert len(children) == 3
        return Nodetype.NAME, f'{children[0][1]}/{children[2][1]}'

    def visit_identifier(self, children: str) -> NameDesc:
        """Process identifier."""
        return Nodetype.NAME, children

    def visit_expression(
        self,
        children: LitNode | NameDesc | tuple[L, LitNode] | tuple[LitNode, L, LitNode],
    ) -> Expr:
        """Process expression, literals are assumed to be integers only."""
        if children[0] in {
            Node.LITERAL,
            Nodetype.NAME,
        }:
            assert isinstance(children[1], str | bool | int | float)
            return cast('Expr', children)

        assert isinstance(children[0], tuple)
        if len(children) == 3:
            assert isinstance(children[0][1], int)
            assert isinstance(children[1][1], str)
            assert isinstance(children[2][1], int)
            return Node.EXPRESSION_BINARY, children[1][1], children[0][1], children[2][1]
        assert len(children) == 2
        assert isinstance(children[0][1], str)
        assert isinstance(children[1], tuple)
        assert isinstance(children[1][1], int)
        return Node.EXPRESSION_UNARY, children[0][1], children[1][1]

    def visit_boolean_literal(self, children: str) -> LitNode:
        """Process boolean literal."""
        return Node.LITERAL, children[1] == 'TRUE'

    def visit_float_literal(self, children: str) -> LitNode:
        """Process float literal."""
        return Node.LITERAL, float(children)

    def visit_decimal_literal(self, children: str) -> LitNode:
        """Process decimal integer literal."""
        return Node.LITERAL, int(children)

    def visit_octal_literal(self, children: str) -> LitNode:
        """Process octal integer literal."""
        return Node.LITERAL, int(children, 8)

    def visit_hexadecimal_literal(self, children: str) -> LitNode:
        """Process hexadecimal integer literal."""
        return Node.LITERAL, int(children, 16)

    def visit_character_literal(self, children: tuple[L, str, L]) -> LitNode:
        """Process char literal."""
        return Node.LITERAL, children[1]

    def visit_string_literals(self, children: tuple[tuple[L, str, L], ...]) -> LitNode:
        """Process string literal."""
        return Node.LITERAL, ''.join(x[1] for x in children)


def get_types_from_idl(text: str) -> Typesdict:
    """Get types from idl message definition.

    Args:
        text: Message definition.

    Returns:
        List of message message names and parsetrees.

    """
    return parse_message_definition(VisitorIDL(), text)
