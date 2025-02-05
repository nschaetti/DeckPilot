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
import os
import importlib.util
import logging


# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PanelNode:
    """
    Represents a node in the panel hierarchy.
    Each node can contain buttons and sub-panels.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent=None
    ):
        """
        Constructor for the PanelNode class.

        Args:
            name (str): Name of the panel.
            path (str): Path to the panel directory.
            parent (PanelNode): Parent panel.
        """
        self.name = name
        self.path = path
        self.parent = parent
        self.buttons = {}  # {button_name: button_path}
        self.sub_panels = {}  # {sub_panel_name: PanelNode}
        self.icon = self._load_icon()
    # end __init__

    # region PUBLIC METHODS

    # Add button
    def add_button(
            self,
            button_name,
            button_path
    ):
        """
        Adds a button to the current panel.

        Args:
            button_name (str): Name of the button.
            button_path (str): Path to the Python file that will be executed when the button is pressed
        """
        icon_path = os.path.join(self.path, f"{button_name}.png")
        icon = self._load_image(icon_path) if os.path.exists(icon_path) else None
        self.buttons[button_name] = (button_path, icon)
    # end add_button

    # Add sub-panel
    def add_sub_panel(
            self,
            sub_panel_name,
            sub_panel_node
    ):
        """
        Adds a sub-panel (child panel).

        Args:
            sub_panel_name (str): Name of the sub-panel.
            sub_panel_node (PanelNode): Sub-panel node.
        """
        self.sub_panels[sub_panel_name] = sub_panel_node
    # end add_sub_panel

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    #  Load icon
    def _load_icon(self):
        """
        Loads the icon for the panel.
        """
        icon_path = os.path.join(self.path, f"{self.name}.png")
        if os.path.exists(icon_path):
            return icon_path
        # end if
        return None
    # end _load_icon

    # Load image
    def _load_image(self, image_path):
        """
        Loads an image from a file.

        Args:
            image_path (str): Path to the image file.

        Returns:
            PIL.Image: The loaded image.
        """
        try:
            from PIL import Image
            return Image.open(image_path)
        except ImportError:
            logging.error("PIL is required to load images.")
            return None
        # end try
    # end _load_images

    # endregion PRIVATE METHODS

# end PanelNode


# PanelRegistry
class PanelRegistry:

    # Constructor
    def __init__(
            self,
            base_path
    ):
        """
        Constructor for the PanelRegistry class.

        Args:
            base_path (str): Path to the directory where the buttons and sub-panels are stored.
        """
        self.base_path = base_path
        self.root = PanelNode("root", base_path)
        self.load_panel(self.root)
    # end __init__

    # Load panel
    def load_panel(
            self,
            panel_node
    ):
        """
        Recursively loads a panel and its sub-panels.

        Args:
            panel_node (PanelNode): Panel node to load.
        """
        if not os.path.exists(panel_node.path):
            logging.error(f"Panel {panel_node.path} does not exist.")
            return
        # end if

        # For each file in the directory
        for entry in os.scandir(panel_node.path):
            if entry.is_file() and entry.name.endswith(".py"):
                button_name = os.path.splitext(entry.name)[0]
                panel_node.add_button(button_name, entry.path)
                logging.info(f"Added button: {button_name} -> {entry.path} (Panel: {panel_node.name})")
            elif entry.is_dir():
                sub_panel_node = PanelNode(entry.name, entry.path, parent=panel_node)
                panel_node.add_sub_panel(entry.name, sub_panel_node)
                logging.info(f"Added sub-panel: {entry.name} (Panel: {panel_node.name})")
                self.load_panel(sub_panel_node)
            # end if
        # end for
    # end load_panel

    # Get panel
    def get_panel(self, path_list):
        """
        Retrieves a panel node based on a list representing the path.

        Args:
            path_list (list): List of panel names representing the path.

        Returns:
            PanelNode or None: The corresponding panel node, or None if not found.
        """
        current_node = self.root
        for panel_name in path_list:
            if panel_name in current_node.sub_panels:
                current_node = current_node.sub_panels[panel_name]
            else:
                logging.warning(f"Panel '{panel_name}' not found in hierarchy.")
                return None
            # end if
        # end for
        return current_node
    # end get_panel

    def print_structure(
            self,
            node=None,
            indent=0
    ):
        """
        Prints the hierarchy of panels and buttons.

        Args:
            node (PanelNode): The current node to print.
            indent (int): Indentation level for hierarchy display.
        """
        if node is None:
            node = self.root
        # end if

        print("  " * indent + f"[Panel] {node.name}")
        if node.icon:
            print("  " * indent + "  (Icon loaded)")
        # end if

        for button_name, (button_path, button_icon) in node.buttons.items():
            icon_status = " (Icon loaded)" if button_icon else ""
            print("  " * (indent + 1) + f"🔘 {button_name} → {button_path}{icon_status}")
        # end for

        for sub_panel in node.sub_panels.values():
            self.print_structure(sub_panel, indent + 1)
        # end for
    # end print_structure

# end PanelRegistry

