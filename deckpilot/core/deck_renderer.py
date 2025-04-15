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
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from deckpilot.utils import load_package_font, load_package_icon


# Manage the rendering of the Stream Deck
class DeckRenderer:

    # Constructor
    def __init__(
            self,
            deck_manager
    ):
        """
        Constructor for the DeckRenderer class.

        Args:
        - deck_manager (DeckManager): Reference to the Stream Deck manager.
        """
        # Deck Manager
        self._deck_manager = deck_manager

        # Empty icon
        self.empty_icon = load_package_icon("empty.svg")
    # end __init__

    # region PROPERTIES

    @property
    def deck_manager(self):
        """
        Get the Stream Deck manager.
        """
        return self._deck_manager
    # end deck_manager

    @property
    def deck(self):
        """
        Get the Stream Deck device.
        """
        return self._deck_manager.deck
    # end deck

    # endregion PROPERTIES

    # region PUBLIC METHODS

    # Reset the Stream Deck
    def reset_deck(self):
        """
        Clear the Stream Deck.
        """
        self.deck.reset()
    # end reset_deck

    # Clear the Stream Deck
    def clear_deck(self):
        """
        Clear the Stream Deck.
        """
        # Clear the deck
        for key_index in range(self.deck.key_count()):
            self.render_key(key_index, self.empty_icon)
        # end for
    # end clear_deck

    # Update a key on the Stream Deck
    def update_key(self, key_index, image):
        """
        Update a key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        self.deck.set_key_image(key_index, image)
    # end update

    # Set a key on the Stream Deck
    def set_key(self, key_index, image):
        """
        Set a key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        self.update_key(key_index, image)
    # end set_key

    # Set image key on the Stream Deck
    def set_image_key(self, key_index, image):
        """
        Set an image key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        self.update_key(key_index, image)
    # end set_image_key

    # Render an icon on the Stream Deck
    def render_key(self, key_index, icon, text=""):
        """
        Render an icon on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - icon (PIL.Image): Icon to display on the key.
        - text (str): Text to display on the key.
        """
        # Create key image
        image = PILHelper.create_scaled_key_image(self.deck, icon, margins=[0, 0, 20, 0])
        draw = ImageDraw.Draw(image)

        # Load font from package
        font = load_package_font("barlow.otf", 14)
        draw.text((image.width / 2, image.height - 5), text=text, font=font, anchor="ms", fill="white")

        image = PILHelper.to_native_key_format(self.deck, image)

        # Update key
        self.deck.set_key_image(key_index, image)
    # end render_key

    # endregion PUBLIC METHODS

# end DeckRenderer
