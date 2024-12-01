import autoed
import sys
import os
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('.'))

project = 'AutoED'
#copyright = '2024, Science and Technology Facilities Council (STFC)'
copyright = '2024, Marko Petrovic'
author = 'STFC'
version = autoed.__version__
release = autoed.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinx.ext.napoleon",
]

templates_path = ['_templates']
exclude_patterns = []

pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_context = {
  'display_github': True,
  'current_language': 'en',
  'current_version': "1.0",
  'myversions': [["1.0", "link to 1.0"], ["2.0", "link to 2.0"]],
  "github_user": "mpks",
  "github_repo": "autoed",
  "github_version": "master",
  "conf_py_path": "/docs/source/",
}

html_theme = 'sphinx_rtd_theme'
# html_theme = 'alabaster'
html_static_path = ['_static']
html_css_files = ['custom.css']
