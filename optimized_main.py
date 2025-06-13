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

# Modern UI styling - graceful fallback
try:
    import ttkbootstrap as ttk_bs

    MODERN_UI_AVAILABLE = True
except ImportError:
    MODERN_UI_AVAILABLE = False
    print("⚠️ ttkbootstrap not available - using standard styling")
    # Install with: pip install ttkbootstrap

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

# Global UI variables
window = None
output_text = None
transcribe_button = None
format_var = None
format_menu = None
progress_bar = None


def validate_system_dependencies():
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


def load_cached_whisper_model():
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


def convert_seconds_to_timestamp(seconds: float, sep=":") -> str:
    """Format seconds to HH:MM:SS - no dependencies"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}{sep}{m:02}{sep}{s:02}"


def extract_audio_duration_ffprobe(file_path):
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


def extract_basic_audio_metadata(file_path):
    """Simple audio info extraction - requires only FFprobe"""
    try:
        duration = extract_audio_duration_ffprobe(file_path)
        if duration > 0:
            return f"📊 Duration: {duration:.1f}s"
        return "📊 Could not read audio info"
    except Exception as e:
        return f"📊 Audio info error: {e}"


def execute_fallback_transcription(file_path):
    """Enhanced fallback transcription with proper timing"""
    start_time = time.time()

    try:
        # Try using system speech recognition as fallback
        import speech_recognition as sr

        r = sr.Recognizer()

        # Convert to WAV first if needed
        wav_path = convert_audio_to_wav(file_path)

        # Get actual audio duration
        audio_duration = extract_audio_duration_ffprobe(wav_path or file_path)

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
        audio_duration = extract_audio_duration_ffprobe(file_path)
        error_text = f"[Transcription failed: {e}]"

        return {
            "text": error_text,
            "segments": [{"start": 0, "end": audio_duration or 5, "text": error_text}],
            "processing_time": processing_time,
            "speedup": 0,
            "audio_duration": audio_duration or 5,
        }


def convert_audio_to_wav(input_path):
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


def execute_intelligent_transcription(file_path, duration_hint=None):
    """Smart transcription - uses best available method"""
    print(f"[TRANSCRIPTION] Processing: {file_path}")

    if WHISPER_AVAILABLE:
        return execute_whisper_transcription(file_path, duration_hint)
    else:
        print("🔄 Using fallback transcription method...")
        return execute_fallback_transcription(file_path)


def execute_whisper_transcription(file_path, duration_hint=None):
    """Optimized Whisper transcription - only if dependencies available"""
    if not WHISPER_AVAILABLE:
        return execute_fallback_transcription(file_path)

    model = load_cached_whisper_model()
    device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
    use_fp16 = TORCH_AVAILABLE and torch.cuda.is_available()

    print(f"🚀 Using device: {device}, FP16: {use_fp16}")

    # Get actual audio duration for speed calculation
    if duration_hint is None:
        duration_hint = extract_audio_duration_ffprobe(file_path)

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


def save_transcription_to_file(result, file_path, selected_format):
    """Simple file saving with proper formatting"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{timestamp}_{base_name}.{selected_format}"
    out_path = os.path.join(out_dir, filename)

    if selected_format == "txt":
        export_structured_text_format(result, out_path)
    else:
        export_subtitle_format(result["segments"], out_path, fmt=selected_format)

    return out_path


def export_structured_text_format(result, out_path):
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
                start_time = convert_seconds_to_timestamp(seg["start"])
                end_time = convert_seconds_to_timestamp(seg["end"])
                text = seg["text"].strip()
                f.write(f"[{start_time} - {end_time}] {text}\n")
        else:
            f.write("(No timestamp information available)\n")


def export_subtitle_format(segments, out_path, fmt="srt"):
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

                start = convert_seconds_to_timestamp(seg["start"], sep=start_sep)
                end = convert_seconds_to_timestamp(seg["end"], sep=end_sep)

                # Clean and validate text
                text = seg["text"].strip()
                if not text:
                    text = "[no text]"

                # Format based on subtitle type
                if fmt == "srt":
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
                elif fmt == "vtt":
                    f.write(f"{start} --> {end}\n{text}\n\n")


