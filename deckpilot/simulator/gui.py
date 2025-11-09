"""
Stream Deck Simulator - Graphical User Interface

This module provides a graphical user interface for the Stream Deck simulator,
allowing visual interaction with the simulated Stream Deck device.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps
import io
import threading
import time

from .streamdeck_sim import StreamDeckVirtualPadSim


class StreamDeckSimulatorGUI:
    """
    Graphical user interface for the Stream Deck simulator.
    Displays a grid that matches the connected simulated device (defaults to 3x15).
    """

    def __init__(self, deck=None, on_close=None):
        """
        Creates a new Stream Deck simulator GUI.

        Args:
            deck: A simulated StreamDeck instance to visualize. If None, a new
                 StreamDeckVirtualPadSim instance will be created.
            on_close (callable | None): Optional callback invoked after the
                 window has been destroyed.
        """
        # Create a deck if none is provided (defaults to 3 x 15 virtual pad)
        self.deck = deck or StreamDeckVirtualPadSim()
        self._on_close_callback = on_close
        
        # Create the main window
        self.root = tk.Tk()
        self.root.title(f"Stream Deck Simulator - {self.deck.deck_type()}")
        self.root.resizable(False, False)
        
        # Configure the window style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create the grid of buttons
        self.buttons = []
        self.button_images = []  # Keep references to avoid garbage collection
        
        rows, cols = self.deck.key_layout()
        
        # Create a frame for the buttons with a black background
        self.button_frame = ttk.Frame(self.main_frame, padding="5")
        self.button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.button_frame.configure(style="Black.TFrame")
        self.style.configure("Black.TFrame", background="black")
        
        # Create the buttons
        for row in range(rows):
            for col in range(cols):
                key_index = row * cols + col
                
                # Create a button with a black background
                button = ttk.Button(
                    self.button_frame,
                    text="",
                    width=8,
                    style="StreamDeck.TButton"
                )
                button.grid(row=row, column=col, padx=5, pady=5)
                
                # Configure the button style
                self.style.configure(
                    "StreamDeck.TButton",
                    background="black",
                    foreground="white"
                )
                
                # Bind button events
                button.bind("<ButtonPress-1>", lambda e, idx=key_index: self._on_button_press(idx))
                button.bind("<ButtonRelease-1>", lambda e, idx=key_index: self._on_button_release(idx))
                
                self.buttons.append(button)
                self.button_images.append(None)
        
        # Create a status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Stream Deck Simulator Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Start the update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_button_press(self, key_index):
        """
        Handles button press events.

        Args:
            key_index: Index of the button that was pressed.
        """
        self.deck.press_key(key_index)
        self.status_var.set(f"Key {key_index} pressed")

    def _on_button_release(self, key_index):
        """
        Handles button release events.

        Args:
            key_index: Index of the button that was released.
        """
        self.deck.release_key(key_index)
        self.status_var.set(f"Key {key_index} released")

    def _update_loop(self):
        """
        Background thread that updates the button images.
        """
        while self.running:
            try:
                self._update_button_images()
                time.sleep(0.05)  # Update at 20 Hz
            except Exception as e:
                print(f"Error updating button images: {e}")

    def _update_button_images(self):
        """
        Updates the button images based on the current state of the deck.
        """
        for key_index in range(self.deck.key_count()):
            image_data = self.deck.get_key_image(key_index)
            
            if image_data:
                try:
                    # Convert the image data to a Tkinter PhotoImage
                    image = Image.open(io.BytesIO(image_data))

                    # Adjust orientation based on the deck's native format
                    image_format = self.deck.key_image_format()
                    flip = image_format.get("flip", (False, False)) if isinstance(image_format, dict) else (False, False)
                    rotation = image_format.get("rotation", 0) if isinstance(image_format, dict) else 0

                    if isinstance(flip, (tuple, list)):
                        horizontal, vertical = (bool(flip[0]), bool(flip[1]))
                        if horizontal:
                            image = ImageOps.mirror(image)
                        if vertical:
                            image = ImageOps.flip(image)
                    if rotation:
                        image = image.rotate(-rotation, expand=True)
                    
                    # Resize the image to fit the button
                    image = image.resize((64, 64))
                    
                    # Convert to Tkinter PhotoImage
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update the button image
                    self.button_images[key_index] = photo
                    self.buttons[key_index].configure(image=photo)
                except Exception as e:
                    print(f"Error updating image for key {key_index}: {e}")
            else:
                # No image, show a blank button
                self.button_images[key_index] = None
                self.buttons[key_index].configure(image="")

    def _on_close(self):
        """
        Handles window close events.
        """
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(1.0)
        self.root.destroy()
        if self._on_close_callback:
            try:
                self._on_close_callback()
            except Exception as exc:
                print(f"Simulator close callback failed: {exc}")

    def run(self):
        """
        Runs the GUI main loop.
        """
        self.root.mainloop()


def launch_simulator(deck=None, start_thread=True, on_close=None):
    """
    Launches the Stream Deck simulator GUI.

    Args:
        deck: A simulated StreamDeck instance to visualize. If None, a new
             StreamDeckVirtualPadSim instance will be created.
        start_thread (bool): When True (default), the GUI mainloop runs in a
             dedicated daemon thread. Set to False to manage the mainloop
             yourself (required when Tk must run on the main thread).
        on_close (callable | None): Optional callback invoked when the window
             closes.
    
    Returns:
        The StreamDeckSimulatorGUI instance.
    """
    gui = StreamDeckSimulatorGUI(deck, on_close=on_close)

    if start_thread:
        # Run the GUI in a separate thread
        gui_thread = threading.Thread(target=gui.run, daemon=True)
        gui_thread.start()
    
    return gui


if __name__ == "__main__":
    # Test the GUI
    gui = StreamDeckSimulatorGUI()
    gui.run()
