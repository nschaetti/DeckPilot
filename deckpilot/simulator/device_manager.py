"""
Stream Deck Simulator - Device Manager

This module provides a simulated DeviceManager class that mimics the behavior of the
real Stream Deck DeviceManager, allowing for automated testing without requiring
the physical hardware.
"""

from pathlib import Path

from .configuration import load_simulator_devices, SimulatorConfigError
from .streamdeck_sim import (
    StreamDeckOriginalSim,
    StreamDeckMiniSim,
    StreamDeckXLSim,
    StreamDeckVirtualPadSim,
)


class DeviceManager:
    """
    Simulated central device manager to enumerate virtual Stream Deck devices.
    This class mimics the behavior of the real Stream Deck DeviceManager.
    """

    def __init__(self, transport=None, config_path=None):
        """
        Creates a new simulated StreamDeck DeviceManager.

        Args:
            transport (str, optional): Ignored parameter, included for API compatibility.
            config_path (str | Path | None): Optional simulator configuration file.
        """
        self._virtual_decks = []
        self._config_path = Path(config_path) if config_path else None

        if self._config_path:
            try:
                self._virtual_decks = load_simulator_devices(self._config_path)
            except SimulatorConfigError as exc:
                raise RuntimeError(f"Failed to load simulator config '{self._config_path}': {exc}") from exc

        if not self._virtual_decks:
            # By default, create one of each supported device type
            self._create_default_devices()

    def _create_default_devices(self):
        """
        Creates default virtual Stream Deck devices.
        By default, creates one of each supported device type.
        """
        # Create one of each supported device type with unique serial numbers
        self._virtual_decks = [
            StreamDeckOriginalSim(serial_number="SIM-ORIGINAL-001"),
            StreamDeckMiniSim(serial_number="SIM-MINI-001"),
            StreamDeckXLSim(serial_number="SIM-XL-001"),
            StreamDeckVirtualPadSim(serial_number="SIM-VPAD-001"),
        ]

    def enumerate(self):
        """
        Returns the list of virtual Stream Deck devices.

        Returns:
            list: List of simulated StreamDeck instances.
        """
        return self._virtual_decks

    def add_virtual_device(self, device):
        """
        Adds a virtual Stream Deck device to the manager.
        This method is specific to the simulator and not part of the original API.

        Args:
            device: A simulated StreamDeck instance to add.
        """
        self._virtual_decks.append(device)

    def remove_virtual_device(self, device):
        """
        Removes a virtual Stream Deck device from the manager.
        This method is specific to the simulator and not part of the original API.

        Args:
            device: A simulated StreamDeck instance to remove.
        """
        if device in self._virtual_decks:
            self._virtual_decks.remove(device)

    def clear_virtual_devices(self):
        """
        Removes all virtual Stream Deck devices from the manager.
        This method is specific to the simulator and not part of the original API.
        """
        self._virtual_decks = []
