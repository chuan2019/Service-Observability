"""Elasticsearch logging configuration and setup."""

import json
import logging
import logging.config
from datetime import datetime
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError

from app.core.config import settings


class ElasticsearchHandler(logging.Handler):
    """Custom logging handler that sends logs to Elasticsearch."""

    def __init__(self, es_client: Elasticsearch, index_prefix: str = "logs"):
        super().__init__()
        self.es_client = es_client
        self.index_prefix = index_prefix

    def emit(self, record):
        """Emit a log record to Elasticsearch."""
        try:
            # Create the log document
            log_doc = self.format_log_record(record)

            # Generate index name with date
            index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"

            # Send to Elasticsearch
            self.es_client.index(index=index_name, body=log_doc)
        except (ConnectionError, TransportError) as e:
            # If Elasticsearch is not available, log to console
            print(f"Failed to send log to Elasticsearch: {e}")
        except Exception as e:
            # Handle any other exceptions
            print(f"Error in ElasticsearchHandler: {e}")

    def format_log_record(self, record) -> dict[str, Any]:
        """Format log record for Elasticsearch."""
        # Get the formatted message
        message = self.format(record)

        # Base log document
        log_doc = {
            "@timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "application": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }

        # Add exception info if present
        if record.exc_info:
            log_doc["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    self.formatException(record.exc_info) if record.exc_info else None
                ),
            }

        # Add extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ]:
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        log_doc[key] = value
                    except (TypeError, ValueError):
                        log_doc[key] = str(value)

        return log_doc


def create_elasticsearch_client() -> Elasticsearch:
    """Create and configure Elasticsearch client."""
    es_config = {
        "hosts": [
            f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
        ],
        "request_timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True,
    }

    # Add authentication if provided
    if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
        es_config["http_auth"] = (
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD,
        )

    # Add SSL configuration
    if settings.ELASTICSEARCH_USE_SSL:
        es_config["use_ssl"] = True
        es_config["verify_certs"] = False  # For development only

    return Elasticsearch(**es_config)


def setup_logging():
    """Setup application logging with Elasticsearch integration."""

    # Create Elasticsearch client
    try:
        es_client = create_elasticsearch_client()
        # Test connection
        es_client.ping()
        es_available = True
        print("Elasticsearch connection established")
    except Exception as e:
        es_available = False
        print(f"Elasticsearch not available: {e}")
        print("Logs will only be written to console and file")

    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    # Add Elasticsearch handler if available
    if es_available:
        # Create logs directory
        import os

        os.makedirs("logs", exist_ok=True)

        # Add Elasticsearch handler to config
        es_handler = ElasticsearchHandler(
            es_client, settings.ELASTICSEARCH_INDEX_PREFIX
        )
        es_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(es_handler)

    # Create logs directory first
    import os

    os.makedirs("logs", exist_ok=True)

    # Apply logging configuration
    logging.config.dictConfig(logging_config)
