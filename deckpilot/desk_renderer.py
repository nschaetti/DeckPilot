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
        self._deck_manager = deck_manager
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

    # Clear the Stream Deck
    def clear_deck(self):
        """
        Clear the Stream Deck.
        """
        self.deck.reset()
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

    # Render the content of a PanelNode on the Stream Deck
    def render(self, panel_node):
        """
        Render the content of a PanelNode on the Stream Deck.

        Args:
        - panel_node (PanelNode): PanelNode to render.
        """
        pass
    # end render

    # endregion PUBLIC METHODS

# end DeckRenderer
