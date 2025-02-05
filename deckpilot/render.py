

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

        # It's a button
        if isinstance(data, tuple):  # It's a button
            script_path, icon = data
        else:
            script_path, icon = None, data.icon
        # end if

        # Convert image to Stream Deck format
        if icon:
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



