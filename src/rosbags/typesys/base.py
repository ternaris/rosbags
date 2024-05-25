# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Types and helpers used by message definition converters."""

from __future__ import annotations

import keyword
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rosbags.interfaces.typing import Typesdict

    from .peg import Visitor


class TypesysError(Exception):
    """Parser error."""


def normalize_fieldname(name: str) -> str:
    """Normalize field name.

    Avoid collisions with Python keywords.

    Args:
        name: Field name.

    Returns:
        Normalized name.

    """
    if keyword.iskeyword(name):
        return f'{name}_'
    return name


def parse_message_definition(visitor: Visitor, text: str) -> Typesdict:
    """Parse message definition.

    Args:
        visitor: Visitor instance to use.
        text: Message definition.

    Returns:
        Parsetree of message.

    Raises:
        TypesysError: Message parsing failed.

    """
    try:
        rule = visitor.RULES['specification']
        pos = rule.skip_ws(text, 0)
        npos, trees = rule.parse(text, pos)
        assert npos == len(text), f'Could not parse: {text!r}'
        return visitor.visit(trees)  # type: ignore[return-value]
    except Exception as err:
        msg = f'Could not parse: {text!r}'
        raise TypesysError(msg) from err
