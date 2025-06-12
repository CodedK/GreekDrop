<p align="center">
  <img src="logo.png" alt="GreekDrop Logo" width="180"/>
</p>

<h1 align="center">GreekDrop</h1>
<p align="center">
  <b>Transcribe Greek audio to text with blazing speed and simplicity.</b><br>
  <i>AI-powered. Open source. No cloud required.</i>
</p>

---

## 🚀 What is GreekDrop?

**GreekDrop** is a modern, open-source desktop app for transcribing Greek audio files into text and subtitles. Powered by state-of-the-art AI (OpenAI Whisper), it's designed for speed, privacy, and ease of use—no internet connection or cloud upload required.

- **Drag & drop** your audio file, or select it with a click.
- **Get instant, accurate transcriptions** in Greek.
- **Export** as plain text, SRT, or VTT subtitles.
- **Runs locally** on your PC—your audio never leaves your machine.

---

## 🏆 Why You'll Love It

- **Lightning Fast**: Optimized for both CPU and GPU. Model loads once, so batch jobs fly.
- **Privacy First**: All processing is local. No data leaves your computer.
- **No Hassle**: No accounts, no subscriptions, no cloud. Just run and transcribe.
- **Beautifully Simple**: Minimal, intuitive interface. Drag, drop, done.
- **Open Source**: Hack it, improve it, or use it as you wish.

---

## ✨ Features

- 🎙️ **Greek Language AI**: Best-in-class transcription for Greek audio.
- 🖥️ **GPU Acceleration**: Up to 12x real-time speed on modern NVIDIA GPUs.
- 📁 **Multi-format Export**: TXT, SRT, and VTT subtitle support.
- 🧠 **Smart Preprocessing**: Automatic silence removal and audio cleanup.
- 🔄 **Batch Ready**: Model loads once for many files—perfect for heavy workloads.
- 🛠️ **Minimal Dependencies**: Works with just Python and FFmpeg. AI features auto-disable if missing.

---

## 🖼️ Screenshot

<p align="center">
  <img src="screenshot.png" alt="GreekDrop Screenshot" width="600"/>
</p>

---

## ⚡ Quick Start

1. **Install Python 3.9+** and [FFmpeg](https://ffmpeg.org/download.html).
2. **Install dependencies:**
   ```bash
   pip install -r requirements_optimized.txt
   ```
3. **Run the app:**
   ```bash
   python optimized_main.py
   ```
4. *(Optional)* For GPU acceleration:
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

---

## 🖱️ Usage

- **Drag & drop** your audio file onto the app, or click "Select Audio File."
- Choose your **output format** (TXT, SRT, VTT).
- Click **Preload AI** for instant processing (loads the model once).
- Your transcription appears in seconds. Export and enjoy!

---

## 🧩 Advanced

- **Build a standalone .exe:**
  Run:
  ```bash
  python build_executable.py
  ```
  Distribute the resulting file—no Python required!

- **Minimal mode:**
  If AI dependencies are missing, GreekDrop falls back to basic transcription (if possible).

---

## 🛡️ Privacy & Security

- **All processing is local.**
  Your audio and transcriptions never leave your device.

---

## 💡 Interesting Facts

- GreekDrop uses the same AI model as OpenAI's Whisper, but runs entirely on your hardware.
- With a modern GPU, you can transcribe an hour of audio in just a few minutes.
- The app is designed to degrade gracefully: if you're missing AI libraries, it still works for basic needs.
- The logo combines a drop (for "drop your file") and a waveform (for audio)—simple, memorable, and meaningful.

---

## 🤝 Contributing

Pull requests, feature ideas, and bug reports are welcome!
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

MIT License.
See [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>GreekDrop – Fast, private, and open Greek audio transcription for everyone.</i>
</p>

---

**Tip:**
If you like GreekDrop, star the repo and share it with your friends!
