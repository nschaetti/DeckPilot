# DeckPilot 🚀

DeckPilot is a customizable interface for your **Stream Deck**, allowing you to assign scripts to buttons, manage multiple windows, and navigate through hierarchical categories. Designed for flexibility and efficiency, DeckPilot helps streamline your workflow by providing intuitive controls and automation.

## Features

- ✅ Assign scripts or commands to buttons
- ✅ Multi-window support for better organization
- ✅ Category-based navigation with nested levels
- ✅ Customizable UI for enhanced usability
- ✅ Open-source and extensible

## Installation

### Requirements
- Python 3.8+
- Dependencies listed in `requirements.txt`

### Setup
```sh
# Clone the repository
git clone https://github.com/yourusername/DeckPilot.git
cd DeckPilot

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

```sh
# Launch DeckPilot with your configuration
python -m deckpilot --config config/config.toml
```

- `--root` lets you point to a different panel directory (defaults to `config/root`).
- `--log-level` controls verbosity (`DEBUG`, `INFO`, etc.).
- `--log-filter` lets you combine regex-based filters on the log level, class source, or message. Repeat the option to OR multiple rules (e.g. `--log-filter "type=INFO|WARNING" --log-filter "source=Panel.*"`).

### Advanced logging filters

You can now narrow the CLI output to the signals you care about directly from the command line:

```sh
python -m deckpilot start \
  --config config/config.toml \
  --log-level DEBUG \
  --log-filter "type=WARNING|ERROR" \
  --log-filter "source=Panel.*"
```

Each `--log-filter` takes comma- or semicolon-separated `key=regex` pairs (`type`, `source`, or `message`). The above example only prints warnings/errors and, additionally, any message originating from classes whose name starts with `Panel`.

### Simulator mode

DeckPilot ships with a full software simulator so you can build layouts
without hardware:

```sh
python -m deckpilot \
  --config config/config.toml \
  --use-simulator \
  --show-simulator
```

- `--use-simulator` swaps the hardware driver for a virtual Stream Deck.
- `--show-simulator` opens an interactive window representing the deck.
- `--simulator-config` points to a TOML file under `config/simulators`
  (Original, Mini, XL, or Virtual Pad). The default is the 3 × 5 Stream Deck
  Original profile.

## Contributing
Contributions are welcome! Feel free to submit issues, feature requests, or pull requests.

## License
[MIT License](LICENSE)

---

🚀 **DeckPilot** – Take full control of your Stream Deck experience!
