"""deckpilot.core.deck_manager module for DeckPilot.
"""


# Imports
import logging
import signal
import time
import threading

# Import the DeviceManager from the simulator or the real hardware
from deckpilot.utils import Logger
from deckpilot.comm import event_bus, EventType, context
from .deck_renderer import DeckRenderer


class DeckManager:
    """
    Manages the Stream Deck device.
    """

    def __init__(self, use_simulator=False, simulator_config=None):
        """
        Constructor for the DeckManager class.
        
        Args:
            use_simulator (bool): Whether to use the Stream Deck simulator instead of hardware.
            simulator_config (Path | str | None): Optional simulator configuration file.
        """
        # Import the appropriate DeviceManager
        if use_simulator:
            from deckpilot.simulator.switcher import (
                DeviceManager as SimulatorDeviceManager,
                use_simulator as configure_simulator,
            )

            # Set up simulator
            configure_simulator(True, config_path=str(simulator_config) if simulator_config else None)
            message = "Using Stream Deck simulator"
            if simulator_config:
                message += f" (config: {simulator_config})"
            Logger().inst().info(message)
            self.DeviceManager = SimulatorDeviceManager
        else:
            from StreamDeck.DeviceManager import DeviceManager as HardwareDeviceManager
            Logger().inst().info("Using Stream Deck hardware")
            self.DeviceManager = HardwareDeviceManager
        # end if

        self._deck = None
        self._stream_decks = None
        self._serial_number = None
        self._brightness = 30
        self._initialized = False
        self._renderer = DeckRenderer(self)
        self._use_simulator = use_simulator

        # Callbacks
        self._key_change_callbacks = list()

    # end def __init__

    # region PROPERTIES

    @property
    def deck(self):
        """
        Get the Stream Deck device.
        """
        return self._deck

    # end def deck
    @property
    def initialized(self):
        """
        Get the initialization status.
        """
        return self._initialized

    # end def initialized
    @property
    def renderer(self):
        """
        Get the DeckRenderer.
        """
        return self._renderer

    # end def renderer
    # endregion PROPERTIES

    # region PUBLIC

    def add_key_change_callback(self, callback):
        """Add a key change function to the list of callbacks.
        
        Args:
            callback (function): The callback function.
        """
        self._key_change_callbacks.append(callback)

    # end def add_key_change_callback
    # Initialize the Stream Deck
    def init_deck(self, serial_number, device_index, brightness):
        """Initialize the Stream Deck device.
        
        :raise RuntimeError: If no matching Stream Deck is found.
        
        Args:
            serial_number (str): Serial number of the Stream Deck.
            device_index (int): Index of the Stream Deck.
            brightness (int): Brightness level for the Stream Deck.
        """
        # Capture signal interrupt
        signal.signal(signal.SIGINT, self._signal_handler)

        # Get StreamDeck(s)
        self._stream_decks = self.DeviceManager().enumerate()
        Logger().inst().info(f"Found {len(self._stream_decks)} Stream Deck(s).")
        Logger().inst().debug(f"StreamDecks found: {self._stream_decks}")

        # Set brightness
        self._brightness = brightness

        # Find the specific StreamDeck
        deck = None
        if serial_number:
            for d in self._stream_decks:
                if d.get_serial_number() == serial_number:
                    deck = d
                    break
                # end if
            # end for
        elif device_index is not None and 0 <= device_index < len(self._stream_decks):
            deck = self._stream_decks[device_index]

        # end if
        # Error if no StreamDeck found
        if deck is None:
            Logger().inst().fatal("ERROR: No matching StreamDeck found!")
            raise RuntimeError("No matching StreamDeck found!")

        # end if
        # Set deck
        self._deck = deck
        self._serial_number = serial_number
        self._initialized = True

        # Log
        Logger().inst().info(f"Selected StreamDeck {self._deck} initialized.")

    # end def init_deck
    # Main
    def main(
            self,
            clock_tick_interval=2,
            hidden_clock_tick_interval=1,
    ):
        """Main method for the DeckManager class.
        
        Args:
            clock_tick_interval (int): Interval for the periodic event in seconds.
            hidden_clock_tick_interval (int): Interval for the hidden tick event in seconds.
        """
        # Open the specific StreamDeck
        if self.deck.is_visual():
            # Check that the StreamDeck is initialized
            if not self.initialized:
                Logger().inst().info("ERROR: StreamDeck not initialized!")
                return

            # end if
            # Open the StreamDeck
            self.deck.open()

            # Clear the deck
            self._renderer.reset_deck()

            # Log
            Logger().inst().info(
                f"Opened '{self.deck.deck_type()}' "
                f"device (serial number: '{self.deck.get_serial_number()}', "
                f"fw: '{self.deck.get_firmware_version()}')"
            )

            # Set the brightness
            self.deck.set_brightness(self._brightness)

            # Launch initialized event
            event_bus.publish(EventType.INITIALIZED, (self.deck,))

            # Set the key callback
            self.deck.set_key_callback(self._key_change_callback)

            # Start the periodic event thread
            if clock_tick_interval > 0:
                threading.Thread(
                    target=self._send_periodic_event,
                    args=(clock_tick_interval,),
                    daemon=True
                ).start()

            # end if
            # Start the hidden tick event thread
            if hidden_clock_tick_interval > 0:
                threading.Thread(
                    target=self._send_hidden_periodic_event,
                    args=(hidden_clock_tick_interval,),
                    daemon=True
                ).start()

            # end if
            # Start the key event listener
            for t in threading.enumerate():
                try:
                    t.join()
                except RuntimeError:
                    pass
            # end for
        else:
            Logger().inst().info("ERROR: No visual StreamDeck found!")

        # end if
    # end def main
    
    # endregion PUBLIC

    # region PRIVATE

    # Update touch image
    def _update_key_image(deck, key, state):
        """Update touch image
        
        Args:
            deck (StreamDeck): the StreamDeck
            key (int): the key index
            state (bool): the key state
        """
        # Log
        Logger().inst().info(f"Deck {deck.id()} Key {key} = {state}")

    # end def _update_key_image
    # endregion PRIVATE

    # region EVENTS

    # Callback for periodic event
    def _send_periodic_event(self, interval):
        """
        Callback for periodic event

        Args:
        - interval: int - the interval in seconds
        """
        time_i = 0
        time_count = 0
        while True:
            Logger.inst().debugg(f"DeckManager: Sending periodic event")

            # Publish the periodic event
            event_bus.send_event(context.active_panel, EventType.CLOCK_TICK, data=(time_i, time_count))

            # Sleep
            time.sleep(interval)

            time_i += 1
            time_count += interval

        # end while
    # end def _send_periodic_event
    # Callback for periodic event
    def _send_hidden_periodic_event(self, interval: int):
        """Callback for periodic event
        
        Args:
            interval (int): int - the interval in seconds
        """
        time_i = 0
        time_count = 0
        while True:
            Logger.inst().debug(f"DeckManager: Sending hidden periodic event")

            # Publish the periodic event
            event_bus.publish(EventType.INTERNAL_CLOCK_TICK, data=(time_i, time_count))

            # Sleep
            time.sleep(interval)

            time_i += 1
            time_count += interval

        # end while
    # end def _send_hidden_periodic_event
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
        # Logger().inst().info(f"Deck {deck.id()} Key {key} = {state}")

        # Publish the key change event
        event_bus.publish(EventType.KEY_CHANGED, (deck, key, state))

    # end def _key_change_callback
    # Signal handler
    def _signal_handler(self, sig, frame):
        """
        Signal handler for the Stream Deck.
        """
        # Send the exit event
        event_bus.publish(EventType.EXIT, ())

        # Close the StreamDeck
        Logger().inst().info(f"Closing StreamDeck {self._deck.get_serial_number()}...")
        self._deck.reset()
        self._deck.close()

        # Log
        Logger().inst().info("Exiting...")
        exit(0)

    # end def _signal_handler
    # endregion EVENTS


# end class DeckManager
