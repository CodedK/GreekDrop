
# 🎧 GreekDrop


**GreekDrop** is a no-fluff, smart audio-to-text tool built for the Greek language.
Drop your audio. Get your lines. Fast.

Powered by OpenAI's Whisper, wrapped in a clean GUI, no terminal, no drama.

---

## 🧠 What It Does

* 🎹 Transcribes Greek audio to:
  * 📝 `<span>.txt</span>` (pure transcript)
  * 🎬 `<span>.srt</span>` (subtitles for editing)
  * 🌐 `<span>.vtt</span>` (captions for the web)
* 👟 Click-based GUI (no CLI)
* 🎷 Supports `<span>.wav</span>`, `<span>.mp3</span>`, `<span>.m4a</span>`
* 🧠 Whisper `<span>medium</span>` model (GPU support if available)
* For makers, editors, journalists, rappers, teachers, students — **anyone who drops Greek audio and needs text back**.

---

## 🚦 Requirements

* Python 3.10+
* FFmpeg installed and added to PATH
* Python packages:
  ```
  pip install openai-whisper torch
  ```

---

## 🧃 Install on Windows (Quick Guide)

### 1. Install Python

* Download from [python.org](https://www.python.org/)
* ✅ On installer: check **"Add Python to PATH"**

### 2. Install FFmpeg

* Download: [ffmpeg-release-essentials.zip]()
* Extract to: `<span>C:\ffmpeg</span>`
* Add to PATH:

  * Press `<span>Win + S</span>`, search: *"Environment Variables"
  * Edit system variable `<span>Path</span>`
  * Add new: `<span>C:\ffmpeg\bin</span>`
  * OK → OK → Done
* Test: Open PowerShell and run:

  ```
  ffmpeg -version
  ```

  You should see the version info.

### 3. Install Python Packages

```
pip install openai-whisper torch
```

---

## 🚀 Run It

```
python main.py
```

* Or double-click `<span>main.py</span>` to launch the GUI.
* Drag-and-drop `<span>.mp3</span>`, `<span>.wav</span>`, `<span>.m4a</span>` to transcribe.

---

## 🔧 For Devs

* GUI built with `<span>tkinter</span>`
* Drag-and-drop via `<span>tkinterdnd2</span>`
* Whisper `<span>medium</span>` model is loaded on each transcription

---

## 📃 License

MIT

---

🚀 From Greece with ❤️
