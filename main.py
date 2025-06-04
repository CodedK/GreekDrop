import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import whisper

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
            f.write("WEBVTT\\n\\n")
        for i, seg in enumerate(segments, 1):
            if fmt in {"srt", "vtt"}:
                f.write(f"{i}\\n")
                start = format_timestamp(seg["start"], vtt=(fmt == "vtt"))
                end = format_timestamp(seg["end"], vtt=(fmt == "vtt"))
                sep = " --> "
                f.write(f"{start}{sep}{end}\\n")
                f.write(f"{seg['text'].strip()}\\n\\n")


def save_transcription_result(result, file_path, selected_format):
    """Save transcription result to file in the specified format."""
    base_path = os.path.splitext(file_path)[0]

    if selected_format == "txt":
        out_path = f"{base_path}_transcript.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    else:
        out_path = f"{base_path}_subtitles.{selected_format}"
        export_subtitles(result["segments"], out_path, fmt=selected_format)

    return out_path


def run_whisper_transcription(file_path):
    """Load Whisper model and perform transcription."""
    model = whisper.load_model("medium")
    return model.transcribe(file_path, language="el")


def cleanup_ui(btn, progress_bar):
    """Reset UI elements after transcription completion."""
    btn.config(state=tk.NORMAL)
    progress_bar.stop()
    progress_bar.grid_remove()


def perform_transcription(file_path, output_text, window, progress_bar, btn):
    try:
        output_text.insert(tk.END, "🎧 Ανάλυση ήχου...\n")
        window.update()

        result = run_whisper_transcription(file_path)
        selected_format = format_var.get()
        out_path = save_transcription_result(result, file_path, selected_format)

        output_text.insert(tk.END, f"✅ Ολοκληρώθηκε!\\nΑρχείο: {out_path}\\n\\n")
        output_text.insert(tk.END, result["text"])
    except (OSError, RuntimeError, ValueError) as e:
        messagebox.showerror("Σφάλμα", f"Συνέβη σφάλμα:\\n{str(e)}")
    finally:
        cleanup_ui(btn, progress_bar)


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


# === GUI Setup ===
window = tk.Tk()
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

window.mainloop()
