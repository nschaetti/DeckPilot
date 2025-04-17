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

# Imports
import typer
import toml
from pathlib import Path
from rich.traceback import install

from deckpilot.utils.logger import setup_logger
from deckpilot.elements import PanelRegistry
from deckpilot.comm import EventBus
from deckpilot.core import DeckManager


# Install rich traceback
install(show_locals=True)


# New app
app = typer.Typer()


# Load configuration
def load_config(config_path):
    return toml.load(config_path)
# end load_config


@app.command()
def start(
        config: Path = typer.Option("config.yaml", help="Chemin vers le fichier de configuration."),
        root: Path = typer.Option("config/root", help="Chemin vers le panneau racine."),
        log_level: str = typer.Option("INFO", help="Niveau de logging : DEBUG, INFO, WARNING, ERROR")
) -> None:
    """
    Start the StreamDeck controller.

    :param config: Path to the configuration file
    :param root: Path to the root panel
    :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Setup logger
    logger = setup_logger(level=log_level)

    # Load the configuration
    logger.info(f"Loading configuration from {config}")
    config = load_config(config)
    logger.debug(f"Configuration: {config}")

    # Configuration of the Stream Deck
    streamdeck_brightness = config['streamdeck']['brightness']
    streamdeck_device_index = config['streamdeck'].get('device_index', None)
    streamdeck_serial_number = config['streamdeck'].get('serial_number', None)

    # Debugging
    logger.info(f"StreamDeck brightness: {streamdeck_brightness}")
    logger.info(f"StreamDeck device index: {streamdeck_device_index}")
    logger.info(f"StreamDeck serial number: {streamdeck_serial_number}")

    # Create DeckManager
    deck_manager = DeckManager()

    # Configuration of the panels
    registry = PanelRegistry(root, deck_manager.renderer)
    registry.print_structure()

    # Init Deck
    deck_manager.init_deck(
        streamdeck_serial_number,
        streamdeck_device_index,
        streamdeck_brightness
    )

    # Main loop
    deck_manager.main(config['general'].get('clock_tick_interval', 2))
# end start
