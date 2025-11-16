# Event System

DeckPilot ships with a lightweight publish/subscribe bus in `deckpilot/comm/event_bus.py`. It is central to the framework because it keeps panels, plugins, and background services decoupled. This page documents the available events and demonstrates how to publish or listen to them.

## Event types

`deckpilot.comm.event_bus.EventType` enumerates the topics emitted by the core runtime:

- **System** — `INITIALIZED`, `EXIT`
- **Clock** — `CLOCK_TICK` (visible panels), `INTERNAL_CLOCK_TICK` (hidden)
- **Keys** — `KEY_CHANGED`, `KEY_PRESSED`, `KEY_RELEASED`
- **Items** — `ITEM_RENDERED`, `ITEM_PRESSED`, `ITEM_RELEASED`
- **Panels** — `PANEL_RENDERED`, `PANEL_ACTIVATED`, `PANEL_PAGE_CHANGED`, `PANEL_NEXT_PAGE`, `PANEL_PREVIOUS_PAGE`, `PANEL_PARENT`

You can use the enum or pass raw strings (`event_bus.publish("obs/scene")`).

## Subscribing to events

```python
from deckpilot.comm import event_bus, EventType


class StatusLight(Button):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        event_bus.subscribe(self, EventType.PANEL_ACTIVATED, self._on_panel)

    def _on_panel(self, payload):
        if payload.get("panel") == self.parent.name:
            self._active = True
            self.refresh_layout()
```

`event_bus.subscribe` stores a reference to the subscriber instance and the callable. DeckPilot automatically removes subscriptions when the object is garbage collected, but it is still a good habit to unsubscribe manually for long-lived plugins.

## Publishing events

```python
event_bus.publish(
    EventType.PANEL_PAGE_CHANGED,
    {"panel": self.name, "page": self.current_page},
)
```

For fire-and-forget notifications where no specific subscriber is expected, use `event_bus.broadcast`. It calls callbacks registered via `subscribe_broadcast` regardless of topic.

## Targeted delivery

`event_bus.send_event(user, topic, data)` delivers a message to a single subscriber (the `user` argument passed during `subscribe`). The panel registry uses this pattern to route key events to the active panel without notifying every other panel in the hierarchy.

## Best practices

- Keep payloads small and serialisable (dicts, tuples, primitives). This makes it easier to test and log them.
- Reuse `EventType` whenever possible. Custom topics are welcome but document them inside your plugin README.
- Log at `DEBUG` level when publishing custom events; the `--log-filter` CLI flag is invaluable while debugging complex interactions.
- Avoid long-running work inside event handlers. Offload IO-heavy tasks to threads or timers and publish another event once the result is ready.
