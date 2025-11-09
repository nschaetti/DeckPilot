"""
Stream Deck Simulator Package

This package provides a simulated Stream Deck implementation that can be used
as a drop-in replacement for the real Stream Deck hardware.
"""

from .switcher import DeviceManager, use_simulator
from .streamdeck_sim import (
    StreamDeckSim,
    StreamDeckOriginalSim,
    StreamDeckMiniSim,
    StreamDeckXLSim,
    StreamDeckVirtualPadSim,
)

__all__ = [
    'DeviceManager',
    'use_simulator',
    'StreamDeckSim',
    'StreamDeckOriginalSim',
    'StreamDeckMiniSim',
    'StreamDeckXLSim',
    'StreamDeckVirtualPadSim',
]
