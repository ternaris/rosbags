# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Code generators for the extensible type system."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rosbags.interfaces.typing import FieldDesc, Typesdict


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
        typ = 'int' if desc[1][0] in {'char', 'byte'} else desc[1][0]
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
        if typ in {'byte', 'char'} or INTLIKE.match(typ):
            typ = {
                'bool': 'bool_',
                'byte': 'uint8',
                'char': 'uint8',
            }.get(typ, typ)
            return f'np.ndarray[None, np.dtype[np.{typ}]]'

    return f'list[{get_typehint(sub)}]'


def generate_python_code(
    typs: Typesdict,
    base: str | None = None,
    remove: Sequence[str] = (),
    add: Sequence[str] = (),
    change: Sequence[str] = (),
) -> str:
    """Generate python code from types dictionary.

    Args:
        typs: Dictionary mapping message typenames to parsetrees.
        base: Base type store.
        remove: Types to remove.
        add: Types to add.
        change: Types to change.

    Returns:
        Code for importable python module.

    """
    lines = [
        '# Copyright 2020 - 2024 Ternaris',
        '# SPDX-License-Identifier:' ' Apache-2.0',
        '#',
        '# THIS FILE IS GENERATED, DO NOT EDIT',
        '"""Message type definitions."""',
        '',
        '# ruff: noqa: E501,F401,F403,F405,F821,N801,N814,TCH004',
        '',
        'from __future__ import annotations',
        '',
        'from dataclasses import dataclass',
        'from typing import TYPE_CHECKING',
        '',
        'from rosbags.interfaces import Nodetype as T',
        '',
    ]
    if base:
        lines += [
            f'from .{base} import *',
            '',
        ]

    lines += [
        'if TYPE_CHECKING:',
        '    from typing import ClassVar',
        '',
        '    import numpy as np',
        '',
    ]
    if not base:
        lines += [
            '    from rosbags.interfaces.typing import Typesdict',
            '',
        ]
    lines += ['']
    if remove:
        lines += [
            'FIELDDEFS = FIELDDEFS.copy()',
            *[f'del FIELDDEFS[{x!r}]' for x in remove],
            *[f'del {x.replace("/", "__")}' for x in remove],
            '',
            '',
        ]

    if not base:
        add = list(typs.keys())

    for name, (consts, fields) in typs.items():
        if name not in add and name not in change:
            continue
        pyname = name.replace('/', '__')
        lines += [
            '@dataclass',
            f'class {pyname}:{"  # type: ignore[no-redef]" if name in change else ""}',
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
        typs = ['', 'T.BASE', 'T.NAME', 'T.ARRAY', 'T.SEQUENCE']
        if ftype[0] == Nodetype.BASE or ftype[0] == Nodetype.NAME:
            return f'({typs[ftype[0]]}, {ftype[1]!r})'
        return f'({typs[ftype[0]]}, (({typs[ftype[1][0][0]]}, {ftype[1][0][1]!r}), {ftype[1][1]}))'

    if base:
        lines += [
            'FIELDDEFS = {',
            '    **FIELDDEFS,',
        ]
    else:
        lines += ['FIELDDEFS: Typesdict = {']
    for name, (consts, fields) in typs.items():
        if name not in add and name not in change:
            continue
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
