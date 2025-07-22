"""
Logging configuration for AWS Assistant.
Provides structured logging with file rotation and error tracking.
"""

import logging
import logging.handlers
import sys

from typing import Optional
from config_manager import config


class AWSAssistantLogger:
    """Centralized logging for AWS Assistant."""

    def __init__(self, name: str = "aws_assistant"):
        self.name = name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with file and console handlers."""
        logger = logging.getLogger(self.name)

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)

        # Get logging configuration
        log_config = config.get_logging_config()
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_format = log_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        log_file = log_config.get("file", "aws_assistant.log")
        max_size = log_config.get("max_size", "10MB")
        backup_count = log_config.get("backup_count", 5)

        # Convert max_size to bytes
        if isinstance(max_size, str):
            if max_size.endswith("MB"):
                max_size = int(max_size[:-2]) * 1024 * 1024
            elif max_size.endswith("KB"):
                max_size = int(max_size[:-2]) * 1024
            else:
                max_size = int(max_size)

        # Create formatter
        formatter = logging.Formatter(log_format)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler with rotation
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_size, backupCount=backup_count
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")

        return logger

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(
        self, message: str, exc_info: Optional[Exception] = None, **kwargs
    ) -> None:
        """Log error message with optional exception info."""
        if exc_info:
            self.logger.error(message, exc_info=exc_info, extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)

    def critical(
        self, message: str, exc_info: Optional[Exception] = None, **kwargs
    ) -> None:
        """Log critical message with optional exception info."""
        if exc_info:
            self.logger.critical(message, exc_info=exc_info, extra=kwargs)
        else:
            self.logger.critical(message, extra=kwargs)

    def log_aws_error(
        self, service: str, operation: str, error: Exception, **kwargs
    ) -> None:
        """Log AWS-specific errors with context."""
        self.error(
            f"AWS {service} {operation} failed",
            exc_info=error,
            service=service,
            operation=operation,
            **kwargs,
        )

    def log_tool_execution(
        self, tool_name: str, success: bool, duration: float, **kwargs
    ) -> None:
        """Log tool execution metrics."""
        level = logging.DEBUG if success else logging.ERROR
        message = f"Tool {tool_name} executed {'successfully' if success else 'with error'} in {duration:.2f}s"
        self.logger.log(
            level,
            message,
            extra={
                "tool_name": tool_name,
                "success": success,
                "duration": duration,
                **kwargs,
            },
        )


# Global logger instance
logger = AWSAssistantLogger()
