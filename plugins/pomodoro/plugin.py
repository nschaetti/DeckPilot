"""Pomodoro plugin entry point."""

from deckpilot.plugins import BasePlugin
from deckpilot.utils import Logger


class PomodoroPlugin(BasePlugin):
    """
    Expose timers and controls as a dedicated panel.
    """

    def register(self) -> None:
        Logger.inst().info("PomodoroPlugin registered: panel mounted via metadata")
    # end def register

# end class PomodoroPlugin


