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
from typing import Any
from deckpilot.elements import Button
from deckpilot.utils import Logger


class HelloButton(Button):
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

        :param name: Name of the button.
        :type name: str
        :param path: Path to the button file.
        :type path: Path
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"HelloButton {name} created.")

        # Blinking state
        self.blinking = 0
        self.blinking_icon = self.get_icon("blink")
    # end __init__

    # region EVENTS

    def on_item_rendered(self):
        """
        Render button
        """
        # Super
        icon = super().on_item_rendered()

        # Return icon
        if self.blinking == 1:
            return self.blinking_icon
        else:
            return icon
        # end if
    # end on_item_rendered

    # On item pressed
    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Super
        icon = super().on_item_released(key_index)

        # Return icon
        if self.blinking == 1:
            return self.blinking_icon
        else:
            return icon
        # end if
    # end on_item_released

    # On periodic event
    def on_periodic_tick(self) -> Any:
        """
        Periodic trick event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_periodic_tick")

        # Toggle blinking
        self.blinking = 1 - self.blinking

        # Update icon
        if not self.pressed:
            if self.blinking == 1:
                return self.blinking_icon
            else:
                return self.get_icon()
            # end if
        # end if
    # end on_periodic_trick

    # endregion EVENTS

# end HelloButton


