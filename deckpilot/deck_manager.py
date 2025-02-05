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
import logging
import signal
import threading
from StreamDeck.DeviceManager import DeviceManager


# Configuration de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DeckManager:
    """
    Manages the Stream Deck device.
    """

    def __init__(self, event_bus):
        """
        Constructor for the DeckManager class.
        """
        self._event_bus = event_bus
        self._deck = None
        self._streamdesks = None
        self._initialized = False
        self._key_change_callbacks = list()
    # end __init__

    # region PROPERTIES

    @property
    def deck(self):
        """
        Get the Stream Deck device.
        """
        return self._deck
    # end deck

    @property
    def initialized(self):
        """
        Get the initialization status.
        """
        return self._initialized
    # end initialized

    # endregion PROPERTIES

    # region PUBLIC METHODS

    def add_key_change_callback(self, callback):
        """
        Add a key change callback.

        Args:
        - callback (function): The callback function.
        """
        self._key_change_callbacks.append(callback)
    # end add_key_change_callback

    def init_deck(self, serial_number, device_index):
        """
        Initialize the Stream Deck device.
        """
        # Capture signal interrupt
        signal.signal(signal.SIGINT, self._signal_handler)

        # Get StreamDeck(s)
        self._streamdecks = DeviceManager().enumerate()
        logging.info(f"Found {len(self._streamdecks)} Stream Deck(s).")

        # Find the specific StreamDeck
        deck = None
        if serial_number:
            for d in self._streamdecks:
                if d.get_serial_number() == serial_number:
                    deck = d
                    break
                # end if
            # end for
        elif device_index is not None and 0 <= device_index < len(self._streamdecks):
            deck = self._streamdecks[device_index]
        # end if

        # Error if no StreamDeck found
        if deck is None:
            logging.error("No matching StreamDeck found.")
            exit(1)
        # end if

        # Set deck
        self._deck = deck
        self._initialized = True
    # end init_deck

    # Main
    def main(
            self,
            brightness
    ):
        """
        Main method for the DeckManager class.

        Args:
        - brightness (int): Brightness level for the Stream Deck.
        """
        # Open the specific StreamDeck
        if self.deck.is_visual():
            # Open the StreamDeck
            self.deck.open()
            self.deck.reset()

            # Log
            logging.info(
                f"Opened '{self.deck.deck_type()}' "
                f"device (serial number: '{self.deck.get_serial_number()}', "
                f"fw: '{self.deck.get_firmware_version()}')"
            )

            # Set the brightness
            self.deck.set_brightness(brightness)

            # Set the initial panel
            # self.deck.current_panel = registry.root

            # Render the root panel
            # render_panel(self.deck, registry.root)

            # Update the keys
            # for key in range(deck.key_count()):
            #     update_key_image(deck, key, False)
            # end for

            # Set the key callback
            self.deck.set_key_callback(self._key_change_callback)

            # Start the key event listener
            for t in threading.enumerate():
                try:
                    t.join()
                except RuntimeError:
                    pass
                # end try
            # end for
        # end if
    # end main

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    # Update touch image
    def _update_key_image(deck, key, state):
        """
        Update touche image

        Args:
        - deck: StreamDeck - the StreamDeck
        - key: int - the key index
        - state: bool - the key state
        """
        # Log
        logging.info(f"Deck {deck.id()} Key {key} = {state}")
    # end _update_key_image

    # Callback for state change of a key
    def _key_change_callback(self, deck, key, state):
        """
        Callback for state change of a key

        Args:
        - deck: StreamDeck - the StreamDeck
        - key: int - the key index
        - state: bool - the key state
        """
        # Log
        logging.info(f"Deck {deck.id()} Key {key} = {state}")

        # Publish the key change event
        self._event_bus.publish("key_change", (deck, key, state))
    # end _key_change_callback

    # Signal handler
    def _signal_handler(self, sig, frame):
        """
        Signal handler for the Stream Deck.
        """
        logging.info("Exiting...")
        for d in self._streamdecks:
            if d.get_serial_number() == self._serial_number:
                d.reset()
                break
            # end if
        # end for
        exit(0)
    # end _signal_handler

    # endregion PRIVATE METHODS

# end DeckManager

