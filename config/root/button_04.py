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
from deckpilot.elements import Button
from deckpilot.utils import Logger


class Button04(Button):
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

    def on_button_rendered(self):
        """
        Render button
        """
        Logger.inst().info(f"Button {self.name} rendered")
    # end on_button_rendered

    def on_button_pressed(self, key_index):
        """
        Event handler for the "button_pressed" event.
        """
        Logger.inst().info(f"Button {self.name} pressed")
    # end on_button_pressed

    def on_button_released(self, key_index):
        """
        Event handler for the "button_released" event.
        """
        Logger.inst().info(f"Button {self.name} released")
    # end on_button_released

# end Button04


