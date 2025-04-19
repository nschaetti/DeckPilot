"""
███████╗ ███████╗ ██████╗██╗  ██╗██████╗ ██╗      ██████╗ ██╗████████╗
██╔══███ ██╔════╝██╔════╝██║  ██║██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
██║  ███╗█████╗  ██║     ███████║██║  ██║██║     ██║   ██║██║   ██║
██║  ███║██╔══╝  ██║     ██╔══██║██║  ██║██║     ██║   ██║██║   ██║
██████╔╝╝███████╗╚██████╗██║  ██║██████╔╝███████╗╚██████╔╝██║   ██║
 ╚═════  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═╝   ╚═╝

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
from importlib.resources import files
from PIL import Image, ImageFont
from deckpilot.utils import Logger, load_image, load_package_icon, load_package_font, load_font


# A class to manage assets (icons, fonts, etc.) for the application.
class AssetManager:
    """
    A class to manage assets (icons, fonts, etc.) for the application.
    """

    # Constructor
    def __init__(
            self,
            icons_directory: str = None,
            fonts_directory: str = None
    ):
        """
        Constructor for the AssetManager class.

        :param icons_directory: The directory where icons are stored.
        :type icons_directory: str
        :param fonts_directory: The directory where fonts are stored.
        :type fonts_directory: str
        """
        # Initialize the dictionaries to hold icons and fonts
        self.icons_directory = icons_directory
        self.fonts_directory = fonts_directory
        self.icons = {}
        self.fonts = {}

        # Load icon assets
        self.load_package_icons()
        self.load_icons(path=self.icons_directory)

        # Load font assets
        self.load_package_fonts()
        self.load_fonts(path=self.fonts_directory)
    # end __init__

    # region PUBLIC

    # Get icon
    def get_icon(self, icon_name: str) -> Image:
        """
        Get an icon by its name.

        :param icon_name: The name of the icon.
        :type icon_name: str
        :return: The icon image.
        :rtype: PIL.Image
        """
        return self.icons.get(icon_name)
    # end get_icon

    # Get font
    def get_font(self, font_name: str, size: int = 14) -> ImageFont:
        """
        Get a font by its name.

        :param font_name: The name of the font.
        :type font_name: str
        :param size: The size of the font.
        :type size: int
        :return: The font object.
        :rtype: Font
        """
        font_file = self.fonts.get(font_name)[0]
        font_type = self.fonts.get(font_name)[1]
        if font_type == "config":
            return load_font(font_file, size)
        elif font_type == "package":
            return load_package_font(font_file, size)
        # end if
    # end get_font

    # Load fonts
    def load_fonts(self, path: str):
        """
        Load fonts from the font directory.

        :param path: The path to the font directory.
        :type path: str
        """
        font_files = [entry for entry in os.listdir(path) if entry.endswith(('.ttf', '.otf'))]

        # Loop through each file in the directory
        for file in font_files:
            # Log
            Logger.inst().info(f"Loading font: {file}")

            # Name and path
            font_name = file.split(".")[0]
            font_path = os.path.join(path, file)

            # Load the font
            # self.fonts[font_name] = load_font(font_path, size)
            self.fonts[font_name] = (font_path, "config")
        # end for
    # end load_fonts

    # Load package fonts
    def load_package_fonts(self):
        """
        Load package fonts.
        """
        fonts_pkg = files("deckpilot.assets")
        package_files = [entry.name for entry in fonts_pkg.iterdir() if entry.is_file()]

        # Loop through each file in the package
        for file in package_files:
            # Info
            Logger.inst().info(f"Loading package font: {file}")

            # Name and extension of the file
            font_name = file.split(".")[0]

            # Load the font
            self.fonts[font_name] = (file, "package")
            # self.fonts[font_name] = load_package_font(file, size)
        # end for
    # end load_package_fonts

    # Load icons from the icon directory
    def load_icons(self, path: str):
        """
        Load icons from the icon directory.

        :param path: The path to the icon directory.
        :type path: str
        """
        icon_files = [entry for entry in os.listdir(path) if entry.endswith(('.png', '.svg'))]

        # Loop through each file in the directory
        for file in icon_files:
            # Log
            Logger.inst().info(f"Loading icon: {file}")

            # Name and path
            icon_name = file.split(".")[0]
            icon_path = os.path.join(path, file)

            # Load the icon
            self.icons[icon_name] = load_image(icon_path)
        # end for
    # end load_icons

    # Load package icons
    def load_package_icons(self):
        """
        Load package icons.
        """
        icons_pkg = files("deckpilot.icons")
        package_files = [entry.name for entry in icons_pkg.iterdir() if entry.is_file()]

        # Loop through each file in the package
        for file in package_files:
            # Log
            Logger.inst().info(f"Loading package icon: {file}")

            # Name and extension of the file
            icon_name = file.split(".")[0]

            # Load the icon
            self.icons[icon_name] = load_package_icon(file)
        # end for
    # end load_package_icons

    # endregion PUBLIC

# end AssetManager

