"""
Stream Deck Simulator - StreamDeck Classes

This module provides simulated StreamDeck classes that mimic the behavior of the
real Stream Deck devices, allowing for automated testing without requiring
the physical hardware.
"""

import threading
import time
from enum import Enum


class ControlType(Enum):
    """
    Type of control, matching the real Stream Deck API.
    """
    KEY = 1
    DIAL = 2
    TOUCHSCREEN = 3


class StreamDeckSim:
    """
    Base class for simulated Stream Deck devices.
    This class mimics the behavior of the real Stream Deck base class.
    """

    KEY_COUNT = 0
    KEY_COLS = 0
    KEY_ROWS = 0

    KEY_PIXEL_WIDTH = 0
    KEY_PIXEL_HEIGHT = 0
    KEY_IMAGE_FORMAT = ""
    KEY_FLIP = (False, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Simulator"
    DECK_VISUAL = True

    def __init__(self, serial_number="SIM-000000"):
        """
        Creates a new simulated Stream Deck instance.

        Args:
            serial_number (str): Serial number for the simulated device.
        """
        self._serial_number = serial_number
        self._is_open = False
        self._connected = True
        self._brightness = 100
        self._key_states = [False] * self.KEY_COUNT
        self._key_images = [None] * self.KEY_COUNT
        
        # Callback for key state changes
        self.key_callback = None
        
        # Thread for simulating the device
        self._read_thread = None
        self._run_read_thread = False
        
        # Lock for thread safety
        self._lock = threading.RLock()

    def open(self):
        """
        Opens the simulated device for input/output.
        """
        self._is_open = True
        self._setup_reader(self._read)

    def close(self):
        """
        Closes the simulated device for input/output.
        """
        self._is_open = False
        self._setup_reader(None)

    def is_open(self):
        """
        Indicates if the simulated device is currently open and ready for use.

        Returns:
            bool: True if the device is open, False otherwise.
        """
        return self._is_open

    def connected(self):
        """
        Indicates if the simulated device is connected.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        return self._connected

    def id(self):
        """
        Returns a unique identifier for the simulated device.

        Returns:
            str: Unique identifier for the device.
        """
        return f"simulator-{self._serial_number}"

    def vendor_id(self):
        """
        Returns a simulated vendor ID.

        Returns:
            int: Simulated vendor ID.
        """
        return 0x0fd9  # Elgato vendor ID

    def product_id(self):
        """
        Returns a simulated product ID.

        Returns:
            int: Simulated product ID.
        """
        return 0x0060  # Default to original Stream Deck product ID

    def key_count(self):
        """
        Returns the number of keys on the simulated device.

        Returns:
            int: Number of keys.
        """
        return self.KEY_COUNT

    def key_layout(self):
        """
        Returns the key layout of the simulated device.

        Returns:
            tuple: (rows, columns) of the key layout.
        """
        return (self.KEY_ROWS, self.KEY_COLS)

    def key_image_format(self):
        """
        Returns the image format for the keys.

        Returns:
            dict: Dictionary describing the image format.
        """
        return {
            'size': (self.KEY_PIXEL_WIDTH, self.KEY_PIXEL_HEIGHT),
            'format': self.KEY_IMAGE_FORMAT,
            'flip': self.KEY_FLIP,
            'rotation': self.KEY_ROTATION,
        }

    def deck_type(self):
        """
        Returns the type of the simulated device.

        Returns:
            str: Type of the simulated device.
        """
        return self.DECK_TYPE

    def is_visual(self):
        """
        Indicates if the simulated device has a visual display.

        Returns:
            bool: True if the device has a visual display, False otherwise.
        """
        return self.DECK_VISUAL

    def reset(self):
        """
        Resets the simulated device, clearing all key images.
        """
        with self._lock:
            self._key_images = [None] * self.KEY_COUNT

    def set_brightness(self, percent):
        """
        Sets the brightness of the simulated device.

        Args:
            percent (int or float): Brightness percentage (0-100 or 0.0-1.0).
        """
        if isinstance(percent, float):
            percent = int(100.0 * percent)

        self._brightness = min(max(percent, 0), 100)

    def get_serial_number(self):
        """
        Returns the serial number of the simulated device.

        Returns:
            str: Serial number of the device.
        """
        return self._serial_number

    def get_firmware_version(self):
        """
        Returns a simulated firmware version.

        Returns:
            str: Simulated firmware version.
        """
        return "1.0.0"

    def set_key_callback(self, callback):
        """
        Sets the callback function for key state changes.

        Args:
            callback (function): Callback function to be called when a key state changes.
        """
        self.key_callback = callback

    def key_states(self):
        """
        Returns the current states of all keys.

        Returns:
            list: List of boolean values indicating the state of each key.
        """
        return self._key_states.copy()

    def set_key_image(self, key, image):
        """
        Sets the image for a key.

        Args:
            key (int): Index of the key.
            image (bytes): Image data for the key.
        """
        if key < 0 or key >= self.KEY_COUNT:
            raise IndexError(f"Invalid key index {key}.")
        
        with self._lock:
            self._key_images[key] = image

    def press_key(self, key):
        """
        Simulates pressing a key.
        This method is specific to the simulator and not part of the original API.

        Args:
            key (int): Index of the key to press.
        """
        if key < 0 or key >= self.KEY_COUNT:
            raise IndexError(f"Invalid key index {key}.")
        
        with self._lock:
            if not self._key_states[key]:
                self._key_states[key] = True
                if self.key_callback and self._is_open:
                    self.key_callback(self, key, True)

    def release_key(self, key):
        """
        Simulates releasing a key.
        This method is specific to the simulator and not part of the original API.

        Args:
            key (int): Index of the key to release.
        """
        if key < 0 or key >= self.KEY_COUNT:
            raise IndexError(f"Invalid key index {key}.")
        
        with self._lock:
            if self._key_states[key]:
                self._key_states[key] = False
                if self.key_callback and self._is_open:
                    self.key_callback(self, key, False)

    def get_key_image(self, key):
        """
        Returns the current image for a key.
        This method is specific to the simulator and not part of the original API.

        Args:
            key (int): Index of the key.

        Returns:
            bytes: Image data for the key.
        """
        if key < 0 or key >= self.KEY_COUNT:
            raise IndexError(f"Invalid key index {key}.")
        
        return self._key_images[key]

    def _setup_reader(self, callback):
        """
        Sets up the reader thread for the simulated device.

        Args:
            callback (function): Callback function for the reader thread.
        """
        if self._read_thread is not None:
            self._run_read_thread = False
            try:
                self._read_thread.join()
            except RuntimeError:
                pass

        if callback is not None:
            self._run_read_thread = True
            self._read_thread = threading.Thread(target=callback)
            self._read_thread.daemon = True
            self._read_thread.start()

    def _read(self):
        """
        Reader thread function for the simulated device.
        This function does nothing in the simulator but is included for API compatibility.
        """
        while self._run_read_thread:
            time.sleep(0.05)  # 20Hz polling rate


class StreamDeckOriginalSim(StreamDeckSim):
    """
    Simulated Stream Deck Original device.
    """
    KEY_COUNT = 15
    KEY_COLS = 5
    KEY_ROWS = 3

    KEY_PIXEL_WIDTH = 72
    KEY_PIXEL_HEIGHT = 72
    KEY_IMAGE_FORMAT = "BMP"
    KEY_FLIP = (True, True)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Original (Simulator)"


class StreamDeckMiniSim(StreamDeckSim):
    """
    Simulated Stream Deck Mini device.
    """
    KEY_COUNT = 6
    KEY_COLS = 3
    KEY_ROWS = 2

    KEY_PIXEL_WIDTH = 80
    KEY_PIXEL_HEIGHT = 80
    KEY_IMAGE_FORMAT = "BMP"
    KEY_FLIP = (True, True)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Mini (Simulator)"


class StreamDeckXLSim(StreamDeckSim):
    """
    Simulated Stream Deck XL device.
    """
    KEY_COUNT = 32
    KEY_COLS = 8
    KEY_ROWS = 4

    KEY_PIXEL_WIDTH = 96
    KEY_PIXEL_HEIGHT = 96
    KEY_IMAGE_FORMAT = "BMP"
    KEY_FLIP = (True, True)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck XL (Simulator)"


class StreamDeckVirtualPadSim(StreamDeckSim):
    """
    Simulated virtual pad with a 3 x 15 layout (45 keys).
    """

    KEY_COUNT = 45
    KEY_COLS = 15
    KEY_ROWS = 3

    KEY_PIXEL_WIDTH = 72
    KEY_PIXEL_HEIGHT = 72
    KEY_IMAGE_FORMAT = "BMP"
    KEY_FLIP = (True, True)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Virtual Pad (Simulator)"
