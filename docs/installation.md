# Installation

DeckPilot ships as a standard Python package and only needs a few native libraries that provide USB access (for the Stream Deck), Cairo rendering, and optional audio playback. Follow the steps below to prepare your workstation.

## Python requirements

- Python 3.10 or newer (the CI and Read the Docs builds use Python 3.11).
- `pip` >= 23.0 and `setuptools` >= 65.0.
- A virtual environment is highly recommended so DeckPilot and StreamDeck do not interfere with system packages.

## System packages

Install the dependencies that the `streamdeck` and `CairoSVG` wheels expect. The exact package names vary slightly between platforms:

- **Linux (Debian/Ubuntu):**

  ```bash
  sudo apt update
  sudo apt install libhidapi-libusb0 libusb-1.0-0-dev libcairo2-dev \
       libpango1.0-dev libgdk-pixbuf-2.0-0 ffmpeg
  ```

- **macOS** (using Homebrew):

  ```bash
  brew install hidapi cairo pango gdk-pixbuf ffmpeg
  ```

- **Windows**:
  - Install the latest [Visual C++ redistributable](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist).
  - Install the official [Stream Deck drivers](https://www.elgato.com/stream-deck).
  - `playsound` can use the default Windows media stack, so no extra audio libraries are required.

You only need OBS WebSocket if you use the OBS plugin. Follow the [official instructions](https://github.com/obsproject/obs-websocket) to enable it and keep the password in sync with `config/config.toml`.

## Install from PyPI (when released)

The package metadata is ready for PyPI. As soon as a release is published you will be able to install it with:

```bash
pip install deckpilot
```

## Install from source

Until a formal release is published, install straight from the repository:

```bash
git clone https://github.com/nschaetti/DeckPilot.git
cd DeckPilot
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install -e .
```

Verify the installation with:

```bash
deckpilot --help
deckpilot devices --use-simulator
```

## Optional components

- **Documentation build** – `pip install -r docs/requirements.txt` installs MkDocs and mkdocstrings for local docs builds.
- **Development tooling** – linting and formatting can be added with your preferred tools; `DeckPilot` ships without an opinionated dev extra.
- **Simulator profiles** – prebuilt simulator configurations live under `config/simulators`. Copy or modify these TOML files to emulate different hardware layouts.

## Upgrading

When running from source, pull the latest changes and reinstall the package in editable mode:

```bash
git pull origin main
pip install -e .
```

For pip-based installs use:

```bash
pip install --upgrade deckpilot
```
