# DeckPilot Documentation

DeckPilot turns a Stream Deck (or the built-in simulator) into a fully scripted
control surface. Layouts, behaviors, and sounds are defined with TOML files and
Python classes, while plugins and the event bus let you automate complex
workflows such as OBS switching, Pomodoro timers, or custom dashboards.

## What you will find here

- **Installation** recipes for Linux, macOS, and Windows, including the system libraries that StreamDeck and CairoSVG depend on.
- A **Quickstart** path that goes from cloning the repository to pressing your first custom button and experimenting with the simulator.
- A **User Guide** that documents every configuration section, how pagination works inside panels, how to wire buttons to Python actions, and how to keep icons, fonts, and sounds organised.
- A **Developer Guide** describing the architecture, the event system, and the plugin contract so that you can extend DeckPilot safely.
- A fully cross-linked **API reference** generated from the codebase.

## TL;DR: launch DeckPilot fast

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
deckpilot start --config config/config.toml --root config/root --use-simulator --show-simulator
```
