"""deckpilot.elements.panel_registry module for DeckPilot.
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
        """Constructor for the PanelRegistry class.
        
        Args:
            base_path (Path): Path to the directory where the buttons and sub-panels are stored.
            deck_renderer (DeckRenderer): Deck renderer instance.
        """
        # Properties
        self._base_path = base_path
        self._deck_renderer = deck_renderer

        # Root panel configuration
        root_params = context.config.get("root", {})
        Logger.inst().debug(f"PanelRegistry: root_params: {root_params}")

        # Load the root panel
        self.root = Panel(
            name="root",
            path=base_path,
            parent=None,
            renderer=deck_renderer,
            active=True,
            **root_params
        )

        # Register root as the active panel
        context.set_active_panel(self.root)

        # Subscribe to events
        event_bus.subscribe(self, EventType.KEY_CHANGED, self._on_key_change)
        event_bus.subscribe(self, EventType.INITIALIZED, self._on_initialize)
        event_bus.subscribe(self, EventType.CLOCK_TICK, self._on_periodic_tick)
        event_bus.subscribe(self, EventType.EXIT, self._on_exit)

    # end def __init__
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
                Logger.inst().warning(f"WARNING: Panel '{panel_name}' not found in hierarchy.")
                return None
            # end if
        # end for
        return current_node

    # end def get_panel
    # Rendering current panel
    def render(self):
        """
        Renders the current panel on the Stream Deck.
        """
        # Render active panel
        context.active_panel.render()

    # end def render
    def print_structure(self):
        """
        Prints the hierarchy of panels and buttons using Rich.
        """
        self.root.print_structure()

    # end def print_structure
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

    # end def _on_initialize
    # On periodic tick
    def _on_periodic_tick(self, time_i: int, time_count: int):
        """Event handler for the "periodic" event.
        This method is called periodically according to the configuration.
        
        Args:
            time_i (int): The current time index.
            time_count (int): The total time count.
        """
        Logger.inst().event(self.__class__.__name__, "main", "on_periodic_tick")

    # end def _on_periodic_tick
    # On exit
    def _on_exit(self):
        """
        Event handler for the "exit" event.
        This method is called when the application is exiting.
        """
        Logger.inst().event(self.__class__.__name__, "main", "on_exit")

    # end def _on_exit
    # On key change
    def _on_key_change(self, deck, key_index, state):
        """Event handler for the "key_change" event.
        This method is called when the state of a key changes.
        
        Args:
            deck (StreamDeck): The StreamDeck instance.
            key_index (int): The index of the key that changed.
            state (Any): Description.
        """
        Logger.inst().event(self.__class__.__name__, "main", "_on_key_change", key_index=key_index, state=state)

        # Key pressed event
        if state:
            event_bus.send_event(context.active_panel, EventType.KEY_PRESSED, key_index)
        else:
            event_bus.send_event(context.active_panel, EventType.KEY_RELEASED, key_index)

        # end if
    # end def _on_key_change
    # endregion EVENTS


# end class PanelRegistry
