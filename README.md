# GreekDrop

GreekDrop is an open-source desktop application that converts Greek audio files to text and subtitles on your own computer.  It is based on the open-source Whisper speech-to-text model and does **all** processing locally – your recordings never leave your machine.

---

## Key Features

* Accurate transcription of Greek speech (Whisper medium model by default)
* Runs entirely offline – privacy by design
* GPU acceleration when a CUDA-compatible GPU is available
* Clean user interface: drag-and-drop or classic "Open file" dialogue
* Export formats: Plain text (`.txt`), SubRip (`.srt`), WebVTT (`.vtt`)
* Batch-friendly: the model is loaded once and reused for subsequent files
* Minimal mandatory dependencies (Python ≥ 3.9 and FFmpeg).  Optional packages enable AI and GPU features.

---

## Requirements

| Purpose             | Package / Tool                                | Mandatory |
| ------------------- | --------------------------------------------- | --------- |
| Core application    | Python ≥ 3.9                                 | ✔︎      |
| Audio processing    | FFmpeg                                        | ✔︎      |
| AI transcription    | `openai-whisper`, `torch`, `torchaudio` | optional  |
| Drag & drop support | `tkinterdnd2`                               | optional  |

> If the optional dependencies are missing GreekDrop will still start, but will fall back to the most basic transcription method that is available on the system.

---

## Installation

1. Clone or download this repository.
2. Install mandatory and (optionally) AI dependencies:

```bash
# mandatory
pip install ffmpeg-python

# add AI and GPU support (recommended)
pip install openai-whisper torch torchaudio

# optional drag & drop for the GUI
pip install tkinterdnd2
```

Make sure FFmpeg is on your system `PATH` (Windows users can place `ffmpeg.exe` next to `python.exe` or add the FFmpeg bin directory to the PATH environment variable).

---

## Quick Start

```bash
python optimized_main.py
```

1. Click **Select Audio File** (or drag a file on the window if drag-and-drop is enabled).
2. Choose an output format (TXT / SRT / VTT).
3. Press **Preload AI** once per session if you plan to transcribe many files – this avoids repeated model loading.
4. The transcription and export file are saved in the `transcriptions` folder.

---

## Command Line Use

GreekDrop is primarily a GUI tool.  If you need automated, headless processing you can import `optimized.py` in your own scripts or build a command-line wrapper, the transcription logic is contained in standalone functions.

---

## Building a Stand-alone Executable (Windows)

The repository contains a helper script that uses PyInstaller or Nuitka.

```bash
python build_executable.py
```

The resulting `.exe` can be distributed without requiring Python on the target system.

---

## Development

* Code style: Flake8 compliant (max line length 100).
* Virtual environments are recommended (e.g. `python -m venv .venv`).
* Tests and continuous integration are not yet configured – contributions welcome.

---

## License

MIT License – see the [LICENSE](LICENSE) file for details.

---

GreekDrop is maintained by volunteers.  Feedback, bug reports and pull requests are appreciated.
