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

Console logger utilities used by DeckPilot.
"""


# Imports
from dataclasses import dataclass
from enum import IntEnum
import inspect
import re
from typing import Optional, Sequence
from rich.console import Console
from rich.traceback import install


install(show_locals=True)


@dataclass(frozen=True)
class LogEntry:
    """Structured representation of a single log line.

    Attributes:
        level: Severity of the log entry.
        label: Human-readable label for the level column.
        source: Origin of the log (class/module name).
        message: Rendered log message text.
    """

    level: "LogLevel"
    label: str
    source: str
    message: str
# end class LogEntry


class LogFilterRule:
    """Single AND-combined rule used to filter log output."""

    _KEY_MAP = {
        "type": "level",
        "level": "level",
        "severity": "level",
        "source": "source",
        "class": "source",
        "cls": "source",
        "message": "message",
        "msg": "message",
        "text": "message",
    }

    def __init__(
            self,
            *,
            level_pattern: Optional[re.Pattern[str]] = None,
            source_pattern: Optional[re.Pattern[str]] = None,
            message_pattern: Optional[re.Pattern[str]] = None,
            raw: str | None = None,
    ) -> None:
        """Create a new filtering rule.

        Args:
            level_pattern: Compiled regex matched against the label/level text.
            source_pattern: Compiled regex matched against the inferred source.
            message_pattern: Compiled regex matched against the message body.
            raw: Original specification string, preserved for display.

        Raises:
            ValueError: If no patterns are provided.
        """
        if not any((level_pattern, source_pattern, message_pattern)):
            raise ValueError("A filter rule must declare at least one criterion")
        # end if
        self.level_pattern = level_pattern
        self.source_pattern = source_pattern
        self.message_pattern = message_pattern
        self.raw = raw or ""
    # end def __init__

    @classmethod
    def from_spec(cls, spec: str) -> "LogFilterRule":
        """Convert a CLI filter specification into a rule.

        A specification is a comma/semicolon-separated list of key/value pairs
        where keys map to one of ``level``, ``source``, or ``message``. Values
        are interpreted as regular expressions (case-insensitive for level).

        Args:
            spec: Raw CLI filter specification, for example
                ``"level=debug,source=my_module"``.

        Returns:
            LogFilterRule: A populated filter rule instance.

        Raises:
            ValueError: If the specification is empty, malformed, references an
                unknown field, or contains an invalid regular expression.
        """
        if not spec or not spec.strip():
            raise ValueError("Empty filter specification")
        # end if

        tokens = [token.strip() for token in re.split(r"[;,]", spec) if token.strip()]

        if not tokens:
            raise ValueError("Filter specification contains no criteria")
        # end if
        
        kwargs: dict[str, re.Pattern[str]] = {}
        for token in tokens:
            if "=" in token:
                key, value = token.split("=", 1)
            elif ":" in token:
                key, value = token.split(":", 1)
            else:
                raise ValueError(f"Invalid token '{token}'. Expected key=value pairs")
            # end if

            key = key.strip().lower()
            field = cls._KEY_MAP.get(key)
            if field is None:
                raise ValueError(f"Unknown filter field '{key}' in '{spec}'")
            # end if

            value = value.strip()
            if not value:
                raise ValueError(f"Missing regex for '{key}' in '{spec}'")
            # end if
            try:
                flags = re.IGNORECASE if field == "level" else 0
                kwargs[field] = re.compile(value, flags)
            except re.error as exc:  # pragma: no cover - regex compilation errors
                raise ValueError(f"Invalid regex '{value}' for '{key}': {exc}") from exc
        # end for

        return cls(
            level_pattern=kwargs.get("level"),
            source_pattern=kwargs.get("source"),
            message_pattern=kwargs.get("message"),
            raw=spec,
        )

    # end def from_spec
    def matches(self, entry: LogEntry) -> bool:
        """Check whether a log entry satisfies this rule.

        Args:
            entry: Log entry to evaluate.

        Returns:
            bool: True if the entry matches all configured criteria, otherwise
            False.
        """
        if self.level_pattern and not self.level_pattern.search(entry.label):
            return False
        # end if
        if self.source_pattern and not self.source_pattern.search(entry.source):
            return False
        # end if
        if self.message_pattern and not self.message_pattern.search(entry.message):
            return False
        # end if
        return True
    # end def matches

    def __str__(self) -> str:
        """Return a readable representation of the rule."""
        return (
            f"<LogFilterRule: raw={self.raw}, level_pattern={self.level_pattern}, "
            f"source_pattern={self.source_pattern}, message_pattern={self.message_pattern}>"
        )
    # end def __str__

    def __repr__(self):
        """Return the canonical representation for debugging."""
        return self.__str__()
    # end def __repr__

# end class LogFilterRule


class LogLevel(IntEnum):
    """Logging severities supported by DeckPilot."""

    DEBUGG = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

# end class LogLevel


# Main logger
class Logger:
    """Rich console logger tailored for DeckPilot output formatting.

    The Logger is implemented as a singleton to keep console configuration
    consistent across DeckPilot commands. It supports structured filtering,
    level-aware styling, and convenience helpers for common log types and
    telemetry-like event entries.
    """

    # Singleton instance
    _instance = None

    # Styles
    _LEVEL_STYLES = {
        LogLevel.DEBUGG: "green",
        LogLevel.DEBUG: "green",
        LogLevel.INFO: None,
        LogLevel.WARNING: "yellow",
        LogLevel.ERROR: "red",
        LogLevel.CRITICAL: "red bold",
    }
    _LEVEL_COL_WIDTH = 8
    _SOURCE_COL_WIDTH = 24

    # New instance
    def __new__(
            cls,
            level=LogLevel.INFO
    ):
        """Create (or return) the singleton Logger instance.

        Args:
            level: Default logging level for the new instance.

        Returns:
            Logger: The singleton logger.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._console = Console()
            cls._instance._level = level
            cls._instance._filters: list[LogFilterRule] = []
        # end if
        return cls._instance
    # end def __new__

    @classmethod
    def inst(cls):
        """Return the singleton instance if it has been created.

        Returns:
            Logger | None: The logger instance or ``None`` if not yet built.
        """
        return cls._instance

    # end def inst
    def set_level(
            self,
            level: LogLevel
    ):
        """Update the minimum severity displayed by the logger.

        Args:
            level: New minimum log level. Messages below this level are skipped.

        Returns:
            None
        """
        self._level = level
    # end def set_level

    def configure_filters(
            self,
            specs: Optional[Sequence[str]]
    ):
        """Configure include filters parsed from CLI-provided specs.

        Args:
            specs: Optional list of rule specifications. If omitted or empty,
                filtering is disabled.

        Raises:
            ValueError: If any specification is invalid.

        Returns:
            None
        """
        self._filters = []
        if not specs:
            return
        # end if

        parsed: list[LogFilterRule] = []
        for spec in specs:
            parsed.append(LogFilterRule.from_spec(spec))
        # end for

        self._filters = parsed
    # end def configure_filters

    def get_level(self):
        """Return the current minimum logging level.

        Returns:
            LogLevel: Active minimum severity threshold.
        """
        return self._level
    # end def get_level

    def _log(
            self,
            msg,
            log_level: LogLevel,
            *,
            source: Optional[str] = None,
            label: Optional[str] = None,
            style: Optional[str] = None,
    ):
        """Dispatch a log entry after applying level and filter checks.

        Args:
            msg: Message content to render.
            log_level: Severity of the message.
            source: Optional source override; defaults to the caller class/module.
            label: Optional label override for the level column.
            style: Optional `rich` style string applied to the level column.

        Returns:
            None
        """
        if self._level > log_level:
            return
        # end if

        level_label = label or LogLevel(log_level).name
        source_name = source or self._infer_source()
        entry = LogEntry(
            level=log_level,
            label=level_label,
            source=source_name,
            message=str(msg),
        )

        # No match, don't print
        if self._filters and not any(rule.matches(entry) for rule in self._filters):
            return
        # end if

        render_style = style or self._LEVEL_STYLES.get(log_level)
        level_markup = self._format_level(level_label, render_style)
        source_markup = self._format_source(source_name)
        formatted = f"{level_markup} {source_markup} {entry.message}".rstrip()
        self._console.log(formatted, _stack_offset=3)
    # end def _log

    def _infer_source(self) -> str:
        """Infer the caller class or module name for display and filtering.

        Returns:
            str: Derived source name or ``"unknown"`` if it cannot be inferred.
        """
        frame = inspect.currentframe()
        try:
            while frame and frame.f_globals.get("__name__") == __name__:
                frame = frame.f_back
            # end while

            if not frame:
                return "unknown"
            # end if

            local_self = frame.f_locals.get("self")
            if local_self is not None:
                return local_self.__class__.__name__
            # end if

            local_cls = frame.f_locals.get("cls")
            if local_cls is not None:
                return local_cls.__name__
            # end if

            return frame.f_globals.get("__name__", "unknown")
        finally:
            del frame
        # end try
    # end def _infer_source

    def _format_level(
            self,
            label: str,
            style: Optional[str]
    ) -> str:
        """Return a padded, optionally styled log-level column.

        Args:
            label: Label text to display.
            style: Optional `rich` style string.

        Returns:
            str: Styled label ready for console output.
        """

        padded = f"{label:<{self._LEVEL_COL_WIDTH}}"
        if style:
            return f"[{style}]{padded}[/]"
        # end if
        return padded
    # end def _format_level

    def _format_source(self, source: Optional[str]) -> str:
        """Return a padded source column.

        Args:
            source: Source text to display.

        Returns:
            str: Styled source column.
        """
        text = (source or "")[:self._SOURCE_COL_WIDTH]
        padded = f"{text:<{self._SOURCE_COL_WIDTH}}"
        return f"[dim]{padded}[/]"
    # end def _format_source

    def debug(
            self,
            msg,
            *,
            source: Optional[str] = None
    ):
        """Log a debug message.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.DEBUG, source=source)
    # end def debug

    def debugg(self, msg, *, source: Optional[str] = None):
        """Log a very verbose debug message (below ``DEBUG``).

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.DEBUGG, source=source)
    # end def debugg

    def info(self, msg, *, source: Optional[str] = None):
        """Log an info message.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.INFO, source=source)
    # end def info

    def warning(self, msg, *, source: Optional[str] = None):
        """Log a warning message.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.WARNING, source=source)
    # end def warning

    def warningg(self, msg, *, source: Optional[str] = None):
        """Log a secondary warning (finer-grained than ``warning``).

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.WARNING, source=source, label="WARNINGG")

    # end def warningg
    def error(self, msg, *, source: Optional[str] = None):
        """Log an error that does not terminate the program.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.ERROR, source=source)

    # end def error
    def critical(self, msg, *, source: Optional[str] = None):
        """Log a critical error that typically leads to termination.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self._log(msg, LogLevel.CRITICAL, source=source)

    # end def critical
    def fatal(self, msg, *, source: Optional[str] = None):
        """Alias for ``critical``.

        Args:
            msg: Message to emit.
            source: Optional source override for display/filtering.

        Returns:
            None
        """
        self.critical(msg, source=source)

    # end def fatal
    def event(
            self,
            class_name: str,
            item_name: str,
            event_name: str,
            **params
    ):
        """Log a structured event emitted by a DeckPilot component.

        Args:
            class_name: Name of the class where the event originated.
            item_name: Logical item involved in the event.
            event_name: Event identifier.
            **params: Optional keyword parameters included in the message.

        Returns:
            None
        """
        if params is None:
            params = {}
        # end if
        event_params = ", ".join([f"{k}:{v}" for k, v in params.items()])
        message = f"{item_name}::{event_name} {event_params}".rstrip()
        self._log(
            message,
            LogLevel.DEBUG,
            source=class_name,
            label="EVENT",
            style="magenta bold",
        )



    # end def event
# end class Logger
# def setup_logger(
#         name: str = "deckpilot",
#         level: str = "INFO"
# ) -> logging.Logger:
#     """
#     Setup the logger for the application
#
#     Args:
#     - name (str): The name of the logger
#     - level (str): The logging level to use
#
#     Returns:
#     - logging.Logger: The logger instance
#     """
#     FORMAT = "%(message)s"
#     console = Console(stderr=True)
#     logging.basicConfig(
#         level=level,
#         format=FORMAT,
#         datefmt="[%X]",
#         handlers=[RichHandler(console=console, rich_tracebacks=True)],
#     )
#     return logging.getLogger(name)
# # end setup_logger

def setup_logger(
        level: str = "INFO",
        filters: Optional[Sequence[str]] = None,
) -> Logger:
    """Initialize and configure the global Logger instance.

    Args:
        level: Log level name (case-insensitive) to apply to the logger.
        filters: Optional list of filter specifications to constrain output.

    Returns:
        Logger: The configured logger instance.
    """
    print(f"filter: {filters}")
    logger = Logger()
    logger.set_level(getattr(LogLevel, level.upper(), LogLevel.INFO))
    logger.configure_filters(filters)
    return logger
# end def setup_logger
