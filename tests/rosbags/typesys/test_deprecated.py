# Copyright 2020 - 2025 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Deprecated Interfaces Tests."""

import importlib

import pytest

from rosbags.typesys import register_types


def test_deprecated_register_types() -> None:
    """Test register_types warns about deprecation."""
    with pytest.deprecated_call():
        register_types({})


def test_deprecated_types_module() -> None:
    """Test register_types warns about deprecation."""
    with pytest.deprecated_call():
        _ = importlib.import_module('rosbags.typesys.types')
