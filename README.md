# 🎧 GreekDrop

**GreekDrop** is a no-fluff, street-smart audio-to-text tool built for the Greek language.  
Drop your audio. Get your lines. Fast.

Powered by OpenAI's Whisper, wrapped in a clean GUI — no terminal, no drama.

---

## 🧠 What It Does

- 🎙️ Transcribes Greek audio to:
  - 📝 `.txt` (pure transcript)
  - 🎬 `.srt` (subtitles for editing)
  - 🌐 `.vtt` (captions for the web)
- 🖱️ Click-based GUI (no CLI)
- 🎧 Supports `.wav`, `.mp3`, `.m4a`
- 🧠 Whisper `medium` model (with GPU support if available)
- Built for makers, editors, journalists, rappers, teachers, students — **anyone who drops Greek audio and needs text back**.

---

## 🚦 Requirements

- Python 3.10+
- `ffmpeg` installed and in PATH
- `pip install openai-whisper torch`

---

## 🪜 Install on Windows

1. **Install Python** → [https://python.org](https://python.org)
   - ✅ Enable “Add Python to PATH”

2. **Install ffmpeg**:
   - Download: [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
   - Unzip to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to Windows PATH

3. **Install dependencies**:
```bash
pip install openai-whisper
pip install torch
