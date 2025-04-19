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
from datetime import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from deckpilot.elements import Button
from deckpilot.core import KeyDisplay
from deckpilot.utils import Logger


# Button that displays the current time (hours, minutes, or seconds).
class ClockButton(Button):
    """
    Button that displays the current time (hours, minutes, or seconds).
    """

    def __init__(
            self,
            name,
            path,
            parent,
            mode: str = "hours",  # "hours", "minutes", or "seconds"
            font_family: str = "Roboto-Bold",
            font_size: int = 360
    ):
        """
        Constructor for the ClockButton class.

        :param name: Name of the button.
        :param path: Path to the button file.
        :param parent: Parent panel.
        :param mode: Mode of the clock display ("hours", "minutes", or "seconds").
        :param font_family: Font family for the clock display.
        :param font_size: Font size for the clock display.
        """
        super().__init__(name, path, parent)
        self.mode = mode  # Affichage choisi
        Logger.inst().info(f"ClockButton {name} created with mode = {mode}")

        # Prepare the font
        self.font = self.am.get_font(font_family, font_size)
    # end __init__

    def get_time_value(self) -> str:
        """
        Get the current time value based on the selected mode.

        :return: The current time value as a string.
        """
        now = datetime.now()
        if self.mode == "hours":
            return now.strftime("%H") + "h"
        elif self.mode == "minutes":
            return now.strftime("%M") + "m"
        elif self.mode == "seconds":
            return now.strftime("%S") + "s"
        else:
            return "--"
        # end if
    # end get_time_value

    def render_icon(self) -> Image.Image:
        """
        Render the icon for the button.

        :return: The rendered icon image.
        """
        image = Image.new("RGB", (512, 512), "black")
        draw = ImageDraw.Draw(image)
        time_text = self.get_time_value()

        # Text size
        text_size = draw.textbbox((0, 0), time_text, font=self.font)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]

        # Center the text
        x = (512 - text_width) / 2
        y = (512 - text_height) / 2

        # Draw
        draw.text((x, y), time_text, font=self.font, fill="white")

        return image
    # end render_icon

    # region EVENTS

    # On item pressed
    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button

        :return: The rendered button display.
        """
        return KeyDisplay(
            text="",
            icon=self.render_icon()
        )
    # end on_item_rendered

    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_pressed" event.

        :param key_index: The index of the key that was pressed.
        :return: The rendered button display.
        """
        return self.on_item_rendered()
    # end on_item_pressed

    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_released" event.

        :param key_index: The index of the key that was released.
        :return: The rendered button display.
        """
        return self.on_item_rendered()
    # end on_item_released

    def on_periodic_tick(self, time_i: int, time_count: int) -> Optional[KeyDisplay]:
        """
        Periodic tick event.

        :param time_i: The current time index.
        :param time_count: The total number of ticks.
        :return: The rendered button display.
        """
        Logger.inst().event(self.__class__.__name__, self.name, f"Tick #{time_i}")
        return self.on_item_rendered()
    # end on_periodic_tick

    # endregion EVENTS

# end ClockButton
