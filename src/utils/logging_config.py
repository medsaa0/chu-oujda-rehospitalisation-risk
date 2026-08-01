import logging
from logging.handlers import RotatingFileHandler

from src.utils.paths import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    """Créer un logger terminal et fichier."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log_filename = f"{name.replace('.', '_')}.log"

    file_handler = RotatingFileHandler(
        LOGS_DIR / log_filename,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger