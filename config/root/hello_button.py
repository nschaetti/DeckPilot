
# Imports
from deckpilot import Button
from rich.console import Console


# Console
console = Console()


class HelloButton(Button):
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
        console.log(f"HelloButton {name} created.")
    # end __init__

    def on_button_rendered(self):
        """
        Render button
        """
        console.log(f"Button {self.name} rendered")
    # end on_button_rendered

    def _on_button_pressed(self, key_index):
        """
        Event handler for the "button_pressed" event.
        """
        console.log(f"Button {self.name} pressed")
    # end _on_button_pressed

    def _on_button_released(self, key_index):
        """
        Event handler for the "button_released" event.
        """
        console.log(f"Button {self.name} released")
    # end _on_button_released

# end HelloButton


