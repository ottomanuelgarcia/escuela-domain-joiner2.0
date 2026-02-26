"""
Módulo de logging centralizado para escuela-domain-joiner
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = "/var/log/escuela-domain-joiner.log"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def setup_logger(name=__name__):
    """
    Configura el logger con rotación de archivos
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Crear carpeta de logs si no existe
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, mode=0o755)
        except Exception as e:
            print(f"Advertencia: No se pudo crear directorio de logs: {e}")
            # Usar /tmp como fallback
            LOG_FILE_ALT = "/tmp/escuela-domain-joiner.log"
            handler = RotatingFileHandler(
                LOG_FILE_ALT, 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
            return logger
    
    try:
        # Handler para archivo con rotación
        handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    except Exception as e:
        print(f"Advertencia: No se pudo configurar logging a archivo: {e}")
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()
