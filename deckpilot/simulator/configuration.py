"""
Utilities for loading simulator configuration files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import toml

from .streamdeck_sim import (
    StreamDeckMiniSim,
    StreamDeckOriginalSim,
    StreamDeckSim,
    StreamDeckVirtualPadSim,
    StreamDeckXLSim,
)


class SimulatorConfigError(Exception):
    """Raised when a simulator configuration file cannot be parsed."""


DEVICE_TYPE_MAP = {
    "original": StreamDeckOriginalSim,
    "streamdeck_original": StreamDeckOriginalSim,
    "mini": StreamDeckMiniSim,
    "streamdeck_mini": StreamDeckMiniSim,
    "xl": StreamDeckXLSim,
    "streamdeck_xl": StreamDeckXLSim,
    "virtual_pad": StreamDeckVirtualPadSim,
}


def _load_raw_config(path: Path) -> dict:
    if not path.exists():
        raise SimulatorConfigError(f"Configuration file '{path}' does not exist")
    try:
        return toml.load(path)
    except (toml.TomlDecodeError, OSError) as exc:
        raise SimulatorConfigError(f"Unable to parse '{path}': {exc}") from exc


def _build_device(entry: dict, index: int) -> StreamDeckSim:
    if "type" not in entry:
        raise SimulatorConfigError(f"Device #{index} missing required 'type' field")

    type_key = str(entry["type"]).lower()
    device_cls = DEVICE_TYPE_MAP.get(type_key)
    if device_cls is None:
        raise SimulatorConfigError(f"Unsupported device type '{type_key}'")

    serial = entry.get("serial") or entry.get("serial_number")
    if not serial:
        serial = f"SIM-{type_key.upper()}-{index:03d}"

    return device_cls(serial_number=serial)


def load_simulator_devices(path: Path | str) -> List[StreamDeckSim]:
    """
    Load simulator device definitions from a TOML configuration file.

    The configuration must contain a ``[[devices]]`` table for each simulated deck,
    with at minimum a ``type`` field. Supported types are: ``original``, ``mini``,
    ``xl``, and ``virtual_pad``.
    """
    config = _load_raw_config(Path(path))
    devices: Iterable[dict] = config.get("devices", [])
    if not devices:
        raise SimulatorConfigError("Configuration must define at least one device")

    return [ _build_device(entry, idx + 1) for idx, entry in enumerate(devices) ]
