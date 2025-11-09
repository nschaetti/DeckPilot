"""deckpilot.plugins package exports Plugin utilities."""

from .base import (
    BasePlugin,
    PluginContext,
    PluginEventHook,
    PluginMetadata,
    PluginPanelDefinition,
)
from .manager import PluginManager

__all__ = [
    "BasePlugin",
    "PluginContext",
    "PluginEventHook",
    "PluginMetadata",
    "PluginPanelDefinition",
    "PluginManager",
]

