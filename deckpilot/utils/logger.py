"""
deckpilot.utils.logger module for DeckPilot.

# =====================================================================
#  DeckPilot - Stream Deck Controller
#  Copyright (C) 2025  Nils Schaetti
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =====================================================================

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
    """
    Structured information about a log message.
    """

    level: "LogLevel"
    label: str
    source: str
    message: str
# end class LogEntry


class LogFilterRule:
    """
    Represents a single AND-combined filtering rule.
    """

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
        if not any((level_pattern, source_pattern, message_pattern)):
            raise ValueError("A filter rule must declare at least one criterion")
        self.level_pattern = level_pattern
        self.source_pattern = source_pattern
        self.message_pattern = message_pattern
        self.raw = raw or ""

    # end __init__
    @classmethod
    def from_spec(cls, spec: str) -> "LogFilterRule":
        """
        Parse a CLI filter specification into a rule.
        """

        if not spec or not spec.strip():
            raise ValueError("Empty filter specification")

        tokens = [token.strip() for token in re.split(r"[;,]", spec) if token.strip()]
        if not tokens:
            raise ValueError("Filter specification contains no criteria")

        kwargs: dict[str, re.Pattern[str]] = {}
        for token in tokens:
            if "=" in token:
                key, value = token.split("=", 1)
            elif ":" in token:
                key, value = token.split(":", 1)
            else:
                raise ValueError(f"Invalid token '{token}'. Expected key=value pairs")

            key = key.strip().lower()
            field = cls._KEY_MAP.get(key)
            if field is None:
                raise ValueError(f"Unknown filter field '{key}' in '{spec}'")

            value = value.strip()
            if not value:
                raise ValueError(f"Missing regex for '{key}' in '{spec}'")
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

    # end from_spec
    def matches(self, entry: LogEntry) -> bool:
        """Return True if the entry satisfies this rule."""

        if self.level_pattern and not self.level_pattern.search(entry.label):
            return False
        if self.source_pattern and not self.source_pattern.search(entry.source):
            return False
        if self.message_pattern and not self.message_pattern.search(entry.message):
            return False
        return True

    # end matches


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
    """
    Rich console logger tailored for DeckPilot output formatting.
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
        """
        Create a singleton instance of the Logger class.
        
        Args:
            level (Any): The logging level to use.
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
        """
        Get the singleton instance of the Logger class.
        
        Returns:
            Any: The singleton instance.
        """
        return cls._instance

    # end def inst
    def set_level(
            self,
            level: LogLevel
    ):
        """
        Set the logging level for the logger.
        
        Args:
            level (LogLevel): The logging level to set.
        """
        self._level = level
    # end def set_level

    def configure_filters(
            self,
            specs: Optional[Sequence[str]]
    ):
        """
        Configure filtering rules for the logger.

        Args:
            specs (Sequence[str]): The filtering rules to configure.
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

    # end configure_filters
    def get_level(self):
        """Get the current logging level.
        
        Returns:
            Any: The current logging level.
        """
        return self._level
    # end def get_level

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
        """
        Log a message with the specified logging level.
        
        Args:
            msg (Any): The message to log.
            log_level (LogLevel): The logging level to use.
            source (Optional[str]): The source of the message.
            label (Optional[str]): The label of the message.
            style (Optional[str]): The style of the message.
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
        """
        Infer the caller class/module for display and filtering.
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
        """Return a padded, optionally styled log-level column."""

        padded = f"{label:<{self._LEVEL_COL_WIDTH}}"
        if style:
            return f"[{style}]{padded}[/]"
        return padded
    # end def _format_level

    def _format_source(self, source: Optional[str]) -> str:
        """Return a padded source column."""

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
        """
        Log a debug message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.DEBUG, source=source)
    # end def debug

    # end def debug
    def debugg(self, msg, *, source: Optional[str] = None):
        """Log a debug message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.DEBUGG, source=source)
    # end def debugg

    def info(self, msg, *, source: Optional[str] = None):
        """Log an info message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.INFO, source=source)
    # end def info

    def warning(self, msg, *, source: Optional[str] = None):
        """Log a warning message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.WARNING, source=source)
    # end def warning

    def warningg(self, msg, *, source: Optional[str] = None):
        """Log a warning message.
        Warning messages are logged for errors that do not lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.WARNING, source=source, label="WARNINGG")

    # end def warningg
    def error(self, msg, *, source: Optional[str] = None):
        """Log an error message.
        Error messages are logged for errors that do not lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.ERROR, source=source)

    # end def error
    def critical(self, msg, *, source: Optional[str] = None):
        """Log a critical message.
        Critical messages are logged for errors that lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(msg, LogLevel.CRITICAL, source=source)

    # end def critical
    def fatal(self, msg, *, source: Optional[str] = None):
        """Log a fatal message. This is an alias for critical.
        Fatal messages are logged for error that leads to program termination.
        
        Args:
            msg (Any): The message to log.
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
        """Log an event with the specified parameters.
        
        Args:
            class_name (str): The name of the class where the event occurred.
            item_name (str): The name of the item associated with the event.
            event_name (str): The name of the event.
            params (Any): Optional dictionary of parameters associated with the event.
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
    """
    Setup the logger for the application

    Args:
    - level (str): The logging level to use
    - filters (Sequence[str] | None): Optional filter specifications

    Returns:
    - Logger: The logger instance
    """
    logger = Logger()
    logger.set_level(getattr(LogLevel, level.upper(), LogLevel.INFO))
    logger.configure_filters(filters)
    return logger
# end def setup_logger


# end def setup_logger
# def get_logger() -> logging.Logger:
#     """
#     Get the logger instance.
#
#     :return: logging.Logger instance
#     """
#     return logging.getLogger("deckpilot")
# # end get_logger
