import gc
import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import warnings

# from concurrent.futures import ThreadPoolExecutor  # Not used in clean version
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

# Optional heavy dependencies - graceful fallback if not available
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not available - CPU-only mode")

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ OpenAI Whisper not available - using fallback transcription")

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    print("⚠️ TkinterDnD2 not available - drag & drop disabled")
    # Fallback to regular Tkinter
    TkinterDnD = tk

VERSION = "2.0.0-CLEAN"

warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)

# Global model cache - only if dependencies available
_model_cache = None
_model_lock = threading.Lock()


def check_dependencies():
    """Check which dependencies are available and inform user"""
    status = {
        "torch": TORCH_AVAILABLE,
        "whisper": WHISPER_AVAILABLE,
        "drag_drop": DRAG_DROP_AVAILABLE,
    }

    print("📋 Dependency Status:")
    for dep, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {dep}")

    return status


def get_cached_model():
    """Load model once and cache it globally - only if whisper available"""
    global _model_cache
    if not WHISPER_AVAILABLE:
        raise ImportError(
            "Whisper not available - install with: pip install openai-whisper"
        )

    with _model_lock:
        if _model_cache is None:
            print("🔄 Loading Whisper model (one-time operation)...")
            device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
            _model_cache = whisper.load_model("medium", device=device)
            print(f"✅ Model loaded on {device}")
        return _model_cache


def format_timestamp(seconds: float, sep=":") -> str:
    """Format seconds to HH:MM:SS - no dependencies"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}{sep}{m:02}{sep}{s:02}"


def get_audio_duration(file_path):
    """Get audio duration in seconds - requires only FFprobe"""
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


def get_audio_info_simple(file_path):
    """Simple audio info extraction - requires only FFprobe"""
    try:
        duration = get_audio_duration(file_path)
        if duration > 0:
            return f"📊 Duration: {duration:.1f}s"
        return "📊 Could not read audio info"
    except Exception as e:
        return f"📊 Audio info error: {e}"


def run_fallback_transcription(file_path):
    """Enhanced fallback transcription with proper timing"""
    start_time = time.time()

    try:
        # Try using system speech recognition as fallback
        import speech_recognition as sr

        r = sr.Recognizer()

        # Convert to WAV first if needed
        wav_path = convert_to_wav_simple(file_path)

        # Get actual audio duration
        audio_duration = get_audio_duration(wav_path or file_path)

        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)

        text = r.recognize_google(audio, language="el-GR")
        processing_time = time.time() - start_time
        speedup = (
            audio_duration / processing_time
            if processing_time > 0 and audio_duration > 0
            else 0
        )

        # Create reasonable segments for the fallback
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
        return {
            "text": error_text,
            "segments": [{"start": 0, "end": 5, "text": error_text}],
            "processing_time": processing_time,
            "speedup": 0,
            "audio_duration": 5,
        }

    except Exception as e:
        processing_time = time.time() - start_time
        audio_duration = get_audio_duration(file_path)
        error_text = f"[Transcription failed: {e}]"

        return {
            "text": error_text,
            "segments": [{"start": 0, "end": audio_duration or 5, "text": error_text}],
            "processing_time": processing_time,
            "speedup": 0,
            "audio_duration": audio_duration or 5,
        }


def convert_to_wav_simple(input_path):
    """Simple audio conversion - requires only FFmpeg"""
    if input_path.lower().endswith(".wav"):
        return input_path

    base_name = os.path.basename(input_path)
    name_wo_ext = os.path.splitext(base_name)[0]
    wav_path = os.path.join(tempfile.gettempdir(), f"{name_wo_ext}_simple.wav")

    command = ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", wav_path]

    try:
        subprocess.run(command, check=True, capture_output=True, timeout=60)
        return wav_path
    except Exception as e:
        print(f"[FFMPEG] Conversion failed: {e}")
        return input_path


def run_transcription_smart(file_path, duration_hint=None):
    """Smart transcription - uses best available method"""
    print(f"[TRANSCRIPTION] Processing: {file_path}")

    if WHISPER_AVAILABLE:
        return run_whisper_transcription_optimized(file_path, duration_hint)
    else:
        print("🔄 Using fallback transcription method...")
        return run_fallback_transcription(file_path)


def run_whisper_transcription_optimized(file_path, duration_hint=None):
    """Optimized Whisper transcription - only if dependencies available"""
    if not WHISPER_AVAILABLE:
        return run_fallback_transcription(file_path)

    model = get_cached_model()
    device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
    use_fp16 = TORCH_AVAILABLE and torch.cuda.is_available()

    print(f"🚀 Using device: {device}, FP16: {use_fp16}")

    # Get actual audio duration for speed calculation
    if duration_hint is None:
        duration_hint = get_audio_duration(file_path)

    start_time = time.time()
    raw_result = model.transcribe(
        file_path,
        language="el",
        verbose=False,
        condition_on_previous_text=False,
        fp16=use_fp16,
        beam_size=1,
        best_of=1,
        temperature=0,
        word_timestamps=False,
        no_speech_threshold=0.6,
        logprob_threshold=-1.0,
        compression_ratio_threshold=2.4,
    )

    processing_time = time.time() - start_time

    # Try multiple sources for audio duration
    audio_duration = (
        raw_result.get("duration")
        or duration_hint
        or (
            max(seg["end"] for seg in raw_result["segments"])
            if raw_result["segments"]
            else 0
        )
        or 0
    )

    speedup = (
        audio_duration / processing_time
        if processing_time > 0 and audio_duration > 0
        else 0
    )

    print(
        f"⚡ Processing speed: {speedup:.2f}x real-time "
        f"({processing_time:.1f}s for {audio_duration:.1f}s audio)"
    )

    return {
        "segments": raw_result["segments"],
        "text": raw_result["text"],
        "processing_time": processing_time,
        "speedup": speedup,
        "audio_duration": audio_duration,
    }


def save_transcription_simple(result, file_path, selected_format):
    """Simple file saving with proper formatting"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{timestamp}_{base_name}.{selected_format}"
    out_path = os.path.join(out_dir, filename)

    if selected_format == "txt":
        export_structured_text(result, out_path)
    else:
        export_subtitles_simple(result["segments"], out_path, fmt=selected_format)

    return out_path


