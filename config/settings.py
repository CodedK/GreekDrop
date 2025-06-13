"""
Configuration and settings for GreekDrop Audio Transcription App.
Contains version info, constants, and dependency management.
"""

import warnings
import threading

# Application metadata
VERSION = "2.0.0-CLEAN"
APP_NAME = "GreekDrop"

# Suppress warnings
warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)

# Global model cache for Whisper - thread-safe
_model_cache = None
_model_lock = threading.Lock()

# Global UI state variables
window = None
output_text = None
transcribe_button = None
format_var = None
format_menu = None
progress_bar = None

# Dependency flags - set during import checks
MODERN_UI_AVAILABLE = False
TORCH_AVAILABLE = False
WHISPER_AVAILABLE = False
DRAG_DROP_AVAILABLE = False

# Audio file extensions supported
AUDIO_EXTENSIONS = (
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".aac",
    ".mp4",
    ".avi",
    ".mov",
)

# Export format options
EXPORT_FORMATS = ["txt", "srt", "vtt"]

# UI Configuration
DEFAULT_WINDOW_SIZE = "950x750"
MIN_WINDOW_SIZE = (850, 650)
DEFAULT_THEME = "flatly"  # ttkbootstrap theme

# Colors (Material Design inspired)
COLORS = {
    "primary": "#007bff",
    "success": "#28a745",
    "warning": "#ffc107",
    "error": "#dc3545",
    "info": "#17a2b8",
    "dark": "#343a40",
    "light": "#f8f9fa",
    "white": "#ffffff",
}


def check_dependencies():
    """Check and set dependency availability flags."""
    global MODERN_UI_AVAILABLE, TORCH_AVAILABLE, WHISPER_AVAILABLE, DRAG_DROP_AVAILABLE

    # Check ttkbootstrap
    try:
        import ttkbootstrap as ttk_bs

        MODERN_UI_AVAILABLE = True
    except ImportError:
        MODERN_UI_AVAILABLE = False
        print("⚠️ ttkbootstrap not available - using standard styling")

    # Check PyTorch
    try:
        import torch

        TORCH_AVAILABLE = True
    except ImportError:
        TORCH_AVAILABLE = False
        print("⚠️ PyTorch not available - CPU-only mode")

    # Check Whisper
    try:
        import whisper

        WHISPER_AVAILABLE = True
    except ImportError:
        WHISPER_AVAILABLE = False
        print("⚠️ OpenAI Whisper not available - using fallback transcription")

    # Check drag & drop
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD

        DRAG_DROP_AVAILABLE = True
    except ImportError:
        DRAG_DROP_AVAILABLE = False
        print("⚠️ TkinterDnD2 not available - drag & drop disabled")

    return {
        "modern_ui": MODERN_UI_AVAILABLE,
        "torch": TORCH_AVAILABLE,
        "whisper": WHISPER_AVAILABLE,
        "drag_drop": DRAG_DROP_AVAILABLE,
    }


def get_model_cache():
    """Get the global model cache reference."""
    return _model_cache, _model_lock


def set_model_cache(model):
    """Set the global model cache (thread-safe)."""
    global _model_cache
    with _model_lock:
        _model_cache = model
