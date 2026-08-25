"""
Rich and standard logging utility.
"""

import logging
import sys

try:
    from rich.logging import RichHandler
    from rich.console import Console
    console = Console()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )
except ImportError:
    console = None
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger("RAG_EVAL")
