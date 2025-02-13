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
"""

# Imports
import argparse
import toml
from rich.console import Console
from rich.traceback import install

# Import the PanelRegistry class
from deckpilot import PanelRegistry, EventBus, DeckManager


# Load configuration
def load_config(config_path):
    return toml.load(config_path)
# end load_config


# Default traceback
install(show_locals=True)

# Create console
console = Console()

# Argument parser
parser = argparse.ArgumentParser(description='StreamDeck Controller')
parser.add_argument(
    '-c',
    '--config',
    type=str,
    required=False,
    default="~/.config/DeckPilot/config.tom",
    help='Path to the configuration file'
)
parser.add_argument(
    '-r',
    '--root',
    type=str,
    required=False,
    default="config/root",
    help='Path to the root panel'
)
args = parser.parse_args()

# Load the configuration
config = load_config(args.config)
console.log(config)

# Configuration of the Stream Deck
STREAMDECK_BRIGHTNESS = config['streamdeck']['brightness']
STREAMDECK_DEVICE_INDEX = config['streamdeck'].get('device_index', None)
STREAMDECK_SERIAL_NUMBER = config['streamdeck'].get('serial_number', None)

# Event bus
event_bus = EventBus()

# Create DeckManager
deck_manager = DeckManager(event_bus)

# Configuration of the panels
registry = PanelRegistry(args.root, event_bus, deck_manager.renderer)
registry.print_structure()


# Main
if __name__ == "__main__":
    # Init Deck
    deck_manager.init_deck(
        STREAMDECK_SERIAL_NUMBER,
        STREAMDECK_DEVICE_INDEX,
        STREAMDECK_BRIGHTNESS
    )

    # Main loop
    deck_manager.main()
# end if