def reset_ui_state(btn, pbar):
    """Clean UI state - no dependencies"""
    if MODERN_UI_AVAILABLE:
        btn.configure(state="normal")
    else:
        btn.config(state=tk.NORMAL)
    pbar.stop()
    pbar.grid_remove()


def process_transcription_workflow(file_path, output_text, window, pbar, btn):
    """Clean transcription pipeline with minimal dependencies"""
    temp_file = None
    try:
        output_text.insert(tk.END, f"🚀 GreekDrop {VERSION} - Clean Edition\n")
        output_text.insert(tk.END, extract_basic_audio_metadata(file_path) + "\n")
        output_text.insert(tk.END, "🎧 Processing audio...\n")
        window.update_idletasks()

        # Simple preprocessing
        if not file_path.lower().endswith(".wav"):
            temp_file = convert_audio_to_wav(file_path)
            processing_file = temp_file
        else:
            processing_file = file_path

        # Smart transcription
        result = execute_intelligent_transcription(processing_file)

        # Save results
        selected_format = format_var.get()
        out_path = save_transcription_to_file(result, file_path, selected_format)

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
        reset_ui_state(btn, pbar)


def select_and_transcribe_audio_file():
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
        target=process_transcription_workflow,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


def handle_file_drop_event(event):
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

        if MODERN_UI_AVAILABLE:
            transcribe_button.configure(state="disabled")
        else:
            transcribe_button.config(state=tk.DISABLED)
        progress_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        progress_bar.start()

        threading.Thread(
            target=process_transcription_workflow,
            args=(file_path, output_text, window, progress_bar, transcribe_button),
            daemon=True,
        ).start()

    except Exception as e:
        messagebox.showerror(
            "Drag & Drop Error", f"Failed to process dropped file: {e}"
        )
        print(f"[DEBUG] Drag & drop error: {e}")


def preload_ai_model_async():
    """Preload model if available"""

    def load():
        try:
            if WHISPER_AVAILABLE:
                load_cached_whisper_model()
                output_text.insert(tk.END, "✅ AI Model preloaded and ready!\n")
            else:
                output_text.insert(
                    tk.END, "ℹ️ Install openai-whisper for AI transcription\n"
                )
        except Exception as e:
            output_text.insert(tk.END, f"⚠️ Model preload failed: {e}\n")

    threading.Thread(target=load, daemon=True).start()


def display_dependency_information():
    """Show dependency status to user"""
    status = validate_system_dependencies()
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


# ========================== MODERN UI SETUP ==========================


def initialize_modern_application():
    """Create modern Material Design-inspired UI"""
    global window, output_text, transcribe_button, format_var, progress_bar

    # Initialize window with modern theme
    if MODERN_UI_AVAILABLE:
        window = ttk_bs.Window(themename="flatly")  # Modern light theme
    else:
        window = TkinterDnD.Tk() if DRAG_DROP_AVAILABLE else tk.Tk()
        window.configure(bg="#f8f9fa")

    window.title(f"🎯 GreekDrop {VERSION}")
    window.geometry("900x700")
    window.minsize(800, 600)

    # Configure grid weights for responsive design
    window.grid_rowconfigure(1, weight=1)
    window.grid_columnconfigure(0, weight=1)

    # Header frame with app title and status
    create_header_frame()

    # Main control panel
    create_control_panel()

    # Output/log area
    create_output_area()

    # Footer with info
    create_footer()

    # Setup drag & drop functionality
    configure_drag_drop_functionality()

    # Apply modern styling
    apply_modern_styling()

    # Welcome message
    show_welcome_message()


def create_header_frame():
    """Create modern header with title and status indicators"""
    global header_frame, status_frame

    if MODERN_UI_AVAILABLE:
        header_frame = ttk_bs.Frame(window, bootstyle="primary")
    else:
        header_frame = tk.Frame(window, bg="#007bff", height=80)

    header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    header_frame.grid_columnconfigure(1, weight=1)

    # App logo/title
    if MODERN_UI_AVAILABLE:
        title_label = ttk_bs.Label(
            header_frame,
            text="🎯 GreekDrop",
            font=("Segoe UI", 20, "bold"),
            bootstyle="inverse-primary",
        )
        version_label = ttk_bs.Label(
            header_frame,
            text=f"v{VERSION}",
            font=("Segoe UI", 10),
            bootstyle="inverse-primary",
        )
    else:
        title_label = tk.Label(
            header_frame,
            text="🎯 GreekDrop",
            font=("Segoe UI", 20, "bold"),
            bg="#007bff",
            fg="white",
        )
        version_label = tk.Label(
            header_frame,
            text=f"v{VERSION}",
            font=("Segoe UI", 10),
            bg="#007bff",
            fg="#b3d9ff",
        )

    title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
    version_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

    # Status indicators
    create_status_indicators()


