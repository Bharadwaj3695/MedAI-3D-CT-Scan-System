import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ==============================================================================
# Directory Setup
# ==============================================================================
# Automatically create the backend/logs folder if it does not exist
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "app.log"

# ==============================================================================
# Logging Configuration
# ==============================================================================
# Format includes: Timestamp, Log Level, Logger Name, File/Line Number, and Message
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(name)s (%(filename)s:%(lineno)d): %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Clear existing handlers to avoid duplicate logs in environments like Uvicorn
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# 1. Console Handler (stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# 2. Rotating File Handler (prevents disk space exhaustion in production)
file_handler = RotatingFileHandler(
    filename=str(LOG_FILE_PATH),
    maxBytes=10485760,  # 10MB per file
    backupCount=5,      # Keep up to 5 backup log files
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

# ==============================================================================
# Logger Retrieval Helper
# ==============================================================================
def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance with the specified name.
    
    Example Usage inside other files:
    ----------------------------------
    from backend.utils.logger import get_logger
    
    # Initialize the logger for the current module
    logger = get_logger(__name__)
    
    # Log messages at various levels
    logger.info("Successfully started the service.")
    logger.warning("Database connection is slow.")
    
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.error("A division by zero occurred", exc_info=True)
    """
    return logging.getLogger(name)
