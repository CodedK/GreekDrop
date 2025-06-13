"""
Model preloading functionality for GreekDrop Audio Transcription App.
Handles asynchronous loading of AI models to improve user experience.
"""

import threading
from config.settings import WHISPER_AVAILABLE
from logic.transcriber import load_cached_whisper_model


def preload_ai_model_async(output_callback=None):
    """Preload AI model asynchronously in the background."""

    def load_model():
        """Background thread function to load the model."""
        try:
            if WHISPER_AVAILABLE:
                load_cached_whisper_model()
                message = "✅ AI Model preloaded and ready!"
                if output_callback:
                    output_callback(message, "success")
                else:
                    print(message)
            else:
                message = "ℹ️ Install openai-whisper for AI transcription"
                if output_callback:
                    output_callback(message, "info")
                else:
                    print(message)
        except Exception as e:
            error_msg = f"⚠️ Model preload failed: {e}"
            if output_callback:
                output_callback(error_msg, "error")
            else:
                print(error_msg)

    # Start loading in background thread
    threading.Thread(target=load_model, daemon=True).start()


def is_model_preloaded():
    """Check if the AI model is already loaded."""
    from config.settings import get_model_cache

    model_cache, _ = get_model_cache()
    return model_cache is not None


def get_model_status():
    """Get current model status information."""
    if not WHISPER_AVAILABLE:
        return {
            "available": False,
            "loaded": False,
            "message": "Whisper not available - install with: pip install openai-whisper",
        }

    is_loaded = is_model_preloaded()
    return {
        "available": True,
        "loaded": is_loaded,
        "message": "Model ready" if is_loaded else "Model not loaded",
    }
