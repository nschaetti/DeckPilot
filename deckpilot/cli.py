"""
 ██████╗ ███████╗ ██████╗██╗  ██╗██████╗ ██╗      ██████╗ ██╗████████╗
██╔════╝ ██╔════╝██╔════╝██║  ██║██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
██║  ███╗█████╗  ██║     ███████║██║  ██║██║     ██║   ██║██║   ██║
██║   ██║██╔══╝  ██║     ██╔══██║██║  ██║██║     ██║   ██║██║   ██║
╚██████╔╝███████╗╚██████╗██║  ██║██████╔╝███████╗╚██████╔╝██║   ██║
 ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═╝   ╚═╝

DeckPilot - A customizable interface for your Stream Deck.
Licensed under the GNU General Public License v3.0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

For a copy of the GNU GPLv3, see <https://www.gnu.org/licenses/>.

deckpilot.cli module for DeckPilot.
"""
from getpass import fallback_getpass
# deckpilot/cli.py
from typing import Tuple, Any, Dict, Optional, Sequence

# Imports
import json
import socket
import signal
import threading
from contextlib import contextmanager, suppress
from pathlib import Path

import toml
import typer
import yaml
from rich.console import Console
from rich.pretty import Pretty
from rich.table import Table
from rich.traceback import install

from deckpilot.utils import setup_logger, Logger
from deckpilot.elements import PanelRegistry
from deckpilot.core import DeckManager, AssetManager
from deckpilot.comm import context
from deckpilot.comm.external_commands import (
    DEFAULT_COMMAND_HOST,
    DEFAULT_COMMAND_PORT,
    EchoCommand,
    ExternalCommandMessage,
    PushCommand,
)
from deckpilot.plugins import PluginManager
from deckpilot.plugins.base import PluginMetadata


# Install rich traceback
install(show_locals=True)


# New app
app = typer.Typer()
console = Console()

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "deckpilot" / "config.toml"
DEFAULT_PLUGIN_DIR = Path.home() / ".config" / "deckpilot" / "plugins"
config_app = typer.Typer(
    help="Inspect and modify DeckPilot configuration files.",
    invoke_without_command=True
)
app.add_typer(config_app, name="config")
shell_app = typer.Typer(help="Send commands to DeckPilot's external control socket.")
app.add_typer(shell_app, name="shell")


def _build_logger(
        level: str,
        filters: Sequence[str]
) -> Logger:
    """Helper to configure the shared logger with CLI validation.

    Args:
        level (str): Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
        filters (list[str]): Optional regex filters applied to log level/source/message.

    Returns:
        Logger: Shared logger instance.
    """
    try:
        return setup_logger(level=level, filters=list(filters) or None)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--log-filter") from exc
    # end try
# end _build_logger


# Load configuration
def load_config(
        config_path: Path
) -> dict[str, Any]:
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
# end def setup_asset_manager


@contextmanager
def _deck_session(
        deck
):
    """Ensure a deck is opened while accessing its properties."""
    opened_here = False
    try:
        need_open = True
        if hasattr(deck, "is_open"):
            with suppress(Exception):
                need_open = not deck.is_open()
            # end with
        # end if
        if need_open:
            deck.open()
            opened_here = True
        # end if
        yield
    finally:
        if opened_here:
            with suppress(Exception):
                deck.close()
            # end with
        # end if
    # end try
# end _deck_session


def _safe_get(
        deck,
        getter,
        description: str,
        fallback,
        logger: Logger
):
    """
    Invoke a getter and fall back gracefully on failure.

    Args:
        deck (Deck): Stream Deck instance.
        getter (Callable): Getter function.
        description (str): Description of the getter.
        fallback: Fallback value if getter fails.
        logger (Logger): Rich logger used for status messages.
    """
    try:
        return getter()
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Failed to read {description} for '{deck.deck_type()}': {exc}")
        return fallback
    # end try
