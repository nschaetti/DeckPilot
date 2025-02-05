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
import logging
import threading
import signal
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Import the PanelRegistry class
from deckpilot import PanelRegistry, render_panel, EventBus, DeckManager


# Configuration de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
def load_config(config_path):
    return toml.load(config_path)
# end load_config

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

# Configuration of the Stream Deck
STREAMDECK_BRIGHTNESS = config['streamdeck']['brightness']
STREAMDECK_DEVICE_INDEX = config['streamdeck'].get('device_index', None)
STREAMDECK_SERIAL_NUMBER = config['streamdeck'].get('serial_number', None)

# Event bus
event_bus = EventBus()

# Create DeckManager
deck_manager = DeckManager(event_bus)

# Configuration of the panels
registry = PanelRegistry(args.root, event_bus)
registry.print_structure()


# Main
if __name__ == "__main__":
    # Capture signal interrupt
    signal.signal(signal.SIGINT, signal_handler)

    # Get StreamDeck(s)
    streamdecks = DeviceManager().enumerate()
    logging.info(f"Found {len(streamdecks)} Stream Deck(s).")

    # Find the specific StreamDeck
    deck = None
    if STREAMDECK_SERIAL_NUMBER:
        for d in streamdecks:
            if d.get_serial_number() == STREAMDECK_SERIAL_NUMBER:
                deck = d
                break
            # end if
        # end for
    elif STREAMDECK_DEVICE_INDEX is not None and 0 <= STREAMDECK_DEVICE_INDEX < len(streamdecks):
        deck = streamdecks[STREAMDECK_DEVICE_INDEX]
    # end if

    # Error if no StreamDeck found
    if deck is None:
        logging.error("No matching StreamDeck found.")
        exit(1)
    # end if

    # Open the specific StreamDeck
    if deck.is_visual():
        # Open the StreamDeck
        deck.open()
        deck.reset()

        # Log
        logging.info(
            f"Opened '{deck.deck_type()}' "
            f"device (serial number: '{deck.get_serial_number()}', "
            f"fw: '{deck.get_firmware_version()}')"
        )

        # Set the brightness
        deck.set_brightness(STREAMDECK_BRIGHTNESS)

        # Set the initial panel
        deck.current_panel = registry.root

        # Render the root panel
        render_panel(deck, registry.root)

        # Update the keys
        # for key in range(deck.key_count()):
        #     update_key_image(deck, key, False)
        # end for

        # Set the key callback
        deck.set_key_callback(key_change_callback)

        # Start the key event listener
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
            # end try
        # end for
    # end if

# end if

