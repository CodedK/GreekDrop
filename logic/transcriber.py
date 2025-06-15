"""
Advanced transcription engine for GreekDrop.
Supports multiple AI models with proper error handling and extensibility.
"""

import time
import warnings
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from config.settings import get_compute_device, is_gpu_forced, is_cpu_forced
from utils.logger import get_logger
from utils.file_utils import validate_audio_file, normalize_file_path


# Suppress common warnings
warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)
warnings.filterwarnings("ignore", category=FutureWarning)


class ModelCache:
    """Thread-safe model cache for preloaded AI models."""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._logger = get_logger()

    def set_model(self, model_name: str, model: Any) -> None:
        """Store a model in the cache."""
        self._models[model_name] = model
        self._logger.log_model_operation("CACHED", model_name)

    def get_model(self, model_name: str) -> Optional[Any]:
        """Retrieve a model from the cache."""
        model = self._models.get(model_name)
        if model:
            self._logger.debug(f"Retrieved cached model: {model_name}")
        return model

    def has_model(self, model_name: str) -> bool:
        """Check if a model is cached."""
        return model_name in self._models

    def clear_model(self, model_name: str) -> None:
        """Remove a model from cache."""
        if model_name in self._models:
            del self._models[model_name]
            self._logger.log_model_operation("CLEARED", model_name)

    def clear_all(self) -> None:
        """Clear all cached models."""
        count = len(self._models)
        self._models.clear()
        self._logger.info(f"Cleared {count} cached models")


