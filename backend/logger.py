"""
Central logging configuration.
"""

import sys

from loguru import logger


logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "{message}"
)

logger.add(
    "logs/application.log",
    level="DEBUG",
    rotation="10 MB",
    retention="10 days",
    compression="zip"
)