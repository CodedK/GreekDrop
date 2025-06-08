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

VERSION = "1.0.8"

warnings.filterwarnings(
    "ignore", category=UserWarning, message="FP16 is not supported on CPU.*"
)


def format_timestamp(seconds: float, sep=":") -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}{sep}{m:02}{sep}{s:02}"


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
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def run_whisper_transcription(file_path, output_text=None, window=None, duration=None):
    print(f"[WHISPER] Using file: {file_path}", flush=True)
    print(f"[WHISPER] Exists: {os.path.exists(file_path)}", flush=True)

    if output_text:
        output_text.insert(tk.END, "\n\n📊 Στατιστικά αρχείου:\n", "info")
        output_text.insert(tk.END, get_audio_metadata(file_path), "info")
        window.update()

    model = whisper.load_model("medium")

    result = {"segments": [], "text": ""}

    start_global = time.time()
    prev_wall = start_global

    raw_result = model.transcribe(
        file_path,
        language="el",
        verbose=False,
        condition_on_previous_text=False,
        fp16=False,
    )

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    today = datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
    out_dir = os.path.join(os.getcwd(), "transcriptions")
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, f"{today}_{base_name}.log")

    if output_text:
        output_text.insert(tk.END, "\n🕓 Χρονικά τμήματα:\n", "info")

    with open(log_path, "w", encoding="utf-8") as log:
        for seg in raw_result["segments"]:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            now = time.time()
            wall_elapsed = now - prev_wall
            prev_wall = now
            audio_seconds = end - start

            start_fmt = format_timestamp(start)
            end_fmt = format_timestamp(end)

            line = (
                f"{start_fmt} -> {end_fmt} -> {text}  "
                f"[parsed {audio_seconds:.0f} secs of audio in {wall_elapsed:.0f} seconds]\n"
            )
            print(line.strip())
            log.write(line)
            if output_text:
                output_text.insert(tk.END, line)
                output_text.see(tk.END)
                window.update()

            result["segments"].append(seg)
            result["text"] += text + " "

    return result


def export_subtitles(segments, out_path, fmt="srt"):
    with open(out_path, "w", encoding="utf-8") as f:
        if fmt == "vtt":
            f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            if fmt in {"srt", "vtt"}:
                start = format_timestamp(seg["start"], sep=":" if fmt == "vtt" else ",")
                end = format_timestamp(seg["end"], sep=":" if fmt == "vtt" else ",")
                f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")


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
        output_text.insert(tk.END, "🎧 Ανάλυση ήχου...\n")
        window.update()
        cleaned_path = remove_silence_ffmpeg(file_path)
        duration = estimate_duration(cleaned_path)
        output_text.insert(
            tk.END, f"⏱️ Εκτιμώμενη διάρκεια: {duration:.2f} sec\n", "stats"
        )
        print(f"⏳ Εκτίμηση λήξης: {str(timedelta(seconds=round(duration)))}")
        result = run_whisper_transcription(cleaned_path, output_text, window, duration)
        selected_format = format_var.get()
        out_path = save_transcription_result(result, file_path, selected_format)
        output_text.insert(
            tk.END, f"\n✅ Ολοκληρώθηκε!\nΑρχείο: {out_path}\n\n", "done"
        )
        print("\n▶️ Πάτησε Enter για έξοδο...")
        input()
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