def create_status_indicators():
    """Create status indicators for dependencies"""
    global status_frame

    if MODERN_UI_AVAILABLE:
        status_frame = ttk_bs.Frame(header_frame, bootstyle="primary")
    else:
        status_frame = tk.Frame(header_frame, bg="#007bff")

    status_frame.grid(row=0, column=2, rowspan=2, padx=20, pady=15, sticky="e")

    # Hardware status
    hardware_info = "GPU" if TORCH_AVAILABLE and torch.cuda.is_available() else "CPU"
    hw_color = "success" if "GPU" in hardware_info else "warning"

    if MODERN_UI_AVAILABLE:
        hw_label = ttk_bs.Label(
            status_frame,
            text=f"🖥️ {hardware_info}",
            bootstyle=f"inverse-{hw_color}",
            font=("Segoe UI", 9),
        )
        ai_status = "🧠 AI Ready" if WHISPER_AVAILABLE else "⚠️ Basic Mode"
        ai_color = "success" if WHISPER_AVAILABLE else "warning"
        ai_label = ttk_bs.Label(
            status_frame,
            text=ai_status,
            bootstyle=f"inverse-{ai_color}",
            font=("Segoe UI", 9),
        )
    else:
        hw_label = tk.Label(
            status_frame,
            text=f"🖥️ {hardware_info}",
            bg="#007bff",
            fg="white",
            font=("Segoe UI", 9),
        )
        ai_status = "🧠 AI Ready" if WHISPER_AVAILABLE else "⚠️ Basic Mode"
        ai_label = tk.Label(
            status_frame, text=ai_status, bg="#007bff", fg="white", font=("Segoe UI", 9)
        )

    hw_label.grid(row=0, column=0, sticky="e", pady=2)
    ai_label.grid(row=1, column=0, sticky="e", pady=2)