def export_structured_text(result, out_path):
    """Export structured text with timestamps and metadata"""
    with open(out_path, "w", encoding="utf-8") as f:
        # Header with metadata
        f.write("=" * 60 + "\n")
        f.write("TRANSCRIPTION RESULT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if result.get("audio_duration"):
            f.write(f"Audio Duration: {result['audio_duration']:.1f} seconds\n")
        if result.get("processing_time"):
            f.write(f"Processing Time: {result['processing_time']:.1f} seconds\n")
        if result.get("speedup"):
            f.write(f"Speed: {result['speedup']:.2f}x real-time\n")

        f.write("=" * 60 + "\n\n")

        # Full text
        f.write("FULL TEXT:\n")
        f.write("-" * 20 + "\n")
        f.write(result["text"].strip() + "\n\n")

        # Timestamped segments (if available)
        if result.get("segments"):
            f.write("TIMESTAMPED SEGMENTS:\n")
            f.write("-" * 40 + "\n")
            for i, seg in enumerate(result["segments"], 1):
                start_time = format_timestamp(seg["start"])
                end_time = format_timestamp(seg["end"])
                text = seg["text"].strip()
                f.write(f"[{start_time} - {end_time}] {text}\n")
        else:
            f.write("(No timestamp information available)\n")


def export_subtitles_simple(segments, out_path, fmt="srt"):
    """Enhanced subtitle export with proper formatting"""
    if not segments:
        # Create minimal file if no segments
        with open(out_path, "w", encoding="utf-8") as f:
            if fmt == "vtt":
                f.write("WEBVTT\n\n")
                f.write("NOTE No timestamped segments available\n\n")
            else:
                f.write(
                    "1\n00:00:00,000 --> 00:00:01,000\n(No timestamped segments available)\n\n"
                )
        return

    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")

        for i, seg in enumerate(segments, 1):
            if fmt in {"srt", "vtt"}:
                # Handle timestamp formatting
                start_sep = ":" if fmt == "vtt" else ","
                end_sep = ":" if fmt == "vtt" else ","

                start = format_timestamp(seg["start"], sep=start_sep)
                end = format_timestamp(seg["end"], sep=end_sep)

                # Clean and validate text
                text = seg["text"].strip()
                if not text:
                    text = "[no text]"

                # Format based on subtitle type
                if fmt == "srt":
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
                elif fmt == "vtt":
                    f.write(f"{start} --> {end}\n{text}\n\n")


def cleanup_ui(btn, pbar):
    """Clean UI state - no dependencies"""
    btn.config(state=tk.NORMAL)
    pbar.stop()
    pbar.grid_remove()


def perform_transcription_clean(file_path, output_text, window, pbar, btn):
    """Clean transcription pipeline with minimal dependencies"""
    temp_file = None
    try:
        output_text.insert(tk.END, f"🚀 GreekDrop {VERSION} - Clean Edition\n")
        output_text.insert(tk.END, get_audio_info_simple(file_path) + "\n")
        output_text.insert(tk.END, "🎧 Processing audio...\n")
        window.update_idletasks()

        # Simple preprocessing
        if not file_path.lower().endswith(".wav"):
            temp_file = convert_to_wav_simple(file_path)
            processing_file = temp_file
        else:
            processing_file = file_path

        # Smart transcription
        result = run_transcription_smart(processing_file)

        # Save results
        selected_format = format_var.get()
        out_path = save_transcription_simple(result, file_path, selected_format)

        # UI feedback
        speedup = result.get("speedup", 0)
        output_text.insert(tk.END, "\n✅ Complete!\n")
        if speedup > 0:
            output_text.insert(tk.END, f"⚡ Speed: {speedup:.2f}x real-time\n")
        output_text.insert(tk.END, f"📁 Saved: {out_path}\n")

        # Optional memory cleanup
        if TORCH_AVAILABLE:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    except Exception as e:
        messagebox.showerror("Error", f"Transcription failed:\n{str(e)}")
        print(f"Error details: {e}")
    finally:
        # Cleanup temp files
        if temp_file and temp_file != file_path and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        cleanup_ui(btn, pbar)


def transcribe_file():
    """File selection and transcription trigger"""
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac")]
    )
    if not file_path:
        return

    output_text.delete("1.0", tk.END)
    transcribe_button.config(state=tk.DISABLED)
    progress_bar.grid(row=0, column=3, padx=10)
    progress_bar.start()

    threading.Thread(
        target=perform_transcription_clean,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


def on_file_drop(event):
    """Drag and drop handler - only if drag/drop available"""
    if not DRAG_DROP_AVAILABLE:
        return

    try:
        # Handle different file path formats from drag & drop
        files = window.tk.splitlist(event.data)
        if not files:
            return

        # Get first file and clean the path
        file_path = files[0]

        # Remove curly braces and quotes that might be added by the system
        file_path = file_path.strip("{}").strip('"').strip("'")

        # Convert forward slashes to backslashes on Windows if needed
        file_path = os.path.normpath(file_path)

        print(f"[DEBUG] Dropped file: {file_path}")

        if not os.path.isfile(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        # Check if it's an audio file
        audio_extensions = (
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
        if not file_path.lower().endswith(audio_extensions):
            messagebox.showerror(
                "Error",
                "Please drop an audio file (.wav, .mp3, .m4a, .flac, .ogg, .aac)",
            )
            return

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"📂 Processing: {os.path.basename(file_path)}\n")

        transcribe_button.config(state=tk.DISABLED)
        progress_bar.grid(row=0, column=3, padx=10)
        progress_bar.start()

        threading.Thread(
            target=perform_transcription_clean,
            args=(file_path, output_text, window, progress_bar, transcribe_button),
            daemon=True,
        ).start()

    except Exception as e:
        messagebox.showerror(
            "Drag & Drop Error", f"Failed to process dropped file: {e}"
        )
        print(f"[DEBUG] Drag & drop error: {e}")


def preload_model():
    """Preload model if available"""

    def load():
        try:
            if WHISPER_AVAILABLE:
                get_cached_model()
                output_text.insert(tk.END, "✅ AI Model preloaded and ready!\n")
            else:
                output_text.insert(
                    tk.END, "ℹ️ Install openai-whisper for AI transcription\n"
                )
        except Exception as e:
            output_text.insert(tk.END, f"⚠️ Model preload failed: {e}\n")

    threading.Thread(target=load, daemon=True).start()


def show_dependency_info():
    """Show dependency status to user"""
    status = check_dependencies()
    info_text = "📋 Dependency Status:\n\n"

    if status["whisper"]:
        info_text += "✅ OpenAI Whisper - Full AI transcription available\n"
    else:
        info_text += "❌ OpenAI Whisper - Install with: pip install openai-whisper\n"

    if status["torch"]:
        info_text += "✅ PyTorch - GPU acceleration available\n"
    else:
        info_text += "❌ PyTorch - CPU only mode\n"

    if status["drag_drop"]:
        info_text += "✅ Drag & Drop - Enabled\n"
    else:
        info_text += "❌ Drag & Drop - Install with: pip install tkinterdnd2\n"

    info_text += "\n💡 App works with minimal dependencies!\n"
    info_text += "Just Python + FFmpeg required for basic functionality."

    messagebox.showinfo("Dependency Status", info_text)


# GUI Setup
window = TkinterDnD.Tk() if DRAG_DROP_AVAILABLE else tk.Tk()
window.title(f"🚀 GreekDrop {VERSION}")
window.geometry("800x600")

frame = tk.Frame(window)
frame.pack(pady=10)

transcribe_button = tk.Button(
    frame,
    text="📂 Select Audio File",
    command=transcribe_file,
    font=("Arial", 14),
    bg="#4CAF50",
    fg="white",
)
transcribe_button.grid(row=0, column=0, padx=10)

format_var = tk.StringVar(value="txt")
format_menu = ttk.Combobox(
    frame,
    textvariable=format_var,
    values=["txt", "srt", "vtt"],
    width=10,
    font=("Arial", 12),
)
format_menu.grid(row=0, column=1)

label = tk.Label(frame, text="📄 Format", font=("Arial", 11))
label.grid(row=0, column=2, padx=5)

# Preload button - only show if Whisper available
if WHISPER_AVAILABLE:
    preload_btn = tk.Button(
        frame,
        text="🚀 Preload AI",
        command=preload_model,
        font=("Arial", 10),
        bg="#2196F3",
        fg="white",
    )
    preload_btn.grid(row=0, column=3, padx=5)

# Info button
info_btn = tk.Button(
    frame,
    text="ℹ️ Info",
    command=show_dependency_info,
    font=("Arial", 10),
    bg="#FF9800",
    fg="white",
)
info_btn.grid(row=0, column=4, padx=5)

progress_bar = ttk.Progressbar(frame, mode="indeterminate")
progress_bar.grid_remove()

output_text = tk.Text(window, wrap=tk.WORD, font=("Consolas", 10))
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Enhanced text styling
output_text.tag_config("info", foreground="#2196F3")
output_text.tag_config("stats", foreground="#FF9800")
output_text.tag_config("done", foreground="#4CAF50", font=("Consolas", 10, "bold"))

# Welcome message with dependency info
output_text.insert(tk.END, f"🚀 GreekDrop {VERSION} - Clean Edition\n")
hardware_info = "GPU" if TORCH_AVAILABLE and torch.cuda.is_available() else "CPU"
output_text.insert(tk.END, f"🖥️ Hardware: {hardware_info} acceleration\n")

if WHISPER_AVAILABLE:
    output_text.insert(tk.END, "🧠 AI Transcription: Ready\n")
else:
    output_text.insert(tk.END, "⚠️ AI Transcription: Install openai-whisper\n")

output_text.insert(tk.END, "💡 Click ℹ️ Info for dependency status\n\n")

# Drag and drop setup with visual feedback - only if available
if DRAG_DROP_AVAILABLE:
    window.drop_target_register(DND_FILES)
    window.dnd_bind("<<Drop>>", on_file_drop)

    # Add visual feedback for drag & drop
    def on_drag_enter(event):
        window.config(bg="#E8F5E8")
        output_text.config(bg="#F0F8F0")
        return event.action

    def on_drag_leave(event):
        window.config(bg="SystemButtonFace")  # Default system color
        output_text.config(bg="white")
        return event.action

    window.dnd_bind("<<DragEnter>>", on_drag_enter)
    window.dnd_bind("<<DragLeave>>", on_drag_leave)

    output_text.insert(tk.END, "📁 Drag & drop enabled - Drop audio files here!\n")
else:
    output_text.insert(tk.END, "📁 Use file button to select audio\n")
    output_text.insert(
        tk.END, "💡 Install tkinterdnd2 for drag & drop: pip install tkinterdnd2\n"
    )

if __name__ == "__main__":
    # Show dependency status on startup
    check_dependencies()
    window.mainloop()
