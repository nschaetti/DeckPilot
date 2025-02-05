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
import logging
from StreamDeck.ImageHelpers import PILHelper


# Render a panel on the Stream Deck
def render_panel(deck, panel_node):
    """
    Render the current panel on the Stream Deck.

    Args:
    - deck: StreamDeck - the StreamDeck instance
    - panel_node: PanelNode - the panel to display
    """
    logging.info(f"Rendering panel: {panel_node.name}")

    # Get all items in the panel (buttons + sub-panels)
    items = list(panel_node.buttons.items()) + list(panel_node.sub_panels.items())

    # Sort to keep a consistent order
    items.sort()

    # Get deck size
    key_count = deck.key_count()

    # Reset all keys
    deck.reset()

    # Assign items to keys
    for i in range(min(len(items), key_count)):
        name, data = items[i]
        print(f"Name: {name}")
        print(f"Data: {data}")
        # It's a button
        if isinstance(data, tuple):  # It's a button
            script_path, icon = data
        else:  # It's a sub-panel
            script_path, icon = None, data.icon
        # end if

        # Convert image to Stream Deck format
        if icon:
            print(f"Deck: {deck}")
            print(f"Icon: {icon}")
            image = PILHelper.create_scaled_image(deck, icon, margins=[5, 5, 5, 5])
            key_image = PILHelper.to_native_format(deck, image)
        else:
            key_image = PILHelper.create_blank_image(deck)
        # end if

        # Set key image
        deck.set_key_image(i, key_image)
    # end for

    # Store current panel
    deck.current_panel = panel_node
# end render_panel



