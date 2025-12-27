"""deckpilot.comm.event_bus module for DeckPilot.
"""


# Imports
from collections import defaultdict
from typing import Callable, Any, Dict, Optional, Union
from enum import Enum
from deckpilot.utils import Logger


class EventType(str, Enum):
    """All events that can be published through the DeckPilot event bus."""

    # System
    EXIT = "exit"
    INITIALIZED = "initialized"
    CLOCK_TICK = "clock/tick"
    INTERNAL_CLOCK_TICK = "internal/clock/tick"
    EXTERNAL_COMMAND = "external/command"
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
    PANEL_PARENT = "panel/parent"
# class EventType


# end class EventType
class UserCallback:
    """
    Class to hold user callback data.
    """

    def __init__(
            self,
            user: object,
            callback: Callable[[Any], None]
    ):
        """Constructor for the UserCallback class.
        
        Args:
            user (object): User object associated with the callback.
            callback (Callable[[Any], None]): Callback function to call when the event is published.
        """
        self.user = user
        self.callback = callback



    # end def __init__
# end class UserCallback
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

    # end def __new__

    def _normalize_event_type(self, event_type: Union[str, EventType]) -> str:
        """Normalize event identifiers for internal dictionaries."""
        if isinstance(event_type, EventType):
            return event_type.value
        return str(event_type)

    # end def _normalize_event_type
    def subscribe_broadcast(
            self,
            callback: Callable[[Any], None]
    ):
        """Subscribe a callback function to a broadcast event.
        
        Args:
            callback (Callable[[Any], None]): Callback function to call when the event is published.
        """
        self._broadcasters.append(callback)

    # end def subscribe_broadcast
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
        event_key = self._normalize_event_type(event_type)
        self._subscribers[event_key].append(UserCallback(user, callback))

    # end def subscribe
    def broadcast(
            self,
            data: Dict[str, Any]
    ):
        """Broadcast an event to all subscribers.
        
        Args:
            data (Dict[str, Any]): Data to pass to the subscribers.
        """
        for callback in self._broadcasters:
            Logger.inst().debug(f"EventBus: broadcast with data {data}")
            if isinstance(data, tuple):
                callback(*data)
            else:
                callback(data)

            # end if
        # end for
    # end def broadcast
    def publish(
            self,
            event_type: str,
            data: Any = None
    ) -> bool:
        """Publish an event and notify all subscribers.
        
        Args:
            event_type (str): Type of event to publish.
            data (Any): Data to pass to the subscribers.
        
        Returns:
            bool: True if the event was published successfully, False otherwise.
        """
        event_sent = False
        event_key = self._normalize_event_type(event_type)
        if event_key in self._subscribers:
            for uscall in self._subscribers[event_key]:
                if data is None:
                    uscall.callback()
                else:
                    if isinstance(data, tuple):
                        uscall.callback(*data)
                    else:
                        uscall.callback(data)
                    # end if
                # end if
                event_sent = True
            # end for
        else:
            Logger.inst().debug(f"EventBus: {event_key} not found")
        # end if
        return event_sent

    # end def publish
    # Send event to a specific user for an event type
    def send_event(
            self,
            user: object,
            event_type: str,
            data: Any = None
    ) -> Optional[Any]:
        """Send an event to a specific user.
        
        Args:
            user (object): User object to send the event to.
            event_type (str): Type of event to send.
            data (Any): Data to pass to the user.
        
        Returns:
            Optional[Any]: The result of the callback function, if any.
        """
        event_key = self._normalize_event_type(event_type)
        if event_key in self._subscribers:
            for uscall in self._subscribers[event_key]:
                if uscall.user == user:
                    if data is None:
                        Logger.inst().debugg(f"EventBus: {event_key} sent to {user}")
                        return uscall.callback()
                    else:
                        Logger.inst().debugg(f"EventBus: {event_key} sent to {user} with data {data}")
                        if isinstance(data, tuple):
                            return uscall.callback(*data)
                        else:
                            return uscall.callback(data)
                        # end if
                    # end if
                # end if
            # end for
        else:
            Logger.inst().debug(f"EventBus: {event_key} not found")
        # end if
    # end def send_event
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
        event_key = self._normalize_event_type(event_type)
        if event_key in self._subscribers:
            self._subscribers[event_key] = [
                uscall for uscall in self._subscribers[event_key] if uscall.user != user
            ]
        else:
            Logger.inst().debug(f"EventBus: {event_key} not found")
        # end if
    # end def unsubscribe
# end class EventBus
# Singleton instance of EventBus
event_bus = EventBus()
