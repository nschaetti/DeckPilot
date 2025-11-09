"""deckpilot.core.deck_renderer module for DeckPilot.
"""


# Imports
import os
from typing import Optional
import threading

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from deckpilot.comm import context
from deckpilot.utils import load_package_icon
from deckpilot.utils import Logger


# Class that specify what to display in a key
class KeyDisplay:
    """
    Represents the display of a key on the Stream Deck.
    """

    # Constructor
    def __init__(
            self,
            text: str,
            icon: Image,
            font: Optional[ImageFont] = None,
            margin_top: int = 0,
            margin_bottom: int = 20,
            margin_left: int = 0,
            margin_right: int = 0,
            text_anchor: str = "ms",
            text_color: str = "white",
    ):
        """Constructor for the KeyDisplay class.
        
        Args:
            text (str): Text to display on the key.
            icon (Image): Icon to display on the key.
            font (ImageFont): Font to use for the text.
            margin_top (int): Top margin for the icon.
            margin_bottom (int): Bottom margin for the icon.
            margin_left (int): Left margin for the icon.
            margin_right (int): Right margin for the icon.
            text_anchor (str): Text anchor position.
            text_color (str): Color of the text.
        """
        self.text = text
        self.icon = icon
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.font = font
        self.text_anchor = text_anchor
        self.text_color = text_color

    # end def __init__
    # region OVERRIDE

    def __repr__(self):
        """
        String representation of the KeyDisplay object.
        """
        return (
            f"KeyDisplay(text={self.text}, icon={self.icon}, font={self.font}, "
            f"margins=({self.margin_top}, {self.margin_right}, {self.margin_bottom}, "
            f"{self.margin_left}), text_anchor={self.text_anchor}, text_color={self.text_color})"
        )

    # end def __repr__
    def __str__(self):
        """
        String representation of the KeyDisplay object.
        """
        return (
            f"KeyDisplay(text={self.text}, icon={self.icon}, font={self.font}, "
            f"margins=({self.margin_top}, {self.margin_right}, {self.margin_bottom}, {self.margin_left}), "
            f"text_anchor={self.text_anchor}, text_color={self.text_color})"
        )



    # end def __str__
# end class KeyDisplay
# Manage the rendering of the Stream Deck
class DeckRenderer:
    """Render text, icons, and panels on the connected Stream Deck device."""

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
        self.am = context.asset_manager
        self.empty_icon = self.am.get_icon("empty")

        # Locks
        self._render_lock = threading.RLock()

    # end def __init__
    # region PROPERTIES

    @property
    def deck_manager(self):
        """
        Get the Stream Deck manager.
        """
        return self._deck_manager

    # end def deck_manager
    @property
    def deck(self):
        """
        Get the Stream Deck device.
        """
        return self._deck_manager.deck

    # end def deck
    # endregion PROPERTIES

    # region PUBLIC METHODS

    # Reset the Stream Deck
    def reset_deck(self):
        """
        Clear the Stream Deck.
        """
        self.deck.reset()

    # end def reset_deck
    # Clear the Stream Deck
    def clear_deck(self):
        """
        Clear the Stream Deck.
        """
        with self._render_lock:
            # Clear the deck
            for key_index in range(self.deck.key_count()):
                Logger.inst().debug(f"RENDER_KEY {key_index} {self.empty_icon}")
                self.render_key(
                    key_index,
                    KeyDisplay(
                        text="",
                        icon=self.empty_icon,
                        font=None,
                        margin_top=0,
                        margin_bottom=0,
                        margin_left=0,
                        margin_right=0,
                        text_anchor="ms",
                        text_color="white"
                    )
                )

            # end for
        # end with
    # end def clear_deck
    # Update a key on the Stream Deck
    def update_key(self, key_index, image):
        """
        Update a key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        with self._render_lock:
            self.deck.set_key_image(key_index, image)

        # end with
    # end def update_key
    # Set a key on the Stream Deck
    def set_key(self, key_index, image):
        """
        Set a key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        self.update_key(key_index, image)

    # end def set_key
    # Set image key on the Stream Deck
    def set_image_key(self, key_index, image):
        """
        Set an image key on the Stream Deck.

        Args:
        - key_index (int): Index of the key to update.
        - image (PIL.Image): Image to display on the key.
        """
        self.update_key(key_index, image)

    # end def set_image_key
    # Render an icon on the Stream Deck
    def render_key(
            self,
            key_index: int,
            key_display: KeyDisplay
    ):
        """Render an icon on the Stream Deck.
        
        Args:
            key_index (int): Index of the key to update.
            key_display (KeyDisplay): KeyDisplay object containing the text and icon to display.
        """
        with self._render_lock:
            # Create key image
            image = PILHelper.create_scaled_key_image(
                self.deck,
                key_display.icon,
                margins=[
                    key_display.margin_top,
                    key_display.margin_right,
                    key_display.margin_bottom,
                    key_display.margin_left
                ]
            )

            # Default font
            font = self.am.get_font("default") if key_display.font is None else key_display.font

            if len(key_display.text) > 0:
                # Drawing canvas
                draw = ImageDraw.Draw(image)

                # Draw text on the image
                draw.text(
                    xy=(image.width / 2, image.height - 5),
                    text=key_display.text,
                    font=font,
                    anchor=key_display.text_anchor,
                    fill=key_display.text_color
                )

            # end if
            # Transform image to native key format
            image = PILHelper.to_native_key_format(self.deck, image)

            # Log
            Logger.inst().debug(f"Deck {self.deck.id()} Key {key_index} = {key_display.text} with icon {key_display.icon}")

            # Update key
            self.deck.set_key_image(key_index, image)

        # end with
    # end def render_key
    # endregion PUBLIC METHODS

# end class DeckRenderer
