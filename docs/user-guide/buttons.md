# Buttons

Buttons convert Stream Deck key presses into Python logic. They are regular classes that inherit from `deckpilot.elements.Button` (defined in `deckpilot/elements/panel_nodes.py`) and override whichever hooks they need:

- `on_item_rendered` – return the initial `deckpilot.core.KeyDisplay` when the layout is drawn.
- `on_item_pressed` / `on_item_released` – react to key interactions. Return a `KeyDisplay` to update the icon/text or `None` to keep the previous frame.
- `on_periodic_tick` / `on_internal_periodic_tick` – handle timers (see [Automations](automations.md)). These methods receive a time index and count controlled by `[general]` in `config/config.toml`.
- `on_dispatch_received` – react to messages broadcast by the parent panel.

## Creating a button

```python
# config/root/hello_button.py
from deckpilot.elements import Button
from deckpilot.utils import Logger


class HelloButton(Button):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        self.icon_active = self.am.get_icon("hello_pressed")
        self.icon_inactive = self.am.get_icon("hello")

    def on_item_pressed(self, key_index):
        Logger.inst().info("Hello from key %s", key_index)
        self.parent.dispatch(self, {"message": "hello"})
        return super().on_item_pressed(key_index)
```

Register the new script inside `items.toml`:

```toml
[[items]]
name = "hello"
path = "hello_button.py"
type = "button"
```

## Using assets

All buttons receive `self.am` (an `deckpilot.core.AssetManager` instance). Use it to fetch icons, fonts, and sounds by name:

```python
display = KeyDisplay(
    icon=self.am.get_icon("obs_live"),
    text="LIVE",
    text_color=(255, 0, 0),
    font=self.am.get_font("barlow.otf", 18),
)

self.am.play_sound("click")
```

The asset manager automatically resolves `.png` and `.svg` files; SVGs are converted to PNG via CairoSVG and cached automatically.

## Logging and diagnostics

`deckpilot.utils.Logger` is a rich-aware logger that already knows how to colourise output inside the CLI. Call `Logger.inst().debug(...)` or `Logger.inst().event(...)` to emit structured traces that can later be filtered with `--log-filter`.

## Communicating with plugins

Buttons are often the glue that connects user actions to plugins.

- To invoke plugin code directly, import the plugin module or use services exposed via `deckpilot.plugins.PluginManager`.
- To broadcast generic events, publish to `deckpilot.comm.event_bus`.

```python
from deckpilot.comm import event_bus, EventType

event_bus.publish(EventType.PANEL_NEXT_PAGE, {"source": self})
```

## Dispatch examples

The `parent.dispatch` API is perfect for intra-panel coordination. For instance, a “scene select” button can notify the status indicator to refresh:

```python
class StatusIndicator(Button):
    def on_dispatch_received(self, source, data):
        if data.get("scene") == self.scene_name:
            self._active = True
        else:
            self._active = False
        return self.refresh()
```
