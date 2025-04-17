"""
 ██████╗ ███████╗ ██████╗██╗  ██╗██████╗ ██╗      ██████╗ ██╗████████╗
██╔════╝ ██╔════╝██╔════╝██║ ███║██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
██║  ███╗█████╗  ██║     █████║  ███████║██║     ██║   ██║██║   ██║
██║   ██║██╔══╝  ██║     ██╔═███║██╔════╝██║     ██║   ██║██║   ██║
╚██████╔╝███████╗╚██████╗██║ ═██║██║     ███████╗╚██████╔╝██║   ██║
 ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝

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
from collections import defaultdict
from typing import Callable, Any, Dict, Optional
from enum import Enum
from deckpilot.utils import Logger


class EventType(str, Enum):
    # System
    EXIT = "exit"
    INITIALIZED = "initialized"
    CLOCK_TICK = "clock/tick"
    # keys events
    KEY_CHANGED = "key/changed"
    KEY_PRESSED = "key/pressed"
    KEY_RELEASED = "key/released"
    # Internal item events
    ITEM_RENDERED = "item/rendered"
    ITEM_PRESSED = "item/pressed"
    ITEM_RELEASED = "item/released"
    # Internal panel events
    PANEL_RENDERED = "panel/rendered"
    PANEL_ACTIVATED = "panel/activated"
    PANEL_DEACTIVATED = "panel/deactivated"
    PANEL_PAGE_CHANGED = "panel/page/changed"
    PANEL_NEXT_PAGE = "panel/page/next"
    PANEL_PREVIOUS_PAGE = "panel/page/previous"
# end EventType


class UserCallback:
    """
    Class to hold user callback data.
    """

    def __init__(
            self,
            user: object,
            callback: Callable[[Any], None]
    ):
        """
        Constructor for the UserCallback class.

        :param user: User object associated with the callback.
        :param callback: Callback function to call when the event is published.
        """
        self.user = user
        self.callback = callback
    # end __init__

# end UserCallback


class EventBus:
    """
    Simple event system for Pub/Sub.
    """

    # Singleton instance
    _instance = None

    def __new__(cls):
        """
        Create a new instance of the EventBus class.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
            cls._instance._broadcasters = list()
        # end if
        return cls._instance
    # end __new__

    def subscribe_broadcast(
            self,
            callback: Callable[[Any], None]
    ):
        """
        Subscribe a callback function to a broadcast event.

        :param callback: Callback function to call when the event is published.
        :type callback: Callable[[Any], None]
        """
        self._broadcasters.append(callback)
    # end subscribe_broadcast

    def subscribe(
            self,
            user: object,
            event_type: str,
            callback: Callable[[Any], None]
    ):
        """
        Subscribe a callback function to an event type.

        Args:
        - event_type (str): Type of event to subscribe to.
        - callback (Callable[[Any], None]): Callback function to call when the event is published.
        """
        self._subscribers[event_type].append(UserCallback(user, callback))
    # end subscribe

    def broadcast(
            self,
            data: Dict[str, Any]
    ):
        """
        Broadcast an event to all subscribers.

        :param data: Data to pass to the subscribers.
        :type data: Dict[str, Any]
        """
        for callback in self._broadcasters:
            Logger.inst().debug(f"EventBus: broadcast with data {data}")
            if isinstance(data, tuple):
                callback(*data)
            else:
                callback(data)
            # end if
        # end for
    # end broadcast

    def publish(
            self,
            event_type: str,
            data: Any = None
    ) -> bool:
        """
        Publish an event and notify all subscribers.

        :param event_type: Type of event to publish.
        :type event_type: str
        :param data: Data to pass to the subscribers.
        :type data: Any
        :return: True if the event was published successfully, False otherwise.
        :rtype: bool
        """
        event_sent = False
        if event_type in EventType:
            if event_type in self._subscribers:
                for uscall in self._subscribers[event_type]:
                    if data is None:
                        # Logger.inst().debug(f"EventBus: {event_type} published")
                        uscall.callback()
                    else:
                        # Logger.inst().debug(f"EventBus: {event_type} published with data {data}")
                        if isinstance(data, tuple):
                            uscall.callback(*data)
                        else:
                            uscall.callback(data)
                        # end if
                    # end if
                    event_sent = True
                # end for
            # end if
        else:
            Logger.inst().warning(f"EventBus: {event_type} not found")
        # end if
        return event_sent
    # end publish

    # Send event to a specific user for an event type
    def send_event(
            self,
            user: object,
            event_type: str,
            data: Any = None
    ) -> Optional[Any]:
        """
        Send an event to a specific user.

        :param user: User object to send the event to.
        :type user: object
        :param event_type: Type of event to send.
        :type event_type: str
        :param data: Data to pass to the user.
        :type data: Any
        :return: The result of the callback function, if any.
        :rtype: Optional[Any]
        """
        if event_type in EventType:
            if event_type in self._subscribers:
                for uscall in self._subscribers[event_type]:
                    if uscall.user == user:
                        if data is None:
                            Logger.inst().debug(f"EventBus: {event_type} sent to {user}")
                            return uscall.callback()
                        else:
                            Logger.inst().debug(f"EventBus: {event_type} sent to {user} with data {data}")
                            if isinstance(data, tuple):
                                return uscall.callback(*data)
                            else:
                                return uscall.callback(data)
                            # end if
                        # end if
                    # end if
                # end for
            # end if
            else:
                Logger.inst().debug(f"EventBus: {event_type} not found")
            # end if
        else:
            Logger.inst().warning(f"EventBus: {event_type} not a valid event type")
        # end if
    # end send_event

    def unsubscribe(
            self,
            user: object,
            event_type: str
    ):
        """
        Unsubscribe a user from an event type.

        Args:
        - user (object): User object to unsubscribe.
        - event_type (str): Type of event to unsubscribe from.
        """
        if event_type in EventType:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    uscall for uscall in self._subscribers[event_type] if uscall.user != user
                ]
            # end if
            else:
                Logger.inst().debug(f"EventBus: {event_type} not found")
            # end if
        else:
            Logger.inst().warning(f"EventBus: {event_type} not a valid event type")
        # end if
    # end unsubscribe

# end EventBus


# Singleton instance of EventBus
event_bus = EventBus()

