"""Configuration file for the Sphinx documentation builder."""

import sys
from pathlib import Path

# Add the project root to the path so we can import the modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# -- Project information -------------------------------------------------
project = "Abstract"
copyright = "2024, Alex Thola"
author = "Alex Thola"
release = "1.0.0"

# -- General configuration ------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pathlib": ("https://docs.python.org/3/library/pathlib", None),
}

# Typehints settings
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# Source patterns
source_suffix = {
    ".rst": None,
    ".md": "myst_parser",
}

# Master document
master_doc = "index"

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output settings
html_theme = "sphinx_rtd_theme"
html_static_path = []
html_css_files = []

# -- Options for autodoc -------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Auto-generate summary tables
autosummary_generate = True

# Don't show type hints in the signature itself
autodoc_typehints = "description"

# Don't show "View page source" link
html_show_sourcelink = False

# -- Nitpicky mode -------------------------------------------------------
# Warn about all cross-references
nitpicky = True
nitpick_ignore = [
    ("py:class", "TypeVar"),
    ("py:class", "Generic"),
    ("py:class", "ABC"),
]
