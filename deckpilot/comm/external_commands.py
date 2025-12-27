"""Utilities for DeckPilot external command messages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, Optional

DEFAULT_COMMAND_HOST = "127.0.0.1"
DEFAULT_COMMAND_PORT = 27876


class ExternalMessageType(IntEnum):
    """Enumerated message types exchanged with the external command socket."""

    ECHO = 1
    PONG = 2
    PUSH = 3
    PUSH_ACK = 4


@dataclass
class ExternalCommandMessage:
    """Base class for socket messages."""

    message_type: int
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {"message_type": int(self.message_type)}
        data.update(self.payload)
        return data

    def to_json(self) -> str:
        """Serialize the message as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ExternalCommandMessage":
        """Factory that returns the appropriate subclass for the payload."""
        return parse_external_command(raw)


class EchoCommand(ExternalCommandMessage):
    """External command that expects a PONG response."""

    def __init__(self, message: str = "PING") -> None:
        super().__init__(
            message_type=int(ExternalMessageType.ECHO),
            payload={"message": message},
        )


class PongResponse(ExternalCommandMessage):
    """Response emitted by DeckPilot when handling an Echo command."""

    def __init__(self, reply: str = "PONG", echo: Optional[str] = None) -> None:
        response_payload = {"message": reply}
        if echo is not None:
            response_payload["echo"] = echo
        super().__init__(
            message_type=int(ExternalMessageType.PONG),
            payload=response_payload,
        )


class PushCommand(ExternalCommandMessage):
    """Simulate a key press on the Stream Deck."""

    def __init__(self, key: int, duration: float = 2.0) -> None:
        if key < 0:
            raise ValueError("key must be >= 0")
        if duration <= 0:
            raise ValueError("duration must be > 0")
        self.key = int(key)
        self.duration = float(duration)
        super().__init__(
            message_type=int(ExternalMessageType.PUSH),
            payload={"key": self.key, "duration": self.duration},
        )


class PushAckResponse(ExternalCommandMessage):
    """Acknowledgement payload for PushCommand operations."""

    def __init__(self, key: int, duration: float, success: bool, error: Optional[str] = None) -> None:
        payload = {
            "key": key,
            "duration": duration,
            "success": success,
        }
        if error:
            payload["error"] = error
        super().__init__(
            message_type=int(ExternalMessageType.PUSH_ACK),
            payload=payload,
        )


def parse_external_command(raw: Dict[str, Any]) -> ExternalCommandMessage:
    """Parse a raw dictionary into an ExternalCommandMessage instance."""
    if "message_type" not in raw:
        raise ValueError("message_type field is required")
    message_type_value = int(raw["message_type"])
    try:
        message_type = ExternalMessageType(message_type_value)
    except ValueError:
        payload = dict(raw)
        payload.pop("message_type", None)
        return ExternalCommandMessage(
            message_type=message_type_value,
            payload=payload,
        )

    if message_type == ExternalMessageType.ECHO:
        return EchoCommand(message=str(raw.get("message", "")))
    if message_type == ExternalMessageType.PONG:
        return PongResponse(reply=str(raw.get("message", "PONG")), echo=raw.get("echo"))
    if message_type == ExternalMessageType.PUSH:
        if "key" not in raw:
            raise ValueError("push command requires a 'key' field")
        duration = float(raw.get("duration", 2.0))
        return PushCommand(key=int(raw["key"]), duration=duration)
    if message_type == ExternalMessageType.PUSH_ACK:
        return PushAckResponse(
            key=int(raw.get("key", -1)),
            duration=float(raw.get("duration", 0)),
            success=bool(raw.get("success", False)),
            error=raw.get("error"),
        )

    payload = dict(raw)
    payload.pop("message_type", None)
    return ExternalCommandMessage(message_type=int(message_type), payload=payload)
