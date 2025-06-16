"""
Enhanced configuration and settings for GreekDrop.
Includes dependency checking, hardware forcing, and clean validation.
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


# Application constants
APP_NAME = "GreekDrop"
VERSION = "2.0.0"
WINDOW_SIZE = "950x750"
MIN_WINDOW_SIZE = (850, 650)

# Audio processing
AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".wma", ".aac"]
EXPORT_FORMATS = [".txt", ".srt", ".vtt", ".json", "All"]

# UI Theme
DEFAULT_THEME = "litera"

# Hardware forcing (can be set via environment variables)
FORCE_CPU_MODE = os.getenv("GREEKDROP_FORCE_CPU", "false").lower() == "true"
FORCE_GPU_MODE = os.getenv("GREEKDROP_FORCE_GPU", "false").lower() == "true"

# Debug mode
DEBUG_MODE = (
    "--debug" in sys.argv or os.getenv("GREEKDROP_DEBUG", "false").lower() == "true"
)

# Paths
TRANSCRIPTIONS_DIR = Path("transcriptions")
LOGS_DIR = Path("logs")
MODELS_DIR = Path("models")

# Create directories
for directory in [TRANSCRIPTIONS_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(exist_ok=True)


class DependencyChecker:
    """Clean dependency validation and availability checking."""

    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None

    def check_all(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Check all dependencies and return status.

        Args:
            force_refresh: Force recheck instead of using cache

        Returns:
            Dictionary with dependency status
        """
        if self._cache is not None and not force_refresh:
            return self._cache

        dependencies = {
            "modern_ui": self._check_ttkbootstrap(),
            "drag_drop": self._check_tkinterdnd2(),
            "whisper": self._check_whisper(),
            "torch": self._check_torch(),
            "audio_processing": self._check_audio_libs(),
        }

        # Hardware status
        dependencies.update(self._get_hardware_status())

        self._cache = dependencies
        return dependencies

    def _check_ttkbootstrap(self) -> bool:
        """Check if ttkbootstrap is available."""
        try:
            import ttkbootstrap

            return True
        except ImportError:
            return False

    def _check_tkinterdnd2(self) -> bool:
        """Check if tkinterdnd2 is available."""
        try:
            import tkinterdnd2

            return True
        except ImportError:
            return False

    def _check_whisper(self) -> bool:
        """Check if OpenAI Whisper is available."""
        try:
            import whisper

            return True
        except ImportError:
            return False

    def _check_torch(self) -> bool:
        """Check if PyTorch is available."""
        try:
            import torch

            return True
        except ImportError:
            return False

    def _check_audio_libs(self) -> bool:
        """Check if audio processing libraries are available."""
        try:
            import soundfile

            return True
        except ImportError:
            try:
                import librosa

                return True
            except ImportError:
                return False

    def _get_hardware_status(self) -> Dict[str, Any]:
        """Get detailed hardware status with forcing logic."""
        hardware = {
            "gpu_available": False,
            "cuda_available": False,
            "forced_mode": None,
            "compute_device": "CPU",
        }

        # Check for forcing
        if FORCE_CPU_MODE:
            hardware["forced_mode"] = "CPU"
            hardware["compute_device"] = "CPU"
            return hardware

        if FORCE_GPU_MODE:
            hardware["forced_mode"] = "GPU"
            hardware["compute_device"] = "GPU"
            return hardware

        # Normal detection
        try:
            import torch

            if torch.cuda.is_available():
                hardware["gpu_available"] = True
                hardware["cuda_available"] = True
                hardware["compute_device"] = "GPU"
        except ImportError:
            pass

        return hardware

    def get_missing_dependencies(self) -> list:
        """Get list of missing dependencies."""
        deps = self.check_all()
        missing = []

        for dep, available in deps.items():
            if isinstance(available, bool) and not available:
                missing.append(dep)

        return missing

    def is_fully_functional(self) -> bool:
        """Check if all core dependencies are available."""
        deps = self.check_all()
        core_deps = ["modern_ui", "whisper", "torch"]
        return all(deps.get(dep, False) for dep in core_deps)


# Global dependency checker instance
_dependency_checker = DependencyChecker()


def check_dependencies(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Check all dependencies using the global checker.

    Args:
        force_refresh: Force recheck instead of using cache

    Returns:
        Dictionary with dependency status
    """
    return _dependency_checker.check_all(force_refresh)


def get_compute_device() -> str:
    """Get the current compute device (CPU/GPU) considering forcing."""
    deps = check_dependencies()
    return deps.get("compute_device", "CPU")


def is_gpu_forced() -> bool:
    """Check if GPU mode is forced."""
    return FORCE_GPU_MODE


def is_cpu_forced() -> bool:
    """Check if CPU mode is forced."""
    return FORCE_CPU_MODE


def get_app_info() -> Dict[str, str]:
    """Get application information."""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "window_size": WINDOW_SIZE,
        "theme": DEFAULT_THEME,
        "debug_mode": str(DEBUG_MODE),
        "compute_device": get_compute_device(),
    }
