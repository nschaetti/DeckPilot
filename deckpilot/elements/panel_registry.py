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
from pathlib import Path
from deckpilot.elements import Panel
from deckpilot.utils import Logger
from deckpilot.comm import event_bus, EventType, context


# PanelRegistry
class PanelRegistry:
    """
    PanelRegistry is responsible for managing the hierarchy of panels and buttons.
    """

    # Constructor
    def __init__(
            self,
            base_path: Path,
            deck_renderer
    ):
        """
        Constructor for the PanelRegistry class.

        :param base_path: Path to the directory where the buttons and sub-panels are stored.
        :type base_path: Path
        :param deck_renderer: Deck renderer instance.
        :type deck_renderer: DeckRenderer
        """
        # Properties
        self._base_path = base_path
        self._deck_renderer = deck_renderer

        # Load the root panel
        self.root = Panel(
            name="root",
            path=base_path,
            parent=None,
            renderer=deck_renderer,
            active=True
        )

        # Register root as the active panel
        context.set_active_panel(self.root)

        # Subscribe to events
        event_bus.subscribe(self, EventType.KEY_CHANGED, self._on_key_change)
        event_bus.subscribe(self, EventType.INITIALIZED, self._on_initialize)
        event_bus.subscribe(self, EventType.CLOCK_TICK, self._on_periodic_tick)
        event_bus.subscribe(self, EventType.EXIT, self._on_exit)
    # end __init__

    # region PUBLIC METHODS

    # Get panel
    def get_panel(self, path_list):
        """
        Retrieves a panel node based on a list representing the path.

        :param path_list: List of panel names representing the path.
        :type path_list: list
        :return: The corresponding panel node, or None if not found.
        :rtype: PanelNode or None
        """
        current_node = self.root
        for panel_name in path_list:
            if panel_name in current_node.sub_panels:
                current_node = current_node.sub_panels[panel_name]
            else:
                Logger.inst().warn(f"WARNING: Panel '{panel_name}' not found in hierarchy.")
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
        # Render active panel
        context.active_panel.render()
    # end render

    def print_structure(self):
        """
        Prints the hierarchy of panels and buttons using Rich.
        """
        self.root.print_structure()
    # end print_structure

    # endregion PUBLIC METHODS

    # region EVENTS

    # On initialize
    def _on_initialize(self, deck):
        """
        Event handler for the "initialized" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, "main", "on_initialize")

        # Render the current panel
        self.render()
    # end _on_initialize

    # On periodic tick
    def _on_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "periodic" event.
        This method is called periodically according to the configuration.

        :param time_i: The current time index.
        :type time_i: int
        :param time_count: The total time count.
        :type time_count: int
        """
        Logger.inst().event(self.__class__.__name__, "main", "on_periodic_tick")
    # end _on_periodic_tick

    # On exit
    def _on_exit(self):
        """
        Event handler for the "exit" event.
        This method is called when the application is exiting.
        """
        Logger.inst().event(self.__class__.__name__, "main", "on_exit")
    # end _on_exit

    # On key change
    def _on_key_change(self, deck, key_index, state):
        """
        Event handler for the "key_change" event.
        This method is called when the state of a key changes.

        :param deck: The StreamDeck instance.
        :type deck: StreamDeck
        :param key_index: The index of the key that changed.
        :type key_index: int
        """
        Logger.inst().event(self.__class__.__name__, "main", "_on_key_change", key_index=key_index, state=state)

        # Key pressed event
        if state:
            event_bus.send_event(context.active_panel, EventType.KEY_PRESSED, key_index)
        else:
            event_bus.send_event(context.active_panel, EventType.KEY_RELEASED, key_index)
        # end if
    # end _on_key_change

    # endregion EVENTS

# end PanelRegistry

