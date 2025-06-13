"""
File utilities for GreekDrop Audio Transcription App.
Handles audio processing, file conversion, metadata extraction, and export operations.
"""

import os
import subprocess
import tempfile
from datetime import datetime
from config.settings import AUDIO_EXTENSIONS


def convert_seconds_to_timestamp(seconds: float, sep=":") -> str:
    """Convert seconds to HH:MM:SS format for timestamps."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}{sep}{m:02}{sep}{s:02}"


def extract_audio_duration_ffprobe(file_path):
    """Extract audio duration in seconds using FFprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except Exception:
        return 0.0


def extract_basic_audio_metadata(file_path):
    """Extract basic audio metadata for display."""
    try:
        duration = extract_audio_duration_ffprobe(file_path)
        if duration > 0:
            return f"📊 Duration: {duration:.1f}s"
        return "📊 Could not read audio info"
    except Exception as e:
        return f"📊 Audio info error: {e}"


def convert_audio_to_wav(input_path):
    """Convert audio file to WAV format for better compatibility."""
    try:
        output_path = tempfile.mktemp(suffix=".wav")
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            output_path,
            "-y",
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    except Exception as e:
        print(f"⚠️ WAV conversion failed: {e}")
        return input_path


def validate_audio_file(file_path):
    """Validate if file is a supported audio format."""
    if not os.path.isfile(file_path):
        return False, f"File not found: {file_path}"

    if not file_path.lower().endswith(AUDIO_EXTENSIONS):
        supported = ", ".join(AUDIO_EXTENSIONS)
        return False, f"Unsupported format. Supported: {supported}"

    return True, "Valid audio file"


def save_transcription_to_file(result, file_path, selected_format):
    """Save transcription result to file in specified format."""
    try:
        base_name = os.path.splitext(file_path)[0]

        if selected_format == "txt":
            output_path = f"{base_name}_transcription.txt"
            export_structured_text_format(result, output_path)
        elif selected_format in ["srt", "vtt"]:
            output_path = f"{base_name}_transcription.{selected_format}"
            export_subtitle_format(
                result.get("segments", []), output_path, selected_format
            )
        else:
            raise ValueError(f"Unsupported format: {selected_format}")

        return output_path
    except Exception as e:
        print(f"❌ Failed to save transcription: {e}")
        return None


def export_structured_text_format(result, output_path):
    """Export transcription as structured text file with metadata."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # Header with metadata
            f.write("=" * 60 + "\n")
            f.write("GREEKDROP TRANSCRIPTION RESULT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {result.get('audio_duration', 0):.1f}s\n")
            f.write(f"Processing: {result.get('processing_time', 0):.1f}s\n")
            f.write(f"Speed: {result.get('speedup', 0):.2f}x real-time\n")
            f.write("=" * 60 + "\n\n")

            # Full text section
            f.write("FULL TEXT:\n")
            f.write("-" * 30 + "\n")
            f.write(result.get("text", "").strip() + "\n\n")

            # Timestamped segments if available
            segments = result.get("segments", [])
            if segments:
                f.write("TIMESTAMPED SEGMENTS:\n")
                f.write("-" * 30 + "\n")
                for segment in segments:
                    start_time = convert_seconds_to_timestamp(segment.get("start", 0))
                    end_time = convert_seconds_to_timestamp(segment.get("end", 0))
                    text = segment.get("text", "").strip()
                    f.write(f"[{start_time} - {end_time}] {text}\n")

        print(f"✅ Text saved: {output_path}")

    except Exception as e:
        print(f"❌ Failed to export text: {e}")
        raise


def export_subtitle_format(segments, output_path, format_type="srt"):
    """Export segments as subtitle file in SRT or VTT format."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            if format_type == "vtt":
                f.write("WEBVTT\n\n")

            for i, segment in enumerate(segments, 1):
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                text = segment.get("text", "").strip()

                if format_type == "srt":
                    # SRT format: HH:MM:SS,mmm
                    start_time = convert_seconds_to_timestamp(start).replace(
                        ":", ",", 2
                    )
                    end_time = convert_seconds_to_timestamp(end).replace(":", ",", 2)
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")

                elif format_type == "vtt":
                    # VTT format: HH:MM:SS.mmm
                    start_time = convert_seconds_to_timestamp(start)
                    end_time = convert_seconds_to_timestamp(end)
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")

        print(f"✅ Subtitles saved: {output_path}")

    except Exception as e:
        print(f"❌ Failed to export subtitles: {e}")
        raise


def cleanup_temp_files(*file_paths):
    """Clean up temporary files safely."""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete temp file {file_path}: {e}")


def normalize_file_path(file_path):
    """Normalize file path for cross-platform compatibility."""
    # Remove quotes if present
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]
    elif file_path.startswith("'") and file_path.endswith("'"):
        file_path = file_path[1:-1]

    # Handle multiple files - take the first one
    if "\n" in file_path or " " in file_path:
        files = file_path.split("\n") if "\n" in file_path else [file_path]
        file_path = files[0].strip()

    # Convert to platform-appropriate path
    return os.path.normpath(file_path)
