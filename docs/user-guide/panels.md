# Panels

Panels are the containers responsible for rendering an entire Stream Deck page. They hold buttons, manage pagination, and forward hardware events to the correct children. The default `config/root` shipped with DeckPilot exposes a single-level hierarchy, but the system supports arbitrarily deep trees of panels.

## Panel anatomy

Each panel is defined by two things:

1. A directory containing scripts and nested resources.
2. An `items.toml` file that specifies the order of `[[items]]` to display.

A minimal panel folder:

```text
media_panel/
  items.toml
  play_button.py
  stop_button.py
```

`items.toml` describes a grid of 15 entries (one per Stream Deck key on the Original). Each entry can be either a button or another panel:

```toml
# media_panel/items.toml
[[items]]
name = "play"
path = "play_button.py"
type = "button"

[[items]]
name = "tools"
path = "tools_panel"
type = "panel"
```

## Panel parameters

`deckpilot.elements.Panel` accepts many keyword arguments that you typically configure through the `[root]` section of `config/config.toml` or plugin metadata:

- `icon_inactive` / `icon_pressed` — icons for the “current panel” key.
- `next_page_bouton_*` and `previous_page_bouton_*` — icons, labels, and margins for pagination controls.
- `parent_bouton_*` — how to navigate back to a parent panel.
- `activated_sound` — optional sound file played when the panel becomes active.

You can override these per panel by subclassing `Panel` and passing custom parameters when instantiating it (see the Pomodoro plugin for a real example).

## Pagination and navigation

When a panel contains more than one “page worth” of entries, DeckPilot automatically wires the “previous” and “next” buttons described above. The current page number can be displayed in a button by reading `self.current_page` inside a panel or button class.

Navigation helpers are implemented inside `deckpilot.elements.Panel` using `deckpilot.core.DeckRenderer`. You rarely need to call them directly; instead you can trigger navigation from a button action:

```python
class BackButton(Button):
    def on_item_released(self, key_index):
        self.parent.go_parent_panel()  # jump to the parent panel
        return super().on_item_released(key_index)
```

## Dispatching messages

Panels expose a `dispatch` method that broadcasts a payload to every child. Buttons typically call `self.parent.dispatch(...)` and other items implement `on_dispatch_received` to react. This is often simpler than emitting custom event bus topics for intra-panel coordination.

## Rendering lifecycle

Panels delegate rendering to `deckpilot.core.DeckRenderer`. The typical flow is:

1. `deckpilot.core.DeckManager` receives `KEY_PRESSED` from the Stream Deck SDK.
2. The `deckpilot.elements.PanelRegistry` forwards the event to the active panel.
3. The panel calls the relevant `on_item_*` hook on the target button and updates the key image with the returned `deckpilot.core.KeyDisplay`.

Understanding this lifecycle helps when debugging why a key does not update: if your button returns `None` the renderer keeps the previous frame.