def create_control_panel():
    """Create modern control panel with buttons and options"""
    global control_frame, transcribe_button, format_var, format_menu, progress_bar

    if MODERN_UI_AVAILABLE:
        control_frame = ttk_bs.Frame(window, bootstyle="light")
    else:
        control_frame = tk.Frame(window, bg="#f8f9fa")

    control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
    control_frame.grid_columnconfigure(0, weight=1)

    # Main action button (prominent)
    if MODERN_UI_AVAILABLE:
        transcribe_button = ttk_bs.Button(
            control_frame,
            text="📂  Select Audio File",
            command=select_and_transcribe_audio_file,
            bootstyle="success-outline",
            width=25,
        )
        transcribe_button.configure(style="Outline.TButton")
    else:
        transcribe_button = tk.Button(
            control_frame,
            text="📂  Select Audio File",
            command=select_and_transcribe_audio_file,
            font=("Segoe UI", 12, "bold"),
            bg="#28a745",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
        )

    transcribe_button.grid(row=0, column=0, pady=10)

    # Options frame
    if MODERN_UI_AVAILABLE:
        options_frame = ttk_bs.Frame(control_frame, bootstyle="light")
    else:
        options_frame = tk.Frame(control_frame, bg="#f8f9fa")

    options_frame.grid(row=1, column=0, pady=10)

    # Format selection
    if MODERN_UI_AVAILABLE:
        format_label = ttk_bs.Label(
            options_frame, text="Export Format:", font=("Segoe UI", 10)
        )
        format_var = tk.StringVar(value="txt")
        format_menu = ttk_bs.Combobox(
            options_frame,
            textvariable=format_var,
            values=["txt", "srt", "vtt"],
            width=12,
            bootstyle="primary",
        )
    else:
        format_label = tk.Label(
            options_frame, text="Export Format:", font=("Segoe UI", 10), bg="#f8f9fa"
        )
        format_var = tk.StringVar(value="txt")
        format_menu = ttk.Combobox(
            options_frame,
            textvariable=format_var,
            values=["txt", "srt", "vtt"],
            width=12,
            font=("Segoe UI", 10),
        )

    format_label.grid(row=0, column=0, padx=(0, 10), pady=5)
    format_menu.grid(row=0, column=1, padx=10, pady=5)

    # Action buttons frame
    if MODERN_UI_AVAILABLE:
        buttons_frame = ttk_bs.Frame(control_frame, bootstyle="light")
    else:
        buttons_frame = tk.Frame(control_frame, bg="#f8f9fa")

    buttons_frame.grid(row=2, column=0, pady=10)

    # Preload AI button (if available)
    if WHISPER_AVAILABLE:
        if MODERN_UI_AVAILABLE:
            preload_btn = ttk_bs.Button(
                buttons_frame,
                text="🚀 Preload AI",
                command=preload_ai_model_async,
                bootstyle="info-outline",
                width=12,
            )
        else:
            preload_btn = tk.Button(
                buttons_frame,
                text="🚀 Preload AI",
                command=preload_ai_model_async,
                font=("Segoe UI", 10),
                bg="#17a2b8",
                fg="white",
                relief="flat",
                padx=15,
                pady=5,
            )
        preload_btn.grid(row=0, column=0, padx=5)

    # Info button
    if MODERN_UI_AVAILABLE:
        info_btn = ttk_bs.Button(
            buttons_frame,
            text="ℹ️ Info",
            command=display_dependency_information,
            bootstyle="warning-outline",
            width=12,
        )
    else:
        info_btn = tk.Button(
            buttons_frame,
            text="ℹ️ Info",
            command=display_dependency_information,
            font=("Segoe UI", 10),
            bg="#ffc107",
            fg="black",
            relief="flat",
            padx=15,
            pady=5,
        )

    info_btn.grid(row=0, column=1, padx=5)

    # Progress bar (hidden by default)
    if MODERN_UI_AVAILABLE:
        progress_bar = ttk_bs.Progressbar(
            control_frame, mode="indeterminate", bootstyle="success-striped"
        )
    else:
        progress_bar = ttk.Progressbar(control_frame, mode="indeterminate")

    progress_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
    progress_bar.grid_remove()


def create_output_area():
    """Create modern output/log area with better styling"""
    global output_text, output_frame

    if MODERN_UI_AVAILABLE:
        output_frame = ttk_bs.Frame(window, bootstyle="secondary")
    else:
        output_frame = tk.Frame(window, bg="#e9ecef")

    output_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
    output_frame.grid_rowconfigure(1, weight=1)
    output_frame.grid_columnconfigure(0, weight=1)

    # Output area label
    if MODERN_UI_AVAILABLE:
        output_label = ttk_bs.Label(
            output_frame,
            text="📝 Transcription Output & Status",
            font=("Segoe UI", 12, "bold"),
            bootstyle="secondary",
        )
    else:
        output_label = tk.Label(
            output_frame,
            text="📝 Transcription Output & Status",
            font=("Segoe UI", 12, "bold"),
            bg="#e9ecef",
        )

    output_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

    # Text area with scrollbar
    text_frame = tk.Frame(output_frame)
    text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)

    output_text = tk.Text(
        text_frame,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#ffffff",
        fg="#212529",
        relief="flat",
        borderwidth=0,
        padx=15,
        pady=15,
    )

    # Scrollbar
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=output_text.yview)
    output_text.configure(yscrollcommand=scrollbar.set)

    output_text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Configure text tags for colored output
    output_text.tag_config(
        "header", foreground="#007bff", font=("Consolas", 12, "bold")
    )
    output_text.tag_config("info", foreground="#17a2b8", font=("Consolas", 10))
    output_text.tag_config(
        "success", foreground="#28a745", font=("Consolas", 10, "bold")
    )
    output_text.tag_config("warning", foreground="#ffc107", font=("Consolas", 10))
    output_text.tag_config("error", foreground="#dc3545", font=("Consolas", 10, "bold"))
    output_text.tag_config("stats", foreground="#6f42c1", font=("Consolas", 10))


