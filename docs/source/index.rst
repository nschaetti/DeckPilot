.. DeckPilot documentation master file, created by
   sphinx-quickstart on Sat Nov  8 13:05:57 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

DeckPilot Documentation
=======================

DeckPilot is a fully customizable Stream Deck controller that renders dynamic
panels, buttons, sounds, and automations from declarative TOML definitions. The
project ships with a CLI entrypoint, a rendering pipeline, and a component
registry designed to be extended through Python plugins.

Get started by installing the package in editable mode, configuring your assets
under ``config/``, and launching the CLI:

.. code-block:: bash

   pip install -e .
   deckpilot start --config config/config.toml --root config/root

API Reference
-------------

The following sections are generated automatically from the source code using
``sphinx-apidoc`` and the Google-style docstrings that accompany the DeckPilot
modules.

.. toctree::
   :maxdepth: 2
   :caption: Reference

   modules
