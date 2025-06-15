"""
Model preloading functionality for GreekDrop Audio Transcription App.
Handles asynchronous loading of AI models to improve user experience.
"""

import threading
from config.settings import check_dependencies
from logic.transcriber import get_transcription_engine


def preload_ai_model_async(output_callback=None):
    """Preload AI model asynchronously in the background."""

    def load_model():
        """Background thread function to load the model."""
        try:
            deps = check_dependencies()
            if deps.get("whisper", False):
                engine = get_transcription_engine()
                success = engine.preload_model("whisper", "base")

                if success:
                    message = "✅ AI Model preloaded and ready!"
                    if output_callback:
                        output_callback(message, "success")
                    else:
                        print(message)
                else:
                    message = "⚠️ Model preload failed"
                    if output_callback:
                        output_callback(message, "error")
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
    try:
        engine = get_transcription_engine()
        cached_models = engine.whisper.get_cached_models()
        return len(cached_models) > 0
    except Exception:
        return False


def get_model_status():
    """Get current model status information."""
    deps = check_dependencies()
    if not deps.get("whisper", False):
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


def get_cached_model():
    """Get the cached model if available."""
    try:
        engine = get_transcription_engine()
        if engine.whisper.model_cache.has_model("base"):
            return engine.whisper.model_cache.get_model("base")
        return None
    except Exception:
        return None
