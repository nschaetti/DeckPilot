"""Runtime glue for the OBS DeckPilot plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from deckpilot.plugins import BasePlugin
from deckpilot.utils import Logger


class OBSPlugin(BasePlugin):
    """Expose OBS operations through the DeckPilot EventBus."""

    def __init__(self, context):
        super().__init__(context)
        self._panel = None

    def register(self) -> None:
        """Attach to the dynamically created OBS panel."""
        self._panel = self._locate_panel()
        if not self._panel:
            Logger.inst().warning("OBSPlugin: panel not found; controls will be disabled.")
            return
        setattr(self._panel, "plugin", self)
        Logger.inst().info("OBSPlugin: panel attached successfully.")

    def _locate_panel(self):
        registry = self.context.panel_registry
        for panel_def in self.metadata.panels:
            path: List[str] = []
            mount = panel_def.mount.strip("/") if panel_def.mount else ""
            if mount:
                path.extend([segment for segment in mount.split("/") if segment])
            path.append(panel_def.name)
            panel = registry.get_panel(path) if path else registry.root
            if panel:
                return panel
        return None

    # Event handlers wired via plugin.yaml ---------------------------------

    def handle_initialized(self, *_args, **_kwargs) -> None:
        """Reconnect to OBS when the Deck is ready."""
        if self._panel and hasattr(self._panel, "reconnect"):
            self._panel.reconnect()

    def handle_scene_activation(self, payload: Dict[str, Any]) -> None:
        if not self._panel:
            return
        scene = payload.get("scene") if isinstance(payload, dict) else payload
        if scene:
            self._panel.change_scene(scene)

    def handle_record_start(self, *_args, **_kwargs) -> None:
        if self._panel:
            self._panel.start_recording()

    def handle_record_stop(self, *_args, **_kwargs) -> None:
        if self._panel:
            self._panel.stop_recording()

    def handle_record_toggle(self, *_args, **_kwargs) -> None:
        if not self._panel:
            return
        if self._panel.is_recording():
            self._panel.stop_recording()
        else:
            self._panel.start_recording()

    def handle_record_pause(self, *_args, **_kwargs) -> None:
        if self._panel:
            self._panel.pause_recording()

    def handle_record_resume(self, *_args, **_kwargs) -> None:
        if self._panel:
            self._panel.resume_recording()

    def handle_stream_toggle(self, *_args, **_kwargs) -> None:
        if not self._panel:
            return
        if self._panel.is_streaming():
            self._panel.stop_streaming()
        else:
            self._panel.start_streaming()

    def handle_input_toggle(self, payload: Dict[str, Any]) -> None:
        if not self._panel:
            return
        input_name = payload.get("input_name")
        is_special = payload.get("is_special_input", False)
        if not input_name:
            return
        if is_special and hasattr(self._panel, "get_special_input"):
            resolved = self._panel.get_special_input(input_name)
        else:
            resolved = input_name
        if resolved:
            self._panel.toggle_input(resolved)
