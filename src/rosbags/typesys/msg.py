# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""MSG Parser.

Grammar, parse tree visitor and conversion functions for message definitions in
`MSG`_ format. It also supports concatened message definitions as found in
Rosbag1 connection information.

.. _MSG: http://wiki.ros.org/msg

"""

from __future__ import annotations

import re
from hashlib import md5
from pathlib import PurePosixPath as Path
from typing import TYPE_CHECKING

from . import types
from .base import Nodetype, TypesysError, normalize_fieldname, parse_message_definition
from .peg import Rule, Visitor, parse_grammar

if TYPE_CHECKING:
    from typing import ClassVar, Tuple, TypeVar, Union

    from rosbags.interfaces.typing import Constdefs, Fielddefs, Fielddesc, Typesdict, Typestore

    T = TypeVar('T')

    StringNode = Tuple[Nodetype, Union[str, Tuple[str, int]]]
    ConstValue = Union[str, bool, int, float]
    Msgdesc = Tuple[Tuple[StringNode, Tuple[str, str, int], str], ...]
    LiteralMatch = Tuple[str, str]

GRAMMAR_MSG = r"""
specification
  = msgdef (msgsep msgdef)*

msgdef
  = r'MSG:\s' scoped_name definition*

msgsep
  = r'================================================================================'

definition
  = const_dcl
  / field_dcl

const_dcl
  = 'string' identifier '=' r'(?!={79}\n)[^\n]+'
  / type_spec identifier '=' float_literal
  / type_spec identifier '=' integer_literal
  / type_spec identifier '=' boolean_literal

field_dcl
  = type_spec identifier default_value?

type_spec
  = array_type_spec
  / bounded_array_type_spec
  / simple_type_spec

array_type_spec
  = simple_type_spec array_size

bounded_array_type_spec
  = simple_type_spec array_bounds

simple_type_spec
  = 'string' '<=' integer_literal
  / scoped_name

array_size
  = '[' integer_literal? ']'

array_bounds
  = '[<=' integer_literal ']'

scoped_name
  = identifier '/' scoped_name
  / identifier

identifier
  = r'[a-zA-Z_][a-zA-Z_0-9]*'

default_value
  = literal

literal
  = float_literal
  / integer_literal
  / boolean_literal
  / string_literal
  / array_literal

boolean_literal
  = r'[tT][rR][uU][eE]'
  / r'[fF][aA][lL][sS][eE]'
  / '0'
  / '1'

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

string_literal
  = '"' r'(\\"|[^"])*' '"'
  / '\'' r'(\\\'|[^'])*' '\''

array_literal
  = '[' array_elements? ']'

array_elements
  = literal ',' array_elements
  / literal
