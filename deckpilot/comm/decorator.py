"""deckpilot.comm.decorator module for DeckPilot.
"""


# Imports
from functools import wraps
from .event_bus import EventBus


# Decorator for subscribing to broadcast
def on_broadcast(event_type: str):
    """Decorator for subscribing to broadcast events.
    
    Args:
        event_type (str): Type of event to subscribe to.
    
    Returns:
        Callable: Decorator function.
    """
    def decorator(func):
        """Register a function as a broadcast listener."""
        EventBus().subscribe_broadcast(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Invoke the wrapped broadcast handler."""
            return func(*args, **kwargs)
        # end def wrapper
        return wrapper
    # end def decorator
    return decorator



# end def on_broadcast
# Decorator for subscribing to events
def on_event(event_type: str):
    """Decorator for subscribing to events.
    
    Args:
        event_type (str): Type of event to subscribe to.
    
    Returns:
        Callable: Decorator function.
    """
    def decorator(func):
        """Register a function as an event listener."""
        EventBus().subscribe(event_type, func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Invoke the wrapped event handler."""
            return func(*args, **kwargs)
        # end def wrapper
        return wrapper
    # end def decorator
    return decorator
# end def on_event
