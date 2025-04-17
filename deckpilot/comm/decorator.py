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

# Imports
from functools import wraps
from .event_bus import EventBus


# Decorator for subscribing to broadcast
def on_broadcast(event_type: str):
    """
    Decorator for subscribing to broadcast events.

    :param event_type: Type of event to subscribe to.
    :type event_type: str
    :return: Decorator function.
    :rtype: Callable
    """
    def decorator(func):
        EventBus().subscribe_broadcast(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        # end wrapper
        return wrapper
    # end decorator
    return decorator
# end decorator



# Decorator for subscribing to events
def on_event(event_type: str):
    """
    Decorator for subscribing to events.

    :param event_type: Type of event to subscribe to.
    :type event_type: str
    :return: Decorator function.
    :rtype: Callable
    """
    def decorator(func):
        EventBus().subscribe(event_type, func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        # end wrapper§
        return wrapper
    # end decorator
    return decorator
# end decorator
