# Automations

DeckPilot does not require a dedicated “automation language”. Instead, buttons, panels, and plugins react to two types of events:

- **Timer ticks** — emitted at the interval configured in `[general]`.
- **Event bus topics** — custom signals published via `deckpilot.comm.event_bus.publish`.

Use these building blocks to implement recurring tasks, watchers, or complex state machines.

## Timer-driven logic

Every `deckpilot.elements.Button` implements `on_periodic_tick`. This method receives `time_i` (how many ticks since DeckPilot started) and `time_count` (total number of ticks emitted).

```python
class ClockButton(Button):
    def on_periodic_tick(self, time_i, time_count):
        now = datetime.now().strftime("%H:%M")
        return KeyDisplay(text=now, icon=self.icon_inactive)
```

Tune the global interval in `config/config.toml`:

```toml
[general]
clock_tick_interval = 1.0
hidden_clock_tick_interval = 5.0
```

`clock_tick_interval` adjusts how frequently visible panels are refreshed, while `hidden_clock_tick_interval` is for tasks that should run in the background even when a panel is not on screen (for example, polling OBS or a web API).

## Event-driven automations

The event bus (`deckpilot.comm.event_bus`) works like a Publish/Subscribe system. Components subscribe to enumerated topics (see `EventType`) and publish messages whenever something interesting happens.

```python
from deckpilot.comm import event_bus, EventType


class SceneWatcher(Button):
    def __init__(self, name, path, parent):
        super().__init__(name, path, parent)
        event_bus.subscribe(self, EventType.PANEL_PAGE_CHANGED, self._on_page_changed)

    def _on_page_changed(self, payload):
        if payload.get("panel") == self.parent.name:
            self._refresh_state()
```

### Custom topics

You are not limited to `EventType`. Pass any string as the topic name:

```python
CUSTOM_TOPIC = "obs/scene/activated"
event_bus.subscribe(self, CUSTOM_TOPIC, self._on_scene)
event_bus.publish(CUSTOM_TOPIC, {"name": "Intro"})
```

## Combining timers and events

Complex automations often chain both systems: a timer fetches data from a web service and a custom event notifies interested buttons to refresh their icons. This decouples slow operations from rendering and keeps your buttons responsive.
