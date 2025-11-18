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

---

Common plugin data structures and contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from deckpilot.comm.event_bus import EventBus

if TYPE_CHECKING:
    from deckpilot.core.deck_manager import DeckManager
    from deckpilot.elements.panel_registry import PanelRegistry


@dataclass
class PluginPanelDefinition:
    """Metadata describing how a plugin contributes a panel."""

    identifier: str
    name: str
    path: str
    mount: str = "root"
    class_path: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginEventHook:
    """Represents a mapping between an EventBus topic and a plugin handler."""

    topic: str
    handler: str
    once: bool = False


@dataclass
class PluginMetadata:
    """Parsed content of plugin.yaml."""

    name: str
    entry_point: str
    version: str = "0.1.0"
    description: Optional[str] = None
    panels: List[PluginPanelDefinition] = field(default_factory=list)
    events: List[PluginEventHook] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PluginMetadata":
        """Create metadata from a YAML dictionary."""
        panels = [
            PluginPanelDefinition(
                identifier=panel.get("id", panel.get("name", "")),
                name=panel.get("name", panel.get("id", "")),
                path=panel["path"],
                mount=panel.get("mount", "root"),
                class_path=panel.get("class"),
                params=panel.get("params", {}),
            )
            for panel in payload.get("panels", [])
        ]
        events = [
            PluginEventHook(
                topic=hook.get("topic") or hook.get("event"),
                handler=hook["handler"],
                once=hook.get("once", False),
            )
            for hook in payload.get("events", [])
            if hook.get("topic") or hook.get("event")
        ]
        return cls(
            name=payload["name"],
            entry_point=payload["entry_point"],
            version=payload.get("version", "0.1.0"),
            description=payload.get("description"),
            panels=panels,
            events=events,
            config=payload.get("config", {}),
        )


@dataclass
class PluginContext:
    """Runtime context provided to plugin instances."""

    metadata: PluginMetadata
    base_path: Path
    event_bus: EventBus
    panel_registry: "PanelRegistry"
    deck_manager: "DeckManager"
    global_config: Dict[str, Any]


class BasePlugin:
    """
    Abstract base class that all plugins should inherit from.
    """

    def __init__(self, context: PluginContext):
        self._context = context
    # end def __init__

    @property
    def context(self) -> PluginContext:
        return self._context
    # end context

    @property
    def metadata(self) -> PluginMetadata:
        return self._context.metadata
    # end metadata

    def register(self) -> None:
        """
        Hook to set up event listeners, panels, and services.
        """
        raise NotImplementedError
    # end def registrer

# end class BasePlugin

