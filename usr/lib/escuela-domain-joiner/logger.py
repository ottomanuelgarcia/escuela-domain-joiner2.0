"""
Módulo de logging centralizado para escuela-domain-joiner
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# log file paths for different purposes
LOG_BASE = "/var/log/escuela-domain-joiner"
LOG_FILE = LOG_BASE + "/escuela-domain-joiner.log"  # legacy/general
LOG_INSTALL = LOG_BASE + "/install.log"
LOG_AUTH = LOG_BASE + "/auth.log"
LOG_ACCESS = LOG_BASE + "/access.log"
LOG_ERRORS = LOG_BASE + "/errors.log"

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def _ensure_log_dir():
    """Create base log directory if missing."""
    if not os.path.exists(LOG_BASE):
        try:
            os.makedirs(LOG_BASE, mode=0o755)
        except Exception as e:
            print(f"Advertencia: No se pudo crear directorio de logs: {e}")


def _make_handler(path, when='midnight', backupCount=30):
    """Return a timed rotating file handler for given path."""
    try:
        handler = RotatingFileHandler(
            path,
            maxBytes=5*1024*1024,
            backupCount=3
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        return handler
    except Exception as e:
        print(f"Advertencia: No se pudo configurar handler para {path}: {e}")
        return None


def setup_logger(name, filepath, when='midnight', backupCount=30):
    """Create or retrieve a logger writing to **filepath** with rotation.

    Parameters like ``when``/``backupCount`` are placeholders; rotation is
    size-based by default but handlers may be replaced later.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # avoid duplicate handlers
    if not logger.handlers:
        handler = _make_handler(filepath, when, backupCount)
        if handler:
            logger.addHandler(handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
    return logger


# create loggers for various purposes
logger = setup_logger('edj', LOG_FILE)
install_logger = setup_logger('edj.install', LOG_INSTALL)
auth_logger = setup_logger('edj.auth', LOG_AUTH)
access_logger = setup_logger('edj.access', LOG_ACCESS)
error_logger = setup_logger('edj.errors', LOG_ERRORS)
