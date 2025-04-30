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

This program is distributed in the hope th at it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

For a copy of the GNU GPLv3, see <https://www.gnu.org/licenses/>.
"""

# Imports
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

from deckpilot.core import KeyDisplay
from deckpilot.elements import Button, Panel, Item
from deckpilot.utils import Logger


# A button that starts and stops OBS recording/streaming
class OBSRecordButton(Button):
    """
    OBS Record/streaming Button
    """

    # Constructor
    def __init__(
            self,
            name: str,
            path: Path,
            parent,
            icon_active: str,
            icon_inactive: str,
            icon_pressed: str,
            icon_error: str,
            icon_confirm: str = "default_inactive",
            icon_paused: str = "default_inactive",
            action: str = "record",
            margin_top: Optional[int] = 0,
            margin_right: Optional[int] = 0,
            margin_bottom: Optional[int] = 0,
            margin_left: Optional[int] = 0,
            icon_x_offset: Optional[int] = 0,
            icon_y_offset: Optional[int] = 0
    ):
        """
        Constructor for the OBSRecordButton class.

        :param name: Name of the button.
        :param path: Path to the button file.
        :param parent: Parent panel.
        :param icon_active: Path to the active icon.
        :param icon_inactive: Path to the inactive icon.
        :param icon_paused: Path to the paused icon.
        :param icon_pressed: Path to the pressed icon.
        :param icon_confirm: Path to the confirm icon.
        :param icon_error: Path to the error icon.
        :param action: Action to perform ("record" or "stream").
        :param margin_top: Top margin.
        :param margin_right: Right margin.
        :param margin_bottom: Bottom margin.
        :param margin_left: Left margin.
        :param icon_x_offset: X offset for the icon.
        :param icon_y_offset: Y offset for the icon.
        """
        super().__init__(name, path, parent)
        Logger.inst().info(f"{self.__class__.__name__} {name} created.")
        self.parent = parent

        # Icon
        self.icon_active = self.am.get_icon(icon_active)
        self.icon_inactive = self.am.get_icon(icon_inactive)
        self.icon_paused = self.am.get_icon(icon_paused)
        self.icon_pressed = self.am.get_icon(icon_pressed)
        self.icon_confirm = self.am.get_icon(icon_confirm)
        self.icon_error = self.am.get_icon(icon_error)

        # Action
        self.action = action
        if action not in ["record", "stream"]:
            raise ValueError("Action must be 'record' or 'stream'.")
        self.action = action

        # State
        self.state = "not-connected"

        # Set margins
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left

        # Set icon offsets
        self.icon_x_offset = icon_x_offset
        self.icon_y_offset = icon_y_offset

        # Keep time of last press (for double press detection)
        self.last_press_time = None
    # end __init__

    # region PRIVATE

    def _get_icon(self):
        """
        Get the icon for the button.

        :return: The icon for the button.
        """
        try:
            if self.state == "not-connected":
                return self.icon_error
            elif self.state == "active":
                return self.icon_active
            elif self.state == "paused":
                return self.icon_paused
            elif self.state == "confirm":
                return self.icon_confirm
            else:
                return self.icon_inactive
            # end if
        except Exception as e:
            return self.icon_error
        # end try
    # end _get_icon

    # Set last press time at current time
    def set_last_press_time(self):
        """
        Set the last press time to the current time.
        """
        self.last_press_time = datetime.now()
    # end set_last_press_time

    # Detect double press
    def is_double_press(self) -> bool:
        """
        Check if the button was double pressed.

        :return: True if double pressed, False otherwise.
        """
        if self.last_press_time is None:
            return False
        # end if

        # Get the time difference
        time_diff = datetime.now() - self.last_press_time

        # Check if the time difference is less than 0.5 seconds
        return time_diff.total_seconds() < 0.5
    # end is_double_press

    # endregion PRIVATE

    # region EVENTS

    def on_dispatch_received(self, source: Item, data: dict):
        """
        Dispatch data to the item.

        :param source: Source item.
        :param data: Data to dispatch.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_dispatch_received")

        # Initialisation or on_record_state_changed
        if data['event'] == "on_obs_connected":
            self.state = "inactive"
            Logger.inst().debug(f"{self.__class__.__name__} \"{self.name}\" is state={self.state}")
        elif data['event'] == "on_record_state_changed":
            # Get the current state
            if self.action == "record":
                if self.parent.is_recording_paused():
                    self.state = "paused"
                elif self.parent.is_recording():
                    self.state = "active"
                else:
                    self.state = "inactive"
                # end if
            # end ifW

            # Debug log
            Logger.inst().debug(f"{self.__class__.__name__} \"{self.name}\" is state={self.state}")
        elif data['event'] == "on_stream_state_changed":
            if self.action == "stream":
                if self.parent.is_streaming():
                    self.state = "active"
                else:
                    self.state = "inactive"
                # end if
            # end if

            # Debug log
            Logger.inst().debug(f"{self.__class__.__name__} \"{self.name}\" is state={self.state}")
        elif data['event'] == "on_obs_disconnected":
            self.state = "not-connected"
            Logger.inst().debug(f"{self.__class__.__name__} \"{self.name}\" is state={self.state}")
        # end if

        # Refresh the button
        self.parent.refresh_me(self)
    # end on_dispatch_received

    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button

        :return: The rendered button display.
        """
        # Return icon
        key_display = KeyDisplay(
            text="",
            icon=self._get_icon()
        )

        # Margin
        key_display.margin_top = self.margin_top
        key_display.margin_right = self.margin_right
        key_display.margin_bottom = self.margin_bottom
        key_display.margin_left = self.margin_left

        return key_display
    # end on_item_rendered

    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_pressed" event.
        """
        # Super
        icon = super().on_item_pressed(key_index).icon

        # Return icon
        key_display = KeyDisplay(
            text="",
            icon=icon
        )

        # Margin
        key_display.margin_top = self.margin_top
        key_display.margin_right = self.margin_right
        key_display.margin_bottom = self.margin_bottom
        key_display.margin_left = self.margin_left

        # Return icon
        return key_display
    # end on_item_pressed

    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_released" event.
        """
        # Start/stop recording
        if self.action == "record":
            if self.is_double_press():
                self.parent.stop_recording()
            else:
                if self.parent.is_recording():
                    self.parent.pause_recording()
                elif self.parent.is_recording_paused():
                    self.parent.resume_recording()
                else:
                    self.parent.start_recording()
                # end if

                # Set last press time
                self.set_last_press_time()
            # end if
        elif self.action == "stream":
            if self.state == "confirm":
                if self.parent.is_streaming():
                    self.parent.stop_streaming()
                else:
                    self.parent.start_streaming()
                # end if
            else:
                self.state = "confirm"
            # end if
        # end if

        # KeyDisplay
        key_display = KeyDisplay(
            text="",
            icon=self._get_icon()
        )

        # Margin
        key_display.margin_top = self.margin_top
        key_display.margin_right = self.margin_right
        key_display.margin_bottom = self.margin_bottom
        key_display.margin_left = self.margin_left

        return key_display
    # end on_item_released

    # endregion EVENTS

# end OBSRecordButton

