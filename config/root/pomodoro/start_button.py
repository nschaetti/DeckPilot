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
from PIL import Image, ImageDraw, ImageFont
from deckpilot.elements import Button
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay


class StartButton(Button):
    """
    Button that starts a timer.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            duration: int,
            font_family: str = "Roboto-Bold",
            font_size: int = 180,
            font_color: str = "white",
    ):
        """
        Constructor for the Button class.

        :param name: Name of the button.
        :type name: str
        :param path: Path to the button file.
        :type path: Path
        :param parent: Parent panel.
        :type parent: PanelNode
        :param duration: Duration of the timer in seconds.
        :type duration: int
        :param font_family: Font family for the countdown display.
        :type font_family: str
        :param font_size: Font size for the countdown display.
        :type font_size: int
        :param font_color: Font color for the countdown display.
        :type font_color: str
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"{self.__class__.__name__} {name} created.")
        self.duration = duration
        self.font = self.am.get_font(font_family, font_size)
        self.font_color = font_color
    # end __init__

    # region RENDER

    # Format the time based on the selected mode
    def _format_time(self) -> str:
        """
        Format the time based on the selected mode.

        :return: Formatted time string.
        """
        total = max(0, int(self.duration))

        # Format the time string based on the selected mode
        hours = f"{total // 3600:02}"
        minutes = f"{(total % 3600) // 60:02}"

        # Return the formatted time string
        if total // 3600 > 0:
            return f"{hours}h{minutes}"
        else:
            return f"{minutes}m"
        # end if
    # end _format_time

    # Render the icon
    def _render_icon(self, active: bool = False) -> Image.Image:
        """
        Render the icon for the button.

        :param active: Whether the button is active or not.
        :type active: bool
        :return: The rendered icon image.
        """
        color = "blue" if active else "black"
        text_color = "black" if active else self.font_color
        image = Image.new("RGB", (512, 512), color)
        draw = ImageDraw.Draw(image)
        text = self._format_time()

        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) / 2
        y = (512 - text_height) / 2

        draw.text((x, y), text, font=self.font, fill=text_color)
        return image
    # end _render_icon

    # endregion RENDER

    # region EVENTS

    # On item pressed
    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button

        :return: The rendered button display.
        """
        return KeyDisplay(
            text="",
            icon=self._render_icon()
        )
    # end on_item_rendered

    # On item pressed
    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for when the item is pressed.

        :param key_index: Index of the key that was pressed.
        :type key_index: int
        :return: KeyDisplay object or None.
        :rtype: Optional[KeyDisplay]
        """
        Logger.inst().info(f"{self.__class__.__name__} {self.name} pressed.")
        return KeyDisplay(
            text="",
            icon=self._render_icon(active=True)
        )
    # end on_item_pressed

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
        self.parent.dispatch(source=self, data={'action': "start", "duration": self.duration})
        return KeyDisplay(
            text="",
            icon=self._render_icon()
        )
    # end on_item_released

    # endregion EVENTS

# end Button01

