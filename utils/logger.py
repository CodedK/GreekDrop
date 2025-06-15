"""
Comprehensive logging system for GreekDrop.
Handles file writes, model loading, errors, and debug information.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class GreekDropLogger:
    """Centralized logging system for GreekDrop application."""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("GreekDrop")
        self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # File handler for all logs
        log_file = (
            logs_dir / f"greekdrop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.info(f"GreekDrop logging initialized - Debug: {debug_mode}")
        self.info(f"Log file: {log_file}")

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = True) -> None:
        """Log critical message with exception info."""
        self.logger.critical(message, exc_info=exc_info)

    def log_file_operation(
        self, operation: str, file_path: str, success: bool = True
    ) -> None:
        """Log file operations with detailed info."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"FILE_OP [{status}] {operation}: {file_path}")

    def log_model_operation(
        self, operation: str, model_name: str, details: Optional[str] = None
    ) -> None:
        """Log AI model operations."""
        message = f"MODEL_OP {operation}: {model_name}"
        if details:
            message += f" - {details}"
        self.info(message)

    def log_hardware_detection(
        self, gpu_available: bool, device_name: str = ""
    ) -> None:
        """Log hardware detection results."""
        mode = "GPU" if gpu_available else "CPU"
        message = f"HARDWARE_DETECTION: {mode} mode active"
        if device_name:
            message += f" ({device_name})"
        self.info(message)

    def log_transcription_start(self, file_path: str, format_type: str) -> None:
        """Log transcription start."""
        self.info(
            f"TRANSCRIPTION_START: {os.path.basename(file_path)} -> {format_type}"
        )

    def log_transcription_complete(
        self, file_path: str, duration: float, output_files: list
    ) -> None:
        """Log transcription completion."""
        self.info(
            f"TRANSCRIPTION_COMPLETE: {os.path.basename(file_path)} in {duration:.2f}s"
        )
        for output_file in output_files:
            self.info(f"TRANSCRIPTION_OUTPUT: {output_file}")


# Global logger instance
_logger_instance: Optional[GreekDropLogger] = None


def get_logger() -> GreekDropLogger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = GreekDropLogger()
    return _logger_instance


def init_logger(debug_mode: bool = False) -> GreekDropLogger:
    """Initialize the global logger."""
    global _logger_instance
    _logger_instance = GreekDropLogger(debug_mode=debug_mode)
    return _logger_instance
