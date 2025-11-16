# Architecture Overview

DeckPilot is intentionally split into small, testable layers. Understanding how they interact helps when you need to add a feature or diagnose a bug.

## High-level data flow

1. **CLI (`deckpilot/cli.py`)** parses the command line, loads configuration, and instantiates helpers such as the logger, asset manager, and plugin manager.
2. **DeckManager (`deckpilot/core/deck_manager.py`)** opens the Stream Deck hardware or simulator, listens for key events, and drives the render loop.
3. **PanelRegistry (`deckpilot/elements/panel_registry.py`)** builds the panel hierarchy from the `root` directory and keeps track of the active panel.
4. **Panel and Button classes (`deckpilot/elements/panel_nodes.py`)** render buttons, process presses, and respond to timers.
5. **Plugins (`plugins/*`)** contribute additional panels, listen to events, or call third-party APIs.
6. **Event bus (`deckpilot/comm/event_bus.py`)** lets all of the above publish and subscribe to structured events.

## CLI commands

The Typer-based CLI exposes three subcommands:

- `deckpilot start` — launches the full runtime. Accepts options for simulator usage, log filters, and the configuration paths.
- `deckpilot devices` — lists hardware or simulated decks. Useful for discovering device indices.
- `deckpilot show` — prints detailed metadata (serial number, firmware, key layout) for one deck.

The CLI also sets up the shared `deckpilot.utils.Logger` instance, which is injected into other components through `deckpilot.comm.context`.

## Core services

`DeckManager`
: Wraps the Stream Deck SDK and normalises simulator/hardware behaviour. It exposes `init_deck` (open device, set brightness) and `main` (rendering loop). Inside the loop it emits `EventType.KEY_CHANGED` and the periodic clock events.

`DeckRenderer`
: Resizes icons, composes text overlays, and writes pixel buffers back to the hardware. Buttons create `deckpilot.core.KeyDisplay` objects instead of dealing with PIL primitives directly.

`AssetManager`
: Caches icons, fonts, and sounds. SVG files are converted to PNG on demand via CairoSVG. Sounds are played asynchronously using `playsound` so the render loop remains responsive.

`context` (`deckpilot/comm/context.py`)
: A lightweight registry shared across modules (similar to a dependency container). The CLI records references to the configuration, asset manager, panel registry, deck manager, and plugin manager so other modules can access them without circular imports.

## Simulator

All Stream Deck APIs are abstracted behind `DeckManager` and the classes under `deckpilot/simulator`. The simulator mirrors key layout, button geometry, and image formats so you can run integration tests without hardware. Use `--use-simulator` to activate it and `--show-simulator` to embed the Tk GUI.

## Rendering pipeline

1. `PanelRegistry` subscribes to `EventType.KEY_CHANGED`.
2. When a key changes state, the registry forwards the event to the active `Panel`.
3. The panel calls the button hook, receives a `KeyDisplay`, and passes it to `DeckRenderer`.
4. `DeckRenderer` resolves icons/fonts via the asset manager and writes the resulting image buffer to the Stream Deck.

Plugins and panels are notified about lifecycle events (`INITIALIZED`, `PANEL_RENDERED`, `EXIT`) through the event bus, which keeps the renderer decoupled from business logic.
