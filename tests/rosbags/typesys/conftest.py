# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Test Fixturest."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import numpy as np
import pytest

if sys.version_info >= (3, 12):  # pragma: no cover
    from typing import override
else:  # pragma: no cover
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def _comparable() -> Generator[None, None, None]:
    """Make messages containing numpy arrays comparable.

    Notes:
        This solution is necessary as numpy.ndarray is not directly patchable.

    """
    frombuffer = np.frombuffer

    class CNDArray:
        """Comparable ndarray."""

        def __init__(self, child: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]) -> None:
            self.child = child

        @override
        def __eq__(self, other: object) -> bool:
            if isinstance(other, CNDArray):
                other = other.child
            assert isinstance(other, np.ndarray)
            return bool(
                np.equal(
                    self.child,
                    cast('np.ndarray[tuple[int, ...], np.dtype[np.uint8]]', other),
                ).all(),
            )

        def byteswap(self) -> CNDArray:
            return CNDArray(self.child.byteswap())

        def __deepcopy__(self, _: dict[str, object]) -> CNDArray:
            return self

        def __getattr__(self, name: str) -> object:
            return cast('object', getattr(self.child, name))

        def __hash__(self) -> int:
            return hash(self.child)

    def wrap_frombuffer(mem: bytes, dtype: str, count: int, offset: int) -> CNDArray:
        return CNDArray(frombuffer(mem, dtype=dtype, count=count, offset=offset))

    with patch.object(np, 'frombuffer', wrap_frombuffer):
        yield