def create_footer():
    """Create footer with drag & drop indicator"""
    global footer_frame

    if MODERN_UI_AVAILABLE:
        footer_frame = ttk_bs.Frame(window, bootstyle="dark")
    else:
        footer_frame = tk.Frame(window, bg="#343a40", height=40)

    footer_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)

    if DRAG_DROP_AVAILABLE:
        footer_text = "📁 Drag & drop audio files anywhere to transcribe"
    else:
        footer_text = "💡 Install tkinterdnd2 for drag & drop functionality"

    if MODERN_UI_AVAILABLE:
        footer_label = ttk_bs.Label(
            footer_frame,
            text=footer_text,
            font=("Segoe UI", 9),
            bootstyle="inverse-dark",
        )
    else:
        footer_label = tk.Label(
            footer_frame,
            text=footer_text,
            font=("Segoe UI", 9),
            bg="#343a40",
            fg="#ffffff",
        )

    footer_label.pack(pady=10)


def configure_drag_drop_functionality():
    """Configure drag & drop functionality with visual feedback - renamed from setup_drag_drop"""
    if DRAG_DROP_AVAILABLE and hasattr(window, "drop_target_register"):
        window.drop_target_register(DND_FILES)
        window.dnd_bind("<<Drop>>", handle_file_drop_event)

        def on_drag_enter(event):
            if MODERN_UI_AVAILABLE:
                window.configure(bg="#e8f5e8")
            else:
                window.configure(bg="#e8f5e8")
            output_text.configure(bg="#f0f8f0")
            return event.action

        def on_drag_leave(event):
            if MODERN_UI_AVAILABLE:
                window.configure(bg="#ffffff")
            else:
                window.configure(bg="#f8f9fa")
            output_text.configure(bg="#ffffff")
            return event.action

        window.dnd_bind("<<DragEnter>>", on_drag_enter)
        window.dnd_bind("<<DragLeave>>", on_drag_leave)


def apply_modern_styling():
    """Apply additional modern styling"""
    if not MODERN_UI_AVAILABLE:
        # Apply some basic modern styling for fallback
        window.option_add("*TCombobox*Listbox.selectBackground", "#007bff")

        # Modern button hover effects (simplified)
        def on_enter(event):
            event.widget.configure(relief="solid", borderwidth=1)

        def on_leave(event):
            event.widget.configure(relief="flat", borderwidth=0)

        if hasattr(transcribe_button, "bind"):
            transcribe_button.bind("<Enter>", on_enter)
            transcribe_button.bind("<Leave>", on_leave)


def show_welcome_message():
    """Show welcome message with modern formatting"""
    output_text.insert(tk.END, "🎯 GreekDrop Audio Transcription\n", "header")
    output_text.insert(tk.END, f"Version {VERSION} - Clean Edition\n\n", "info")

    # Hardware info
    hardware_info = "GPU" if TORCH_AVAILABLE and torch.cuda.is_available() else "CPU"
    output_text.insert(tk.END, f"🖥️ Hardware: {hardware_info} acceleration\n", "info")

    # AI status
    if WHISPER_AVAILABLE:
        output_text.insert(tk.END, "🧠 AI Transcription: Ready\n", "success")
    else:
        output_text.insert(
            tk.END, "⚠️ AI Transcription: Install openai-whisper\n", "warning"
        )

    # Drag & drop status
    if DRAG_DROP_AVAILABLE:
        output_text.insert(tk.END, "📁 Drag & drop: Enabled\n", "success")
    else:
        output_text.insert(tk.END, "📁 Drag & drop: Install tkinterdnd2\n", "warning")

    output_text.insert(
        tk.END, "\n💡 Click ℹ️ Info for detailed dependency status\n", "info"
    )
    output_text.insert(
        tk.END, "🚀 Ready to transcribe Greek audio files!\n\n", "success"
    )


# ========================== MODIFIED GUI SETUP ==========================

# Create the modern UI
initialize_modern_application()

if __name__ == "__main__":
    # Show dependency status on startup
    validate_system_dependencies()
    window.mainloop()
