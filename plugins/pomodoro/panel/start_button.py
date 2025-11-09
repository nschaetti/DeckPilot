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
from deckpilot.elements import Button, Item
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
            icon_current: str,
            icon_next: str,
            icon_current_next: str,
            duration: int = 0,
            action: str = "start",
            font_family: str = "Roboto-Bold",
            font_size: int = 180,
            font_color: str = "white",
            icon_inactive: str = "default",
            icon_pressed: str = "default_pressed",
            margin_top: Optional[int] = None,
            margin_right: Optional[int] = None,
            margin_bottom: Optional[int] = None,
            margin_left: Optional[int] = None,
            icon_x_offset: Optional[int] = 0,
            icon_y_offset: Optional[int] = 0,
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
        :param icon_current: Icon for the current state.
        :type icon_current: str
        :param icon_next: Icon for the next state.
        :type icon_next: str
        :param icon_current_next: Icon for the current and next state.
        :type icon_current_next: str
        :param font_family: Font family for the countdown display.
        :type font_family: str
        :param font_size: Font size for the countdown display.
        :type font_size: int
        :param font_color: Font color for the countdown display.
        :type font_color: str
        :param icon_inactive: Icon for the inactive state.
        :param icon_pressed: Icon for the pressed state.
        :param action: Action to perform when the button is pressed.
        :type action: str
        :param margin_top: Top margin for the icon.
        :type margin_top: Optional[int]
        :param margin_right: Right margin for the icon.
        :type margin_right: Optional[int]
        :param margin_bottom: Bottom margin for the icon.
        :type margin_bottom: Optional[int]
        :param margin_left: Left margin for the icon.
        :type margin_left: Optional[int]
        :param icon_x_offset: X offset for the icon.
        :type icon_x_offset: Optional[int]
        :param icon_y_offset: Y offset for the icon.
        :type icon_y_offset: Optional[int]
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"{self.__class__.__name__} {name} created.")
        self.duration = duration
        self.font = self.am.get_font(font_family, font_size)
        self.font_color = font_color
        self.action = action

        # Countdown state
        self._countdown_state = "inactive"

        # Icons
        self.icon_current = self.am.get_icon(icon_current)
        self.icon_next = self.am.get_icon(icon_next)
        self.icon_current_next = self.am.get_icon(icon_current_next)
        self.icon_background = self.am.get_icon(icon_inactive)
        self.icon_pressed = self.am.get_icon(icon_pressed)
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.icon_x_offset = icon_x_offset
        self.icon_y_offset = icon_y_offset
    # end __init__

    # region PUBLIC

    # Set countdown state
    def set_countdown_state(self, state: str):
        """
        Set the countdown state.

        :param state: Countdown state ("inactive", "active", "paused").
        :type state: str
        """
        self._countdown_state = state
        Logger.inst().info(f"{self.__class__.__name__} {self.name} countdown state set to {state}.")
    # end set_countdown_state

    # endregion PUBLIC

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

    # Get state icon
    def _get_state_icon(self) -> Image.Image:
        """
        Get the icon for the current state.

        Returns:
            Image.Image: The icon for the current state.
        """
        if self._countdown_state == "active":
            return self.icon_current
        elif self._countdown_state == "next":
            return self.icon_next
        elif self._countdown_state == "active_next":
            return self.icon_current_next
        # end if
        return self.icon_background
    # end _get_state_icon

    # Render the icon
    def _render_icon(self, active: bool = False) -> Image.Image:
        """
        Render the icon for the button.

        :param active: Whether the button is active or not.
        :type active: bool
        :return: The rendered icon image.
        """
        base_icon = self.icon_pressed if active else self._get_state_icon()
        image = base_icon.copy().convert("RGBA")
        draw = ImageDraw.Draw(image)

        if self.action == "start":
            text = self._format_time()
            bbox = draw.textbbox((0, 0), text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (512 - text_width) / 2 + self.icon_x_offset
            y = (512 - text_height) / 2 + self.icon_y_offset
            draw.text((x, y), text, font=self.font, fill=self.font_color)
        # end if

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

        # Current state
        current_state = self._countdown_state

        # Action
        if action == "update":
            if duration == self.duration:
                self._countdown_state = "active"
            else:
                self._countdown_state = "inactive"
            # end if
        elif action == "next":
            if duration == self.duration:
                if self._countdown_state == "active":
                    self._countdown_state = "active_next"
                else:
                    self._countdown_state = "next"
                # end if
            # end if
        # end if

        # State changed
        if self._countdown_state != current_state:
            self.parent.refresh_me(item=self)
        # end if
    # end on_dispatch_received

    # On item pressed
    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button

        :return: The rendered button display.
        """
        # KeyDisplay
        key_display = KeyDisplay(
            text="",
            icon=self._render_icon()
        )

        # Add margins if given
        if self.margin_top is not None:
            key_display.margin_top = self.margin_top
        # end if

        if self.margin_right is not None:
            key_display.margin_right = self.margin_right
        # end if

        if self.margin_bottom is not None:
            key_display.margin_bottom = self.margin_bottom
        # end if

        if self.margin_left is not None:
            key_display.margin_left = self.margin_left
        # # end if

        return key_display
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

        # KeyDisplay
        key_display = KeyDisplay(
            text="",
            icon=self._render_icon(active=True)
        )

        # Add margins if given
        if self.margin_top is not None:
            key_display.margin_top = self.margin_top
        # end if

        if self.margin_right is not None:
            key_display.margin_right = self.margin_right
        # end if

        if self.margin_bottom is not None:
            key_display.margin_bottom = self.margin_bottom
        # end if

        if self.margin_left is not None:
            key_display.margin_left = self.margin_left
        # end if

        return key_display
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

        if self.action == "start":
            # self.parent.dispatch(source=self, data={'action': self.action, "duration": self.duration})
            self.parent.add_countdown(self.duration)
        elif self.action == "pause":
            self.parent.pause_countdown()
            # self.parent.dispatch(source=self, data={'action': self.action})
        elif self.action == "stop":
            self.parent.stop_countdown()
            # self.parent.dispatch(source=self, data={'action': self.action})
        else:
            raise ValueError(f"Unknown action: {self.action}")
        # end if

        # KeyDisplay
        key_display = KeyDisplay(
            text="",
            icon=self._render_icon()
        )

        # Add margins if given
        if self.margin_top is not None:
            key_display.margin_top = self.margin_top
        # end if

        if self.margin_right is not None:
            key_display.margin_right = self.margin_right
        # end if

        if self.margin_bottom is not None:
            key_display.margin_bottom = self.margin_bottom
        # end if

        if self.margin_left is not None:
            key_display.margin_left = self.margin_left
        # end if

        return key_display
    # end on_item_released

    # endregion EVENTS

# end StartButton

