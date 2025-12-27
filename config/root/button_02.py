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
from typing import Optional
from deckpilot.elements import Button
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay


class Button02(Button):
    """
    Button that says hello
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent
    ):
        """
        Constructor for the Button class.

        Args:
            name (str): Name of the button.
            path (str): Path to the button file.
            parent (PanelNode): Parent panel.
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"{self.__class__.__name__} {name} created.")
    # end __init__

    # On item released
    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for when the item is released.

        :param key_index: Index of the key that was released.
        :type key_index: int
        :return: KeyDisplay object or None.
        :rtype: Optional[KeyDisplay]
        """
        Logger.inst().info(f"{self.__class__.__name__} {self.name} released.")
        self.parent.dispatch(source=self, data={'message': "Hello World!"})
        return super().on_item_released(key_index)

    # end on_item_released

    # On item pressed
    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for when the item is pressed.

        Args:
            key_index (int): Index of the key that was pressed.

        Returns:
            KeyDisplay: KeyDisplay object.
        """
        Logger.inst().info(f"{self.__class__.__name__} {self.name} pressed.")
        self.parent.dispatch(source=self, data={'message': "Hello World!"})
        return super().on_item_pressed(key_index)
    # end def on_item_pressed

# end Button02


