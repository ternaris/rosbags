# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Code Generator Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from rosbags.interfaces import Nodetype
from rosbags.typesys import TypesysError
from rosbags.typesys.codegen import generate_python_code

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict


def test_generate_python_code() -> None:
    """Test python code generator."""
    defs: Typesdict = {'foo': ([], [('b', (Nodetype.BASE, ('bool', 0)))])}

    res = generate_python_code(defs)
    assert 'class foo:\n' in res

    res = generate_python_code(defs, 'empty')
    assert 'from . import empty' in res
    assert 'class foo:\n' not in res

    res = generate_python_code(defs, 'empty', add=('foo',))
    assert 'class foo:\n' in res

    res = generate_python_code(defs, 'empty', change=('foo',))
    assert 'class foo:\n' in res

    res = generate_python_code(defs, 'empty', keep=('bar',))
    assert 'bar = base.bar\n' in res


@pytest.mark.parametrize(
    ('c1', 'c2', 'f1', 'f2'),
    [
        ('class', 'class_', 'o1', 'o2'),
        ('o1', 'class', 'class_', 'o2'),
        ('o1', 'o2', 'class', 'class_'),
    ],
)
def test_reject_ambiguous_python_names(c1: str, c2: str, f1: str, f2: str) -> None:
    """Reject names that would overwrite each other in Python."""
    typesdict: Typesdict = {
        'foo': (
            [
                (c1, 'bool', True),
                (c2, 'bool', False),
            ],
            [
                (f1, (Nodetype.BASE, ('bool', 0))),
                (f2, (Nodetype.BASE, ('bool', 0))),
            ],
        )
    }
    with pytest.raises(TypesysError, match='conflicting Python names'):
        generate_python_code(typesdict)