"""


def normalize_msgtype(name: str) -> str:
    """Normalize message typename.

    Args:
        name: Message typename.

    Returns:
        Normalized name.

    """
    path = Path(name)
    if path.parent.name != 'msg':
        path = path.parent / 'msg' / path.name
    return str(path)


def normalize_fieldtype(typename: str, field: Fielddesc, names: list[str]) -> Fielddesc:
    """Normalize field typename.

    Args:
        typename: Type name of field owner.
        field: Field definition.
        names: Valid message names.

    Returns:
        Normalized fieldtype.

    """
    dct = {Path(name).name: name for name in names}
    ftype, args = field
    name = args if ftype == int(Nodetype.NAME) else args[0][1]

    assert isinstance(name, (str, tuple))
    if name in VisitorMSG.BASETYPES or name[0] in VisitorMSG.BASETYPES:
        ifield = (Nodetype.BASE, name)
    else:
        assert isinstance(name, str)
        if name in dct:
            name = dct[name]
        elif name == 'Header':
            name = 'std_msgs/msg/Header'
        elif '/' not in name:
            name = str(Path(typename).parent / name)
        elif '/msg/' not in name:
            name = str((path := Path(name)).parent / 'msg' / path.name)
        ifield = (Nodetype.NAME, name)

    if ftype == int(Nodetype.NAME):
        return ifield  # type: ignore[return-value]

    assert not isinstance(args, str)
    return (ftype, (ifield, args[1]))  # type: ignore[return-value]


def denormalize_msgtype(typename: str) -> str:
    """Undo message tyoename normalization.

    Args:
        typename: Normalized message typename.

    Returns:
        ROS1 style name.

    """
    assert '/msg/' in typename
    return str((path := Path(typename)).parent.parent / path.name)


class VisitorMSG(Visitor):
    """MSG file visitor."""

    RULES = parse_grammar(GRAMMAR_MSG, re.compile(r'(\s|#[^\n]*$)+', re.M | re.S))

    BASETYPES: ClassVar[set[str]] = {
        'bool',
        'octet',
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
    }

    def visit_const_dcl(
        self,
        children: tuple[StringNode, StringNode, LiteralMatch, ConstValue],
    ) -> tuple[StringNode, tuple[str, str, ConstValue]]:
        """Process const declaration, suppress output."""
        value: str | bool | int | float
        if (typ := children[0][1]) == 'string':
            assert isinstance(children[3], str)
            value = children[3].strip()
        else:
            value = children[3]
        assert isinstance(typ, str)
        assert isinstance(children[1][1], str)
        return (Nodetype.CONST, ''), (typ, children[1][1], value)

    def visit_specification(
        self,
        children: tuple[tuple[str, Msgdesc], tuple[tuple[str, tuple[str, Msgdesc]], ...]],
    ) -> Typesdict:
        """Process start symbol."""
        typelist = [children[0], *[x[1] for x in children[1]]]
        typedict = dict(typelist)
        names = list(typedict.keys())
        res: Typesdict = {}
        for name, items in typedict.items():
            consts: Constdefs = [
                (normalize_fieldname(x[1][1]), x[1][0], x[1][2])
                for x in items
                if x[0] == (Nodetype.CONST, '')
            ]
            fields: Fielddefs = [
                (
                    normalize_fieldname(field[1][1]),
                    normalize_fieldtype(
                        name,
                        field[0],  # type: ignore[arg-type]
                        names,
                    ),
                )
                for field in items
                if field[0] != (Nodetype.CONST, '')
            ]
            res[name] = consts, fields
        return res

    def visit_msgdef(
        self,
        children: tuple[str, StringNode, tuple[T | None]],
    ) -> tuple[str, tuple[T, ...]]:
        """Process single message definition."""
        assert len(children) == 3
        assert isinstance(children[1][1], str)
        return normalize_msgtype(children[1][1]), tuple(x for x in children[2] if x is not None)

    def visit_msgsep(self, _: str) -> None:
        """Process message separator, suppress output."""

    def visit_array_type_spec(
        self,
        children: tuple[StringNode, tuple[LiteralMatch, tuple[int, ...], LiteralMatch]],
    ) -> tuple[Nodetype, tuple[StringNode, int]]:
        """Process array type specifier."""
        if length := children[1][1]:
            return Nodetype.ARRAY, (children[0], length[0])
        return Nodetype.SEQUENCE, (children[0], 0)

    def visit_bounded_array_type_spec(
        self,
        children: tuple[StringNode, tuple[StringNode, int, StringNode]],
    ) -> tuple[Nodetype, tuple[StringNode, int]]:
        """Process bounded array type specifier."""
        return Nodetype.SEQUENCE, (children[0], children[1][1])

    def visit_simple_type_spec(
        self,
        children: StringNode | tuple[LiteralMatch, LiteralMatch, int],
    ) -> StringNode:
        """Process simple type specifier."""
        if len(children) > 2:
            assert (Rule.LIT, '<=') in children
            assert isinstance(children[0], tuple)
            assert isinstance(children[2], int)
            return Nodetype.NAME, (children[0][1], children[2])
        typespec = children[1]
        assert isinstance(typespec, str)
        dct: dict[str, str | tuple[str, int]] = {
            'time': 'builtin_interfaces/msg/Time',
            'duration': 'builtin_interfaces/msg/Duration',
            'byte': 'octet',
            'char': 'uint8',
            'string': ('string', 0),
        }
        return Nodetype.NAME, dct.get(typespec, typespec)

    def visit_scoped_name(
        self,
        children: StringNode | tuple[StringNode, LiteralMatch, StringNode],
    ) -> StringNode:
        """Process scoped name."""
        if len(children) == 2:
            return children
        assert len(children) == 3
        return (
            Nodetype.NAME,
            '/'.join(x[1] for x in children if x[0] != Rule.LIT),  # type: ignore[misc]
        )

    def visit_identifier(self, children: str) -> StringNode:
        """Process identifier."""
        return (Nodetype.NAME, children)

    def visit_boolean_literal(self, children: str) -> bool:
        """Process boolean literal."""
        return children.lower() in {'true', '1'}

    def visit_float_literal(self, children: str) -> float:
        """Process float literal."""
        return float(children)

    def visit_decimal_literal(self, children: str) -> int:
        """Process decimal integer literal."""
        return int(children)

    def visit_octal_literal(self, children: str) -> int:
        """Process octal integer literal."""
        return int(children, 8)

    def visit_hexadecimal_literal(self, children: str) -> int:
        """Process hexadecimal integer literal."""
        return int(children, 16)

    def visit_string_literal(self, children: str) -> str:
        """Process integer literal."""
        return children[1]


def get_types_from_msg(text: str, name: str) -> Typesdict:
    """Get type from msg message definition.

    Args:
        text: Message definiton.
        name: Message typename.

    Returns:
        list with single message name and parsetree.

    """
    return parse_message_definition(VisitorMSG(), f'MSG: {name}\n{text}')


def gendefhash(
    typename: str,
    subdefs: dict[str, tuple[str, str]],
    typestore: Typestore = types,
    ros_version: int = 1,
) -> tuple[str, str]:
    """Generate message definition and hash for type.

    The subdefs argument will be filled with child definitions.

    Args:
        typename: Name of type to generate definition for.
        subdefs: Child definitions.
        typestore: Custom type store.
        ros_version: ROS version number.

    Returns:
        Message definition and hash.

    Raises:
        TypesysError: Type does not exist.

    """
    typemap = (
        {'builtin_interfaces/msg/Time': 'time', 'builtin_interfaces/msg/Duration': 'duration'}
        if ros_version == 1
        else {}
    )

    deftext: list[str] = []
    hashtext: list[str] = []
    if typename not in typestore.FIELDDEFS:
        msg = f'Type {typename!r} is unknown.'
        raise TypesysError(msg)

    for name, typ, value in typestore.FIELDDEFS[typename][0]:
        stripped_name = name.rstrip('_')
        deftext.append(f'{typ} {stripped_name}={value}')
        hashtext.append(f'{typ} {stripped_name}={value}')

    for name, desc in typestore.FIELDDEFS[typename][1]:
        if name == 'structure_needs_at_least_one_member':
            continue
        stripped_name = name.rstrip('_')
        if desc[0] == int(Nodetype.BASE):
            args = desc[1]
            if args == 'octet':
                args = 'byte'
            elif args[0] == 'string':
                args = f'string<={args[1]}' if args[1] else 'string'
            deftext.append(f'{args} {stripped_name}')
            hashtext.append(f'{args} {stripped_name}')
        elif desc[0] == int(Nodetype.NAME):
            args = desc[1]
            assert isinstance(args, str)
            subname = args
            if subname in typemap:
                deftext.append(f'{typemap[subname]} {stripped_name}')
                hashtext.append(f'{typemap[subname]} {stripped_name}')
            else:
                if subname not in subdefs:
                    subdefs[subname] = ('', '')
                    subdefs[subname] = gendefhash(subname, subdefs, typestore, ros_version)
                deftext.append(f'{denormalize_msgtype(subname)} {stripped_name}')
                hashtext.append(f'{subdefs[subname][1]} {stripped_name}')
        else:
            assert desc[0] == 3 or desc[0] == 4
            assert isinstance(desc[1], tuple)
            subdesc, num = desc[1]
            isubtype, isubname = subdesc
            count = '' if num == 0 else str(num) if desc[0] == int(Nodetype.ARRAY) else f'<={num}'
            if isubtype == int(Nodetype.BASE):
                if isubname == 'octet':
                    isubname = 'byte'
                elif isubname[0] == 'string':
                    isubname = f'string<={isubname[1]}' if isubname[1] else 'string'
                deftext.append(f'{isubname}[{count}] {stripped_name}')
                hashtext.append(f'{isubname}[{count}] {stripped_name}')
            elif isubname in typemap:
                assert isinstance(isubname, str)
                deftext.append(f'{typemap[isubname]}[{count}] {stripped_name}')
                hashtext.append(f'{typemap[isubname]}[{count}] {stripped_name}')
            else:
                assert isinstance(isubname, str)
                if isubname not in subdefs:
                    subdefs[isubname] = ('', '')
                    subdefs[isubname] = gendefhash(isubname, subdefs, typestore, ros_version)
                deftext.append(f'{denormalize_msgtype(isubname)}[{count}] {stripped_name}')
                hashtext.append(f'{subdefs[isubname][1]} {stripped_name}')

    if ros_version == 1 and typename == 'std_msgs/msg/Header':
        deftext.insert(0, 'uint32 seq')
        hashtext.insert(0, 'uint32 seq')

    deftext.append('')
    return '\n'.join(deftext), md5('\n'.join(hashtext).encode()).hexdigest()  # noqa: S324


def generate_msgdef(
    typename: str,
    typestore: Typestore = types,
    ros_version: int = 1,
) -> tuple[str, str]:
    """Generate message definition for type.

    Args:
        typename: Name of type to generate definition for.
        typestore: Custom type store.
        ros_version: ROS version number.

    Returns:
        Message definition.

    """
    subdefs: dict[str, tuple[str, str]] = {}
    msgdef, md5sum = gendefhash(typename, subdefs, typestore, ros_version)

    msgdef = ''.join(
        [
            msgdef,
            *[f'{"=" * 80}\nMSG: {denormalize_msgtype(k)}\n{v[0]}' for k, v in subdefs.items()],
        ],
    )

    return msgdef, md5sum
