# Quickstart

This walkthrough guides you from a clean checkout to a working Stream Deck (or simulator) layout. It covers the most common CLI options and demonstrates how to create a button that reacts to events.

## 1. Create and activate a virtual environment

```bash
git clone https://github.com/nschaetti/DeckPilot.git
cd DeckPilot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install -e .
```

## 2. Inspect the provided configuration

Explore `config/config.toml` to understand how assets, plugins, and Stream Deck parameters are wired. The default configuration points to the example panels under `config/root` and ships with icons, fonts, and sounds.

## 3. Discover connected devices (or use the simulator)

First, list the hardware Stream Decks connected to your machine:

```bash
deckpilot devices
```

Use `--use-simulator` to list the virtual profiles defined under `config/simulators`. Each simulated device exposes the same metadata as the hardware, so you can prototype layouts without plugging a deck in:

```bash
deckpilot devices --use-simulator --simulator-config config/simulators/xl.toml
```

## 4. Launch DeckPilot

The `start` command wires everything together: it loads the TOML config, instantiates the panel registry, and enters the rendering loop.

```bash
deckpilot start \
  --config config/config.toml \
  --root config/root \
  --log-level INFO \
  --log-filter "type=WARNING|ERROR"
```

If you do not have a Stream Deck connected, enable the simulator and optionally open the GUI:

```bash
deckpilot start \
  --config config/config.toml \
  --root config/root \
  --use-simulator \
  --show-simulator
```

The CLI prints the currently mounted panels and any events dispatched by buttons. When using a real device you should see the icons defined in `config/icons` (for example `hello_button.png`) appear instantly.

## 5. Add your first button

Buttons live under `config/root` (or any nested panel directory). They are standard Python classes that inherit from `deckpilot.elements.Button` and override hook methods such as `on_item_pressed` or `on_periodic_tick`.

Create `config/root/my_button.py` with:

```python
from deckpilot.elements import Button
from deckpilot.utils import Logger


class HelloButton(Button):
    def on_item_pressed(self, key_index):
        Logger.inst().info("Launching OBS scene switch")
        self.parent.dispatch(source=self, data={"action": "obs.switch"})
        return super().on_item_pressed(key_index)
```

Register the new button inside `config/root/items.toml`:

```toml
[[items]]
name = "hello"
path = "my_button.py"
type = "button"
```

Reload DeckPilot (Ctrl+C then rerun `deckpilot start`) and the new button will appear next to the existing examples.

## 6. Tweak assets and sounds

Icons from `config/icons` and sounds from `config/sounds` are exposed through `deckpilot.core.AssetManager`. Update a button class with:

```python
def on_item_press(self, key_index):
    self.icon_active = self.am.get_icon("obs_live")
    self.am.play_sound("click")
    return super().on_item_pressed(key_index)
```

DeckPilot automatically reloads PNG/SVG assets when the manager is asked for them, so you can iterate quickly on graphics.

## 7. Troubleshooting

- Use `--log-level DEBUG` together with `--log-filter` (for example `"source=Panel.*"`) to see all event bus notifications.
- `deckpilot show --index 0` prints every property of a connected Stream Deck, which helps verify firmware versions and USB IDs.
- To keep the simulator window active while DeckPilot runs, pass `--show-simulator`—closing the window gracefully stops the CLI loop.
