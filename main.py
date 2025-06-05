"""
GreekDrop - Greek Audio Transcription Tool

A tkinter-based GUI application that transcribes Greek audio files to text
using OpenAI's Whisper model. Supports multiple output formats including
plain text, SRT, and VTT subtitles.
"""

import os
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk
import whisper
import warnings
from tkinterdnd2 import DND_FILES, TkinterDnD

VERSION = "1.0.7"

warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)


def format_timestamp(seconds: float, vtt=False) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}" if vtt else f"{h:02}:{m:02}:{s:02},{ms:03}"


def get_audio_metadata(file_path):
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,channels,sample_rate",
            "-of",
            "default=noprint_wrappers=1",
            file_path,
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return result.stdout
    except Exception as e:
        return f"[ERROR] FFprobe failed: {e}"


def estimate_duration(file_path):
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
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return float(result.stdout.strip())
    except (ValueError, AttributeError, subprocess.SubprocessError):
        return 0.0


def export_subtitles(segments, out_path, fmt="srt"):
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            if fmt in {"srt", "vtt"}:
                f.write(f"{i}\n")
                start = format_timestamp(seg["start"], vtt=(fmt == "vtt"))
                end = format_timestamp(seg["end"], vtt=(fmt == "vtt"))
                f.write(f"{start} --> {end}\n{seg['text'].strip()}\n\n")


def save_transcription_result(result, file_path, selected_format):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    today = datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
    out_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(out_dir, exist_ok=True)
    ext = selected_format if selected_format != "txt" else "txt"
    filename = f"{today}_{base_name}.{ext}"
    out_path = os.path.join(out_dir, filename)
    if selected_format == "txt":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    else:
        export_subtitles(result["segments"], out_path, fmt=selected_format)
    return out_path


def run_whisper_transcription(file_path, output_text=None, window=None, duration=None):
    print(f"[WHISPER] Using file: {file_path}", flush=True)
    print(f"[WHISPER] Exists: {os.path.exists(file_path)}", flush=True)
    if output_text:
        output_text.insert(tk.END, "\n\n📊 Στατιστικά αρχείου:\n", "info")
        output_text.insert(tk.END, get_audio_metadata(file_path), "info")
        window.update()
    model = whisper.load_model("medium")
    start_time = time.time()
    result = {}

    def progress_loop():
        while not result:
            elapsed = time.time() - start_time
            if duration:
                processed_ratio = min(elapsed / duration, 1)
                eta = timedelta(seconds=int((1 - processed_ratio) * duration))
                window.after(0, lambda: update_eta(f"⏳ Εκτίμηση λήξης: {str(eta)}\n"))
            time.sleep(1)

    def update_eta(text):
        output_text.insert(tk.END, text, "stats")
        output_text.see(tk.END)
        window.update()

    threading.Thread(target=progress_loop, daemon=True).start()
    result = model.transcribe(
        file_path,
        language="el",
        verbose=False,
        condition_on_previous_text=False,
        fp16=False,
    )

    if output_text:
        output_text.insert(tk.END, "\n🕓 Χρονικά τμήματα:\n", "info")
        for segment in result.get("segments", []):
            start = format_timestamp(segment["start"], vtt=False).replace(",", ":")
            end = format_timestamp(segment["end"], vtt=False).replace(",", ":")
            output_text.insert(
                tk.END, f"{start} -> {end} -> {segment['text'].strip()}\n"
            )
        output_text.insert(tk.END, "\n")

    return result


def remove_silence_ffmpeg(input_path):
    base_name = os.path.basename(input_path)
    name_wo_ext = os.path.splitext(base_name)[0]
    cleaned_path = os.path.join(tempfile.gettempdir(), f"{name_wo_ext}_cleaned.mp3")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-af",
        "silenceremove=1:0:-50dB",
        cleaned_path,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        return cleaned_path
    except subprocess.CalledProcessError as e:
        print(f"[FFMPEG] Error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        return input_path


def cleanup_ui(btn, pbar):
    btn.config(state=tk.NORMAL)
    pbar.stop()
    pbar.grid_remove()


def perform_transcription(file_path, output_text, window, pbar, btn):
    cleaned_path = None
    try:
        output_text.insert(tk.END, "🎧 Ανάλυση ήχου...")
        window.update()

        cleaned_path = remove_silence_ffmpeg(file_path)
        duration = estimate_duration(cleaned_path)
        output_text.insert(
            tk.END, f"\n⏱️ Εκτιμώμενη διάρκεια: {duration:.2f} sec\n", "stats"
        )
        result = run_whisper_transcription(cleaned_path, output_text, window, duration)
        selected_format = format_var.get()
        out_path = save_transcription_result(result, file_path, selected_format)

        output_text.insert(
            tk.END, f"\n✅ Ολοκληρώθηκε!\nΑρχείο: {out_path}\n\n", "done"
        )
        output_text.insert(tk.END, result["text"])
    except Exception as e:
        messagebox.showerror("Σφάλμα", f"Συνέβη σφάλμα:\n{str(e)}")
    finally:
        if cleaned_path and cleaned_path != file_path and os.path.exists(cleaned_path):
            os.remove(cleaned_path)
        cleanup_ui(btn, pbar)


def transcribe_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav *.mp3 *.m4a")]
    )
    if not file_path:
        return
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, f"🔄 GreekDrop {VERSION} ξεκινά...\n")
    window.update()
    transcribe_button.config(state=tk.DISABLED)
    progress_bar.grid(row=0, column=3, padx=10)
    progress_bar.start()
    threading.Thread(
        target=perform_transcription,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


def on_file_drop(event):
    file_path = window.tk.splitlist(event.data)[0].strip("{}")
    if not os.path.isfile(file_path):
        messagebox.showerror("Σφάλμα", "Το αρχείο δεν βρέθηκε.")
        return
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, f"🔄 GreekDrop {VERSION} ξεκινά...\n")
    window.update()
    transcribe_button.config(state=tk.DISABLED)
    progress_bar.grid(row=0, column=3, padx=10)
    progress_bar.start()
    threading.Thread(
        target=perform_transcription,
        args=(file_path, output_text, window, progress_bar, transcribe_button),
        daemon=True,
    ).start()


# GUI
window = TkinterDnD.Tk()
window.title(f"🎙️ GreekDrop {VERSION}")
window.geometry("750x570")
frame = tk.Frame(window)
frame.pack(pady=10)
transcribe_button = tk.Button(
    frame, text="📂 Επέλεξε αρχείο ήχου", command=transcribe_file, font=("Arial", 14)
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
label = tk.Label(frame, text="📄 Επιλογή εξόδου", font=("Arial", 11))
label.grid(row=0, column=2, padx=5)
progress_bar = ttk.Progressbar(frame, mode="indeterminate")
progress_bar.grid_remove()
output_text = tk.Text(window, wrap=tk.WORD, font=("Courier", 11))
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
output_text.tag_config("info", foreground="blue")
output_text.tag_config("stats", foreground="orange")
output_text.tag_config("done", foreground="green")
window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", on_file_drop)
window.mainloop()
