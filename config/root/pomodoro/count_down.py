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
from datetime import datetime, timedelta
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from deckpilot.elements import Button, Item
from deckpilot.core import KeyDisplay
from deckpilot.utils import Logger


# Button that displays a countdown.
class CountdownButton(Button):
    """
    Button that displays a countdown.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            mode: str = "seconds",  # "hours", "minutes", "seconds"
            duration: int = 0,       # Durée initiale en secondes
            font_family: str = "Roboto-Bold",
            font_size: int = 360
    ):
        """
        Constructor for the CountdownButton class.

        :param name: Name of the button.
        :param path: Path to the button file.
        :param parent: Parent panel.
        :param mode: Mode of the countdown display ("hours", "minutes", or "seconds").
        :param duration: Duration of the countdown in seconds.
        :param font_family: Font family for the countdown display.
        :param font_size: Font size for the countdown display.
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"CountdownButton {name} created with mode = {mode} and duration = {duration}s")

        # Initialize the countdown button
        self.mode = mode
        self.initial_duration = duration  # Durée définie à l'initialisation
        self.remaining = duration
        self._end_time = None
        self.running = False
        self.font = self.am.get_font(font_family, font_size)
    # end __init__

    # region PRIVATE METHODS

    # Start the countdown
    def _start(self, seconds: int):
        """
        Start the countdown.

        :param seconds: Duration of the countdown in seconds.
        """
        Logger.inst().info(f"CountdownButton {self.name} started for {seconds}s")
        if not self.running:
            self.remaining = seconds
            self._end_time = datetime.now() + timedelta(seconds=seconds)
            self.running = True
        # end if
    # end _start

    def _restart(self):
        """
        Restart the countdown with the initial duration.
        """
        Logger.inst().info(f"CountdownButton {self.name} restarted")
        self._start(self.initial_duration)
    # end _restart

    def _stop(self):
        """
        Stop the countdown.
        """
        Logger.inst().info(f"CountdownButton {self.name} stopped")
        self._end_time = None
        self.remaining = 0
        self.running = False
    # end _stop

    # endregion

    # region RENDER

    # Format the time based on the selected mode
    def _format_time(self) -> str:
        """
        Format the time based on the selected mode.

        :return: Formatted time string.
        """
        total = max(0, int(self.remaining))

        if self.mode == "hours":
            return f"{total // 3600:02}" + "h"
        elif self.mode == "minutes":
            return f"{(total % 3600) // 60:02}" + "m"
        elif self.mode == "seconds":
            return f"{total % 60:02}" + "s"
        else:
            return "--"
        # end if
    # end _format_time

    # Render the icon
    def _render_icon(self) -> Image.Image:
        """
        Render the icon for the button.

        :return: The rendered icon image.
        """
        image = Image.new("RGB", (512, 512), "black")
        draw = ImageDraw.Draw(image)
        text = self._format_time()

        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) / 2
        y = (512 - text_height) / 2

        draw.text((x, y), text, font=self.font, fill="white")
        return image
    # end _render_icon

    # endregion RENDER

    # region EVENTS

    # Receive data from dispatching
    def on_dispatch_received(self, source: Item, data: dict):
        """
        Dispatch data to the item.

        :param source: Source item.
        :type source: Item
        :param data: Data to dispatch.
        :type data: dict
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_dispatch_received")

        # Action and duration
        action = data.get("action")
        duration = data.get("duration", 0)

        # Action
        if action == "start":
            self._start(duration)
        elif action == "stop":
            self._stop()
        elif action == "restart":
            self._restart()
        else:
            Logger.inst().error(f"Unknown action: {action}")
        # end if
    # end on_dispatch_received

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

    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_released" event.

        :param key_index: The index of the key that was released.
        :return: The rendered button display.
        """
        # Par défaut : redémarre le compte à rebours
        self._restart()
        return self.on_item_rendered()
    # end on_item_released

    def on_periodic_tick(self, time_i: int, time_count: int) -> Optional[KeyDisplay]:
        """
        Periodic trick event.

        :param time_i: The current time index.
        :param time_count: The total number of time indices.
        :return: The rendered button display.
        """
        if self._end_time:
            delta = (self._end_time - datetime.now()).total_seconds()
            self.remaining = max(0, delta)
            if self.remaining <= 0:
                self._stop()
            # end if
        # end if

        return self.on_item_rendered()
    # end on_periodic_tick

    # endregion EVENTS

# end CountdownButton
