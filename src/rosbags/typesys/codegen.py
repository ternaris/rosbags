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
            return f'np.ndarray[tuple[int, ...], np.dtype[np.{typ}]]'

    return f'list[{get_typehint(sub)}]'


def generate_python_code(
    typs: Typesdict,
    base: str | None = None,
    remove: Sequence[str] = (),
    add: Sequence[str] = (),
    change: Sequence[str] = (),
    keep: Sequence[str] = (),
) -> str:
    """Generate python code from types dictionary.

    Args:
        typs: Dictionary mapping message typenames to parsetrees.
        base: Base type store.
        remove: Types to remove.
        add: Types to add.
        change: Types to change.
        keep: Types to keep.

    Returns:
        Code for importable python module.

    """
    _ = remove
    if not base:
        add = list(typs.keys())
    lines = [
        '# Copyright 2020 - 2024 Ternaris',
        ('# SPDX-License-Identifier:' ' Apache-2.0'),
        '#',
        '# THIS FILE IS GENERATED, DO NOT EDIT',
        '"""Message type definitions."""',
        '',
        '# ruff: noqa: N801,N814,N816,TCH004',
        '',
        'from __future__ import annotations',
        '',
    ]
    if add or change:
        lines += ['from dataclasses import dataclass']
    lines += [
        'from typing import TYPE_CHECKING',
        '',
    ]
    if add or change:
        lines += [
            'from rosbags.interfaces import Nodetype as T',
            '',
        ]
    if base:
        lines += [
            f'from . import {base} as base',
            '',
        ]

    lines += [
        'if TYPE_CHECKING:',
    ]
    if add or change:
        lines += [
            '    from typing import ClassVar',
            '',
        ]
    lines += [
        '    import numpy as np',
        '',
        '    from rosbags.interfaces.typing import Typesdict',
        '',
    ]
    lines += ['']

    if keep:
        for name in keep:
            pyname = name.replace('/', '__')
            lines += [f'{pyname} = base.{pyname}']
        lines += ['', '']

    for name, (consts, fields) in typs.items():
        if name not in add and name not in change:
            continue
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
        typs = ['', 'T.BASE', 'T.NAME', 'T.ARRAY', 'T.SEQUENCE']
        if ftype[0] == Nodetype.BASE or ftype[0] == Nodetype.NAME:
            return f'({typs[ftype[0]]}, {ftype[1]!r})'
        return f'({typs[ftype[0]]}, (({typs[ftype[1][0][0]]}, {ftype[1][0][1]!r}), {ftype[1][1]}))'

    if base:
        lines += [
            'FIELDDEFS: Typesdict = {',
            # '    **base.FIELDDEFS,',
        ]
        for typ in keep:
            lines += [f'    {typ!r}: base.FIELDDEFS[{typ!r}],']
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
    if not any('np.ndarray' in x for x in lines):
        idx = lines.index('    import numpy as np')
        _ = lines.pop(idx)
        _ = lines.pop(idx)
    return '\n'.join(lines)
