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
from tkinter import filedialog, messagebox, ttk

import whisper
from tkinterdnd2 import DND_FILES, TkinterDnD

VERSION = "1.0.0"


def format_timestamp(seconds: float, vtt=False) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    if vtt:
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
    else:
        return f"{h:02}:{m:02}:{s:02},{ms:03}"


def export_subtitles(segments, out_path, fmt="srt"):
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            if fmt in {"srt", "vtt"}:
                f.write(f"{i}\n")
                start = format_timestamp(seg["start"], vtt=(fmt == "vtt"))
                end = format_timestamp(seg["end"], vtt=(fmt == "vtt"))
                sep = " --> "
                f.write(f"{start}{sep}{end}\n")
                f.write(f"{seg['text'].strip()}\n\n")


def save_transcription_result(result, file_path, selected_format):
    """Save transcription result to file in the specified format."""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    date_str = time.strftime("%Y.%m.%d")
    output_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, f"{date_str}_{base_name}.{selected_format}")

    if selected_format == "txt":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    else:
        export_subtitles(result["segments"], out_path, fmt=selected_format)

    return out_path


...
# All other content remains the same as previously uploaded


def run_whisper_transcription(file_path, output_text=None, window=None):
    print(f"[WHISPER] Using file: {file_path}", flush=True)
    print(f"[WHISPER] Exists: {os.path.exists(file_path)}", flush=True)

    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except Exception as e:
        print("[ERROR] FFmpeg check failed:", e)
        raise RuntimeError(
            "Το FFmpeg δεν είναι εγκατεστημένο ή δεν υπάρχει στο PATH"
        ) from e

    if output_text and window:
        output_text.insert(tk.END, "⏳ Το Whisper επεξεργάζεται το αρχείο...\n")
        output_text.see(tk.END)
        window.update()

    print("[DEBUG] Starting model load...", flush=True)
    start = time.time()
    model = whisper.load_model("medium")
    print(f"[DEBUG] Model loaded in {time.time() - start:.2f} sec", flush=True)

    return model.transcribe(file_path, language="el", verbose=True)


def remove_silence_ffmpeg(input_path):
    """Removes silence from an audio file using FFmpeg and returns the cleaned temp path."""
    base_name = os.path.basename(input_path)
    name_wo_ext = os.path.splitext(base_name)[0]
    cleaned_path = os.path.join(tempfile.gettempdir(), f"{name_wo_ext}_cleaned.mp3")

    command = [
        "ffmpeg",
        "-y",  # overwrite
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
        stderr_msg = e.stderr.decode() if e.stderr else "Unknown error"
        print(f"[FFMPEG] Failed to clean silence: {stderr_msg}")
        return input_path


def cleanup_ui(btn, pbar):
    """Reset UI elements after transcription completion."""
    btn.config(state=tk.NORMAL)
    pbar.stop()
    pbar.grid_remove()


def perform_transcription(file_path, output_text, window, pbar, btn):
    cleaned_path = None
    try:
        output_text.insert(tk.END, "🎧 Ανάλυση ήχου...\n")
        window.update()

        cleaned_path = remove_silence_ffmpeg(file_path)
        result = run_whisper_transcription(cleaned_path, output_text, window)
        selected_format = format_var.get()
        out_path = save_transcription_result(result, file_path, selected_format)

        output_text.insert(tk.END, f"✅ Ολοκληρώθηκε!\nΑρχείο: {out_path}\n\n")
        output_text.insert(tk.END, result["text"])
    except (OSError, RuntimeError, ValueError) as e:
        messagebox.showerror("Σφάλμα", f"Συνέβη σφάλμα:\n{str(e)}")
    finally:
        # Clean up temporary file
        if cleaned_path and cleaned_path != file_path and os.path.exists(cleaned_path):
            try:
                os.remove(cleaned_path)
                print(f"[CLEANUP] Removed temp file: {cleaned_path}")
            except OSError as e:
                print(f"[CLEANUP] Failed to remove temp file: {e}")
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
    dropped_data = event.data.strip()
    print(f"[DROP] Got: {event.data}")  # Προσωρινά για έλεγχο
    files = window.tk.splitlist(dropped_data)  # allows multiple files
    if not files:
        messagebox.showerror("Σφάλμα", "Δεν εντοπίστηκε έγκυρο αρχείο.")
        return

    file_path = files[0].strip("{}")
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


# === GUI Setup ===
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

# Enable drag and drop
window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", on_file_drop)

window.mainloop()
