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
    # end __new__

    # region PROPERTIES

    @property
    def active_panel(self):
        """
        Get the active panel.

        :return:
        """
        return self.get("active_panel")
    # end active_panel

    @property
    def config(self):
        """
        Get the configuration.

        :return:
        """
        return self._objects.get("config", None)
    # end config

    @property
    def deck_manager(self):
        """
        Get the DeckManager.

        :return:
        """
        return self.get("deck_manager")
    # end deck_manager

    @property
    def panel_registry(self):
        """
        Get the PanelRegistry.

        :return:
        """
        return self.get("panel_registry")
    # end panel_registry

    @property
    def asset_manager(self):
        """
        Get the AssetManager.

        :return:
        """
        return self.get("asset_manager")
    # end asset_manager

    # endregion PROPERTIES

    # region PUBLIC

    def set_active_panel(self, panel):
        """
        Set the active panel.

        :param panel:
        :return:
        """
        Logger.inst().debug(f"Context: set active panel: {panel}")
        self.register("active_panel", panel)
    # end set_active_panel

    def register(self, key, obj):
        """
        Register an object with a key.

        :param key:
        :param obj:
        :return:
        """
        self._objects[key] = obj
    # end register

    def get(self, key):
        """
        Get an object by its key.

        :param key:
        :return:
        """
        return self._objects.get(key)
    # end get

    def unregister(self, key):
        """
        Unregister an object by its key.

        :param key:
        :return:
        """
        self._objects.pop(key, None)
    # end unregister

    # endregion PUBLIC

# end Context


# Global registry instance
context = Context()

