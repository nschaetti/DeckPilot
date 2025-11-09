# Copyright (C) 2025  Nils Schaetti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# deckpilot/cli.py
from typing import Tuple, Any, Dict, Optional, Sequence

# Imports
import signal
import threading
from contextlib import contextmanager, suppress
from pathlib import Path

import toml
import typer
from rich.console import Console
from rich.table import Table
from rich.traceback import install

from deckpilot.utils import setup_logger, Logger
from deckpilot.elements import PanelRegistry
from deckpilot.core import DeckManager, AssetManager
from deckpilot.comm import context
from deckpilot.plugins import PluginManager


# Install rich traceback
install(show_locals=True)


# New app
app = typer.Typer()
console = Console()


# Load configuration
def load_config(config_path: Path) -> dict[str, Any]:
    """Load the DeckPilot configuration file.

    Args:
        config_path (Path): Path to the TOML configuration.

    Returns:
        dict[str, Any]: Parsed configuration dictionary.
    """
    return toml.load(config_path)


# end def load_config
# Setup configuration
def setup_config(
        config_path: Path,
        logger: Logger
) -> tuple[dict[str, Any], Any, Any, Any]:
    """Load and register the configuration.

    Args:
        config_path (Path): Path to the DeckPilot configuration file.
        logger (Logger): Rich logger used for status messages.

    Returns:
        tuple[dict[str, Any], Any, Any, Any]: Configuration dictionary along
        with StreamDeck serial number, device index, and brightness.
    """
    # Load the configuration
    logger.info(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    context.register("config", config)
    logger.debug(f"Configuration: {config}")

    # Configuration of the Stream Deck
    streamdeck_brightness = config['streamdeck']['brightness']
    streamdeck_device_index = config['streamdeck'].get('device_index', None)
    streamdeck_serial_number = config['streamdeck'].get('serial_number', None)

    # Both device_index and serial_number cannot be none
    if streamdeck_device_index is None and streamdeck_serial_number is None:
        raise typer.BadParameter(
            "At least one of --device-index or --serial-number must be provided.",
            param_hint="--device-index or --serial-number"
        )
    # end if

    # Debugging
    logger.info(f"StreamDeck brightness: {streamdeck_brightness}")
    logger.info(f"StreamDeck device index: {streamdeck_device_index}")
    logger.info(f"StreamDeck serial number: {streamdeck_serial_number}")

    return config, streamdeck_serial_number, streamdeck_device_index, streamdeck_brightness
# end def setup_config


# end def setup_config
def setup_asset_manager(
        config: Dict[str, Any]
) -> AssetManager:
    """Instantiate and register the AssetManager.

    Args:
        config (dict[str, Any]): Loaded DeckPilot configuration.

    Returns:
        AssetManager: Configured asset manager instance.
    """
    asset_manager = AssetManager(
        icons_directory=config['assets'].get('icons_directory', None),
        fonts_directory=config['assets'].get('fonts_directory', None),
        sounds_directory=config['assets'].get('sounds_directory', None),
    )
    context.register("asset_manager", asset_manager)
    return asset_manager
@contextmanager
def _deck_session(deck, logger: Logger):
    """Ensure a deck is opened while accessing its properties."""
    opened_here = False
    try:
        need_open = True
        if hasattr(deck, "is_open"):
            with suppress(Exception):
                need_open = not deck.is_open()
        if need_open:
            deck.open()
            opened_here = True
        yield
    finally:
        if opened_here:
            with suppress(Exception):
                deck.close()


def _safe_get(deck, getter, description: str, fallback, logger: Logger):
    """
    Invoke a getter and fall back gracefully on failure.
    """
    try:
        return getter()
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Failed to read {description} for '{deck.deck_type()}': {exc}")
        return fallback


def _resolve_simulator_config(
        use_simulator: bool,
        simulator_config: Optional[Path],
        logger: Logger
) -> Optional[Path]:
    """
    Validate simulator CLI args and fallback to default config if needed.

    Args:
        use_simulator (bool): Whether to use the simulator.
        simulator_config (Path | None): Path to the simulator config.
        logger (Logger): Rich logger used for status messages.

    Returns:
        Configured simulator config path.
    """
    if simulator_config and not use_simulator:
        raise typer.BadParameter(
            "--simulator-config requires --use-simulator",
            param_hint="--simulator-config"
        )
    # end if

    resolved = simulator_config
    default_sim_config = Path("config/simulators/original.toml")
    if use_simulator and resolved is None and default_sim_config.exists():
        resolved = default_sim_config
        logger.info(f"Defaulting to simulator config: {resolved}")
    # end if

    return resolved
# end def _resolve_simulator_config


def _enumerate_stream_decks(
        use_simulator: bool,
        simulator_config: Optional[Path]
) -> Sequence[Any]:
    """
    Enumerate Stream Decks either from hardware or the simulator.
    """
    if use_simulator:
        from deckpilot.simulator.switcher import (
            DeviceManager as SimulatorDeviceManager,
            use_simulator as configure_simulator,
        )

        configure_simulator(True, config_path=str(simulator_config) if simulator_config else None)
        manager = SimulatorDeviceManager()
    else:
        from StreamDeck.DeviceManager import DeviceManager as HardwareDeviceManager
        manager = HardwareDeviceManager()
    # end if

    return manager.enumerate()
# end def _enumerate_stream_decks


def _format_bool(value: bool) -> str:
    """Return a short yes/no string for table output."""
    return "Yes" if value else "No"
# end def _format_bool


# end def setup_asset_manager
@app.command()
def start(
        config: Path = typer.Option(help="Chemin vers le fichier de configuration."),
        root: Path = typer.Option("config/root", help="Chemin vers le panneau racine."),
        log_level: str = typer.Option("INFO", help="Niveau de logging : DEBUG, INFO, WARNING, ERROR"),
        use_simulator: bool = typer.Option(False, help="Use the Stream Deck simulator instead of hardware"),
        show_simulator: bool = typer.Option(
            False,
            help="Display and interact with the virtual Stream Deck window (requires --use-simulator)",
        ),
        simulator_config: Optional[Path] = typer.Option(
            None,
            help="Path to a simulator configuration file (TOML). Requires --use-simulator.",
        ),
) -> None:
    """Start the DeckPilot CLI entry point.

    Args:
        config (Path): Path to the DeckPilot configuration file.
        root (Path): Root panel directory.
        log_level (str): Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
        use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
        show_simulator (bool): Whether to launch the visual simulator window (requires --use-simulator).
        simulator_config (Path | None): Optional simulator configuration file.
    """
    if show_simulator and not use_simulator:
        raise typer.BadParameter("--show-simulator requires --use-simulator", param_hint="--show-simulator")
    # end if

    # Setup logger
    logger = setup_logger(level=log_level)

    # Load the configuration
    config, sd_serial, sd_index, sd_brightness = setup_config(
        config_path=config,
        logger=logger
    )

    # Set up the assert manager
    setup_asset_manager(config)

    # Get simulator config
    resolved_sim_config = _resolve_simulator_config(
        use_simulator=use_simulator,
        simulator_config=simulator_config,
        logger=logger,
    )

    # Create DeckManager with simulator option
    deck_manager = DeckManager(
        use_simulator=use_simulator,
        simulator_config=resolved_sim_config,
    )
    context.register("deck_manager", deck_manager)

    # Configuration of the panels
    registry = PanelRegistry(root, deck_manager.renderer)
    context.register("registry", registry)

    # Load plugins
    plugins_root = Path(context.config.get('plugins', {}).get('directory', "plugins"))
    plugin_manager = PluginManager(
        plugins_root=plugins_root,
        panel_registry=registry,
        deck_manager=deck_manager,
        config=context.config,
    )
    plugin_manager.discover_and_load()
    context.register("plugin_manager", plugin_manager)

    # Init Deck
    deck_manager.init_deck(
        serial_number=sd_serial,
        device_index=sd_index,
        brightness=sd_brightness
    )

    clock_tick_interval = config['general'].get('clock_tick_interval', 2)
    hidden_clock_tick_interval = config['general'].get('hidden_clock_tick_interval', 1)

    def run_deck_loop():
        deck_manager.main(
            clock_tick_interval=clock_tick_interval,
            hidden_clock_tick_interval=hidden_clock_tick_interval
        )
    # end def run_deck_loop

    if use_simulator and show_simulator:
        logger.info("Showing Stream Deck simulator window")
        from deckpilot.simulator.gui import launch_simulator

        def _request_shutdown():
            logger.info("Simulator window closed, shutting down DeckPilot")
            signal.raise_signal(signal.SIGINT)

        deck_thread = threading.Thread(target=run_deck_loop, daemon=True)
        deck_thread.start()

        gui = launch_simulator(
            deck_manager.deck,
            start_thread=False,
            on_close=_request_shutdown
        )
        logger.info("Simulator GUI launched")
        gui.run()
    else:
        run_deck_loop()
# end def start


@app.command()
def devices(
        log_level: str = typer.Option("INFO", help="Niveau de logging : DEBUG, INFO, WARNING, ERROR"),
        use_simulator: bool = typer.Option(False, help="Use the Stream Deck simulator instead of hardware"),
        simulator_config: Optional[Path] = typer.Option(
            None,
            help="Path to a simulator configuration file (TOML). Requires --use-simulator.",
        ),
) -> None:
    """
    List all Stream Deck devices detected by DeckPilot.

    Args:
        log_level (str): Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
        use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
        simulator_config (Path | None): Optional simulator configuration file.
    """
    logger = setup_logger(level=log_level)
    resolved_sim_config = _resolve_simulator_config(use_simulator, simulator_config, logger)

    # Get stream decks
    decks = _enumerate_stream_decks(use_simulator, resolved_sim_config)
    if not decks:
        logger.warning("No Stream Deck devices detected.")
        return
    # end if

    table = Table(title="Detected Stream Deck devices")
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Type", style="bold")
    table.add_column("Serial")
    table.add_column("Firmware")
    table.add_column("Visual", justify="center")
    table.add_column("Connected", justify="center")
    table.add_column("Keys", justify="right")
    table.add_column("Layout", justify="center")

    for idx, deck in enumerate(decks):
        with _deck_session(deck, logger):
            rows, cols = _safe_get(deck, deck.key_layout, "key layout", (0, 0), logger)
            table.add_row(
                str(idx),
                deck.deck_type(),
                _safe_get(deck, deck.get_serial_number, "serial number", "Unknown", logger),
                _safe_get(deck, deck.get_firmware_version, "firmware version", "Unknown", logger),
                _format_bool(_safe_get(deck, deck.is_visual, "visual capability", False, logger)),
                _format_bool(_safe_get(deck, deck.connected, "connection state", False, logger)),
                str(_safe_get(deck, deck.key_count, "key count", 0, logger)),
                f"{rows}×{cols}",
            )
    # end for

    console.print(table)
# end def devices


@app.command()
def show(
        index: Optional[int] = typer.Option(
            None,
            "--index",
            "-i",
            help="Device index as shown by the `devices` command.",
        ),
        serial: Optional[str] = typer.Option(
            None,
            "--serial",
            "-s",
            help="Stream Deck serial number (alternative to --index).",
        ),
        log_level: str = typer.Option("INFO", help="Niveau de logging : DEBUG, INFO, WARNING, ERROR"),
        use_simulator: bool = typer.Option(False, help="Use the Stream Deck simulator instead of hardware"),
        simulator_config: Optional[Path] = typer.Option(
            None,
            help="Path to a simulator configuration file (TOML). Requires --use-simulator.",
        ),
) -> None:
    """
    Display properties of a single Stream Deck device.
    """
    if (index is None and serial is None) or (index is not None and serial is not None):
        raise typer.BadParameter("Provide either --index or --serial (but not both).")

    logger = setup_logger(level=log_level)
    resolved_sim_config = _resolve_simulator_config(use_simulator, simulator_config, logger)
    decks = _enumerate_stream_decks(use_simulator, resolved_sim_config)

    if not decks:
        logger.warning("No Stream Deck devices detected.")
        raise typer.Exit(code=1)
    # end if

    target_deck = None
    target_index = -1

    if index is not None:
        if index < 0 or index >= len(decks):
            raise typer.BadParameter(f"Index {index} is out of range (found {len(decks)} devices).", param_hint="--index")
        target_deck = decks[index]
        target_index = index
    else:
        for idx, deck in enumerate(decks):
            with _deck_session(deck, logger):
                deck_serial = _safe_get(deck, deck.get_serial_number, "serial number", None, logger)
            if deck_serial == serial:
                target_deck = deck
                target_index = idx
                break
        # end for
        if target_deck is None:
            raise typer.BadParameter(f"No Stream Deck with serial '{serial}' found.", param_hint="--serial")
    # end if

    default_key_format = {
        "size": (0, 0),
        "format": "?",
        "flip": (False, False),
        "rotation": 0,
    }
    with _deck_session(target_deck, logger):
        layout_rows, layout_cols = _safe_get(target_deck, target_deck.key_layout, "key layout", (0, 0), logger)
        key_format = _safe_get(
            target_deck,
            target_deck.key_image_format,
            "key image format",
            default_key_format,
            logger
        )
        serial_number = _safe_get(target_deck, target_deck.get_serial_number, "serial number", "Unknown", logger)
        device_id = _safe_get(target_deck, target_deck.id, "device id", "Unknown", logger)
        firmware = _safe_get(target_deck, target_deck.get_firmware_version, "firmware version", "Unknown", logger)
        vendor_id = _safe_get(target_deck, target_deck.vendor_id, "vendor id", None, logger)
        product_id = _safe_get(target_deck, target_deck.product_id, "product id", None, logger)
        connected = _safe_get(target_deck, target_deck.connected, "connection state", False, logger)
        visual = _safe_get(target_deck, target_deck.is_visual, "visual capability", False, logger)
        key_count = _safe_get(target_deck, target_deck.key_count, "key count", 0, logger)

    vendor_str = hex(vendor_id) if vendor_id is not None else "Unknown"
    product_str = hex(product_id) if product_id is not None else "Unknown"

    details = Table(show_header=False, title=f"Stream Deck #{target_index}")
    details.add_row("Deck type", target_deck.deck_type())
    details.add_row("Serial number", serial_number)
    details.add_row("Device ID", device_id)
    details.add_row("Firmware", firmware)
    details.add_row("Vendor ID", vendor_str)
    details.add_row("Product ID", product_str)
    details.add_row("Connected", _format_bool(connected))
    details.add_row("Visual", _format_bool(visual))
    details.add_row("Key count", str(key_count))
    details.add_row("Key layout", f"{layout_rows}×{layout_cols}")
    details.add_row("Key image size", f"{key_format['size'][0]}×{key_format['size'][1]} px")
    details.add_row("Key image format", key_format['format'])
    details.add_row("Key image flip", f"{key_format['flip'][0]} / {key_format['flip'][1]}")
    details.add_row("Key image rotation", f"{key_format['rotation']}°")

    console.print(details)
# end def show
