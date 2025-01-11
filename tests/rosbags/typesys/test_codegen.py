# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Code Generator Tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rosbags.interfaces import Nodetype
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
