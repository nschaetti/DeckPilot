"""deckpilot.core.deck_manager module for DeckPilot.
"""


# Imports
import json
import logging
import signal
import socket
import threading
import time

# Import the DeviceManager from the simulator or the real hardware
from deckpilot.utils import Logger
from deckpilot.comm import event_bus, EventType, context
from deckpilot.comm.external_commands import (
    DEFAULT_COMMAND_HOST,
    DEFAULT_COMMAND_PORT,
    EchoCommand,
    ExternalCommandMessage,
    PongResponse,
    PushAckResponse,
    PushCommand,
)
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
        self._command_server: socket.socket | None = None
        self._command_host = DEFAULT_COMMAND_HOST
        self._command_port = DEFAULT_COMMAND_PORT

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

            # Start external command socket
            self._start_external_command_listener()

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

    def _start_external_command_listener(self) -> None:
        """Launch the socket listener for external commands."""
        if self._command_server is not None:
            return
        # end if
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._command_host, self._command_port))
            server.listen()
        except OSError as exc:
            Logger().inst().error(f"Failed to start external command socket: {exc}")
            return
        # end try
        self._command_server = server
        threading.Thread(
            target=self._accept_external_commands,
            daemon=True
        ).start()
        Logger().inst().info(
            f"Listening for external commands on {self._command_host}:{self._command_port}"
        )
    # end def _start_external_command_listener

    def _accept_external_commands(self) -> None:
        """Accept incoming socket connections."""
        while self._command_server:
            try:
                client, address = self._command_server.accept()
            except OSError:
                break
            # end try
            threading.Thread(
                target=self._handle_external_client,
                args=(client, address),
                daemon=True
            ).start()
        # end while
    # end def _accept_external_commands

    def _handle_external_client(self, client: socket.socket, address) -> None:
        """Handle an external command client connection."""
        with client:
            try:
                raw_text = self._recv_line(client)
            except OSError:
                return
            # end try
            if not raw_text:
                return
            # end if
            try:
                payload = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                Logger().inst().warning(f"Invalid JSON from {address}: {exc}")
                return
            # end try
            try:
                message = ExternalCommandMessage.from_dict(payload)
            except ValueError as exc:
                Logger().inst().warning(f"Invalid external command from {address}: {exc}")
                return
            # end try
            response = self._build_external_response(message)
            if response is not None:
                try:
                    client.sendall((response.to_json() + "\n").encode("utf-8"))
                except OSError as exc:
                    Logger().inst().warning(f"Failed to send response to {address}: {exc}")
            # end if
        # end with
    # end def _handle_external_client

    @staticmethod
    def _recv_line(sock: socket.socket) -> str:
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
    # end def _recv_line

    def _build_external_response(self, message: ExternalCommandMessage) -> ExternalCommandMessage | None:
        """Return a response for well-known command types."""
        if isinstance(message, EchoCommand):
            return PongResponse(echo=message.payload.get("message"))
        # end if
        if isinstance(message, PushCommand):
            success, error = self._handle_push_command(message)
            return PushAckResponse(
                key=message.key,
                duration=message.duration,
                success=success,
                error=error
            )
        return None
    # end def _build_external_response

    def _handle_push_command(self, command: PushCommand) -> tuple[bool, str | None]:
        """Schedule a simulated key press."""
        deck = self.deck
        if deck is None:
            return False, "Stream Deck not initialized"
        try:
            key_count = deck.key_count()
        except Exception as exc:
            Logger().inst().error(f"Unable to get key count: {exc}")
            return False, "Unable to determine key count"
        if command.key >= key_count:
            return False, f"Key {command.key} out of range (max {key_count - 1})"

        threading.Thread(
            target=self._simulate_key_press,
            args=(command.key, command.duration),
            daemon=True
        ).start()
        return True, None
    # end def _handle_push_command

    def _simulate_key_press(self, key: int, duration: float) -> None:
        """Trigger a key press/release pair for the specified duration."""
        Logger().inst().info(f"Simulating key #{key} press for {duration} seconds")
        try:
            self._key_change_callback(self.deck, key, True)
            time.sleep(duration)
            self._key_change_callback(self.deck, key, False)
        except Exception as exc:
            Logger().inst().error(f"Failed to simulate key press: {exc}")
    # end def _simulate_key_press

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
        if self._command_server:
            try:
                self._command_server.close()
            except OSError:
                pass
            self._command_server = None

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
