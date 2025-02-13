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
    # end __init__

    # region PROPERTIES

    # endregion PROPERTIES

    # region PUBLIC METHODS

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
            console.log(f"Checking icon: {icon_path}")
            # Load icon
            if os.path.exists(icon_path):
                console.log(f"Loading icon: {icon_path}")
                return load_image(icon_path)
            # end if
        # end for
        console.log(f"Using default icon for {self.name}")
        return self.default_icon
    # end get_icon

    # endregion PUBLIC METHODS

    # region EVENTS

    # On item rendered
    @abc.abstractmethod
    def on_item_rendered(self):
        """
        Event handler for the "item_rendered" event.
        """
        ...
    # end on_item_rendered

    # On item pressed
    @abc.abstractmethod
    def on_item_pressed(self, key_index):
        """
        Event handler for the "item_pressed" event.
        """
        ...
    # end on_item_pressed

    # On item released
    @abc.abstractmethod
    def on_item_released(self, key_index):
        """
        Event handler for the "item_released" event.
        """
        ...
    # end on_item_released

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
        super().__init__(
            name,
            path,
            parent,
            load_package_icon("button_default.svg")
        )
    # end __init__

    def on_item_rendered(self):
        """
        Render button
        """
        # Log
        console.log(f"{self.__class__.__name__}({self.name})::on_item_renderer")

        # Return icon
        return self.get_icon()
    # end on_item_rendered

    def on_item_pressed(self, key_index):
        """
        Event handler for the "on_item_pressed" event.
        """
        # Log
        console.log(f"{self.__class__.__name__}({self.name})::on_item_pressed")
        icon = self.get_icon("pressed")
        console.log(f"Icon: {icon}")
        # Get the icon
        return icon
    # end on_item_pressed

    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        console.log(f"{self.__class__.__name__}({self.name})::on_item_released")

        # Return icon
        return self.get_icon()
    # end on_item_released

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
    # end __init__

    # region PROPERTIES

    # Number of pages
    @property
    def n_pages(self):
        """
        Get the number of pages in the panel.
        """
        return self.get_n_pages(self.n_elements)
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
        self.active = active
    # end set_active

    # Set inactive
    def set_inactive(self):
        """
        Set the panel to inactive.
        """
        self.active = False
    # end set_inactive

    # Next page
    def next_page(self):
        """
        Moves to the next page in the panel.
        """
        if self.current_page < self.n_pages - 1:
            self.current_page += 1
            # self.render()
        # end if
    # end next_page

    # Previous page
    def previous_page(self):
        """
        Moves to the previous page in the panel.
        """
        if self.current_page > 0:
            self.current_page -= 1
            # self.render()
        # end if
    # end previous_page

    # Get the number of pages
    def get_n_pages(self, n_elements):
        """
        Get the number of pages in the panel.

        Args:
            n_elements (int): Number of elements.
            rec (bool):
        """
        element_count = n_elements
        first_page = True
        n_pages = 1

        if self.parent is None and element_count <= 14:
            return 1
        elif self.parent and element_count <= 13:
            return 1
        # end i

        # Remove first page
        if not self.parent:
            element_count -= 14
        else:
            element_count -= 13
        # end if

        while element_count > 0:
            n_pages += 1
            element_count -= 13
        # end while

        return n_pages
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
        # Clear the deck
        self.renderer.clear_deck()

        # If we are on the first page, show "Upper" buttons
        if self.current_page == 0 and self.parent:
            self.renderer.render_key(0, self.parent_folder_icon, "Parent")
        # end if

        # Not on first page, show "Previous" button
        if self.current_page > 0:
            self.renderer.render_key(0, self.previous_page_icon, "Précédent")
        # end if

        # Render each button
        for i, item in enumerate(self.items.values()):
            item_index = i + 1 if self.parent else i
            if item_index <= 13:
                item_icon = item.on_item_rendered()
                console.log(f"item_icon: {item_icon}")
                if item_icon:
                    self.renderer.render_key(item_index, item_icon, item.name)
                # end if
            # end if
        # end for

        # More than one page and not at the last
        if self.n_pages > 1 and self.current_page < self.n_pages - 1:
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

    # Handle key change
    def _handle_key_pressed(self, key_index):
        """
        Handles a key change event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Item index and item
        item_index = key_index - 1 if self.parent else key_index
        item = list(self.items.values())[item_index] if item_index >= 0 else self.parent

        # Log
        console.log(f"Panel({self.name})::handle_key_pressed item {item_index}, item type {item.__class__.__name__}")

        # Dispatch event
        item_icon = item.on_item_pressed(key_index)

        # Update icon if needed
        if item_icon:
            self.renderer.render_key(key_index, item_icon, item.name)
        # end if
    # end handle_key_pressed

    # end handle_key_pressed

    # Handle key released
    def _handle_key_released(self, key_index):
        """
        Handles a key change event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Item index
        item_index = key_index - 1 if self.parent else key_index
        item = list(self.items.values())[item_index] if item_index >= 0 else self.parent

        # Log
        console.log(f"Panel({self.name})::handle_key_released item {item_index}, item type {item.__class__.__name__}")

        # Dispatch event
        item_icon = item.on_item_released(key_index)

        # Update icon if needed
        if item_icon:
            self.renderer.render_key(key_index, item_icon, item.name)
        # end if

        # Key 0, and a parent
        if type(item) is Panel:
            self.set_inactive()
            item.set_active(True)
            item.render()
        # end if
    # end _handle_key_released

    # endregion PRIVATE METHODS

    # region EVENTS

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
        return self.get_icon()
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

    # endregion EVENTS

# end Panel


