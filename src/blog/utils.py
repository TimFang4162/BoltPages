"""Logging utilities."""

import logging
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=False)]
    )
    return logging.getLogger("rich")


console = Console()
