"""deckpilot.comm.context module for DeckPilot.
"""


# Imports
from deckpilot.utils import Logger


# Singleton Registry
class Context:
    """
    Singleton Registry class to manage objects.
    """

    # Class variable to hold the singleton instance
    _instance = None

    def __new__(cls):
        """
        Create a new instance of the Registry class if it doesn't exist.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._objects = {}
        # end if
        return cls._instance

    # end def __new__
    # region PROPERTIES

    @property
    def active_panel(self):
        """Get the active panel.
        """
        return self.get("active_panel")

    # end def active_panel
    @property
    def config(self):
        """Get the configuration.
        """
        return self._objects.get("config", None)

    # end def config
    @property
    def deck_manager(self):
        """Get the DeckManager.
        """
        return self.get("deck_manager")

    # end def deck_manager
    @property
    def panel_registry(self):
        """Get the PanelRegistry.
        """
        return self.get("panel_registry")

    # end def panel_registry
    @property
    def asset_manager(self):
        """Get the AssetManager.
        """
        return self.get("asset_manager")

    # end def asset_manager
    # endregion PROPERTIES

    # region PUBLIC

    def set_active_panel(self, panel):
        """Set the active panel.
        
        Args:
            panel (Any): Description.
        """
        Logger.inst().debug(f"Context: set active panel: {panel}")
        self.register("active_panel", panel)

    # end def set_active_panel
    def register(self, key, obj):
        """Register an object with a key.
        
        Args:
            key (Any): Description.
            obj (Any): Description.
        """
        self._objects[key] = obj

    # end def register
    def get(self, key):
        """Get an object by its key.
        
        Args:
            key (Any): Description.
        """
        return self._objects.get(key)

    # end def get
    def unregister(self, key):
        """Unregister an object by its key.
        
        Args:
            key (Any): Description.
        """
        self._objects.pop(key, None)

    # end def unregister
    # endregion PUBLIC



# end class Context
# Global registry instance
context = Context()

