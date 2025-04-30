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
import obsws_python as obs
import obsws_python.error as obs_error
from deckpilot.elements import Button, Item
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay


class OBSInputButton(Button):
    """
    Button to activate/deactivate an OBS input.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            input_name: str,
            icon_input_inactive: str,
            icon_input_active: str,
            icon_input_error: str = "default_inactive",
            icon_pressed: str = "default_pressed",
            is_special_input: bool = False,
            font_family: str = "Roboto-Bold",
            font_size: int = 180,
            font_color: str = "white",
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
        :param input_name: Name of the OBS input to control.
        :type input_name: str
        :param icon_input_inactive: Icon for the inactive state.
        :type icon_input_inactive: str
        :param icon_input_active: Icon for the active state.
        :type icon_input_active: str
        :param icon_input_error: Icon for the error state.
        :type icon_input_error: str
        :param icon_pressed: Icon for the pressed state.
        :type icon_pressed: str
        :param is_special_input: Flag to indicate if the input is special.
        :type is_special_input: bool
        :param font_family: Font family for the countdown display.
        :type font_family: str
        :param font_size: Font size for the countdown display.
        :type font_size: int
        :param font_color: Font color for the countdown display.
        :type font_color: str
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
        self.font = self.am.get_font(font_family, font_size)
        self.font_color = font_color
        self.parent = parent

        # Icons
        self.icon_input_inactive = self.am.get_icon(icon_input_inactive)
        self.icon_pressed = self.am.get_icon(icon_pressed)
        self.icon_input_active = self.am.get_icon(icon_input_active)
        self.icon_input_error = self.am.get_icon(icon_input_error)
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.icon_x_offset = icon_x_offset
        self.icon_y_offset = icon_y_offset

        # Input settings
        self.input_name = input_name
        self.input_active = None
        self.is_special_input = is_special_input
    # end __init__

    # region PRIVATE

    def _get_icon(self):
        """
        Get the icon for the button.

        Returns:
            KeyDisplay: The icon to display.
        """
        if self.input_active:
            return self.icon_input_active
        elif self.input_active is not None:
            return self.icon_input_inactive
        else:
            return self.icon_input_error
        # end if
    # end _get_icon

    def _get_input_name(self) -> str:
        """
        Get the input name.

        Returns:
            str: The input name.
        """
        if self.is_special_input:
            return self.parent.get_special_input(self.input_name)
        else:
            return self.input_name
        # end if
    # end _get_input_name

    # endregion PRIVATE

    # region EVENTS

    def on_dispatch_received(self, source: Item, data: dict):
        """
        Dispatch the data to the appropriate method.

        :param source: Source item.
        :type source: Item
        :param data: Data to dispatch.
        :type data: dict
        """
        Logger.inst().event("OBSSceneButton", self.name, "dispatch", data=data)

        # Initialisation or update scene
        if data['event'] == "on_input_mute_state_changed" and data['data'].input_name == self.input_name:
            # Input mute state
            input_muted = data['data'].input_muted
            self.input_active = not input_muted
            Logger.inst().debug(f"Input \"{self.input_name}\" is muted={self.input_active}")
            self.parent.refresh_me(self)
        elif data['event'] == "on_obs_connected":
            # Get the current input state
            try:
                obs_input_name = self._get_input_name()
                input_muted = self.parent.get_input_mute_state(obs_input_name).input_muted
                self.input_active = not input_muted
                Logger.inst().debug(f"Input \"{self.input_name}\" is muted={self.input_active}")
                self.parent.refresh_me(self)
            except Exception as e:
                Logger.inst().error(f"Failed to get input mute state: {self.input_name} → {e}")
            # end try
        elif data['event'] == "on_obs_disconnected":
            self.input_active = None
            Logger.inst().debug(f"Input \"{self.input_name}\" is disconnected")
            self.parent.refresh_me(self)
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
            icon=self._get_icon()
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
            icon=self.icon_pressed
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

        # Change scene
        try:
            self.parent.toggle_input_mute(self._get_input_name())
            Logger.inst().info(f"Toggle input mute state: {self.input_name}")
        except Exception as e:
            Logger.inst().error(f"Failed to toggle input mute state: {self.input_name} → {e}")
        # end try

        # KeyDisplay
        key_display = KeyDisplay(
            text="",
            icon=self._get_icon()
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

# end OBSSceneButton

