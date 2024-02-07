# Copyright 2020-2023  Ternaris.
# SPDX-License-Identifier: Apache-2.0
"""Sphinx Configuration."""

project = 'Rosbags'
copyright = '2020-2023, Ternaris'
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
