
# Imports
from deckpilot import Button
from rich.console import Console


# Console
console = Console()


class LaunchButton(Button):
    """
    Button that launches a program
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
        console.log(f"LaunchButton {name} created.")
    # end __init__

    def render(self):
        """
        Render button
        """
        console.log(f"Render {self.name}")
    # end render

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

# end LaunchButton


