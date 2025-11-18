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

deckpilot.utils.utils module for DeckPilot.

"""

# Imports
import os
import cairosvg
import importlib.resources
from rich.console import Console
from PIL import Image
from PIL import ImageFont
from io import BytesIO

from deckpilot.utils import Logger


# Load image
def load_image(image_path):
    """
    Loads an image from a file.

    Args:
        image_path (str): Path to the image file.

    Returns:
        PIL.Image: The loaded image.
    """
    # Determine file extension
    file_ext = os.path.splitext(image_path)[1].lower()

    # Transform SVG to PNG
    if file_ext == '.svg':
        # Convert SVG to PNG
        png_filename = image_path.replace(".svg", ".png")
        cairosvg.svg2png(url=image_path, write_to=png_filename)
        image_filename = png_filename
    elif file_ext == '.png':
        image_filename = image_path
    else:
        raise ValueError("Unsupported file type: {}".format(file_ext))

    # end if
    try:
        return Image.open(image_filename)
    except ImportError:
        Logger.inst().error("ERROR: PIL is required to load images.")
        return None
    # end def load_image


# end def load_image
# Load package icon
def load_package_icon(icon_name):
    """Load an icon from the package.
    
    Args:
        icon_name (Any): Name of the icon file (e.g., "icon.svg").
    
    Returns:
        Any: Loaded image as PIL.Image object.
    """
    try:
        # Determine file extension
        file_ext = icon_name.lower().split('.')[-1]

        # Load the binary file from the package resources
        with importlib.resources.open_binary("deckpilot.icons", icon_name) as file:
            icon_data = file.read()  # Read file content

            if file_ext == "svg":
                # Convert SVG to PNG
                png_data = cairosvg.svg2png(bytestring=icon_data)
                return Image.open(BytesIO(png_data))
            elif file_ext == "png":
                # Load PNG directly
                return Image.open(BytesIO(icon_data))
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            # end if
        # end with
    except ImportError:
        Logger.inst().error("PIL and CairoSVG are required to load images.")
        return None
    except Exception as e:
        Logger.inst().error(f"Failed to load {icon_name}: {e}")
        return None
    # end def load_package_icon


# end def load_package_icon
def load_package_font(font_name, size=14):
    """
    Load a font from the package DeckPilot/assets/.

    Args:
        font_name (str): Name of the font file.
        size (int): Size of the font.

    Returns:
        PIL.ImageFont: Loaded font.
    """
    try:
        with importlib.resources.open_binary("deckpilot.assets", font_name) as file:
            return ImageFont.truetype(file, size)
        # end with
    except Exception as e:
        Logger.inst().error(f"Erreur: Impossible de charger la police {font_name}. {e}")
        return ImageFont.load_default()
    # end def load_package_font


# end def load_package_font
def load_font(font_path, size):
    """
    Load a font from the specified path.

    Args:
        font_path (str): Path to the font file.
        size (int): Size of the font.

    Returns:
        PIL.ImageFont: Loaded font.
    """
    try:
        # Open file
        with open(font_path, "rb") as file:
            # Load font
            font = ImageFont.truetype(file, size)
            return font
        # end with
    except Exception as e:
        Logger.inst().fatal(f"Cannot load font {font_path}. {e}")
        raise
    # end def load_font
# end def load_font