# end def _safe_get


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
    """Enumerate Stream Decks either from hardware or the simulator.

    Args:
        use_simulator (bool): Whether to use the simulator.
        simulator_config (Path | None): Path to the simulator config.
_enumerate_stream_decks
    Returns:
        List[Deck]: List of detected Stream Deck devices.
    """
    if use_simulator:
        from deckpilot.simulator import (
            DeviceManager as SimulatorDeviceManager,
            use_simulator as configure_simulator,
        )
        configure_simulator(use_sim=True, config_path=str(simulator_config) if simulator_config else None)
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


def _ensure_config_path(config_path: Path, is_default: bool) -> Path:
    """Validate that a configuration file exists before accessing it."""
    if config_path.exists():
        return config_path
    # end if
    if is_default:
        console.print(f"[red]Default configuration file not found: {config_path}[/red]")
        raise typer.Exit(code=1)
    # end if
    raise typer.BadParameter(
        message=f"Configuration file '{config_path}' not found.",
        param_hint="--path"
    )
# end def _ensure_config_path


def _config_path_from_ctx(
        ctx: typer.Context,
        override: Optional[Path]
) -> tuple[Path, bool]:
    if override is not None:
        return override, False
    # end if
    if ctx.obj and "config_path" in ctx.obj:
        return ctx.obj["config_path"], ctx.obj.get("is_default_path", True)
    # end if
    return DEFAULT_CONFIG_PATH, True
# end def _config_path_from_ctx


def _print_config(config_path: Path) -> None:
    """Pretty-print a configuration file."""
    config = load_config(config_path)
    console.print(f"[bold]Configuration file:[/bold] {config_path}")
    console.print(Pretty(config, expand_all=True))
# end def _print_config


def _split_key_path(key_path: str) -> list[str]:
    parts = [segment.strip() for segment in key_path.split(".") if segment.strip()]
    if not parts:
        raise typer.BadParameter("Configuration key cannot be empty.", param_hint="key")
    # end if
    return parts
# end def _split_key_path


def _get_nested_value(config: dict, key_path: list[str]):
    current = config
    for key in key_path:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(key)
        # end if
        current = current[key]
    # end for
    return current
# end def _get_nested_value


def _get_parent_and_key(config: dict, key_path: list[str]) -> tuple[dict, str]:
    if len(key_path) == 1:
        return config, key_path[0]
    # end if
    parent = _get_nested_value(config, key_path[:-1])
    if not isinstance(parent, dict):
        raise KeyError(key_path[-1])
    # end if
    return parent, key_path[-1]
# end def _get_parent_and_key


def _coerce_value(raw_value: str, reference_value: Any):
    if isinstance(reference_value, bool):
        lowered = raw_value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        raise typer.BadParameter(
            message=f"Cannot convert '{raw_value}' to boolean.",
            param_hint="value"
        )
    if isinstance(reference_value, int) and not isinstance(reference_value, bool):
        try:
            return int(raw_value)
        except ValueError as exc:
            raise typer.BadParameter(
                message=f"Cannot convert '{raw_value}' to integer.",
                param_hint="value"
            ) from exc
    if isinstance(reference_value, float):
        try:
            return float(raw_value)
        except ValueError as exc:
            raise typer.BadParameter(
                message=f"Cannot convert '{raw_value}' to float.",
                param_hint="value"
            ) from exc
    if isinstance(reference_value, (list, dict)):
        raise typer.BadParameter(
            message="Editing list or table values via CLI is not supported.",
            param_hint="value"
        )
    return raw_value
# end def _coerce_value


def _load_plugin_metadata(manifest: Path) -> PluginMetadata:
    """Read plugin metadata from a manifest file."""
    with manifest.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    # end with
    return PluginMetadata.from_dict(payload)
# end def _load_plugin_metadata


def _send_external_command(
        command: ExternalCommandMessage,
        host: str,
        port: int,
        timeout: float = 5.0
) -> dict[str, Any]:
    """Send an external command message and return the parsed JSON response."""
    payload = (command.to_json() + "\n").encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as conn:
            conn.sendall(payload)
            raw_response = _receive_line(conn)
    except OSError as exc:
        raise RuntimeError(f"Unable to reach DeckPilot at {host}:{port}: {exc}") from exc
    if not raw_response:
        raise RuntimeError("Connection closed without a response.")
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response: {exc}") from exc
# end def _send_external_command


