"""
Stream Deck Simulator - Switcher Module

This module provides a mechanism to switch between the real Stream Deck hardware
and the simulator. It exposes a DeviceManager class that can be used as a drop-in
replacement for the real Stream Deck DeviceManager.
"""

import os
import importlib

# Default to using the real hardware
USE_SIMULATOR = os.environ.get('STREAMDECK_USE_SIMULATOR', '').lower() in ('true', '1', 'yes')

# Cache for the device manager class
_device_manager_class = None
_simulator_config_path = None


def use_simulator(use_sim=True, config_path=None):
    """
    Set whether to use the simulator or the real hardware.
    
    Args:
        use_sim (bool): True to use the simulator, False to use the real hardware.
        config_path (str | None): Optional simulator configuration file path.
    """
    global USE_SIMULATOR, _device_manager_class, _simulator_config_path
    USE_SIMULATOR = use_sim
    if config_path is not None:
        _simulator_config_path = config_path
    _device_manager_class = None  # Reset the cache


def get_simulator_config_path():
    """
    Returns the configured simulator configuration path, if any.
    """
    return _simulator_config_path


def get_device_manager_class():
    """
    Get the appropriate DeviceManager class based on the current configuration.
    
    Returns:
        class: The DeviceManager class to use.
    """
    global _device_manager_class
    
    if _device_manager_class is None:
        if USE_SIMULATOR:
            # Import the simulator
            from deckpilot.simulator.device_manager import DeviceManager as SimDeviceManager
            _device_manager_class = SimDeviceManager
        else:
            # Import the real hardware
            from StreamDeck.DeviceManager import DeviceManager as RealDeviceManager
            _device_manager_class = RealDeviceManager
    
    return _device_manager_class


# DeviceManager class that dynamically selects the implementation
class DeviceManager:
    """
    DeviceManager class that dynamically selects between the real hardware
    and simulator implementations based on the current configuration.
    """
    
    def __init__(self, transport=None):
        """
        Creates a new StreamDeck DeviceManager, using either the real hardware
        or simulator implementation based on the current configuration.
        
        Args:
            transport (str, optional): Transport to use (passed to real hardware implementation).
        """
        manager_class = get_device_manager_class()
        if USE_SIMULATOR:
            self._manager = manager_class(transport=transport, config_path=get_simulator_config_path())
        else:
            self._manager = manager_class(transport)
    
    def enumerate(self):
        """
        Detect attached StreamDeck devices.
        
        Returns:
            list: List of StreamDeck instances, one for each detected device.
        """
        return self._manager.enumerate()
    
    # For simulator-specific methods
    def __getattr__(self, name):
        """
        Forward any other attribute access to the underlying implementation.
        
        Args:
            name (str): Name of the attribute to access.
            
        Returns:
            Any: The attribute from the underlying implementation.
        """
        return getattr(self._manager, name)
