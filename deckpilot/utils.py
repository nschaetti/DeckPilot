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
import cairosvg
import importlib.resources
from rich.console import Console
from PIL import Image
from PIL import ImageFont
from io import BytesIO


# Console
console = Console()


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
        console.log("ERROR: PIL is required to load images.")
        return None
    # end try
# end load_images


# Load package icon
def load_package_icon(icon_name):
    """
    Load an icon from the package.

    Args:
        icon_name (str): Name of the icon to load.

    Returns:
        PIL.Image: The loaded icon.
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
    except ImportError:
        console.log("[red]ERROR: PIL and CairoSVG are required to load images.[/red]")
        return None
    except Exception as e:
        console.log(f"[red]ERROR: Failed to load {icon_name}: {e}[/red]")
        return None
    # end try
# end load_package_icon


def load_package_font(font_name, size):
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
    except Exception as e:
        print(f"Erreur: Impossible de charger la police {font_name}. {e}")
        return ImageFont.load_default()
    # end try
# end load_package_font
