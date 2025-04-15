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
import time
import threading
from StreamDeck.DeviceManager import DeviceManager

from .deck_renderer import DeckRenderer


# Logger
logger = logging.getLogger(__name__)


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
        self._serial_number = None
        self._brightness = 30
        self._initialized = False
        self._key_change_callbacks = list()
        self._renderer = DeckRenderer(self)
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

    @property
    def renderer(self):
        """
        Get the DeckRenderer.
        """
        return self._renderer
    # end renderer

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

    # Initialize the Stream Deck
    def init_deck(self, serial_number, device_index, brightness):
        """
        Initialize the Stream Deck device.

        Args:
        - serial_number (str): Serial number of the Stream Deck.
        - device_index (int): Index of the Stream Deck.
        - brightness (int): Brightness level for the Stream Deck.
        """
        # Capture signal interrupt
        signal.signal(signal.SIGINT, self._signal_handler)

        # Get StreamDeck(s)
        self._streamdecks = DeviceManager().enumerate()
        logger.info(f"Found {len(self._streamdecks)} Stream Deck(s).")

        # Set brightness
        self._brightness = brightness

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
            logger.info("ERROR: No matching StreamDeck found!")
            exit(1)
        # end if

        # Set deck
        self._deck = deck
        self._serial_number = serial_number
        self._initialized = True

        # Log
        logger.info(f"Selected StreamDeck {self._deck} initialized.")
    # end init_deck

    # Main
    def main(
            self,
            clock_tick_interval=2
    ):
        """
        Main method for the DeckManager class.

        Args:
        - brightness (int): Brightness level for the Stream Deck.
        """
        # Open the specific StreamDeck
        if self.deck.is_visual():
            # Check that the StreamDeck is initialized
            if not self.initialized:
                logger.info("ERROR: StreamDeck not initialized!")
                return
            # end if

            # Open the StreamDeck
            self.deck.open()

            # Clear the deck
            self._renderer.reset_deck()

            # Log
            logger.info(
                f"Opened '{self.deck.deck_type()}' "
                f"device (serial number: '{self.deck.get_serial_number()}', "
                f"fw: '{self.deck.get_firmware_version()}')"
            )

            # Set the brightness
            self.deck.set_brightness(self._brightness)

            # Launch initialized event
            self._event_bus.publish("initialized", (self.deck,))

            # Set the key callback
            self.deck.set_key_callback(self._key_change_callback)

            # Start the periodic event thread
            if clock_tick_interval > 0:
                threading.Thread(target=self._send_periodic_event, args=(clock_tick_interval,), daemon=True).start()
            # end if

            # Start the key event listener
            for t in threading.enumerate():
                try:
                    t.join()
                except RuntimeError:
                    pass
                # end try
            # end for
        else:
            logger.info("ERROR: No visual StreamDeck found!")
        # end if
    # end main

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    # Update touch image
    def _update_key_image(deck, key, state):
        """
        Update touch image

        Args:
        - deck: StreamDeck - the StreamDeck
        - key: int - the key index
        - state: bool - the key state
        """
        # Log
        logger.info(f"Deck {deck.id()} Key {key} = {state}")
    # end _update_key_image

    # Callback for periodic event
    def _send_periodic_event(self, interval):
        """
        Callback for periodic event

        Args:
        - interval: int - the interval in seconds
        """
        while True:
            # Publish the periodic event
            self._event_bus.publish("periodic", ())

            # Sleep
            time.sleep(interval)
        # end while
    # end _send_periodic_event

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
        # logger.info(f"Deck {deck.id()} Key {key} = {state}")

        # Publish the key change event
        self._event_bus.publish("key_change", (deck, key, state))
    # end _key_change_callback

    # Signal handler
    def _signal_handler(self, sig, frame):
        """
        Signal handler for the Stream Deck.
        """
        # Send the exit event
        self._event_bus.publish("exit", ())

        # Close the StreamDeck
        logger.info(f"Closing StreamDeck {self._deck.get_serial_number()}...")
        self._deck.reset()
        self._deck.close()

        # Log
        logger.info("Exiting...")
        exit(0)
    # end _signal_handler

    # endregion PRIVATE METHODS

# end DeckManager

