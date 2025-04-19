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
from typing import Optional, List, Union
import toml
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from deckpilot.utils import Logger
from deckpilot.core import DeckRenderer, KeyDisplay
from deckpilot.comm import event_bus, EventType, context


# Logger
console = Console()


# Item
class Item(abc.ABC):
    """
    Represents an item in the panel.
    """

    # Constructor
    def __init__(
            self,
            name: str,
            path: Optional[Path] = None,
            parent: Optional['Panel'] = None
    ):
        """
        Constructor for the Item class.

        :param name: Name of the item.
        :type name: str
        :param path: Path to the item file.
        :type path: Path
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        self.name = name
        self.path = path
        self.parent = parent
        self.am = context.asset_manager

        # Events
        event_bus.subscribe(self, EventType.ITEM_RENDERED, self.on_item_rendered)
        event_bus.subscribe(self, EventType.ITEM_PRESSED, self.on_item_pressed)
        event_bus.subscribe(self, EventType.ITEM_RELEASED, self.on_item_released)
        event_bus.subscribe(self, EventType.CLOCK_TICK, self.on_periodic_tick)
        event_bus.subscribe(self, EventType.INTERNAL_CLOCK_TICK, self.on_internal_periodic_tick)

        # Icons
        self.icon_inactive = self.am.get_icon("default")
        self.icon_active = self.am.get_icon("default_pressed")
    # end __init__

    # region PROPERTIES

    # endregion PROPERTIES

    # region OVERRIDE

    # String representation
    def __str__(self):
        """
        String representation of the item.
        """
        return f"{self.__class__.__name__}({self.name})"
    # end __str__

    # String representation
    def __repr__(self):
        """
        String representation of the item.
        """
        return f"{self.__class__.__name__}({self.name})"
    # end __repr__

    # endregion OVERRIDE

    # region EVENTS

    # Receive data from dispatching
    @abc.abstractmethod
    def on_dispatch_received(self, source: 'Item', data: dict):
        """
        Dispatch data to the item.

        :param source: Source item.
        :type source: Item
        :param data: Data to dispatch.
        :type data: dict
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_dispatch_received")
    # end on_dispatch_received

    # On item rendered
    @abc.abstractmethod
    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Event handler for the "item_rendered" event.

        :return: KeyDisplay instance.
        :rtype: KeyDisplay
        """
        return KeyDisplay(
            text=self.name,
            icon=self.icon_inactive,
        )
    # end on_item_rendered

    # On item pressed
    @abc.abstractmethod
    def on_item_pressed(self, key_index)-> Optional[KeyDisplay]:
        """
        Event handler for the "item_pressed" event.
        """
        return KeyDisplay(
            text=self.name,
            icon=self.icon_active,
        )
    # end on_item_pressed

    # On item released
    @abc.abstractmethod
    def on_item_released(self, key_index)-> Optional[KeyDisplay]:
        """
        Event handler for the "item_released" event.
        """
        return KeyDisplay(
            text=self.name,
            icon=self.icon_inactive,
        )
    # end on_item_released

    # On periodic tick
    @abc.abstractmethod
    def on_periodic_tick(self, time_i: int, time_count: int) -> Optional[KeyDisplay]:
        """
        Event handler for the "periodic" event.

        :param time_i: Time index.
        :type time_i: int
        :param time_count: Time count.
        :type time_count: int
        """
        ...
    # end on_periodic_tick

    # On internal periodic tick
    def on_internal_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "internal_periodic" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_internal_periodic_tick")
    # end on_internal_periodic_tick

    # endregion EVENTS

# end Item


# Button
class Button(Item):
    """
    Represents a button on the Stream Deck.
    """

    # Constructor
    def __init__(
            self,
            name: str,
            path: Optional[Path] = None,
            parent: Optional['Panel'] = None
    ):
        """
        Constructor for the Button class.

        :param name: Name of the button.
        :type name: str
        :param path: Path to the button file.
        :type path: Path
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        # Call parent constructor
        super().__init__(
            name,
            path,
            parent
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

    # Receive data from dispatching
    def on_dispatch_received(self, source: 'Item', data: dict):
        """
        Dispatch data to the item.

        :param source: Source item.
        :type source: Item
        :param data: Data to dispatch.
        :type data: dict
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_dispatch_received")
    # end on_dispatch_received

    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Render button
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_renderer")

        # Return icon
        return KeyDisplay(
            text=self.name,
            icon=self.icon_inactive,
        )
    # end on_item_rendered

    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_pressed" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_pressed")
        icon = self.icon_active

        # Set pressed
        self._pressed = True

        # Get the icon
        return KeyDisplay(
            text=self.name,
            icon=icon,
        )
    # end on_item_pressed

    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_released")

        # Set pressed
        self._pressed = False

        # Return icon
        return KeyDisplay(
            text=self.name,
            icon=self.icon_inactive,
        )
    # end on_item_released

    def on_periodic_tick(self, time_i: int, time_count: int) -> Optional[KeyDisplay]:
        """
        Event handler for the "periodic" event.

        :param time_i: Time index.
        :type time_i: int
        :param time_count: Time count.
        :type time_count: int
        """
        # Log
        # Logger.inst().info(f"[blue bold]{self.__class__.__name__}[/]({self.name})::on_periodic_tick")
        return None
    # end on_periodic_tick

    # On internal periodic tick
    def on_internal_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "internal_periodic" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_internal_periodic_tick")
    # end on_internal_periodic_tick

    # endregion EVENTS

# end Button


# A special button for the parent panel
class ParentButton(Button):
    """
    Represents a button that navigates to the parent panel.
    """

    # Constructor
    def __init__(self, name, parent):
        """
        Constructor for the ParentButton class.

        :param name: Name of the button.
        :type name: str
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        super().__init__(name=name, parent=parent)
        self.icon_inactive = self.am.get_icon("parent")
        self.icon_active = self.am.get_icon("parent_pressed")
    # end __init__

    # region EVENTS

    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_released")

        # Send parent button pressed event
        event_bus.send_event(self.parent, EventType.PANEL_PARENT)

        # Return None because we don't want to change the icon
        # otherwise it would overwrite new icon
        return None
    # end on_item_released

    # endregion EVENTS

# end ParentButton


# A special button for next page
class NextPageButton(Button):
    """
    Represents a button that navigates to the next page.
    """

    # Constructor
    def __init__(self, name, parent):
        """
        Constructor for the NextPageButton class.

        :param name: Name of the button.
        :type name: str
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        super().__init__(name=name, parent=parent)
        self.icon_inactive = self.am.get_icon("next_page")
        self.icon_active = self.am.get_icon("next_page_pressed")
    # end __init__

    # region EVENTS

    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_released")

        # Send next page button pressed event
        event_bus.send_event(self.parent, EventType.PANEL_NEXT_PAGE)

        # Return None because we don't want to change the icon
        return None
    # end on_item_released

    # endregion EVENTS

# end NextPageButton


# A special button for previous page
class PreviousPageButton(Button):
    """
    Represents a button that navigates to the previous page.
    """

    # Constructor
    def __init__(self, name, parent):
        """
        Constructor for the PreviousPageButton class.

        :param name: Name of the button.
        :type name: str
        :param parent: Parent panel.
        :type parent: PanelNode
        """
        super().__init__(name=name, parent=parent)
        self.icon_inactive = self.am.get_icon("previous_page")
        self.icon_active = self.am.get_icon("previous_page_pressed")
    # end __init__

    # region EVENTS

    def on_item_released(self, key_index):
        """
        Event handler for the "on_item_released" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_released")

        # Send previous page button pressed event
        event_bus.send_event(self.parent, EventType.PANEL_PREVIOUS_PAGE)

        # Return None because we don't want to change the icon
        return None
    # end on_item_released

    # endregion EVENTS

# end PreviousPageButton


# A page on a panel
class PanelPage:
    """
    Represents a page on a panel.
    """

    # PageItem
    class PageItem:
        """
        Represents an item on a page.
        """

        # Constructor
        def __init__(self, position: int, item: Item):
            """
            Constructor for the PageItem class.

            :param position: Position of the item on the page.
            :param item: Item instance.
            """
            self.position = position
            self.item = item
        # end __init__

        # String representation
        def __str__(self):
            """
            String representation of the PageItem.
            """
            return f"<PageItem {self.position} {self.item}>"
        # end __str__

        # String representation
        def __repr__(self):
            """
            String representation of the PageItem.
            """
            return f"<PageItem {self.position} {self.item}>"
        # end __repr__

    # end PageItem

    # Constructor
    def __init__(self, page_number: int):
        """
        Constructor for the PanelPage class.

        :param page_number: Page number.
        :type page_number: int
        """
        self.capacity = 15
        self.cols = 5
        self.rows = 3
        self.page_number = page_number
        self.items = []
    # end __init__

    # region PROPERTIES

    @property
    def n_items(self):
        """
        Get the number of items on the page.
        """
        return len(self.items)
    # end n_items

    @property
    def space_left(self):
        """
        Get the space left on the page.
        """
        return self.capacity - len(self.items)
    # end space_left

    @property
    def is_full(self):
        """
        Check if the page is full.
        """
        return self.space_left == 0
    # end is_full

    @property
    def is_empty(self):
        """
        Check if the page is empty.
        """
        return self.space_left == self.capacity
    # end is_empty

    # endregion PROPERTIES

    # region PUBLIC

    # Get an item at a specific position
    def get_item(self, position: int) -> Item:
        """
        Get an item at a specific position on the page.

        :param position: Position of the item.
        :type position: int
        :return: Item instance.
        :rtype: Item
        :raise ValueError: If the item is not found on the page.
        """
        for item in self.items:
            if item.position == position:
                return item.item
            # end if
        # end for
        raise ValueError(f"Item at position {position} not found on page {self.page_number}")
    # end get_item

    # Get item position
    def get_item_position(self, item: Item) -> int:
        """
        Get the position of an item on the page.

        :param item: Item instance.
        :type item: Item
        :return: Position of the item.
        :rtype: int
        :raise ValueError: If the item is not found on the page.
        """
        for page_item in self.items:
            if page_item.item == item:
                return page_item.position
            # end if
        # end for
        raise ValueError(f"Item {item.name} not found on page {self.page_number}")
    # end get_item_position

    # Get an item by 2D position
    def get_item_by_2d_position(self, x: int, y: int) -> Item:
        """
        Get an item by its 2D position on the page.

        :param x: X position.
        :type x: int
        :param y: Y position.
        :type y: int
        :return: Item instance.
        :rtype: Item
        """
        index = y * self.cols + x
        return self.get_item(index)
    # end get_item_by_2d_position

    # Get 2D position of an item
    def get_2d_position(self, item: Item) -> (int, int):
        """
        Get the 2D position of an item on the page.

        :param item: Item instance.
        :type item: Item
        :return: Tuple of (x, y) position.
        :rtype: tuple
        """
        index = self.get_item_position(item)
        return index % self.cols, index // self.cols
    # end get_2d_position

    # Add an item
    def push(self, item: Item):
        """
        Adds an item to the page.

        :param item: Item instance.
        :type item: Item
        """
        if self.space_left <= 0:
            Logger.inst().error(f"Page {self.page_number} is full, cannot add item {item.name}")
            raise ValueError(f"Page {self.page_number} is full, cannot add item {item.name}")
        else:
            self.items.append(PanelPage.PageItem(len(self.items), item))
        # end if
    # end push

    # Remove an item
    def pull(self, item: Item):
        """
        Removes an item from the page.

        :param item: Item instance.
        :type item: Item
        """
        if item.name in self.items:
            del self.items[item.name]
            self._recompute_positions()
        else:
            Logger.inst().error(f"Item {item.name} not found on page {self.page_number}")
            raise ValueError(f"Item {item.name} not found on page {self.page_number}")
        # end if
    # end pull

    # endregion PUBLIC

    # region PRIVATE

    # Recompute position of items
    def _recompute_positions(self):
        """
        Recomputes the positions of items on the page.
        """
        for i, item in enumerate(self.items.values()):
            item.position = i
        # end for
    # end _recompute_positions

    # endregion PRIVATE

    # region MAGIC_METHODS

    # String representation
    def __str__(self):
        """
        String representation of the page.
        """
        return f"<Page {self.page_number} ({len(self.items)} items) {self.items}>"
    # end __str__

    # String representation
    def __repr__(self):
        """
        String representation of the page.
        """
        return f"<Page {self.page_number} ({len(self.items)} items) {self.items}>"
    # end __repr__

    # Iterator
    def __iter__(self):
        return iter(self.items)
    # end __iter__

    # Contains
    def __contains__(self, item):
        return item in self.items
    # end __contains__

    # Get item
    def __getitem__(self, index):
        return self.items[index]
    # end __getitem__

    def __len__(self):
        return len(self.items)
    # end __len__

    # endregion MAGIC_METHODS

# end PanelPage


# Panel
class Panel(Item):
    """
    Represents a node in the panel hierarchy.
    Each node can contain buttons and sub-panels.
    """

    # Constructor
    def __init__(
            self,
            name: str,
            path: Path,
            renderer: DeckRenderer,
            parent: Optional['Panel'] = None,
            active: bool = False
    ):
        """
        Constructor for the PanelNode class.

        Args:
            name (str): Name of the panel.
            path (Path): Path to the panel directory.
            renderer (DeckRenderer): Deck renderer instance.
            parent (PanelNode): Parent panel.
            active (bool): Active state.
        """
        super().__init__(
            name,
            path,
            parent
        )

        # Log
        Logger.inst().info(f"[{self.__class__.__name__}] Creating panel {name}, path={path}")

        # Attributes
        self.items = {}
        self.renderer = renderer
        self._active = active
        self.current_page_number = 0

        # Icons
        self.parent_folder_icon = context.asset_manager.get_icon("parent_folder")
        self.next_page_icon = context.asset_manager.get_icon("next_page")
        self.previous_page_icon = context.asset_manager.get_icon("previous_page")
        self.button_default_icon = context.asset_manager.get_icon("button_default")
        self.icon_inactive = self.am.get_icon("default_panel")
        self.icon_active = self.am.get_icon("default_panel_pressed")

        # Events
        event_bus.subscribe(self, EventType.KEY_RELEASED, self.on_key_released)
        event_bus.subscribe(self, EventType.KEY_PRESSED, self.on_key_pressed)
        event_bus.subscribe(self, EventType.PANEL_RENDERED, self.on_panel_rendered)
        event_bus.subscribe(self, EventType.PANEL_ACTIVATED, self.on_panel_activated)
        event_bus.subscribe(self, EventType.PANEL_DEACTIVATED, self.on_panel_deactivated)
        event_bus.subscribe(self, EventType.PANEL_PAGE_CHANGED, self.on_panel_page_changed)
        event_bus.subscribe(self, EventType.PANEL_NEXT_PAGE, self.on_panel_next_page)
        event_bus.subscribe(self, EventType.PANEL_PREVIOUS_PAGE, self.on_panel_previous_page)
        event_bus.subscribe(self, EventType.PANEL_PARENT, self.on_panel_parent_pressed)

        # If I find a items.toml in the directory
        if (self.path / "items.toml").exists():
            # I load the items listed in the toml file
            self.load_items()
        # end if

        # We assign a page to each item according to the number of buttons
        Logger.inst().debug(f"Panel {self.name} has {len(self.items)} items ({self.items}")
        self.pages = self._create_pages(self.items)
        Logger.inst().info(f"Assigned pages and elements: {self.pages}")
    # end __init__

    # region PROPERTIES

    # Active
    @property
    def active(self):
        """
        Get the active state of the panel.
        """
        return self._active
    # end active

    # Set active
    @active.setter
    def active(self, value):
        """
        Set the active state of the panel.
        """
        if value:
            context.set_active_panel(self)
        # end if

        # Newly activated panel
        if value and not self._active:
            # Send event
            event_bus.send_event(self, EventType.PANEL_ACTIVATED)
        # end if

        # Newly deactivated panel
        if not value and self._active:
            # Send event
            event_bus.send_event(self, EventType.PANEL_DEACTIVATED)
        # end if

        self._active = value
    # end active

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

    # region PUBLIC

    # Dispatch data across panel's items
    def dispatch(
            self,
            source: Item,
            data: dict
    ):
        """
        Dispatch data across the panel's items.

        :param source: Source item.
        :type source: Item
        :param data: Data to dispatch.
        :type data: dict
        """
        for item in self.items.values():
            if isinstance(item, Item):
                item.on_dispatch_received(source, data)
            # end if
        # end for
    # end dispatch

    # Go to parent
    def go_to_parent(self):
        """
        Moves to the parent panel.
        """
        if self.has_parent():
            self.parent.active = True
            self.active = False
            event_bus.send_event(self.parent, EventType.PANEL_RENDERED)
        # end if
    # end go_to_parent

    # Next page
    def next_page(self):
        """
        Moves to the next page in the panel.
        """
        # If there is a next page
        if self.current_page_number < self.n_pages - 1:
            event_bus.send_event(self, EventType.PANEL_PAGE_CHANGED, data=(self.current_page_number, self.current_page_number + 1))
            self.current_page_number += 1
            event_bus.send_event(self, EventType.PANEL_RENDERED)
        # end if
    # end next_page

    # Previous page
    def previous_page(self):
        """
        Moves to the previous page in the panel.
        """
        if self.current_page_number > 0:
            event_bus.send_event(self, EventType.PANEL_PAGE_CHANGED, data=(self.current_page_number, self.current_page_number - 1))
            self.current_page_number -= 1
            event_bus.send_event(self, EventType.PANEL_RENDERED)
        # end if
    # end previous_page

    # Has a next page ?
    def has_next_page(self):
        """
        Checks if the panel has a next page.
        """
        return self.current_page_number < self.n_pages - 1
    # end has_next_page

    # Has a previous page ?
    def has_previous_page(self):
        """
        Checks if the panel has a previous page.
        """
        return self.current_page_number > 0
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
            return context.get("active_panel")
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
            Logger.inst().error(f"Button {button_instance.name} already exists in {self.name}")
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

        :param child_name: Name of the child panel.
        :type child_name: str
        :param child: Child panel.
        :type child: PanelNode
        """
        if child_name in self.items:
            Logger.inst().warn(f"Child {child_name} already exists in {self.name}")
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
                Logger.inst().debug(f"Loading item {item_config['name']} of type {item_config['type']}")

                # Item parameters
                item_type = item_config['type']

                # If it's a button
                if item_type == 'button':
                    self.load_button(item_config)
                elif item_type == 'panel':
                    self.load_child(item_config)
                # end if
            # end for
        # end if
    # end load_items

    # Load button
    def load_button(self, button_config: dict):
        """
        Loads a button from the panel directory.

        :param button_config: Button parameters.
        :type button_config: dict
        """
        button_path = self.path / button_config['path']
        if button_path.exists():
            button_class = self._load_button_class(button_path)
            if button_class:
                button_params = button_config['params'] if 'params' in button_config else {}
                button_instance = button_class(
                    name=button_config['name'],
                    path=button_path,
                    parent=self,
                    **button_params
                )
                self.add_button(button_instance)
                Logger.inst().info(f"Add button: {button_instance.name}")
            # end if
        else:
            Logger.inst().error(f"Button {button_config['name']} not found in {self.name}")
        # end if
    # end load_button

    # Load child
    def load_child(self, child_config: dict):
        """
        Loads a child panel from the panel directory.

        :param child_config: Child parameters.
        :type child_config: dict
        """
        child_path = self.path / child_config['path']
        child_name = child_config['name']
        Logger.inst().info(f"Loading child: {child_path}, {child_name}")

        # If the child has a path directory which is not special (., ..), add it.
        if child_path.exists() and child_path.is_dir():
            child_params = child_config['params'] if 'params' in child_config else {}
            child = Panel(
                name=child_name,
                path=child_path,
                parent=self,
                renderer=self.renderer,
                **child_params
            )
            self.add_child(child.name, child)
            Logger.inst().info(f"Add child: {child.name} (Parent Panel: {self.name})")
        else:
            Logger.inst().error(f"Child {child_name} not valid: {child_path}")
        # end if
    # end load_child

    # Render panel
    def render(self):
        """
        Renders the current panel on the Stream Deck.
        """
        # Log
        Logger.inst().info(f"Rendering panel {self.name} for page {self.current_page_number}")
        Logger.inst().debug(f"Panel {self.name} render: {self.pages[self.current_page_number]}")

        # Clear the deck
        self.renderer.clear_deck()

        # Render each button of current page
        for i, page_item in enumerate(self.pages[self.current_page_number]):
            key_display = event_bus.send_event(page_item.item, EventType.ITEM_RENDERED)
            if key_display:
                Logger.inst().debug(f"RENDER_KEY {i} {key_display}")
                self.renderer.render_key(
                    key_index=i,
                    key_display=key_display
                )
            # end if
        # end for
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

    # endregion PUBLIC

    # region PRIVATE

    # Compute key shifting
    def _compute_key_shift(self):
        """
        Computes the key shift based on the current page.
        """
        # If we are on the first page, show "Upper" buttons
        if (self.current_page_number == 0 and self.parent) or self.has_previous_page():
            return 1
        # end if
        return 0
    # end _compute_key_shift

    # Load button class
    def _load_button_class(self, filepath: Union[Path, str]) -> Optional[type]:
        """
        Load a button class dynamically from a Python file.

        :param filepath: Path to the button file.
        :type filepath: Union[Path, str]
        :return: Button class.
        :rtype: type
        """
        # Module name
        if isinstance(filepath, Path):
            module_name = os.path.splitext(filepath.name)[0]
        else:
            module_name = os.path.splitext(os.path.basename(filepath))[0]
        # end if

        # Try
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(filepath))
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
            Logger.inst().error(f"Loading {filepath}: {e}")
        # end try

        return None
    # end _load_button_class

    # Handle special keys
    def _handle_special_key_pressed(self, key_index):
        """
        Handles special keys.

        Args:
            key_index (int): Index of the key.
        """
        # Check special keys
        if self.has_next_page() and key_index == 14:
            Logger.inst().event("Panel", self.name, "_handle_special_key_pressed", action="next_page")
            return True
        elif self.has_previous_page() and key_index == 0:
            Logger.inst().event("Panel", self.name, "_handle_special_key_pressed", action="previous_page")
            return True
        elif self.has_parent() and key_index == 0:
            Logger.inst().event("Panel", self.name, "_handle_special_key_pressed", action="parent")
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
        # if self._handle_special_key_pressed(key_index):
        #    return
        # end if

        try:
            # Items on this page
            current_page = self.pages[self.current_page_number]
            item = current_page.get_item(key_index)

            # Debug
            Logger.inst().debug(f"Panel {self.name} _handle_key_pressed key_index={key_index} item={item}")

            # Send item pressed event to the item
            key_display = event_bus.send_event(item, EventType.ITEM_PRESSED, key_index)

            # Update icon if needed
            if key_display:
                Logger.inst().debug(f"RENDER_KEY {key_index} {key_display}")
                self.renderer.render_key(
                    key_index=key_index,
                    key_display=key_display
                )
            # end if
        except ValueError as e:
            Logger.inst().debug(f"Panel {self.name} _handle_key_pressed key_index={key_index} out of range: {e}")
        # end try
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
            Logger.inst().event("Panel", self.name, "_handle_special_key_released", action="next_page")
            event_bus.send_event(self, EventType.PANEL_NEXT_PAGE)
            event_bus.send_event(self, EventType.PANEL_RENDERED)
            return True
        elif self.has_previous_page() and key_index == 0:
            Logger.inst().event("Panel", self.name, "_handle_special_key_released", action="previous_page")
            event_bus.send_event(self, EventType.PANEL_PREVIOUS_PAGE)
            event_bus.send_event(self, EventType.PANEL_RENDERED)
            return True
        elif self.has_parent() and key_index == 0:
            Logger.inst().event("Panel", self.name, "_handle_special_key_released", action="parent")
            event_bus.send_event(self, EventType.PANEL_DEACTIVATED)
            event_bus.send_event(self.parent, EventType.PANEL_ACTIVATED)
            event_bus.send_event(self.parent, EventType.PANEL_RENDERED)
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
        try:
            # Items on this page
            current_page = self.pages[self.current_page_number]
            item = current_page.get_item(key_index)

            # Debug
            Logger.inst().debug(f"Panel {self.name} _handle_key_released key_index={key_index} item={item}")

            # Send item pressed event to the item
            key_display = event_bus.send_event(item, EventType.ITEM_RELEASED, key_index)

            # If it's a button
            if isinstance(item, Button):
                # Update icon if needed
                if key_display:
                    Logger.inst().debug(f"RENDER_KEY {key_index} {key_display}")
                    self.renderer.render_key(
                        key_index=key_index,
                        key_display=key_display
                    )
                # end if
            elif isinstance(item, Panel):
                # If it's a panel, render the panel
                item.active = True
                self.active = False
                event_bus.send_event(item, EventType.PANEL_RENDERED)
            # end if
        except ValueError as e:
            Logger.inst().debug(f"Panel {self.name} _handle_key_released key_index={key_index} out of range: {e}")
        # end try
    # end _handle_key_released

    # Create pages
    def _create_pages(self, items) -> List[PanelPage]:
        """
        Create pages for the panel.

        :param items: List of items to be assigned to pages.
        :return: List of pages.
        """
        # Go through the items
        page = PanelPage(page_number=0)
        pages = [page]

        # Add the parent button if needed
        if self.parent:
            page.push(ParentButton(name="Parent", parent=self))
        # If the page is empty, and there is a previous page, add the previous page button

        # Copy items
        items_to_add = [item for item in items.values()]

        # For each item
        for i in range(len(items)):
            # Pop the item
            item = items_to_add.pop(0)

            # Add the parent button if needed
            # if self.parent and len(pages) == 0 and page.is_empty:
            #     page.push(ParentButton(name="Parent", parent=self))
            # If the page is empty, and there is a previous page, add the previous page button
            if len(pages) > 1 and page.is_empty:
                page.push(PreviousPageButton(name="PreviousPage", parent=self))
            # end if

            # If it's not the last space, add the item
            # OR if it's the last space and there is only one item left, add the item
            if page.space_left > 1 or (page.space_left == 1 and len(items_to_add) == 1):
                page.push(item)
            else:
                # If there is one space left, add the next page button
                page.push(NextPageButton(name="NextPage", parent=self))
                items_to_add.insert(0, item)
            # end if

            # If no space left, and remaining items, create a new page
            if page.is_full and len(items_to_add) != 0:
                page = PanelPage(page_number=len(pages))
                pages.append(page)
            # end if
        # end for

        return pages
    # end _create_pages

    # endregion PRIVATE

    # region EVENTS

    # On panel rendered
    def on_panel_rendered(self):
        """
        Event handler for the "panel_rendered" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_panel_rendered")
        self.render()
    # end on_panel_rendered

    # On panel activated
    def on_panel_activated(self):
        """
        Event handler for the "panel_activated" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_panel_activated")
    # end on_panel_activated

    # On panel deactivated
    def on_panel_deactivated(self):
        """
        Event handler for the "panel_deactivated" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_panel_deactivated")
    # end on_panel_deactivated

    # On page changed
    def on_panel_page_changed(self, old_page, new_page):
        """
        Event handler for the "page_changed" event.

        :param old_page: Old page index.
        :type old_page: int
        :param new_page: New page index.
        :type new_page: int
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_page_changed", old_page=old_page, new_page=new_page)
    # end on_panel_page_changed

    # On next page
    def on_panel_next_page(self):
        """
        Event handler for the "next_page" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_next_page")
        self.next_page()
    # end on_panel_next_page

    # On previous page
    def on_panel_previous_page(self):
        """
        Event handler for the "previous_page" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_previous_page")
        self.previous_page()
    # end on_panel_previous_page

    # On parent button pressed
    def on_panel_parent_pressed(self):
        """
        Event handler for the "parent" event.
        """
        Logger.inst().event(self.__class__.__name__, self.name, "on_parent")
        self.go_to_parent()
    # end on_panel_parent_pressed

    # On item rendered
    def on_item_rendered(self) -> Optional[KeyDisplay]:
        """
        Event handler for the "item_rendered" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_rendered")

        # Return icon
        return KeyDisplay(
            text=self.name,
            icon=self.icon_inactive
        )
    # end on_item_rendered

    # On item pressed
    def on_item_pressed(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "item_pressed" event.

        Args:
            key_index (int): Index of the key that was pressed.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_pressed", key_index=key_index)

        # Return icon
        return KeyDisplay(
            text=self.name,
            icon=self.icon_active
        )
    # end on_item_pressed

    # On dispatch received
    def on_dispatch_received(self, source: Item, data: dict):
        """
        Event handler for the "dispatch_received" event.

        :param source: Source item.
        :type source: Item
        :param data: Data received.
        :type data: dict
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_dispatch_received", source=source.name, data=data)
    # end on_dispatch_received

    # On item released
    def on_item_released(self, key_index) -> Optional[KeyDisplay]:
        """
        Event handler for the "item_released" event.

        Args:
            key_index (int): Index of the key that was released.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_item_released", key_index=key_index)

        # Return no icon to not overwrite new panel
        return None
    # end on_item_released

    # On key pressed
    def on_key_pressed(self, key_index):
        """
        Event handler for the "key_pressed" event.

        :param key_index: Index of the key that was pressed.
        :type key_index: int
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_key_pressed", key_index=key_index)

        # If active, handle key change
        if self.active:
            self._handle_key_pressed(key_index)
        # end if
    # end on_key_pressed

    # On key released
    def on_key_released(self, key_index):
        """
        Event handler for the "key_released" event.

        :param key_index: Index of the key that was released.
        :type key_index: int
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_key_released", key_index=key_index)

        # If active, handle key change
        if self.active:
            self._handle_key_released(key_index)
        # end if
    # end on_key_released

    # On periodic tick
    def on_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "periodic" event.

        :param time_i: Current time index.
        :type time_i: int
        :param time_count: Total time count.
        :type time_count: int
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_periodic_tick")

        # Propagate to children
        for i, page_item in enumerate(self.pages[self.current_page_number]):
            Logger.inst().debug(f"on_periodic_tick {i} {page_item}")
            if isinstance(page_item.item, Button):
                Logger.inst().debug(f"on_periodic_tick {i} {page_item.item} is button")
                key_display = event_bus.send_event(page_item.item, EventType.CLOCK_TICK, data=(time_i, time_count))
                if key_display:
                    Logger.inst().debug(f"RENDER_KEY {i} {key_display}")
                    self.renderer.render_key(
                        key_index=i,
                        key_display=key_display,
                    )
                # end if
            # end if
        # end for
    # end on_periodic_tick

    # On internal periodic tick
    def on_internal_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "internal_periodic" event.
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_internal_periodic_tick")
    # end on_internal_periodic_tick

    # endregion EVENTS

# end Panel


