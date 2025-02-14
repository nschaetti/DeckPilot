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
import os
import importlib.util
import logging
from rich.console import Console
from rich.tree import Tree
from rich.console import Console
from rich.text import Text

from .panel_nodes import Panel


# Console
console = Console()


# PanelRegistry
class PanelRegistry:

    # Constructor
    def __init__(
            self,
            base_path,
            event_bus,
            deck_renderer
    ):
        """
        Constructor for the PanelRegistry class.

        Args:
            base_path (str): Path to the directory where the buttons and sub-panels are stored.
            event_bus (EventBus): Event bus for the application.
            deck_renderer (DeckRenderer): Deck renderer instance.
        """
        self._event_bus = event_bus
        self.base_path = base_path
        self.root = Panel("root", base_path, parent=None, renderer=deck_renderer, active=True)
        self._deck_renderer = deck_renderer

        # Subscribe to events
        self._event_bus.subscribe("key_change", self._on_key_change)
        self._event_bus.subscribe("initialized", self._on_initialize)
        self._event_bus.subscribe("periodic", self._on_periodic_tick)
        self._event_bus.subscribe("exit", self._on_exit)
    # end __init__

    # region PUBLIC METHODS

    # Get panel
    def get_panel(self, path_list):
        """
        Retrieves a panel node based on a list representing the path.

        Args:
            path_list (list): List of panel names representing the path.

        Returns:
            PanelNode or None: The corresponding panel node, or None if not found.
        """
        current_node = self.root
        for panel_name in path_list:
            if panel_name in current_node.sub_panels:
                current_node = current_node.sub_panels[panel_name]
            else:
                console.log(f"WARNING: Panel '{panel_name}' not found in hierarchy.")
                return None
            # end if
        # end for
        return current_node
    # end get_panel

    # Rendering current panel
    def render(self):
        """
        Renders the current panel on the Stream Deck.
        """
        # Get active panel
        active_panel = self._get_active_panel()

        # Render active panel
        active_panel.render()
    # end render

    def print_structure(self):
        """
        Prints the hierarchy of panels and buttons using Rich.
        """
        self.root.print_structure()
    # end print_structure

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    # Get active panel
    def _get_active_panel(self):
        """
        Retrieves the active panel.
        """
        return self.root.get_active_panel()
    # end _get_active_panel

    # endregion PRIVATE METHODS

    # region EVENTS

    # On initialize
    def _on_initialize(self, deck):
        """
        Event handler for the "initialized" event.
        """
        # Log
        console.log(f"[yellow bold]PanelRegistry[/]::_on_initialize")

        # Render the current panel
        self.render()
    # end _on_initialize

    # On periodic tick
    def _on_periodic_tick(self):
        """
        Event handler for the "periodic" event.
        """
        console.log(f"[yellow bold]PanelRegistry[/]::_on_periodic_tick")

        # Active panel
        active_panel = self._get_active_panel()

        # Periodic tick
        active_panel.on_periodic_tick()
    # end _on_periodic_tick

    # On exit
    def _on_exit(self):
        """
        Event handler for the "exit" event.
        """
        console.log(f"[yellow bold]PanelRegistry[/]::_on_exit")
        # self._deck_renderer.clear_deck()
    # end _on_exit

    # On key change
    def _on_key_change(self, deck, key_index, state):
        """
        Event handler for the "key_change" event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        console.log(f"[yellow bold]PanelRegistry[/]::_on_key_change {key_index} state {state}")

        # Active panel
        active_panel = self._get_active_panel()

        # Key pressed event
        if state:
            active_panel.on_key_pressed(key_index)
        else:
            active_panel.on_key_released(key_index)
        # end if
    # end _on_key_change

    # endregion EVENTS

# end PanelRegistry

