#!/usr/bin/env python3
"""
Test script for the Stream Deck simulator.
This script tests the basic functionality of the simulator.
"""

import time
import sys
from PIL import Image, ImageDraw, ImageFont

# Import the simulator
from deckpilot.simulator.switcher import DeviceManager, use_simulator
from deckpilot.simulator.gui import launch_simulator

# Use the simulator
use_simulator(True)

# Create a device manager
manager = DeviceManager()

# Enumerate devices
decks = manager.enumerate()

if not decks:
    print("No Stream Deck devices found.")
    sys.exit(1)

# Use the first deck
deck = decks[0]
print(f"Using {deck.deck_type()} (Serial: {deck.get_serial_number()})")

# Open the deck
deck.open()

# Set brightness
deck.set_brightness(100)

# Launch the simulator GUI
simulator_gui = launch_simulator(deck)

# Define a key callback
def key_callback(deck, key, state):
    print(f"Key {key} {'pressed' if state else 'released'}")
    
    # If key is pressed, update its image
    if state:
        # Create a simple image with the key number
        image = Image.new("RGB", deck.key_image_format()["size"], color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a colored rectangle based on key number
        color = (
            (key * 20) % 255,  # R
            (255 - key * 20) % 255,  # G
            (key * 40) % 255   # B
        )
        draw.rectangle(
            (5, 5, image.width - 5, image.height - 5),
            fill=color
        )
        
        # Draw the key number
        draw.text(
            (image.width // 2, image.height // 2),
            str(key),
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        # Convert the PIL image to the format required by the Stream Deck
        image_format = deck.key_image_format()
        if image_format["format"] == "BMP":
            from io import BytesIO
            
            # Save the image to a BytesIO object
            image_bytes = BytesIO()
            image.save(image_bytes, format="BMP")
            
            # Set the image on the key
            deck.set_key_image(key, image_bytes.getvalue())

# Set the key callback
deck.set_key_callback(key_callback)

# Main loop
try:
    print("Press Ctrl+C to exit")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    # Close the deck
    deck.close()
    print("Exiting...")