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
from typing import Any, Optional
from deckpilot.elements import Button
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay


class HelloButton(Button):
    """
    Button that says hello
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            label: str
    ):
        """
        Constructor for the Button class.

        :param name: Name of the button.
        :type name: str
        :param path: Path to the button file.
        :type path: Path
        :param parent: Parent panel.
        :type parent: PanelNode
        :param label: Label for the button.
        :type label: str
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"HelloButton {name} created.")

        # Set label
        self.label = label

        # Blinking state
        self.blinking = 0
        self.blinking_icon = self.am.get_icon("default_blinking")
    # end __init__

    # region EVENTS

    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button
        """
        # Super
        icon = super().on_item_rendered().icon

        # Return icon
        if self.blinking == 1:
            return KeyDisplay(
                text=self.label,
                icon=self.blinking_icon,
                text_color='red'
            )
        else:
            return KeyDisplay(
                text=self.label,
                icon=icon,
            )
        # end if
    # end on_item_rendered

    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_pressed" event.
        """
        # Super
        icon = super().on_item_pressed(key_index).icon
        text = super().on_item_pressed(key_index).text

        # Return icon
        return KeyDisplay(
            text=self.label,
            icon=icon,
            text_color="blue"
        )
    # end on_item_pressed

    # On item pressed
    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_released" event.
        """
        # Super
        icon = super().on_item_released(key_index).icon

        # Return icon
        if self.blinking == 1:
            return KeyDisplay(
                text=self.label,
                icon=self.blinking_icon,
                text_color='red'
            )
        else:
            return KeyDisplay(
                text=self.label,
                icon=icon,
            )
        # end if
    # end on_item_released

    # On periodic event
    def on_periodic_tick(self, time_i: int, time_count: int) -> Optional[KeyDisplay]:
        """
        Periodic trick event.

        :param time_i: The current time index.
        :type time_i: int
        :param time_count: The total time count.
        :type time_count: int
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_periodic_tick")

        # Toggle blinking
        self.blinking = 1 - self.blinking

        # Logger
        Logger.inst().debug(f"HelloButton {self.name} blinking = {self.blinking}, pressed = {self.pressed}")

        # Update icon
        if not self.pressed:
            if self.blinking == 1:
                return KeyDisplay(
                    text=self.label,
                    icon=self.blinking_icon,
                    text_color='red'
                )
            else:
                return KeyDisplay(
                    text=self.label,
                    icon=self.icon_inactive,
                )
            # end if
        # end if

        return None
    # end on_periodic_trick

    # endregion EVENTS

# end HelloButton


