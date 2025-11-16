# Configuration

DeckPilot reads two kinds of configuration files:

- `config/config.toml` — global settings such as which Stream Deck to use, where icons are stored, or how pagination behaves.
- `items.toml` files located in each panel directory — describe which buttons or nested panels live on the current page.

## Global configuration (`config/config.toml`)

The sample file included in the repository demonstrates every supported section. Use it as a template and version-control your changes alongside your custom panels. The excerpt below mirrors the default settings:

```toml
[streamdeck]
brightness = 30
device_index = 0

[general]
clock_tick_interval = 1
hidden_clock_tick_interval = 0

[assets]
icons_directory = "config/icons"
fonts_directory = "config/fonts"
sounds_directory = "config/sounds"

[plugins]
directory = "plugins"

[obs]
obs_host = "localhost"
obs_port = 4455
obs_password = "obspass1234##"
```

### Key sections

`[streamdeck]` controls which physical deck DeckPilot should open. You **must** set either `device_index` or `serial_number`.

| Key | Type | Description |
| --- | --- | --- |
| `brightness` | int | LED brightness in percent (0–100). |
| `device_index` | int | Index as printed by `deckpilot devices`. |
| `serial_number` | str | Optional serial number if you prefer a stable identifier. |

`[general]` exposes timing knobs that affect the periodic callbacks invoked on buttons/panels.

| Key | Type | Description |
| --- | --- | --- |
| `clock_tick_interval` | float | Interval (seconds) between `EventType.CLOCK_TICK` notifications. |
| `hidden_clock_tick_interval` | float | How often hidden panels receive `EventType.INTERNAL_CLOCK_TICK`. |

`[assets]` tells the `deckpilot.core.AssetManager` where to load icons, fonts, and sounds. Paths are relative to the repository root by default.

`[root]` customises pagination controls, for example which icon to display on “next page” buttons, margins, and the sound to play when a page is activated. These options are passed verbatim to `deckpilot.elements.Panel`.

`[plugins]` sets the location of third-party plugins. By default this points to `plugins` in the repository; point it to another directory to keep your custom plugins separate from upstream ones.

`[obs]` contains connection details that OBS-related buttons or plugins can reuse (host, port, password).

## Panel directories

The `root` directory referenced by `deckpilot start --root` contains:

- Python modules implementing buttons or panels.
- `items.toml` describing the order of the deck slots.
- Nested folders when a button needs to open a sub-panel (each nested folder contains its own `items.toml` and scripts).

Example layout:

```text
config/root/
  items.toml
  button_01.py
  hello_button.py
  media_panel/
    items.toml
    play_button.py
    pause_button.py
```

Every `[[items]]` entry in `items.toml` has three keys:

- `name` — unique identifier inside the panel, also shown in logs.
- `path` — relative path to the Python file implementing the class. For nested panels this is a folder name.
- `type` — either `"button"` for `deckpilot.elements.Button` subclasses or `"panel"` for nested `deckpilot.elements.Panel` definitions.

## Environment variables

DeckPilot does not currently read environment variables directly, but nothing prevents you from extending `config/config.toml` with your own sections and reading them from button code or plugins via `context.config`:

```toml
[myservice]
token = "${MYSERVICE_TOKEN}"
```

Use a templating step or `python-dotenv` in your launch scripts if you need to inject secrets securely.
