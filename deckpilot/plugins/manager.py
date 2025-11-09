"""Plugin discovery and lifecycle management."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from deckpilot.comm import event_bus
from deckpilot.comm.event_bus import EventBus
from deckpilot.elements import Panel, PanelRegistry
from deckpilot.utils import Logger

from .base import BasePlugin, PluginContext, PluginMetadata
from ..core import DeckManager


class PluginManager:
    """
    Locate plugin packages, load their metadata, and wire them into DeckPilot.

    Parameters:
        plugins_root (Path): Path to the directory containing plugin packages.
        panel_registry (PanelRegistry): The panel registry instance.
        deck_manager (DeckManager): The deck manager instance.
        config (dict): Global configuration for the application.
        bus (EventBus): The event bus instance.
    """

    def __init__(
            self,
            plugins_root: Path,
            panel_registry: PanelRegistry,
            deck_manager: DeckManager,
            config: Optional[dict] = None,
            bus: EventBus = event_bus,
    ):
        self._plugins_root = Path(plugins_root).expanduser().resolve()
        self._panel_registry = panel_registry
        self._deck_manager = deck_manager
        self._config = config or {}
        self._bus = bus
        self._plugins: List[BasePlugin] = []
        self._ensure_on_path(self._plugins_root.parent)
    # end def __init__

    @staticmethod
    def _ensure_on_path(path: Path) -> None:
        """
        Ensure that the given path is on the Python path.
        """
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
        # end if
    # end def _ensure_on_path

    def discover_and_load(self) -> None:
        """
        Scan the plugins directory and load each plugin.
        """
        if not self._plugins_root.exists():
            Logger.inst().warning(f"Plugin directory {self._plugins_root} does not exist.")
            return
        # end if

        for plugin_dir in sorted(self._plugins_root.iterdir()):
            manifest = plugin_dir / "plugin.yaml"

            # Ignore non-directory, ot not plugin.yaml
            if not plugin_dir.is_dir() or not manifest.exists():
                if plugin_dir.is_dir():
                    Logger.inst().warning(f"PluginManager: ignoring directory {plugin_dir}, missing plugin.yaml file.")
                # end if
                continue
            # end if

            try:
                # Get metadata and class
                metadata = self._load_metadata(manifest=manifest)
                plugin = self._instantiate_plugin(plugin_dir=plugin_dir, metadata=metadata)

                # Log error
                if plugin is None:
                    Logger.inst().warning(f"PluginManager: failed to instantiate plugin at {plugin_dir}")
                    continue
                # end if

                # Mount main panel
                self._mount_panels(plugin=plugin, metadata=metadata, plugin_dir=plugin_dir)
                plugin.register()
                self._wire_event_hooks(plugin, metadata)
                self._plugins.append(plugin)
                Logger.inst().info(f"PluginManager: loaded plugin '{metadata.name}' from {plugin_dir}")
            except Exception as exc:
                Logger.inst().error(f"PluginManager: failed to load plugin at {plugin_dir}: {exc}")
            # end try
        # end for
    # end def discover_and_load

    def _load_metadata(
            self,
            manifest: Path
    ) -> PluginMetadata:
        """
        Load the plugin metadata from the plugin manifest.

        Args:
            manifest (Path): Path to the plugin manifest file.
        """
        with manifest.open("r", encoding="utf-8") as fh:
            payload = yaml.safe_load(fh) or {}
        # end with
        return PluginMetadata.from_dict(payload)
    # end def _load_metadata

    def _instantiate_plugin(
            self,
            plugin_dir: Path,
            metadata: PluginMetadata
    ) -> Optional[BasePlugin]:
        """
        Instantiate the plugin class.

        Args:
             plugin_dir (Path): Path to the plugin directory.
             metadata (PluginMetadata): Plugin metadata.
        """
        cls = self._resolve_entry_point(metadata.entry_point)
        if cls is None:
            return None
        # end if

        context = PluginContext(
            metadata=metadata,
            base_path=plugin_dir,
            event_bus=self._bus,
            panel_registry=self._panel_registry,
            deck_manager=self._deck_manager,
            global_config=self._config,
        )
        return cls(context)
    # end def _instantiate_plugin

    @staticmethod
    def _resolve_entry_point(
            entry_point: str
    ):
        """
        Resolve the entry point to a class.

        Args:
            entry_point (str): Entry point string in the form "module:class".
        """
        module_name, _, attr_name = entry_point.partition(":")
        if not module_name or not attr_name:
            Logger.inst().error(f"Invalid entry_point '{entry_point}'")
            return None
        # end if
        module = importlib.import_module(module_name)
        return getattr(module, attr_name, None)
    # end def _resolve_entry_point

    def _mount_panels(self, plugin: BasePlugin, metadata: PluginMetadata, plugin_dir: Path) -> None:
        for panel_def in metadata.panels:
            mount_target = self._get_mount_target(panel_def.mount)

            if mount_target is None:
                Logger.inst().warning(
                    f"PluginManager: mount target '{panel_def.mount}' not found for panel {panel_def.identifier}"
                )
                continue
            # end if

            panel_path = (plugin_dir / panel_def.path).resolve()
            if not panel_path.exists():
                Logger.inst().warning(
                    f"PluginManager: panel path '{panel_path}' missing for plugin {metadata.name}"
                )
                continue
            # end if

            panel_class = self._resolve_entry_point(panel_def.class_path) if panel_def.class_path else Panel
            panel_instance = panel_class(
                name=panel_def.name,
                path=panel_path,
                renderer=mount_target.renderer,
                parent=mount_target,
                active=False,
                **panel_def.params,
            )

            mount_target.add_child(panel_instance.name, panel_instance)
            if hasattr(mount_target, "refresh_layout"):
                mount_target.refresh_layout()
            # end if

            Logger.inst().info(
                f"PluginManager: mounted panel '{panel_instance.name}' from plugin '{metadata.name}'"
            )
        # end for
    # end def _mount_panels

    def _get_mount_target(
            self,
            mount: str
    ) -> Optional[Panel]:
        """
        Get the mount target for a panel.
        """
        if mount in ("", "root", "/", None):
            return self._panel_registry.root
        # end if
        path_list = [segment for segment in mount.split("/") if segment]
        return self._panel_registry.get_panel(path_list)
    # end def _get_mount_target

    def _wire_event_hooks(
            self,
            plugin: BasePlugin,
            metadata: PluginMetadata
    ) -> None:
        """
        Wire the event hooks for a plugin.

        Args:
            plugin (BasePlugin): The plugin instance.
            metadata (PluginMetadata): The plugin metadata.
        """
        for hook in metadata.events:
            handler = getattr(plugin, hook.handler, None)
            if handler is None:
                Logger.inst().warning(
                    f"PluginManager: handler '{hook.handler}' not found on plugin '{metadata.name}'"
                )
                continue
            # end if
            self._bus.subscribe(
                plugin,
                hook.topic,
                handler,
            )
        # end for
    # end def _wire_event_hooks

    @property
    def plugins(self) -> List[BasePlugin]:
        return list(self._plugins)
    # end plugins

# end class PluginManager
