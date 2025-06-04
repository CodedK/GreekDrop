import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import whisper


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


def perform_transcription(file_path, output_text, window):
    """Perform the actual transcription and file writing."""
    model = whisper.load_model("medium")
    output_text.insert(tk.END, "🎧 Ανάλυση ήχου...\n")
    window.update()

    result = model.transcribe(file_path, language="el")
    base_path = os.path.splitext(file_path)[0]
    selected_format = format_var.get()

    if selected_format == "txt":
        out_path = f"{base_path}_transcript.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    else:
        out_path = f"{base_path}_subtitles.{selected_format}"
        export_subtitles(result["segments"], out_path, fmt=selected_format)

    output_text.insert(tk.END, f"✅ Ολοκληρώθηκε!\nΑρχείο: {out_path}\n\n")
    output_text.insert(tk.END, result["text"])


def transcribe_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.wav *.mp3 *.m4a")]
    )
    if not file_path:
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "⏳ Φόρτωση μοντέλου...\n")
    window.update()

    try:
        perform_transcription(file_path, output_text, window)
    except Exception as e:
        messagebox.showerror("Σφάλμα", f"Κάτι πήγε στραβά:\n{str(e)}")


# === GUI Setup ===
window = tk.Tk()
window.title("🎙️ Whisper Greek Transcriber")
window.geometry("750x550")

frame = tk.Frame(window)
frame.pack(pady=10)

btn = tk.Button(
    frame, text="📂 Επέλεξε αρχείο ήχου", command=transcribe_file, font=("Arial", 14)
)
btn.grid(row=0, column=0, padx=10)

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

output_text = tk.Text(window, wrap=tk.WORD, font=("Courier", 11))
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

window.mainloop()
