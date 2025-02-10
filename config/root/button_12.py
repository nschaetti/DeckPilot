
# Imports
from deckpilot import Button
from rich.console import Console


# Console
console = Console()


class Button12(Button):
    """
    Button that says hello
    """

    # Constructor
    def __init__(
            self,
            name,
            path,
            parent
    ):
        """
        Constructor for the Button class.

        Args:
            name (str): Name of the button.
            path (str): Path to the button file.
            parent (PanelNode): Parent panel.
        """
        super().__init__(name, path, parent)
        console.log(f"{self.__class__.__name__} {name} created.")
    # end __init__

    def on_button_rendered(self):
        """
        Render button
        """
        console.log(f"Button {self.name} rendered")
    # end on_button_rendered

    def on_button_pressed(self, key_index):
        """
        Event handler for the "button_pressed" event.
        """
        console.log(f"Button {self.name} pressed")
    # end on_button_pressed

    def on_button_released(self, key_index):
        """
        Event handler for the "button_released" event.
        """
        console.log(f"Button {self.name} released")
    # end on_button_released

# end Button12


