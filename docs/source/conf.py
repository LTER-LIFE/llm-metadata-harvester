# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))   # repo root so "mypackage" is importable

project = 'LLM metadata harvester'
copyright = '2025, Zehao Lu, Thijs van der Plas'
author = 'Zehao Lu, Thijs van der Plas'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',   # generate API docs from docstrings
    'sphinx.ext.napoleon',  # Google / NumPy style docstrings
    'sphinx.ext.viewcode',  # add links to source
    'sphinx.ext.intersphinx', # link to Python / other projects
    'sphinx.ext.autosummary', # optional: generate summary stubs
]

# Example autodoc defaults
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': False,
    'show-inheritance': True,
}

templates_path = ['_templates']
exclude_patterns = []
autosummary_generate = True  # generate autosummary pages

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
