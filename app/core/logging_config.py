import os
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Define custom TRACE level
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)

logging.Logger.trace = trace

def setup_logging():
    # Ensure log directories exist
    srv_log_dir = os.path.dirname(settings.SRV_LOG_FILE_LOCATION)
    access_log_dir = os.path.dirname(settings.ACCESS_LOG_FILE_LOCATION)
    
    if srv_log_dir:
        os.makedirs(srv_log_dir, exist_ok=True)
    if access_log_dir:
        os.makedirs(access_log_dir, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(process)d:%(threadName)s] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": settings.APP_LOG_LEVEL,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.SRV_LOG_FILE_LOCATION,
                "formatter": "detailed",
                "maxBytes": settings.LOG_FILE_SIZE_BYTE,
                "backupCount": settings.LOG_FILE_BACKUP_COUNT,
                "level": settings.APP_LOG_LEVEL,
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.ACCESS_LOG_FILE_LOCATION,
                "formatter": "default",
                "maxBytes": settings.LOG_FILE_SIZE_BYTE,
                "backupCount": settings.LOG_FILE_BACKUP_COUNT,
                "level": "INFO",
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": settings.ROOT_LOG_LEVEL,
            },
            "app": {
                "handlers": ["console", "file"],
                "level": settings.APP_LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "access_file"],
                "level": "INFO",
                "propagate": False,
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    logging.info(f"Logging initialized with ROOT_LEVEL={settings.ROOT_LOG_LEVEL}, APP_LEVEL={settings.APP_LOG_LEVEL}")
    logging.info(f"Server logs: {settings.SRV_LOG_FILE_LOCATION}")
    logging.info(f"Access logs: {settings.ACCESS_LOG_FILE_LOCATION}")