class WhisperTranscriber:
    """OpenAI Whisper transcription engine."""

    def __init__(self):
        self.logger = get_logger()
        self.model_cache = ModelCache()
        self._compute_device = get_compute_device()

    def preload_model(self, model_name: str = "base") -> bool:
        """
        Preload Whisper model into cache.

        Args:
            model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

        Returns:
            True if successful, False otherwise
        """
        try:
            import whisper

            if self.model_cache.has_model(model_name):
                self.logger.info(f"Model {model_name} already cached")
                return True

            self.logger.log_model_operation("PRELOAD_START", model_name)
            start_time = time.time()

            # Load model with appropriate device
            device = self._get_device_string()
            self.logger.info(f"Loading Whisper model '{model_name}' on {device}")

            model = whisper.load_model(model_name, device=device)

            # Cache the model
            self.model_cache.set_model(model_name, model)

            load_time = time.time() - start_time
            self.logger.log_model_operation(
                "PRELOAD_SUCCESS", model_name, f"Loaded in {load_time:.2f}s on {device}"
            )

            return True

        except ImportError:
            self.logger.error("Whisper not available - cannot preload model")
            return False
        except Exception as e:
            self.logger.error(f"Model preload failed: {str(e)}", exc_info=True)
            return False

    def transcribe_audio(
        self,
        audio_file_path: str,
        model_name: str = "base",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_file_path: Path to audio file
            model_name: Whisper model to use
            progress_callback: Optional callback for progress updates

        Returns:
            Transcription result dictionary
        """
        start_time = time.time()

        try:
            # Validate input
            normalized_path = normalize_file_path(audio_file_path)
            is_valid, message = validate_audio_file(normalized_path)

            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid audio file: {message}",
                    "text": "",
                    "segments": [],
                }

            # Import Whisper
            try:
                import whisper
            except ImportError:
                return {
                    "success": False,
                    "error": "OpenAI Whisper not installed",
                    "text": "",
                    "segments": [],
                }

            # Update progress
            if progress_callback:
                progress_callback("Preparing transcription...")

            # Get or load model
            model = self.model_cache.get_model(model_name)
            if not model:
                self.logger.info(f"Model {model_name} not cached, loading...")
                if not self.preload_model(model_name):
                    return {
                        "success": False,
                        "error": f"Failed to load model: {model_name}",
                        "text": "",
                        "segments": [],
                    }
                model = self.model_cache.get_model(model_name)

            # Log transcription start
            self.logger.log_transcription_start(normalized_path, "Whisper")

            if progress_callback:
                progress_callback("Transcribing audio...")

            # Perform transcription
            result = model.transcribe(
                normalized_path,
                language="el",  # Greek language
                task="transcribe",
                fp16=self._should_use_fp16(),
                verbose=False,
            )

            # Process result
            transcription_time = time.time() - start_time

            output = {
                "success": True,
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", "el"),
                "processing_time": transcription_time,
                "model_used": model_name,
                "compute_device": self._compute_device,
                "audio_file": Path(normalized_path).name,
            }

            # Log completion
            self.logger.log_transcription_complete(
                normalized_path, transcription_time, ["In-memory result"]
            )

            if progress_callback:
                progress_callback("Transcription complete!")

            return output

        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "error": error_msg,
                "text": "",
                "segments": [],
                "processing_time": time.time() - start_time,
            }

    def _get_device_string(self) -> str:
        """Get device string for Whisper model loading."""
        if is_cpu_forced():
            return "cpu"
        elif is_gpu_forced():
            return "cuda"
        else:
            return "cuda" if self._compute_device == "GPU" else "cpu"

    def _should_use_fp16(self) -> bool:
        """Determine if FP16 should be used."""
        return self._compute_device == "GPU" and not is_cpu_forced()

    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

    def get_cached_models(self) -> List[str]:
        """Get list of currently cached models."""
        return list(self.model_cache._models.keys())

    def clear_model_cache(self) -> None:
        """Clear all cached models to free memory."""
        self.model_cache.clear_all()


class TranscriptionEngine:
    """
    Main transcription engine with support for multiple AI models.
    Easily extensible for additional models (e.g., Wav2Vec2, SpeechT5, etc.)
    """

    def __init__(self):
        self.logger = get_logger()
        self.whisper = WhisperTranscriber()
        self._engines = {"whisper": self.whisper}

    def preload_model(self, engine: str = "whisper", model_name: str = "base") -> bool:
        """
        Preload a model for the specified engine.

        Args:
            engine: Engine name ('whisper', future: 'wav2vec2', etc.)
            model_name: Model name/size

        Returns:
            True if successful, False otherwise
        """
        if engine not in self._engines:
            self.logger.error(f"Unknown transcription engine: {engine}")
            return False

        return self._engines[engine].preload_model(model_name)

    def transcribe(
        self,
        audio_file_path: str,
        engine: str = "whisper",
        model_name: str = "base",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio using the specified engine.

        Args:
            audio_file_path: Path to audio file
            engine: Engine to use ('whisper')
            model_name: Model name/size
            progress_callback: Optional progress callback

        Returns:
            Transcription result dictionary
        """
        if engine not in self._engines:
            return {
                "success": False,
                "error": f"Unknown transcription engine: {engine}",
                "text": "",
                "segments": [],
            }

        return self._engines[engine].transcribe_audio(
            audio_file_path, model_name, progress_callback
        )

    def get_available_engines(self) -> List[str]:
        """Get list of available transcription engines."""
        return list(self._engines.keys())

    def get_engine_models(self, engine: str) -> List[str]:
        """Get available models for an engine."""
        if engine in self._engines and hasattr(
            self._engines[engine], "get_available_models"
        ):
            return self._engines[engine].get_available_models()
        return []

    def clear_all_caches(self) -> None:
        """Clear all model caches across all engines."""
        for engine in self._engines.values():
            if hasattr(engine, "clear_model_cache"):
                engine.clear_model_cache()

        self.logger.info("Cleared all transcription engine caches")


# Global transcription engine instance
_transcription_engine: Optional[TranscriptionEngine] = None


def get_transcription_engine() -> TranscriptionEngine:
    """Get the global transcription engine instance."""
    global _transcription_engine
    if _transcription_engine is None:
        _transcription_engine = TranscriptionEngine()
    return _transcription_engine


def preload_default_model() -> bool:
    """Preload the default Whisper model."""
    engine = get_transcription_engine()
    return engine.preload_model("whisper", "base")


def transcribe_audio_file(
    audio_file_path: str, progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Transcribe an audio file using the default engine.

    Args:
        audio_file_path: Path to audio file
        progress_callback: Optional progress callback

    Returns:
        Transcription result dictionary
    """
    engine = get_transcription_engine()
    return engine.transcribe(audio_file_path, progress_callback=progress_callback)
