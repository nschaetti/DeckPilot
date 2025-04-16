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

from collections import defaultdict
from typing import Callable, Any

from deckpilot.utils import Logger


class EventBus:
    """
    Simple event system for Pub/Sub.
    """

    # Constructor
    def __init__(self):
        """
        Constructor for the EventBus class.
        """
        self._subscribers = defaultdict(list)
    # end __init__

    def subscribe(
            self,
            event_type: str,
            callback: Callable[[Any], None]
    ):
        """
        Subscribe a callback function to an event type.

        Args:
        - event_type (str): Type of event to subscribe to.
        - callback (Callable[[Any], None]): Callback function to call when the event is published.
        """
        self._subscribers[event_type].append(callback)
    # end subscribe

    def publish(
            self,
            event_type: str,
            data: Any = None
    ):
        """
        Publish an event and notify all subscribers.

        Args:
        - event_type (str): Type of event to publish.
        - data (Any): Data to pass to the subscribers.
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                if data is None:
                    Logger.inst().debug(f"EventBus: {event_type} published")
                    callback()
                else:
                    Logger.inst().debug(f"EventBus: {event_type} published with data {data}")
                    if isinstance(data, tuple):
                        callback(*data)
                    else:
                        callback(data)
                    # end if
                # end if
            # end for
        # end if
    # end publish

# end EventBus
