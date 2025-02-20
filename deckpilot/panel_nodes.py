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
import abc
import os
import importlib
import importlib.util
from typing import Any, Optional, Dict

import toml
from pathlib import Path

from pex.targets import current
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from .utils import load_image, load_package_icon


# Console
console = Console()


# Item
class Item(abc.ABC):
    """
    Represents an item in the panel.
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent,
            default_icon
    ):
        """
        Constructor for the Item class.

        Args:
            name (str): Name of the item.
            path (str): Path to the item file.
            parent (PanelNode): Parent panel.
            default_icon: Default icon for the item.
        """
        self.name = name
        self.path = path
        self.parent = parent
        self.default_icon = default_icon
        self.icons = {}

        # Load icons
        self._load_icons()
    # end __init__

    # region PROPERTIES

    # endregion PROPERTIES

    # region PUBLIC METHODS

    # Load icon
    def load_icon(self, path):
        """
        Loads an icon from a file.

        Args:
            path (str): Path to the icon file.
        """
        return load_image(path)
    # end load_icon

    # Get icon path
    def get_icon_path(self, state=None):
        """
        Get the icon path for the item.

        Args:
            state (str): State of the button.
        """
        for ext in ["svg", "png"]:
            # Icon path
            if state:
                icon_path = Path(self.path).parent / f"{self.name}_{state}.{ext}"
            else:
                icon_path = Path(self.path).parent / f"{self.name}.{ext}"
            # end if
            icon_path = str(icon_path)

            # Load icon
            if os.path.exists(icon_path):
                return icon_path
            # end if
        # end for

        return None
    # end get_icon_path

    # Get icon
    def get_icon(self, state=None):
        """
        Get the icon for the item.

        Args:
            state (str): State of the button.
        """
        for ext in ["svg", "png"]:
            # Icon path
            if state:
                icon_path = Path(self.path).parent / f"{self.name}_{state}.{ext}"
            else:
                icon_path = Path(self.path).parent / f"{self.name}.{ext}"
            # end if
            icon_path = str(icon_path)

            # Load icon
            if os.path.exists(icon_path):
                return load_image(icon_path)
            # end if
        # end for

        return self.default_icon
    # end get_icon

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    # Add icon
    def _add_icon(self, state, icon):
        """
        Adds an icon to the item.

        Args:
            state (str): State of the icon.
            icon (PIL.Image): Icon image.
        """
        self.icons[state] = icon
    # end _add_icon

    # Add icon by path
    def _add_icon_by_path(self, state, path):
        """
        Adds an icon to the item by path.

        Args:
            state (str): State of the icon.
            path (str): Path to the icon file.
        """
        console.log(f"Item {self.name}, adding icon {path} for state {state}")
        icon = load_image(path)
        self._add_icon(state, icon)
    # end _add_icon_by_path

    # Load icons
    def _load_icons(self):
        """
        Loads icons for the item.
        """
        icons = {}

        # List all files with the item name inside
        for file_name in os.listdir(os.path.dirname(self.path)):
            if file_name.startswith(self.name) and (file_name.endswith(".png") or file_name.endswith(".svg")):
                # State is after __
                state = file_name.split("__")[-1].split(".")[0]

                # Add icon
                self._add_icon_by_path(state, os.path.join(os.path.dirname(self.path), file_name))
            # end if
        # end for
    # end _load_icons

    # endregion PRIVATE METHODS

    # region EVENTS

    # On item rendered
    @abc.abstractmethod
    def on_item_rendered(self):
        """
        Event handler for the "item_rendered" event.
        """
        return self.get_icon("inactive")
    # end on_item_rendered

    # On item pressed
    @abc.abstractmethod
    def on_item_pressed(self, key_index)-> Any:
        """
        Event handler for the "item_pressed" event.
        """
        return self.get_icon("pressed")
    # end on_item_pressed

    # On item released
    @abc.abstractmethod
    def on_item_released(self, key_index)-> Any:
        """
        Event handler for the "item_released" event.
        """
        return self.get_icon("inactive")
    # end on_item_released

    # On periodic tick
    @abc.abstractmethod
    def on_periodic_tick(self) -> Any:
        """
        Event handler for the "periodic" event.
        """
        ...
    # end on_periodic_tick

    # endregion EVENTS

# end Item


# Button
class Button(Item):
    """
    Represents a button on the Stream Deck.
    """

    # Constructor
    def __init__(self, name, path, parent):
        """
        Constructor for the Button class.

        Args:
            name (str): Name of the button.
            path (str): Path to the button file.
            parent (PanelNode): Parent panel.
        """
        # Call parent constructor
        super().__init__(
            name,
            path,
            parent,
            default_icon=load_package_icon("button_default.svg")
        )

        # Pressed
        self._pressed = False
    # end __init__

    # region PROPERTIES

    @property
    def pressed(self):
        """
        Get the pressed state of the button.
        """
        return self._pressed
    # end pressed

    # endregion PROPERTIES

    # region EVENTS

    def on_item_rendered(self):
        """
        Render button
        """
        # Log
        console.log(f"[blue bold]{self.__class__.__name__}[/]({self.name})::on_item_renderer")

        # Return icon
        return self.get_icon()
    # end on_item_rendered

    def on_item_pressed(self, key_index):
        """
        Event handler for the "on_item_pressed" event.
        """
        # Log
        console.log(f"[blue bold]{self.__class__.__name__}[/]({self.name})::on_item_pressed")
        icon = self.get_icon("pressed")

        # Set pressed
        self._pressed = True

        # Get the icon
        return icon
    # end on_item_pressed

    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        console.log(f"[blue bold]{self.__class__.__name__}[/]({self.name})::on_item_released")

        # Set pressed
        self._pressed = False

        # Return icon
        return self.get_icon()
    # end on_item_released

    def on_periodic_tick(self) -> Any:
        """
        Event handler for the "periodic" event.
        """
        # Log
        # console.log(f"[blue bold]{self.__class__.__name__}[/]({self.name})::on_periodic_tick")
        return None
    # end on_periodic_tick

    # endregion EVENTS

# end Button


# Panel
class Panel(Item):
    """
    Represents a node in the panel hierarchy.
    Each node can contain buttons and sub-panels.
    """

    # Constructor
    def __init__(self, name, path, renderer, parent=None, active=False):
        """
        Constructor for the PanelNode class.

        Args:
            name (str): Name of the panel.
            path (str): Path to the panel directory.
            renderer (DeckRenderer): Deck renderer instance.
            parent (PanelNode): Parent panel.
            active (bool): Active state.
        """
        super().__init__(
            name,
            path,
            parent,
            default_icon=load_package_icon("folder_default.svg")
        )

        # Log
        console.log(f"Panel {name} created.")

        # Attributes
        self.items = {}
        self.renderer = renderer
        self.active = active
        self.current_page = 0

        # Icons
        self.parent_folder_icon = load_package_icon("parent_folder.svg")
        self.next_page_icon = load_package_icon("next_page.svg")
        self.previous_page_icon = load_package_icon("previous_page.svg")
        self.button_default_icon = load_package_icon("button_default.svg")

        # Load buttons and sub-panels
        if os.path.exists(os.path.join(self.path, "items.toml")):
            self.load_items()
        else:
            self.load_buttons()
            self.load_children()
        # end if

        # Compute page assignment
        self.pages = self._page_assignment()
        console.log(self.pages)
    # end __init__

    # region PROPERTIES

    # Number of pages
    @property
    def n_pages(self):
        """
        Get the number of pages in the panel.
        """
        return len(self.pages)
    # end n_pages

    # Number of buttons
    @property
    def n_buttons(self):
        """
        Get the number of buttons in the panel.
        """
        return len([button for button in self.items if isinstance(button, Button)])
    # end n_buttons

    # Number of children
    @property
    def n_children(self):
        """
        Get the number of children in the panel.
        """
        return len([child for child in self.items if isinstance(child, Panel)])
    # end n_children

    # Total number of elements
    @property
    def n_elements(self):
        """
        Get the total number of elements in the panel.
        """
        return len(self.items)
    # end n_elements

    # endregion PROPERTIES

    # region PUBLIC METHODS

    # Set active
    def set_active(self, active):
        """
        Set the active state of the panel.

        Args:
            active (bool): Active state.
        """
        # Activated event
        if active and not self.active:
            console.log(f"Panel({self.name})::set_active")
            self.on_panel_activated()
        # end if

        # Set active
        self.active = active
    # end set_active

    # Set inactive
    def set_inactive(self):
        """
        Set the panel to inactive.
        """
        # Deactivated event
        if self.active:
            console.log(f"Panel({self.name})::set_inactive")
            self.on_panel_deactivated()
        # end if

        # Set inactive
        self.active = False
    # end set_inactive

    # Next page
    def next_page(self):
        """
        Moves to the next page in the panel.
        """
        # If there is a next page
        if self.current_page < self.n_pages - 1:
            self.on_page_changed(self.current_page, self.current_page + 1)
            self.current_page += 1
        # end if
    # end next_page

    # Previous page
    def previous_page(self):
        """
        Moves to the previous page in the panel.
        """
        if self.current_page > 0:
            self.on_page_changed(self.current_page, self.current_page - 1)
            self.current_page -= 1
        # end if
    # end previous_page

    # Has a next page ?
    def has_next_page(self):
        """
        Checks if the panel has a next page.
        """
        return self.current_page < self.n_pages - 1
    # end has_next_page

    # Has a previous page ?
    def has_previous_page(self):
        """
        Checks if the panel has a previous page.
        """
        return self.current_page > 0
    # end has_previous_page

    # Has parent ?
    def has_parent(self):
        """
        Checks if the panel has a parent.
        """
        return self.parent is not None
    # end has_parent

    # Get the number of pages
    def get_n_pages(self):
        """
        Get the number of pages in the panel.
        """
        return len(self.pages)
    # end get_n_pages

    # Get active panel
    def get_active_panel(self):
        """
        Retrieves the active panel.

        Returns:
            PanelNode: The active panel.
        """
        if self.active:
            return self
        else:
            for sub_panel in self.items.values():
                if isinstance(sub_panel, Panel):
                    panel = sub_panel.get_active_panel()
                    if panel:
                        return panel
                    # end if
                # end if
            # end for
        # end if
    # end get_active_panel

    # Add button
    def add_button(
            self,
            button_instance
    ):
        """
        Adds a button instance to the panel.

        Args:
            button_instance (Button): Button instance.
        """
        if button_instance.name in self.items:
            console.log(f"[red]Button {button_instance.name} already exists in {self.name}[/]")
            return
        # end if
        self.items[button_instance.name] = button_instance
    # end add_button

    # Add child
    def add_child(
            self,
            child_name,
            child
    ):
        """
        Adds a child panel to the panel.

        Args:
            child_name (str): Name of the child panel.
            child (PanelNode): Child panel.
        """
        if child_name in self.items:
            console.log(f"[red]Child {child_name} already exists in {self.name}[/]")
            return
        # end if
        self.items[child_name] = child
    # end add_child

    # Load items
    def load_items(self):
        """
        Loads items from the items.toml file.
        """
        if os.path.exists(os.path.join(self.path, "items.toml")):
            items = toml.load(os.path.join(self.path, "items.toml"))
            for item_config in items['items']:
                # If it's a button
                if item_config['type'] == 'button':
                    self.load_button(item_config['name'])
                elif item_config['type'] == 'panel':
                    self.load_child(item_config['name'])
                # end if
            # end for
        # end if
    # end load_items

    # Load button
    def load_button(self, button_name):
        """
        Loads a button from the panel directory.

        Args:
            button_name (str): Name of the button.
        """
        button_path = os.path.join(self.path, f"{button_name}.py")
        if os.path.exists(button_path):
            button_class = self._load_button_class(button_path)
            if button_class:
                button_instance = button_class(name=button_name, path=button_path, parent=self)
                self.add_button(button_instance)
                console.log(f"[green]Add button:[/] {button_instance.name}")
            # end if
        else:
            console.log(f"[red]Button {button_name} not found in {self.name}[/]")
        # end if
    # end load_button

    # Load buttons
    def load_buttons(self):
        """
        Loads all button classes from Python files in the panel directory.
        """
        console.log(f"Loading buttons from {self.path}")
        for entry in os.scandir(self.path):
            if entry.is_file() and entry.name.endswith(".py"):
                button_name = os.path.splitext(entry.name)[0]
                self.load_button(button_name)
            # end if
        # end for
    # end load_buttons

    # Load child
    def load_child(self, child_name):
        """
        Loads a child panel from the panel directory.

        Args:
            child_name (str): Name of the child panel.
        """
        child_path = os.path.join(self.path, child_name)
        console.log(f"Loading child: {child_path}, {child_name}")
        if os.path.exists(child_path) and os.path.isdir(child_path) and not (child_name.startswith(".") or (child_name.startswith("__") and child_name.endswith("__"))):
            child = Panel(name=child_name, path=child_path, parent=self, renderer=self.renderer)
            self.add_child(child.name, child)
            console.log(f"[green]Add child:[/] {child.name} (Parent Panel: {self.name})")
        else:
            console.log(f"[red]Child {child_name} not found in {self.name}[/]")
        # end if
    # end load_child

    # Load children
    def load_children(self):
        """
        Loads all child panels from directories in the panel directory.
        """
        for entry in os.scandir(self.path):
            if entry.is_dir() and not (entry.name.startswith(".") or (entry.name.startswith("__") and entry.name.endswith("__"))):
                self.load_child(entry.name)
            # end if
        # end for
    # end load_children

    # Render panel
    def render(self):
        """
        Renders the current panel on the Stream Deck.
        """
        # Log
        console.log(f"Panel({self.name})::render")

        # Clear the deck
        self.renderer.clear_deck()

        # Index shifting
        key_shift = self._compute_key_shift()

        # If we are on the first page, show "Upper" buttons
        if self.current_page == 0 and self.parent:
            self.renderer.render_key(0, self.parent_folder_icon, "Parent")
        # end if

        # Not on first page, show "Previous" button
        if self.has_previous_page():
            self.renderer.render_key(0, self.previous_page_icon, "Précédent")
        # end if

        # Render each button of current page
        for i, item_name in enumerate(self.pages[self.current_page]):
            key_index = i + key_shift
            item = self.items[item_name]
            item_icon = item.on_item_rendered()
            if item_icon:
                self.renderer.render_key(key_index, item_icon, item.name)
            # end if
        # end for

        # More than one page and not at the last
        if self.has_next_page():
            self.renderer.render_key(14, self.next_page_icon, "Suivant")
        # end if

        # Render event
        self.on_item_rendered()
    # end render

    # Print structure
    def print_structure(self, node=None, tree=None):
        """
        Prints the structure of the panel hierarchy.

        Args:
            node (PanelNode): Current node.
            tree (str): Current tree structure.
        """
        is_root = False
        if node is None:
            is_root = True
            node = self
            tree = Tree(f"[bold cyan]📂 {node.name}[/]")  # Root panel
        # end if

        # Add buttons to the tree
        for _, item in node.items.items():
            if isinstance(item, Panel):
                child_tree = tree.add(f"[bold cyan]📂 {item.name}[/]")
                item.print_structure(item, child_tree)
            elif isinstance(item, Button):
                button_text = Text(f"🔘 {item.name}", style="green")
                tree.add(button_text)
            # end if
        # end for

        # Print the tree if we are at the root
        if is_root:
            console.print(tree)
        # end if
    # end print_structure

    # endregion PUBLIC METHODS

    # region PRIVATE METHODS

    # Compute key shifting
    def _compute_key_shift(self):
        """
        Computes the key shift based on the current page.
        """
        # If we are on the first page, show "Upper" buttons
        if (self.current_page == 0 and self.parent) or self.has_previous_page():
            return 1
        # end if
        return 0
    # end _compute_key_shift

    # Load button class
    def _load_button_class(self, filepath):
        """
        Load a button class dynamically from a Python file.

        Args:
            filepath (str): Path to the Python file.

        Returns:
            class or None: The button class or None if not found.
        """
        # Module name
        module_name = os.path.splitext(os.path.basename(filepath))[0]

        # Try
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find button class
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, Button) and obj is not Button:
                    return obj
                # end if
            # end for
        except Exception as e:
            console.log(f"[red]ERROR loading {filepath}: {e}[/red]")
        # end try

        return None
    # end _load_button_class

    #  Load icon
    def _load_icon(self):
        """
        Loads the icon for the panel.
        """
        icon_path = os.path.join(self.path, f"{self.name}.png")
        if os.path.exists(icon_path):
            return self._load_image(icon_path)
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
            console.log("ERROR: PIL is required to load images.")
            return None
        # end try
    # end _load_images

    # Handle special keys
    def _handle_special_key_pressed(self, key_index):
        """
        Handles special keys.

        Args:
            key_index (int): Index of the key.
        """
        # Check special keys
        if self.has_next_page() and key_index == 14:
            console.log(f"Panel({self.name})::_handle_special_key_pressed next page")
            return True
        elif self.has_previous_page() and key_index == 0:
            console.log(f"Panel({self.name})::_handle_special_key_pressed previous page")
            return True
        elif self.has_parent() and key_index == 0:
            console.log(f"Panel({self.name})::_handle_special_key_pressed parent")
            return True
        # end if
        return False
    # end _handle_special_key_pressed

    # Handle key change
    def _handle_key_pressed(self, key_index):
        """
        Handles a key change event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Check special keys
        if self._handle_special_key_pressed(key_index):
            return
        # end if

        # Items on this page
        page_items = self.pages[self.current_page]

        # Item index and item
        item_index = key_index
        item_index = item_index - 1 if self.parent or self.has_previous_page() else item_index

        # Get item
        item = self.items[page_items[item_index]]

        # Log
        console.log(f"Panel({self.name})::handle_key_pressed item {item_index}, item type {item.__class__.__name__}")

        # Dispatch event
        item_icon = item.on_item_pressed(key_index)

        # Update icon if needed
        if item_icon:
            self.renderer.render_key(key_index, item_icon, item.name)
        # end if
    # end handle_key_pressed

    # Handle special keys
    def _handle_special_key_released(self, key_index) -> bool:
        """
        Handles special keys.

        Args:
            key_index (int): Index of the key.
        """
        # Check special keys
        if self.has_next_page() and key_index == 14:
            console.log(f"Panel({self.name})::_handle_special_key_released next page")
            self.next_page()
            self.render()
            return True
        elif self.has_previous_page() and key_index == 0:
            console.log(f"Panel({self.name})::_handle_special_key_released previous page")
            self.previous_page()
            self.render()
            return True
        elif self.has_parent() and key_index == 0:
            console.log(f"Panel({self.name})::_handle_special_key_released parent")
            self.set_inactive()
            self.parent.set_active(True)
            self.parent.render()
            return True
        # end if
        return False
    # end _handle_special_key_released

    # Handle key released
    def _handle_key_released(self, key_index):
        """
        Handles a key change event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Check special keys
        if self._handle_special_key_released(key_index):
            return
        # end if

        # Items on this page
        page_items = self.pages[self.current_page]

        # Item index and item
        item_index = key_index
        item_index = item_index - 1 if self.parent or self.has_previous_page() else item_index

        # Get item
        item = self.items[page_items[item_index]]

        # Log
        console.log(f"Panel({self.name})::handle_key_released item {item_index}, item type {item.__class__.__name__}")

        # Dispatch event
        item_icon = item.on_item_released(key_index)

        # Update icon if needed
        if item_icon:
            self.renderer.render_key(key_index, item_icon, item.name)
        # end if

        # Switch to the active panel
        if type(item) is Panel:
            self.set_inactive()
            item.set_active(True)
            item.render()
        # end if
    # end _handle_key_released

    # Page assignment
    def _page_assignment(self):
        """
        Assigns items to pages.
        """
        # Copy items
        items = list(self.items.keys())

        # How many items on the first page
        n_items_first_page = 14 if self.parent else 15

        # Remove one item for next page button
        if len(items) <= n_items_first_page:
            return {0: items}
        # end if

        # Current page
        current_page = 0

        # Pages
        pages = {}

        # While there are still items to assign
        while len(items) > 0:
            # Items on current page
            n_items = n_items_first_page if current_page == 0 else 14

            # If there are more items than can fit on the page
            if len(items) > n_items:
                n_items -= 1
            # end if

            # Assign the calculated number of items to the current page
            pages[current_page] = items[:n_items]

            # Remove the assigned items
            items = items[n_items:]

            # Next page
            current_page += 1
        # end while

        return pages
    # end _page_assigment

    # endregion PRIVATE METHODS

    # region EVENTS

    # On panel activated
    def on_panel_activated(self):
        """
        Event handler for the "panel_activated" event.
        """
        console.log(f"Panel({self.name})::on_panel_activated")
    # end on_panel_activated

    # On panel deactivated
    def on_panel_deactivated(self):
        """
        Event handler for the "panel_deactivated" event.
        """
        console.log(f"Panel({self.name})::on_panel_deactivated")
    # end on_panel_deactivated

    # On page changed
    def on_page_changed(self, old_page, new_page):
        """
        Event handler for the "page_changed" event.

        Args:
            old_page (int): Old page index.
            new_page (int): New page index.
        """
        console.log(f"Panel({self.name})::on_page_changed {old_page} -> {new_page}")
    # end on_page_changed

    # On item rendered
    def on_item_rendered(self):
        """
        Event handler for the "item_rendered" event.
        """
        # Log
        console.log(f"Panel({self.name})::on_item_renderer")

        # Return icon
        return self.get_icon()
    # end on_item_rendered

    # On item pressed
    def on_item_pressed(self, key_index):
        """
        Event handler for the "item_pressed" event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Log
        console.log(f"Panel({self.name})::on_item_pressed")

        # Return icon
        return self.get_icon("pressed")
    # end on_item_pressed

    # On item released
    def on_item_released(self, key_index):
        """
        Event handler for the "item_released" event.

        Args:
            key_index (int): Index of the key that was released.
        """
        # Log
        console.log(f"Panel({self.name})::on_item_released")

        # Return icon
        return None
    # end on_item_released

    # On key pressed
    def on_key_pressed(self, key_index):
        """
        Event handler for the "key_pressed" event.

        Args:
            deck (StreamDeck): StreamDeck instance.
            state (bool): State of the key (pressed or released
        """
        # Log
        console.log(f"Panel({self.name})::on_key_pressed {key_index}")

        # If active, handle key change
        if self.active:
            self._handle_key_pressed(key_index)
        # end if
    # end on_key_pressed

    # On key released
    def on_key_released(self, key_index):
        """
        Event handler for the "key_released" event.

        Args:
            key_index (int): Index of the key that was pressed.
            state (bool): State of the key (pressed or released
        """
        # Log
        console.log(f"Panel({self.name})::on_key_released {key_index}")

        # If active, handle key change
        if self.active:
            self._handle_key_released(key_index)
        # end if
    # end on_key_released

    # On periodic tick
    def on_periodic_tick(self):
        """
        Event handler for the "periodic" event.
        """
        # Log
        console.log(f"Panel({self.name})::on_periodic_tick")

        # Key shift
        key_shift = self._compute_key_shift()

        # Propagate to children
        for i, item_name in enumerate(self.pages[self.current_page]):
            key_index = i + key_shift
            item = self.items[item_name]
            if isinstance(item, Button):
                tick_icon = item.on_periodic_tick()
                if tick_icon:
                    self.renderer.render_key(key_index, tick_icon, item.name)
                # end if
            # end if
        # end for
    # end on_periodic_tick

    # endregion EVENTS

# end Panel


