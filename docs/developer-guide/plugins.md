# Creating Plugins

Plugins are the preferred way to ship reusable features such as OBS controls, productivity helpers, or corporate dashboards. The built-in plugin loader scans the directory defined in `[plugins]` (`config/config.toml`) and loads each subfolder that contains a `plugin.yaml` manifest.

## Directory layout

```text
plugins/
  myplugin/
    plugin.yaml
    plugin.py
    panel/
      items.toml
      buttons.py
    assets/
      icons/
```

`plugin.yaml` describes how the plugin should be instantiated. Example from `plugins/pomodoro`:

```yaml
# plugins/pomodoro/plugin.yaml
name: pomodoro
version: "1.0.0"
description: Timers and productivity tools for DeckPilot.
entry_point: plugins.pomodoro.plugin:PomodoroPlugin

panels:
  - id: pomodoro-panel
    name: pomodoro
    path: panel
    mount: root
    class: plugins.pomodoro.panel.pomodoro_panel:PomodoroPanel
    params:
      icon_inactive: pomodoro
      icon_pressed: pomodoro_pressed
      activated_sound: click
```

## Manifest fields

`name`
: Human-readable name shown in logs.

`entry_point`
: `module:Class` path to the plugin class.

`version` / `description`
: Metadata only; useful for debugging output.

`panels`
: List of `deckpilot.plugins.base.PluginPanelDefinition`. Each entry specifies the identifier, `path` relative to the plugin root, optional `class` to instantiate, mount target (usually `root`), and additional keyword arguments forwarded to the panel constructor.

`events`
: Optional list of `deckpilot.plugins.base.PluginEventHook`. They bind event bus topics to handler methods on the plugin class.

`config`
: Arbitrary plugin-specific configuration (exposed via `PluginContext.metadata`).

## Plugin classes

Create a class that inherits from `deckpilot.plugins.base.BasePlugin` and override `register`:

```python
from deckpilot.plugins.base import BasePlugin


class PomodoroPlugin(BasePlugin):
    def register(self) -> None:
        self.context.event_bus.subscribe(
            self,
            "pomodoro/complete",
            self._on_complete,
        )

    def _on_complete(self, payload):
        self.context.deck_manager.flash_keys()
```

`PluginContext` gives you access to the DeckManager, PanelRegistry, EventBus, global `config`, and plugin metadata. Use these services instead of importing modules directly when possible.

## Mount targets

Panels contributed by plugins specify a `mount` key. `root` attaches the panel as a top-level child. Any other value is interpreted as the name of a panel already registered in `PanelRegistry`. If the mount target does not exist you will see a warning in the CLI logs.

## Event hooks

Explicit hooks in `plugin.yaml` keep your `register` method tidy:

```yaml
events:
  - topic: "obs/scene"
    handler: "on_scene"
    once: false
```

The plugin manager resolves the handler attribute on your class and subscribes it to the specified topic. This is equivalent to calling `event_bus.subscribe` manually but easier to audit.

## Shipping assets

Plugins can ship their own icons, fonts, or sounds. Use `self.context.panel_registry.root.am` (or the globally registered asset manager via `context.asset_manager`) to load them. Keep assets inside the plugin directory and resolve them with `Path(self.context.base_path, "assets", "icons", "my_icon.png")` to avoid clashes with the main project.
