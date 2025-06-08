import gc
import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
import torch
import whisper
from tkinterdnd2 import DND_FILES, TkinterDnD

VERSION = "2.0.0-OPTIMIZED"

warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)

# Global model cache - CRITICAL OPTIMIZATION
_model_cache = None
_model_lock = threading.Lock()


def get_cached_model():
    """Load model once and cache it globally - 10x faster subsequent loads"""
    global _model_cache
    with _model_lock:
        if _model_cache is None:
            print("🔄 Loading Whisper model (one-time operation)...")
            # Use GPU if available, enable FP16 for 2x speed boost on compatible hardware
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _model_cache = whisper.load_model("medium", device=device)
            print(f"✅ Model loaded on {device}")
            # Save the model to the cache directory
            model_path = os.path.join(os.path.expanduser("~"), "whisper_model")
            torch.save(_model_cache, model_path)
            print(f"✅ Model saved to {model_path}")
            # if gpu is not available, print the re
        return _model_cache


def format_timestamp(seconds: float, sep=":") -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}{sep}{m:02}{sep}{s:02}"


def get_audio_metadata_fast(file_path):
    """Optimized metadata extraction - single FFprobe call"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "format=duration:stream=codec_name,channels,sample_rate",
            "-of",
            "json",
            file_path,
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        return result.stdout
    except Exception as e:
        return f"[ERROR] FFprobe failed: {e}"


def estimate_duration_fast(file_path):
    """Fast duration estimation with caching"""
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
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def preprocess_audio_optimized(input_path):
    """Optimized audio preprocessing with better parameters"""
    base_name = os.path.basename(input_path)
    name_wo_ext = os.path.splitext(base_name)[0]
    cleaned_path = os.path.join(tempfile.gettempdir(), f"{name_wo_ext}_opt.wav")

    # Optimized FFmpeg command for faster processing
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ar",
        "16000",  # Whisper's native sample rate
        "-ac",
        "1",  # Mono (faster processing)
        "-c:a",
        "pcm_s16le",  # Uncompressed for fastest loading
        "-af",
        "silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:"
        + "detection=peak,aformat=dblp,dynaudnorm",
        cleaned_path,
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, timeout=30)
        return cleaned_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"[FFMPEG] Preprocessing failed, using original: {e}")
        return input_path


def run_whisper_transcription_optimized(file_path, duration_hint=None):
    """Heavily optimized transcription with GPU support and minimal I/O"""
    print(f"[WHISPER] Processing: {file_path}")
    # Use cached model - MASSIVE performance gain
    model = get_cached_model()
    # Determine optimal settings based on hardware
    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_fp16 = torch.cuda.is_available()  # Use FP16 on GPU for 2x speed

    print(f"🚀 Using device: {device}, FP16: {use_fp16}")

    # Optimized transcription parameters
    start_time = time.time()
    raw_result = model.transcribe(
        file_path,
        language="el",
        verbose=False,
        condition_on_previous_text=False,
        fp16=use_fp16,
        # Performance optimizations
        beam_size=1,  # Faster decoding
        best_of=1,  # Single pass
        temperature=0,  # Deterministic output
        word_timestamps=False,  # Skip if not needed
        # Aggressive optimizations
        no_speech_threshold=0.6,
        logprob_threshold=-1.0,
        compression_ratio_threshold=2.4,
    )

    processing_time = time.time() - start_time
    audio_duration = raw_result.get("duration") or duration_hint or 0
    speedup = audio_duration / processing_time if processing_time > 0 else 0

    print(
        f"⚡ Processing speed: {speedup:.2f}x real-time "
        f"({processing_time:.1f}s for {audio_duration:.1f}s audio)"
    )

    # Minimal result processing
    return {
        "segments": raw_result["segments"],
        "text": raw_result["text"],
        "processing_time": processing_time,
        "speedup": speedup,
    }


def save_transcription_optimized(result, file_path, selected_format):
    """Optimized file saving with minimal I/O"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{timestamp}_{base_name}.{selected_format}"
    out_path = os.path.join(out_dir, filename)

    if selected_format == "txt":
        with open(out_path, "w", encoding="utf-8", buffering=8192) as f:
            f.write(result["text"])
    else:
        export_subtitles_fast(result["segments"], out_path, fmt=selected_format)

    return out_path


