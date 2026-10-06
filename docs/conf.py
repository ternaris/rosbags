# Copyright 2020-2026 Ternaris
# SPDX-License-Identifier: Apache-2.0
"""Sphinx Configuration."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from sphinx import addnodes

if TYPE_CHECKING:
    from docutils.nodes import document  # type: ignore[import-untyped]
    from sphinx.application import Sphinx

project = 'Rosbags'
copyright = '2020-2026, Ternaris'  # noqa: A001
author = 'Ternaris'

autoapi_python_use_implicit_namespaces = True
autodoc_typehints = 'description'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx_rtd_theme',
]

html_theme = 'sphinx_rtd_theme'


def resolve_store_references(_app: Sphinx, doctree: document) -> None:
    """Resolve inherited message aliases to their defining store's class."""
    for node in doctree.findall(addnodes.pending_xref):
        module = node.get('py:module') or ''
        target = node.get('reftarget') or ''
        if (
            node.get('refdomain') != 'py'
            or not module.startswith('rosbags.typesys.stores.')
            or '__msg__' not in target
            or '.' in target
        ):
            continue
        message = getattr(import_module(module), target, None)
        if isinstance(message, type):
            node['reftarget'] = f'{message.__module__}.{message.__qualname__}'
            node['refspecific'] = False


def setup(app: Sphinx) -> dict[str, bool]:
    """Configure message type cross-reference resolution."""
    app.connect('doctree-read', resolve_store_references)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
