# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Code generators and registration functions for the extensible type system."""

from __future__ import annotations

import re
import sys
from importlib.util import module_from_spec, spec_from_loader
from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype

from . import types
from .base import TypesysError

if TYPE_CHECKING:
    from rosbags.interfaces.typing import FieldDesc, Typesdict, Typestore


INTLIKE = re.compile('^u?(bool|int|float)')


def get_typehint(desc: FieldDesc) -> str:
    """Get python type hint for field.

    Args:
        desc: Field descriptor.

    Returns:
        Type hint for field.

    """
    if desc[0] == Nodetype.BASE:
        if desc[1][0] == 'string':
            return 'str'
        typ = 'int' if desc[1][0] == 'octet' else desc[1][0]
        match = INTLIKE.match(typ)
        assert match, typ
        return match.group(1)

    if desc[0] == Nodetype.NAME:
        assert isinstance(desc[1], str)
        return desc[1].replace('/', '__')

    assert desc[0] in {Nodetype.ARRAY, Nodetype.SEQUENCE}
    sub = desc[1][0]
    if sub[0] == Nodetype.BASE:
        typ = sub[1][0]
        if typ == 'octet' or INTLIKE.match(typ):
            typ = {
                'bool': 'bool_',
                'octet': 'uint8',
            }.get(typ, typ)
            return f'numpy.ndarray[None, numpy.dtype[numpy.{typ}]]'

    return f'list[{get_typehint(sub)}]'


def generate_python_code(typs: Typesdict) -> str:
    """Generate python code from types dictionary.

    Args:
        typs: Dictionary mapping message typenames to parsetrees.

    Returns:
        Code for importable python module.

    """
    lines = [
        '# Copyright 2020 - 2024 Ternaris',
        '# SPDX-License-Identifier: Apache-2.0',
        '#',
        '# THIS FILE IS GENERATED, DO NOT EDIT',
        '"""ROS2 message types."""',
        '',
        '# fmt: off',
        '# ruff: noqa',
        '',
        'from __future__ import annotations',
        '',
        'from dataclasses import dataclass',
        'from typing import TYPE_CHECKING',
        '',
        'from rosbags.interfaces import Nodetype',
        '',
        'if TYPE_CHECKING:',
        '    from typing import Any, ClassVar',
        '',
        '    import numpy',
        '',
        '    from rosbags.interfaces.typing import Typesdict',
        '',
        'A = Nodetype.BASE',
        'B = Nodetype.NAME',
        'C = Nodetype.ARRAY',
        'D = Nodetype.SEQUENCE',
    ]

    for name, (consts, fields) in typs.items():
        pyname = name.replace('/', '__')
        lines += [
            '@dataclass',
            f'class {pyname}:',
            f'    """Class for {name}."""',
            '',
            *[
                (
                    f'    {fname}: {get_typehint(desc)}'
                    f'{" = 0" if fname == "structure_needs_at_least_one_member" else ""}'
                )
                for fname, desc in fields
                or [('structure_needs_at_least_one_member', (Nodetype.BASE, ('uint8', 0)))]
            ],
            *[
                f'    {fname}: ClassVar[{get_typehint((Nodetype.BASE, (ftype, 0)))}] = {fvalue!r}'
                for fname, ftype, fvalue in consts
            ],
            f'    __msgtype__: ClassVar[str] = {name!r}',
        ]

        lines += [
            '',
            '',
        ]

    def get_ftype(ftype: FieldDesc) -> str:
        typs = ['', 'Nodetype.BASE', 'Nodetype.NAME', 'Nodetype.ARRAY', 'Nodetype.SEQUENCE']
        if ftype[0] == Nodetype.BASE or ftype[0] == Nodetype.NAME:
            return f'({typs[ftype[0]]}, {ftype[1]!r})'
        return f'({typs[ftype[0]]}, (({typs[ftype[1][0][0]]}, {ftype[1][0][1]!r}), {ftype[1][1]}))'

    lines += ['FIELDDEFS: Typesdict = {']
    for name, (consts, fields) in typs.items():
        pyname = name.replace('/', '__')
        lines += [
            f"    '{name}': (",
            *(
                [
                    '        [',
                    *[
                        f'            ({fname!r}, {ftype!r}, {fvalue!r}),'
                        for fname, ftype, fvalue in consts
                    ],
                    '        ],',
                ]
                if consts
                else ['        [],']
            ),
            '        [',
            *[
                f'            ({fname!r}, {get_ftype(ftype)}),'
                for fname, ftype in fields
                or [('structure_needs_at_least_one_member', (Nodetype.BASE, ('uint8', 0)))]
            ],
            '        ],',
            '    ),',
        ]
    lines += [
        '}',
        '',
    ]
    return '\n'.join(lines)


def register_types(typs: Typesdict, typestore: Typestore = types) -> None:
    """Register types in type system.

    Args:
        typs: Dictionary mapping message typenames to parsetrees.
        typestore: Type store.

    Raises:
        TypesysError: Type already present with different definition.

    """
    code = generate_python_code(typs)
    name = 'rosbags.usertypes'
    spec = spec_from_loader(name, loader=None)
    assert spec
    module = module_from_spec(spec)
    sys.modules[name] = module
    exec(code, module.__dict__)  # noqa: S102
    fielddefs: Typesdict = module.FIELDDEFS

    for name, (_, fields) in fielddefs.items():
        if name == 'std_msgs/msg/Header':
            continue
        if have := typestore.FIELDDEFS.get(name):
            _, have_fields = have
            have_fields = [(x[0].lower(), x[1]) for x in have_fields]
            new_fields = [(x[0].lower(), x[1]) for x in fields]
            if have_fields != new_fields:
                msg = f'Type {name!r} is already present with different definition.'
                raise TypesysError(msg)

    for name in fielddefs.keys() - typestore.FIELDDEFS.keys():
        pyname = name.replace('/', '__')
        setattr(typestore, pyname, getattr(module, pyname))
        typestore.FIELDDEFS[name] = fielddefs[name]
