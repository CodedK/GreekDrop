"""
Enhanced file utilities for GreekDrop.
Includes robust path validation, comprehensive logging, and "All" format support.
"""

import os
import subprocess
import tempfile
from datetime import datetime
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import time

from config.settings import AUDIO_EXTENSIONS, TRANSCRIPTIONS_DIR
from utils.logger import get_logger


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


def validate_audio_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if the file is a supported audio file.

    Args:
        file_path: Path to the audio file

    Returns:
        Tuple of (is_valid, message)
    """
    logger = get_logger()

    try:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            message = f"File does not exist: {file_path}"
            logger.error(message)
            return False, message

        # Check if it's a file (not directory)
        if not path.is_file():
            message = f"Path is not a file: {file_path}"
            logger.error(message)
            return False, message

        # Check file extension
        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            message = f"Unsupported audio format: {path.suffix}. Supported: {', '.join(AUDIO_EXTENSIONS)}"
            logger.error(message)
            return False, message

        # Check file size (basic validation)
        file_size = path.stat().st_size
        if file_size == 0:
            message = "Audio file is empty"
            logger.error(message)
            return False, message

        # Check if file is readable
        try:
            with open(path, "rb") as f:
                f.read(1024)  # Try reading first 1KB
        except PermissionError:
            message = f"Permission denied reading file: {file_path}"
            logger.error(message)
            return False, message
        except Exception as e:
            message = f"Cannot read audio file: {str(e)}"
            logger.error(message)
            return False, message

        logger.info(
            f"Audio file validation successful: {path.name} ({file_size:,} bytes)"
        )
        return True, "Valid audio file"

    except Exception as e:
        message = f"File validation failed: {str(e)}"
        logger.error(message, exc_info=True)
        return False, message


def normalize_file_path(file_path: str) -> str:
    """
    Normalize file path for cross-platform compatibility.

    Args:
        file_path: Raw file path string

    Returns:
        Normalized file path
    """
    logger = get_logger()

    try:
        # Remove curly braces and quotes that might come from drag & drop
        cleaned = file_path.strip("{}\"' ")

        # Convert to Path object and resolve
        normalized = Path(cleaned).resolve()

        logger.debug(f"Normalized path: {file_path} -> {normalized}")
        return str(normalized)

    except Exception as e:
        logger.error(f"Path normalization failed: {str(e)}", exc_info=True)
        return file_path


def validate_output_directory(output_dir: Path) -> Tuple[bool, str]:
    """
    Validate that output directory exists and is writable.

    Args:
        output_dir: Directory path for outputs

    Returns:
        Tuple of (is_valid, message)
    """
    logger = get_logger()

    try:
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Test write permissions with a temporary file
        test_file = output_dir / ".greekdrop_write_test.tmp"
        try:
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink()  # Delete test file

            logger.debug(f"Output directory validated: {output_dir}")
            return True, "Directory is writable"

        except PermissionError:
            message = f"No write permission for directory: {output_dir}"
            logger.error(message)
            return False, message

    except Exception as e:
        message = f"Directory validation failed: {str(e)}"
        logger.error(message, exc_info=True)
        return False, message


def create_filename_base(audio_file_path: str) -> str:
    """
    Create base filename for output files.

    Args:
        audio_file_path: Path to the original audio file

    Returns:
        Base filename without extension
    """
    audio_path = Path(audio_file_path)
    timestamp = int(time.time())
    return f"{audio_path.stem}_{timestamp}"


def save_transcription_txt(content: str, output_path: Path) -> bool:
    """Save transcription as plain text file."""
    logger = get_logger()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        absolute_path = output_path.resolve()
        logger.log_file_operation("SAVE_TXT", str(absolute_path), success=True)
        print(f"✅ TXT file saved: {absolute_path}")
        return True

    except Exception as e:
        logger.log_file_operation("SAVE_TXT", str(output_path), success=False)
        logger.error(f"Failed to save TXT file: {str(e)}", exc_info=True)
        print(f"❌ Failed to save TXT file: {str(e)}")
        return False


def save_transcription_srt(segments: List[Dict], output_path: Path) -> bool:
    """Save transcription as SRT subtitle file."""
    logger = get_logger()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start_time = format_srt_time(segment.get("start", 0))
                end_time = format_srt_time(segment.get("end", 0))
                text = segment.get("text", "").strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        absolute_path = output_path.resolve()
        logger.log_file_operation("SAVE_SRT", str(absolute_path), success=True)
        print(f"✅ SRT file saved: {absolute_path}")
        return True

    except Exception as e:
        logger.log_file_operation("SAVE_SRT", str(output_path), success=False)
        logger.error(f"Failed to save SRT file: {str(e)}", exc_info=True)
        print(f"❌ Failed to save SRT file: {str(e)}")
        return False


def save_transcription_vtt(segments: List[Dict], output_path: Path) -> bool:
    """Save transcription as VTT subtitle file."""
    logger = get_logger()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")

            for segment in segments:
                start_time = format_vtt_time(segment.get("start", 0))
                end_time = format_vtt_time(segment.get("end", 0))
                text = segment.get("text", "").strip()

                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        absolute_path = output_path.resolve()
        logger.log_file_operation("SAVE_VTT", str(absolute_path), success=True)
        print(f"✅ VTT file saved: {absolute_path}")
        return True

    except Exception as e:
        logger.log_file_operation("SAVE_VTT", str(output_path), success=False)
        logger.error(f"Failed to save VTT file: {str(e)}", exc_info=True)
        print(f"❌ Failed to save VTT file: {str(e)}")
        return False


def save_transcription_json(result: Dict[str, Any], output_path: Path) -> bool:
    """Save complete transcription result as JSON."""
    logger = get_logger()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.log_file_operation("SAVE_JSON", str(output_path), success=True)
        return True

    except Exception as e:
        logger.log_file_operation("SAVE_JSON", str(output_path), success=False)
        logger.error(f"Failed to save JSON file: {str(e)}", exc_info=True)
        return False


def format_srt_time(seconds: float) -> str:
    """Format time for SRT format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def format_vtt_time(seconds: float) -> str:
    """Format time for VTT format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


def save_transcription_to_file(
    result: Dict[str, Any], audio_file_path: str, format_type: str
) -> List[str]:
    """
    Save transcription to file(s) with comprehensive validation and logging.

    Args:
        result: Transcription result dictionary
        audio_file_path: Path to original audio file
        format_type: Output format ('.txt', '.srt', '.vtt', '.json', or 'All')

    Returns:
        List of successfully saved file paths
    """
    logger = get_logger()

    # Validate output directory
    is_valid, message = validate_output_directory(TRANSCRIPTIONS_DIR)
    if not is_valid:
        logger.error(f"Output directory validation failed: {message}")
        return []

    # Create base filename
    filename_base = create_filename_base(audio_file_path)
    saved_files = []

    # Extract content and segments
    text_content = result.get("text", "")
    segments = result.get("segments", [])

    if not text_content and not segments:
        logger.error("No transcription content to save")
        return []

    # Define format handlers
    format_handlers = {
        ".txt": lambda path: save_transcription_txt(text_content, path),
        ".srt": lambda path: save_transcription_srt(segments, path),
        ".vtt": lambda path: save_transcription_vtt(segments, path),
        ".json": lambda path: save_transcription_json(result, path),
    }

    # Determine which formats to save
    if format_type == "All":
        formats_to_save = [".txt", ".srt", ".vtt"]
    else:
        # Clean the format string
        format_clean = format_type.strip().lower()
        if not format_clean.startswith("."):
            format_clean = "." + format_clean
        formats_to_save = [format_clean] if format_clean in format_handlers else []

    if not formats_to_save:
        logger.error(f"Unsupported format type: {format_type}")
        return []

    # Save each format
    for fmt in formats_to_save:
        output_path = TRANSCRIPTIONS_DIR / f"{filename_base}{fmt}"

        try:
            handler = format_handlers[fmt]
            if handler(output_path):
                saved_files.append(str(output_path))
                logger.info(f"Transcription saved: {output_path.name}")
        except Exception as e:
            logger.error(f"Failed to save {fmt} format: {str(e)}", exc_info=True)

    # Log summary
    if saved_files:
        logger.info(f"Transcription save complete: {len(saved_files)} files saved")
        for file_path in saved_files:
            logger.info(f"  -> {Path(file_path).name}")
    else:
        logger.error("No files were saved successfully")

    return saved_files


def extract_basic_audio_metadata(file_path: str) -> str:
    """
    Extract basic metadata from audio file.

    Args:
        file_path: Path to audio file

    Returns:
        Formatted metadata string
    """
    logger = get_logger()

    try:
        path = Path(file_path)
        stat = path.stat()

        # Basic file info
        file_size = stat.st_size
        file_size_mb = file_size / (1024 * 1024)

        metadata = (
            f"File: {path.name}\n"
            f"Size: {file_size_mb:.2f} MB ({file_size:,} bytes)\n"
            f"Format: {path.suffix.upper()}"
        )

        logger.debug(f"Extracted metadata for: {path.name}")
        return metadata

    except Exception as e:
        logger.error(f"Failed to extract metadata: {str(e)}", exc_info=True)
        return f"File: {Path(file_path).name}\nMetadata extraction failed"


def clean_temp_files() -> None:
    """Clean up temporary files created during processing."""
    logger = get_logger()

    temp_patterns = ["*.tmp", ".greekdrop_*", "*.temp"]
    cleaned_count = 0

    for pattern in temp_patterns:
        for temp_file in TRANSCRIPTIONS_DIR.glob(pattern):
            try:
                temp_file.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned temp file: {temp_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clean temp file {temp_file.name}: {str(e)}")

    if cleaned_count > 0:
        logger.info(f"Cleaned {cleaned_count} temporary files")


def get_output_directory() -> str:
    """Get the current output directory path."""
    return str(TRANSCRIPTIONS_DIR.absolute())
