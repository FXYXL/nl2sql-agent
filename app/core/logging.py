import logging
import sys


def setup_logging(level: str = "INFO"):
    fmt = "[%(asctime)s] %(levelname)s %(name)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