def _receive_line(sock: socket.socket) -> str:
    """Read a single newline-terminated line from the socket."""
    buffer = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer.extend(chunk)
        if b"\n" in chunk:
            break
    if not buffer:
        return ""
    line, *_ = buffer.split(b"\n", 1)
    return line.decode("utf-8").strip()
# end def _receive_line


# end def setup_asset_manager
@app.command()
def start(
        config: Path = typer.Option(
            DEFAULT_CONFIG_PATH,
            help="Chemin vers le fichier de configuration."
        ),
        root: Path = typer.Option("config/root", help="Chemin vers le panneau racine."),
        log_level: str = typer.Option("INFO", help="Niveau de logging : DEBUG, INFO, WARNING, ERROR"),
        log_filter: list[str] = typer.Option(
            (),
            "--log-filter",
            "-lf",
            help="Filtre regex pour les logs (ex: 'type=INFO|WARNING,source=Panel.*'). Répéter pour combiner.",
            show_default=False,
        ),
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
        log_filter (list[str]): Optional regex filters applied to log level/source/message.
        use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
        show_simulator (bool): Whether to launch the visual simulator window (requires --use-simulator).
        simulator_config (Path | None): Optional simulator configuration file.
    """
    if show_simulator and not use_simulator:
        raise typer.BadParameter("--show-simulator requires --use-simulator", param_hint="--show-simulator")
    # end if

    # Setup logger
    logger = _build_logger(log_level, log_filter)

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
        # end def

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
    # end if
# end def start


@app.command()
def devices(
        log_level: str = typer.Option("INFO", help="Logging level : DEBUG, INFO, WARNING, ERROR"),
        log_filter: list[str] = typer.Option(
            (),
            "--log-filter",
            "-lf",
            help="Regex filter for the logs (ex: 'type=INFO|WARNING,source=Panel.*'). Répéter pour combiner.",
            show_default=False,
        ),
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
        log_filter (list[str]): Optional regex filters applied to log level/source/message.
        use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
        simulator_config (Path | None): Optional simulator configuration file.
    """
    logger = _build_logger(log_level, log_filter)
    resolved_sim_config = _resolve_simulator_config(
        use_simulator=use_simulator,
        simulator_config=simulator_config,
        logger=logger
    )

    # Get stream decks
    decks = _enumerate_stream_decks(
        use_simulator=use_simulator,
        simulator_config=resolved_sim_config
    )
    if not decks:
        logger.warning("No Stream Deck devices detected.")
        return
    # end if

    # Create table
    table = Table(title="Detected Stream Deck devices")
    table.add_column("Index", justify="right", style="cyan")        # Index
    table.add_column("Type", style="bold")                          # Type
    table.add_column("Serial")                                             # Serial
    table.add_column("Firmware")                                           # Firmware
    table.add_column("Visual", justify="center")                    # Visual
    table.add_column("Connected", justify="center")                 # Connected
    table.add_column("Keys", justify="right")                       # Keys
    table.add_column("Layout", justify="center")                    # Layout

    # For each deck
    for idx, deck in enumerate(decks):
        with _deck_session(deck):
            rows, cols = _safe_get(
                deck=deck,
                getter=deck.key_layout,
                description="key layout",
                fallback=(0, 0),
                logger=logger
            )
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
        # end with
    # end for

    console.print(table)
# end def devices


@app.command()
def plugins(
        path: Path = typer.Option(
            DEFAULT_PLUGIN_DIR,
            "--path",
            "-p",
            help=f"Directory containing DeckPilot plugins. Defaults to {DEFAULT_PLUGIN_DIR}",
        ),
) -> None:
    """Display the list of plugins located in the given directory."""
    plugins_root = Path(path).expanduser()
    if not plugins_root.exists():
        console.print(f"[red]Plugin directory {plugins_root} does not exist.[/red]")
        raise typer.Exit(code=1)
    # end if

    discovered: list[tuple[PluginMetadata, Path]] = []
    skipped: list[str] = []
    for entry in sorted(plugins_root.iterdir()):
        if not entry.is_dir():
            continue
        # end if
        manifest = entry / "plugin.yaml"
        if not manifest.exists():
            skipped.append(entry.name)
            continue
        # end if
        try:
            metadata = _load_plugin_metadata(manifest)
        except Exception as exc:  # pragma: no cover - CLI feedback only
            console.print(f"[red]Failed to load {manifest}: {exc}[/red]")
            continue
        # end try
        discovered.append((metadata, entry))
    # end for

    if not discovered:
        console.print(f"[yellow]No plugins found in {plugins_root}.[/yellow]")
    else:
        table = Table(title=f"Plugins in {plugins_root}")
        table.add_column("Name", style="bold")
        table.add_column("Version", style="cyan")
        table.add_column("Entry Point")
        table.add_column("Directory")
        table.add_column("Description")
        for metadata, directory in discovered:
            table.add_row(
                metadata.name,
                metadata.version,
                metadata.entry_point,
                str(directory),
                metadata.description or "N/A",
            )
        console.print(table)
    # end if

    if skipped:
        skipped_dirs = ", ".join(sorted(skipped))
        console.print(f"[yellow]Skipped directories without plugin.yaml: {skipped_dirs}[/yellow]")
    # end if
# end def plugins


@shell_app.command("echo")
def shell_echo(
        message: str = typer.Argument(
            "PING",
            help="Message to send with the echo command."
        ),
        host: str = typer.Option(
            DEFAULT_COMMAND_HOST,
            "--host",
            help=f"Host for the DeckPilot command socket (default: {DEFAULT_COMMAND_HOST})."
        ),
        port: int = typer.Option(
            DEFAULT_COMMAND_PORT,
            "--port",
            help=f"Port for the DeckPilot command socket (default: {DEFAULT_COMMAND_PORT})."
        ),
) -> None:
    """Send an ECHO external command to the DeckPilot socket."""
    cmd = EchoCommand(message=message)
    try:
        response_payload = _send_external_command(cmd, host, port)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    response = ExternalCommandMessage.from_dict(response_payload)
    console.print(Pretty(response.to_dict(), expand_all=True))
# end def shell_echo


@shell_app.command("push")
def shell_push(
        key: int = typer.Argument(
            ...,
            help="Key index to simulate."
        ),
        duration: float = typer.Option(
            2.0,
            "--duration",
            "-d",
            help="Duration in seconds to hold the key before releasing."
        ),
        host: str = typer.Option(
            DEFAULT_COMMAND_HOST,
            "--host",
            help=f"Host for the DeckPilot command socket (default: {DEFAULT_COMMAND_HOST})."
        ),
        port: int = typer.Option(
            DEFAULT_COMMAND_PORT,
            "--port",
            help=f"Port for the DeckPilot command socket (default: {DEFAULT_COMMAND_PORT})."
        ),
) -> None:
    """Simulate a key press via the DeckPilot external command socket."""
    if key < 0:
        raise typer.BadParameter("Key index must be >= 0.", param_hint="key")
    if duration <= 0:
        raise typer.BadParameter("Duration must be greater than 0.", param_hint="--duration")
    cmd = PushCommand(key=key, duration=duration)
    try:
        response_payload = _send_external_command(cmd, host, port)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    response = ExternalCommandMessage.from_dict(response_payload)
    console.print(Pretty(response.to_dict(), expand_all=True))
# end def shell_push


@config_app.callback()
def config_main(
        ctx: typer.Context,
        path: Optional[Path] = typer.Option(
            None,
            "--path",
            "-p",
            help=f"Configuration file to display. Defaults to {DEFAULT_CONFIG_PATH}",
            show_default=False,
        ),
) -> None:
    """Display the configuration when invoked without a subcommand."""
    config_path = path or DEFAULT_CONFIG_PATH
    ctx.obj = {
        "config_path": config_path,
        "is_default_path": path is None
    }
    if ctx.invoked_subcommand:
        return
    # end if
    resolved = _ensure_config_path(config_path, path is None)
    _print_config(resolved)
# end def config_main


@config_app.command("get")
def config_get(
        ctx: typer.Context,
        key: str = typer.Argument(..., help="Dotted path to the configuration value (ex: streamdeck.brightness)."),
        path: Optional[Path] = typer.Option(
            None,
            "--path",
            "-p",
            help=f"Configuration file to inspect. Defaults to {DEFAULT_CONFIG_PATH}",
            show_default=False,
        ),
) -> None:
    """Get the value of a configuration entry."""
    config_path, is_default = _config_path_from_ctx(ctx, path)
    resolved = _ensure_config_path(config_path, is_default)
    config = load_config(resolved)
    key_path = _split_key_path(key)
    try:
        value = _get_nested_value(config, key_path)
    except KeyError as exc:
        raise typer.BadParameter(
            message=f"Configuration key '{key}' not found.",
            param_hint="key"
        ) from exc
    console.print(Pretty(value, expand_all=True))
# end def config_get


@config_app.command("set")
def config_set(
        ctx: typer.Context,
        key: str = typer.Argument(..., help="Dotted path to the configuration value to change."),
        value: str = typer.Argument(..., help="New value (converted to the current type when possible)."),
        path: Optional[Path] = typer.Option(
            None,
            "--path",
            "-p",
            help=f"Configuration file to edit. Defaults to {DEFAULT_CONFIG_PATH}",
            show_default=False,
        ),
) -> None:
    """Set the value of a configuration entry."""
    config_path, is_default = _config_path_from_ctx(ctx, path)
    resolved = _ensure_config_path(config_path, is_default)
    config = load_config(resolved)
    key_path = _split_key_path(key)
    try:
        parent, final_key = _get_parent_and_key(config, key_path)
    except KeyError as exc:
        raise typer.BadParameter(
            message=f"Configuration key '{key}' not found.",
            param_hint="key"
        ) from exc
    if final_key not in parent:
        raise typer.BadParameter(
            message=f"Configuration key '{key}' not found.",
            param_hint="key"
        )
    reference_value = parent[final_key]
    coerced_value = _coerce_value(value, reference_value)
    parent[final_key] = coerced_value
    with resolved.open("w", encoding="utf-8") as fp:
        toml.dump(config, fp)
    console.print(f"[green]Updated[/green] {key} = {coerced_value!r} in {resolved}")
# end def config_set


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
        log_level: str = typer.Option("INFO", help="Log level : DEBUG, INFO, WARNING, ERROR"),
        log_filter: list[str] = typer.Option(
            (),
            "--log-filter",
            "-lf",
            help="Regex filter for the log (ex: 'type=INFO|WARNING,source=Panel.*'). Répéter pour combiner.",
            show_default=False,
        ),
        use_simulator: bool = typer.Option(False, help="Use the Stream Deck simulator instead of hardware"),
        simulator_config: Optional[Path] = typer.Option(
            None,
            help="Path to a simulator configuration file (TOML). Requires --use-simulator.",
        ),
) -> None:
    """
    Display properties of a single Stream Deck device.

    Args:
        index (int | None): Device index as shown by the `devices` command.
        serial (str | None): Stream Deck serial number (alternative to --index).
        log_level (str): Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
        log_filter (list[str]): Optional regex filters applied to log level/source/message.
        use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
        simulator_config (Path | None): Optional simulator configuration file.
    """
    if (index is None and serial is None) or (index is not None and serial is not None):
        raise typer.BadParameter("Provide either --index or --serial (but not both).")
    # end if

    logger = _build_logger(log_level, log_filter)
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
            raise typer.BadParameter(
                message=f"Index {index} is out of range (found {len(decks)} devices).",
                param_hint="--index"
            )
        # end if
        target_deck = decks[index]
        target_index = index
    else:
        for idx, deck in enumerate(decks):
            with _deck_session(deck):
                deck_serial = _safe_get(deck, deck.get_serial_number, "serial number", None, logger)
            # end with
            if deck_serial == serial:
                target_deck = deck
                target_index = idx
                break
            # end if
        # end for
        if target_deck is None:
            raise typer.BadParameter(
                message=f"No Stream Deck with serial '{serial}' found.",
                param_hint="--serial"
            )
        # end if
    # end if

    default_key_format = {
        "size": (0, 0),
        "format": "?",
        "flip": (False, False),
        "rotation": 0,
    }

    # Enter deck session
    with _deck_session(target_deck):
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
    # end with

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
