"""Apps plugin entry point."""

from deckpilot.plugins import BasePlugin
from deckpilot.utils import Logger


class AppsPlugin(BasePlugin):
    """Expose quick application launchers as a DeckPilot panel."""

    def register(self) -> None:
        Logger.inst().info("AppsPlugin registered: panel mounted via metadata")
