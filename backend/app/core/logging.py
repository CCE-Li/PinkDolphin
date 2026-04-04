import logging
import sys

from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root_logger.setLevel(settings.log_level.upper())
    root_logger.addHandler(handler)
