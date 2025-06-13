"""
Transcription logic for GreekDrop Audio Transcription App.
Handles AI-powered transcription using Whisper and fallback methods.
"""

import gc
import time
import threading
from config.settings import (
    TORCH_AVAILABLE,
    WHISPER_AVAILABLE,
    get_model_cache,
    set_model_cache,
)
from utils.file_utils import (
    convert_audio_to_wav,
    extract_audio_duration_ffprobe,
    cleanup_temp_files,
)


def load_cached_whisper_model():
    """Load Whisper model once and cache it globally for reuse."""
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "Whisper not available - install with: pip install openai-whisper"
        )

    model_cache, model_lock = get_model_cache()

    with model_lock:
        if model_cache is None:
            print("🔄 Loading Whisper model (one-time operation)...")

            # Import here to avoid import errors if not available
            import whisper
            import torch

            device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
            model = whisper.load_model("medium", device=device)
            set_model_cache(model)

            print(f"✅ Model loaded on {device}")
            return model
        else:
            return model_cache


def execute_whisper_transcription(file_path, duration_hint=None):
    """Execute optimized Whisper transcription with proper error handling."""
    if not WHISPER_AVAILABLE:
        return execute_fallback_transcription(file_path)

    start_time = time.time()
    wav_path = None

    try:
        # Load cached model
        model = load_cached_whisper_model()

        # Convert to WAV if needed for better compatibility
        wav_path = convert_audio_to_wav(file_path)

        # Get audio duration for performance metrics
        if duration_hint:
            audio_duration = duration_hint
        else:
            audio_duration = extract_audio_duration_ffprobe(wav_path)

        print(f"🎵 Audio duration: {audio_duration:.1f}s")

        # Perform transcription
        print("🔄 Transcribing audio with Whisper AI...")
        result = model.transcribe(wav_path, language="el")  # Greek language

        # Calculate performance metrics
        processing_time = time.time() - start_time
        speedup = audio_duration / processing_time if processing_time > 0 else 0

        print(f"⚡ Processed in {processing_time:.1f}s ({speedup:.2f}x real-time)")

        # Memory cleanup
        if TORCH_AVAILABLE:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        gc.collect()

        return {
            "text": result["text"],
            "segments": result.get("segments", []),
            "processing_time": processing_time,
            "speedup": speedup,
            "audio_duration": audio_duration,
        }

    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return execute_fallback_transcription(file_path)

    finally:
        # Clean up temporary WAV file
        if wav_path and wav_path != file_path:
            cleanup_temp_files(wav_path)


def execute_fallback_transcription(file_path):
    """Execute fallback transcription using SpeechRecognition library."""
    start_time = time.time()
    wav_path = None

    try:
        # Try using system speech recognition as fallback
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Convert to WAV first if needed
        wav_path = convert_audio_to_wav(file_path)

        # Get actual audio duration
        audio_duration = extract_audio_duration_ffprobe(wav_path or file_path)

        # Load and transcribe audio
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="el-GR")
        processing_time = time.time() - start_time
        speedup = (
            audio_duration / processing_time
            if processing_time > 0 and audio_duration > 0
            else 0
        )

        # Create reasonable segments for the fallback
        segments = create_fallback_segments(text, audio_duration)

        return {
            "text": text,
            "segments": segments,
            "processing_time": processing_time,
            "speedup": speedup,
            "audio_duration": audio_duration,
        }

    except ImportError:
        processing_time = time.time() - start_time
        error_text = (
            "[Transcription requires either OpenAI Whisper or SpeechRecognition library]\n"
            "Install with: pip install openai-whisper\n"
            "or: pip install SpeechRecognition"
        )
        return create_error_result(error_text, processing_time)

    except Exception as e:
        processing_time = time.time() - start_time
        error_text = f"[Fallback transcription failed: {e}]"
        return create_error_result(error_text, processing_time)

    finally:
        # Clean up temporary WAV file
        if wav_path and wav_path != file_path:
            cleanup_temp_files(wav_path)


def create_fallback_segments(text, audio_duration):
    """Create reasonable segments for fallback transcription."""
    segments = []
    if text.strip():
        # Split text into sentences for better segments
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if not sentences:
            sentences = [text.strip()]

        segment_duration = (
            audio_duration / len(sentences) if sentences else audio_duration
        )

        for i, sentence in enumerate(sentences):
            start = i * segment_duration
            end = min((i + 1) * segment_duration, audio_duration)
            segments.append(
                {
                    "start": start,
                    "end": end,
                    "text": sentence + ("." if not sentence.endswith(".") else ""),
                }
            )

    return segments


def create_error_result(error_text, processing_time, audio_duration=5):
    """Create a standardized error result structure."""
    return {
        "text": error_text,
        "segments": [{"start": 0, "end": audio_duration, "text": error_text}],
        "processing_time": processing_time,
        "speedup": 0,
        "audio_duration": audio_duration,
    }


def execute_intelligent_transcription(file_path, duration_hint=None):
    """Execute transcription using the best available method."""
    print(f"[TRANSCRIPTION] Processing: {file_path}")

    if WHISPER_AVAILABLE:
        return execute_whisper_transcription(file_path, duration_hint)
    else:
        print("🔄 Using fallback transcription method...")
        return execute_fallback_transcription(file_path)


def validate_system_dependencies():
    """Check which transcription dependencies are available."""
    status = {
        "torch": TORCH_AVAILABLE,
        "whisper": WHISPER_AVAILABLE,
    }

    # Check SpeechRecognition as fallback
    try:
        import speech_recognition

        status["speech_recognition"] = True
    except ImportError:
        status["speech_recognition"] = False

    print("📋 Transcription Dependencies:")
    for dep, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {dep}")

    return status
