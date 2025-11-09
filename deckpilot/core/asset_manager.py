"""deckpilot.core.asset_manager module for DeckPilot.
"""


# Imports
import os
from importlib.resources import files
from PIL import Image, ImageFont
import threading
from playsound import playsound

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
            fonts_directory: str = None,
            sounds_directory: str = None,
    ):
        """Constructor for the AssetManager class.
        
        Args:
            icons_directory (str): The directory where icons are stored.
            fonts_directory (str): The directory where fonts are stored.
            sounds_directory (str): The directory where sounds are stored.
        """
        # Initialize the dictionaries to hold icons and fonts
        self.icons_directory = icons_directory
        self.fonts_directory = fonts_directory
        self.sounds_directory = sounds_directory
        self.icons = {}
        self.fonts = {}
        self.sounds = {}

        # Load icon assets
        self.load_package_icons()
        self.load_icons(path=self.icons_directory)

        # Load font assets
        self.load_package_fonts()
        self.load_fonts(path=self.fonts_directory)

        # Load sound assets
        self.load_package_sounds()
        self.load_sounds(path=self.sounds_directory)

    # end def __init__
    # region PUBLIC

    # Play a sound
    def play_sound(self, sound_name: str):
        """Play a sound by its name (non-blocking).
        
        Args:
            sound_name (str): The name of the sound.
        """
        # Get the sound
        sound = self.sounds.get(sound_name)
        if sound:
            sound_path = sound[0]
            Logger.inst().debug(f"Playing sound: {sound_path}")
            if sound_path:
                threading.Thread(target=playsound, args=(sound_path,), daemon=True).start()
            # end if
        # end if

    # end def play_sound
    # Get sound
    def get_sound(self, sound_name: str) -> str:
        """Get a sound by its name.
        
        Args:
            sound_name (str): The name of the sound.
        
        Returns:
            str: The path to the sound file.
        """
        return self.sounds.get(sound_name)[0]

    # end def get_sound
    # Get icon
    def get_icon(self, icon_name: str) -> Image:
        """Get an icon by its name.
        
        Args:
            icon_name (str): The name of the icon.
        
        Returns:
            PIL.Image: The icon image.
        """
        return self.icons.get(icon_name)

    # end def get_icon
    # Get font
    def get_font(self, font_name: str, size: int = 14) -> ImageFont:
        """Get a font by its name.
        
        Args:
            font_name (str): The name of the font.
            size (int): The size of the font.
        
        Returns:
            Font: The font object.
        """
        font_file = self.fonts.get(font_name)[0]
        font_type = self.fonts.get(font_name)[1]
        if font_type == "config":
            return load_font(font_file, size)
        elif font_type == "package":
            return load_package_font(font_file, size)

        # end if
    # end def get_font
    # Load fonts
    def load_fonts(self, path: str):
        """Load fonts from the font directory.
        
        Args:
            path (str): The path to the font directory.
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
    # end def load_fonts
    # Load sounds
    def load_sounds(self, path: str):
        """Load sounds from the sound directory.
        
        Args:
            path (str): The path to the sound directory.
        """
        sound_files = [entry for entry in os.listdir(path) if entry.endswith(('.wav', '.mp3'))]

        # Loop through each file in the directory
        for file in sound_files:
            # Log
            Logger.inst().info(f"Loading sound: {file}")

            # Name and path
            sound_name = file.split(".")[0]
            sound_path = os.path.join(path, file)

            # Load the sound
            self.sounds[sound_name] = (sound_path, "config")

        # end for
    # end def load_sounds
    # Load package sounds
    def load_package_sounds(self):
        """
        Load package sounds.
        """
        sounds_pkg = files("deckpilot.sounds")
        package_files = [entry for entry in sounds_pkg.iterdir() if entry.is_file()]

        # Loop through each file in the package
        for entry in package_files:
            # Info
            Logger.inst().info(f"Loading package sound: {entry.name}")

            # Name and extension of the file
            sound_name = entry.stem

            # Load the sound
            self.sounds[sound_name] = (str(entry), "package")

        # end for
    # end def load_package_sounds
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
    # end def load_package_fonts
    # Load icons from the icon directory
    def load_icons(self, path: str):
        """Load icons from the icon directory.
        
        Args:
            path (str): The path to the icon directory.
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
    # end def load_icons
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
    # end def load_package_icons
    # endregion PUBLIC


# end class AssetManager