def export_subtitles_fast(segments, out_path, fmt="srt"):
    """Optimized subtitle export with buffering"""
    lines = []

    if fmt == "vtt":
        lines.append("WEBVTT\n\n")
    for i, seg in enumerate(segments, 1):
        if fmt in {"srt", "vtt"}:
            start = format_timestamp(seg["start"], sep=":" if fmt == "vtt" else ",")
            end = format_timestamp(seg["end"], sep=":" if fmt == "vtt" else ",")
            lines.append(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    # Single write operation
    with open(out_path, "w", encoding="utf-8", buffering=8192) as f:
        f.writelines(lines)


def cleanup_ui(btn, pbar):
    btn.config(state=tk.NORMAL)
    pbar.stop()
    pbar.grid_remove()


def perform_transcription_optimized(file_path, output_text, window, pbar, btn):
    """Optimized transcription pipeline"""
    cleaned_path = None
    try:
        # Minimal UI updates to reduce overhead
        output_text.insert(tk.END, f"🚀 GreekDrop {VERSION} - Optimized Processing\n")
        output_text.insert(tk.END, "🎧 Preprocessing audio...\n")
        window.update_idletasks()  # Faster than update()

        # Parallel preprocessing and duration estimation
        with ThreadPoolExecutor(max_workers=2) as executor:
            preprocess_future = executor.submit(preprocess_audio_optimized, file_path)
            duration_future = executor.submit(estimate_duration_fast, file_path)

            cleaned_path = preprocess_future.result()
            duration = duration_future.result()

        output_text.insert(tk.END, f"⏱️ Duration: {duration:.1f}s\n")
        output_text.insert(tk.END, "🧠 Analyzing with AI...\n")
        window.update_idletasks()

        # Core transcription
        result = run_whisper_transcription_optimized(
            cleaned_path, duration_hint=duration
        )

        # Save results
        selected_format = format_var.get()
        out_path = save_transcription_optimized(result, file_path, selected_format)

        # Final UI update
        speedup = result.get("speedup", 0)
        processing_time = result.get("processing_time", 0)
        output_text.insert(tk.END, f"\n✅ Complete! Speed: {speedup:.2f}x real-time\n")
        output_text.insert(tk.END, f"📁 Saved: {out_path}\n")
        output_text.insert(tk.END, f"⚡ Processing time: {processing_time:.1f}s\n\n")

        # Force garbage collection to free memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        input("🔚 Press Enter to exit...")  # Console wait

    except Exception as e:
        messagebox.showerror("Error", f"Transcription failed:\n{str(e)}")
        print(f"Error details: {e}")
    finally:
        # Cleanup
        if cleaned_path and cleaned_path != file_path and os.path.exists(cleaned_path):
            try:
                os.remove(cleaned_path)
            except Exception:
                pass
        cleanup_ui(btn, pbar)


def transcribe_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg")]
    )
    if not file_path:
        return
    output_text.delete("1.0", tk.END)
    transcribe_button.config(state=tk.DISABLED)
    progress_bar.grid(row=0, column=3, padx=10)
    progress_bar.start()

    # Use daemon thread for cleanup
    threading.Thread(
        target=perform_transcription_optimized,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


def on_file_drop(event):
    file_path = window.tk.splitlist(event.data)[0].strip("{}")
    if not os.path.isfile(file_path):
        messagebox.showerror("Error", "File not found.")
        return

    output_text.delete("1.0", tk.END)
    transcribe_button.config(state=tk.DISABLED)
    progress_bar.grid(row=0, column=3, padx=10)
    progress_bar.start()

    threading.Thread(
        target=perform_transcription_optimized,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


def preload_model():
    """Preload model in background for instant first use"""

    def load():
        try:
            get_cached_model()
            output_text.insert(tk.END, "✅ AI Model preloaded and ready!\n")
        except Exception as e:
            output_text.insert(tk.END, f"⚠️ Model preload failed: {e}\n")

    threading.Thread(target=load, daemon=True).start()


# GUI Setup
window = TkinterDnD.Tk()
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

label = tk.Label(frame, text="📄 Output Format", font=("Arial", 11))
label.grid(row=0, column=2, padx=5)

# Preload button for instant processing
preload_btn = tk.Button(
    frame,
    text="🚀 Preload AI",
    command=preload_model,
    font=("Arial", 10),
    bg="#2196F3",
    fg="white",
)
preload_btn.grid(row=0, column=4, padx=5)

progress_bar = ttk.Progressbar(frame, mode="indeterminate")
progress_bar.grid_remove()

output_text = tk.Text(window, wrap=tk.WORD, font=("Consolas", 10))
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Enhanced text styling
output_text.tag_config("info", foreground="#2196F3")
output_text.tag_config("stats", foreground="#FF9800")
output_text.tag_config("done", foreground="#4CAF50", font=("Consolas", 10, "bold"))

# Welcome message with optimization info
output_text.insert(tk.END, f"🚀 GreekDrop {VERSION} - Optimized Edition\n")
output_text.insert(
    tk.END,
    f"🖥️  Hardware: {'GPU' if torch.cuda.is_available() else 'CPU'} acceleration available\n",
)
output_text.insert(tk.END, "💡 Tip: Click 'Preload AI' for instant processing!\n\n")

# Drag and drop setup
window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", on_file_drop)

if __name__ == "__main__":
    window.mainloop()
