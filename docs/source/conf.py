# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# end if

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DeckPilot'
copyright = '2025, Nils Schaetti'
author = 'Nils Schaetti'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = False
napoleon_use_rtype = False
autodoc_typehints = 'none'
napoleon_type_aliases = {
    'AssetManager': 'deckpilot.core.asset_manager.AssetManager',
    'Logger': 'deckpilot.utils.logger.Logger',
    'KeyDisplay': 'deckpilot.core.deck_renderer.KeyDisplay',
}

autodoc_mock_imports = [
    'StreamDeck',
    'StreamDeck.DeviceManager',
    'StreamDeck.ImageHelpers',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageOps',
    'PIL.ImageTk',
    'playsound',
    'cairosvg',
    'toml',
    'yaml',
    'rich',
    'rich.console',
    'rich.table',
    'rich.traceback',
    'rich.text',
    'rich.tree',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
