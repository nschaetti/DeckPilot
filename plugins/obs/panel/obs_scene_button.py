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
import websocket._exceptions as ws_exceptions
from deckpilot.elements import Button, Item
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay
from deckpilot.comm import event_bus


class OBSSceneButton(Button):
    """
    Button that switches to a specific OBS scene.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            scene_name: str,
            icon_scene_inactive: str,
            icon_scene_active: str,
            icon_scene_error: str = "default_inactive",
            icon_pressed: str = "default_pressed",
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
        :param scene_name: Name of the OBS scene to switch to.
        :type scene_name: str
        :param icon_scene_inactive: Icon for the inactive state.
        :type icon_scene_inactive: str
        :param icon_scene_active: Icon for the active state.
        :type icon_scene_active: str
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

        # Assert that parent is a OBSPanel object
        #if not parent.__class__.__name__ == "OBSPanel":
        #    raise TypeError(f"Parent must be an OBSPanel object, got {type(parent)}")
        # end if
        self.parent = parent

        # Icons
        self.icon_scene_inactive = self.am.get_icon(icon_scene_inactive)
        self.icon_pressed = self.am.get_icon(icon_pressed)
        self.icon_scene_active = self.am.get_icon(icon_scene_active)
        self.icon_scene_error = self.am.get_icon(icon_scene_error)
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.icon_x_offset = icon_x_offset
        self.icon_y_offset = icon_y_offset

        # Scene active ?
        self.scene_name = scene_name
        self.scene_active = None
    # end __init__

    # region PRIVATE

    def _get_icon(self):
        """
        Get the icon for the button.

        :return: The icon for the button.
        """
        if self.scene_active:
            return self.icon_scene_active
        elif self.scene_active is not None:
            return self.icon_scene_inactive
        else:
            return self.icon_scene_error
        # end if
    # end _get_icon

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
        if data['event'] == "on_obs_connected" or data['event'] == "on_current_program_scene_changed":
            try:
                # Get the current scene
                obs_scene = self.parent.get_scene(self.scene_name)

                # Check if the scene is active
                self.scene_active = obs_scene.current

                # Debug log
                Logger.inst().debug(f"Scene \"{self.scene_name}\" is active={self.scene_active} ({obs_scene})")

                # Update the icon
                self.parent.refresh_me(self)
            except ws_exceptions.WebSocketConnectionClosedException as e:
                Logger.inst().error(f"Failed to get scene \"{self.scene_name}\" ({e}), connection closed")
                self.scene_active = None
            except Exception as e:
                Logger.inst().error(f"Failed to get scene \"{self.scene_name}\" ({e})")
                self.scene_active = None
            # end try
        elif data['event'] == "on_obs_disconnected":
            # Reset the scene active state
            self.scene_active = None
            Logger.inst().debug(f"Scene \"{self.scene_name}\" is active={self.scene_active}")
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

        event_bus.publish(
            "obs.scene.activate",
            {
                "scene": self.scene_name,
                "source": self.name,
            }
        )

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
