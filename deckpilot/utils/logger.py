"""deckpilot.utils.logger module for DeckPilot.
"""


# Imports
from enum import IntEnum
import logging
from rich.console import Console
from rich.traceback import install
from rich.logging import RichHandler


install(show_locals=True)


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
    """Rich console logger tailored for DeckPilot output formatting."""

    # Singleton instance
    _instance = None

    # New instance
    def __new__(cls, level=LogLevel.INFO):
        """Create a singleton instance of the Logger class.
        
        Args:
            level (Any): The logging level to use.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._console = Console()
            cls._instance._level = level
        # end if
        return cls._instance

    # end def __new__
    @classmethod
    def inst(cls):
        """Get the singleton instance of the Logger class.
        
        Returns:
            Any: The singleton instance.
        """
        return cls._instance

    # end def inst
    def set_level(self, level: LogLevel):
        """Set the logging level for the logger.
        
        Args:
            level (LogLevel): The logging level to set.
        """
        self._level = level

    # end def set_level
    def get_level(self):
        """Get the current logging level.
        
        Returns:
            Any: The current logging level.
        """
        return self._level

    # end def get_level
    def _log(self, msg, log_level: LogLevel):
        """Log a message with the specified logging level.
        
        Args:
            msg (Any): The message to log.
            log_level (LogLevel): The logging level to use.
        """
        if self._level <= log_level:
            self._console.log(msg, _stack_offset=3)

        # end if
    # end def _log
    def debug(self, msg):
        """Log a debug message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[green]DEBUG\t\t{msg}[/]", LogLevel.DEBUG)

    # end def debug
    def debugg(self, msg):
        """Log a debug message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[green]DEBUGG\t\t{msg}[/]", LogLevel.DEBUGG)

    # end def debugg
    def info(self, msg):
        """Log an info message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"INFO\t\t{msg}", LogLevel.INFO)

    # end def info
    def warning(self, msg):
        """Log a warning message.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[yellow]WARNING\t\t{msg}[/]", LogLevel.WARNING)

    # end def warning
    def warningg(self, msg):
        """Log a warning message.
        Warning messages are logged for errors that do not lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[yellow bold]WARNINGG\t{msg}[/]", LogLevel.WARNING)

    # end def warningg
    def error(self, msg):
        """Log an error message.
        Error messages are logged for errors that do not lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[red]ERROR\t\t{msg}[/]", LogLevel.ERROR)

    # end def error
    def critical(self, msg):
        """Log a critical message.
        Critical messages are logged for errors that lead to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self._log(f"[red bold]CRITICAL\t{msg}[/]", LogLevel.CRITICAL)

    # end def critical
    def fatal(self, msg):
        """Log a fatal message. This is an alias for critical.
        Fatal messages are logged for error that leads to program termination.
        
        Args:
            msg (Any): The message to log.
        """
        self.critical(msg)

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
        self._log(f"[magenta bold]EVENT\t\t{class_name}({item_name})[/]::{event_name} {event_params}", LogLevel.DEBUG)



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
        level: str = "INFO"
) -> Logger:
    """
    Setup the logger for the application

    Args:
    - level (str): The logging level to use

    Returns:
    - Logger: The logger instance
    """
    return Logger(level=getattr(LogLevel, level.upper(), LogLevel.INFO))
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
