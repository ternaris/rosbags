# Copyright 2020 - 2024 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Rosbags typing."""

from typing import Any, Dict, List, Literal, Protocol, Tuple, Union

Basetype = Union[str, Tuple[Literal['string'], int]]
Constdefs = List[Tuple[str, str, Any]]
Fielddesc = Union[
    Tuple[Literal[1], Basetype],
    Tuple[Literal[2], str],
    Tuple[Literal[3, 4], Tuple[Union[Tuple[Literal[1], Basetype], Tuple[Literal[2], str]], int]],
]
Fielddefs = List[Tuple[str, Fielddesc]]
Typesdict = Dict[str, Tuple[Constdefs, Fielddefs]]


class Typestore(Protocol):
    """Type storage."""

    FIELDDEFS: Typesdict
