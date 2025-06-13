# 🎯 GreekDrop Audio Transcription

A modern, modular Python application for transcribing Greek audio files using AI-powered speech recognition.

## ✨ Features

- **🧠 AI-Powered Transcription**: OpenAI Whisper for high-quality Greek speech recognition
- **🎨 Modern UI**: Material Design-inspired interface with ttkbootstrap
- **📁 Drag & Drop**: Intuitive file handling with visual feedback
- **⚡ GPU Acceleration**: CUDA support for faster processing
- **📝 Multiple Export Formats**: TXT, SRT, VTT subtitle formats
- **🔄 Fallback Support**: Graceful degradation when dependencies are missing
- **🏗️ Modular Architecture**: Clean, maintainable codebase

## 🏗️ Architecture

GreekDrop follows a clean, modular architecture for maintainability and extensibility:

```
greekdrop/
├── main.py              # 🚀 Application entry point
├── config/              # ⚙️ Configuration and settings
│   ├── __init__.py
│   └── settings.py      # Dependencies, constants, global state
├── ui/                  # 🎨 User interface components
│   ├── __init__.py
│   └── layout.py        # Modern Material Design UI
├── logic/               # 🧠 Core transcription logic
│   ├── __init__.py
│   ├── transcriber.py   # AI transcription engine
│   └── preload.py       # Async model loading
├── utils/               # 🔧 File handling and utilities
│   ├── __init__.py
│   └── file_utils.py    # Audio processing, file I/O
└── requirements.txt     # 📦 Dependencies
```

### Module Responsibilities

- **`main.py`**: Clean entry point that initializes the application
- **`config/`**: Settings, constants, dependency management
- **`ui/`**: Modern interface with responsive Material Design
- **`logic/`**: AI transcription engine with Whisper and fallbacks
- **`utils/`**: File processing, audio conversion, export utilities

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with tkinter (usually included)
2. **FFmpeg** installed on your system:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd GreekDrop
   ```

2. **Install dependencies**:
   ```bash
   # Full installation (recommended)
   pip install -r requirements.txt

   # Or minimal installation (no AI features)
   pip install ttkbootstrap tkinterdnd2 SpeechRecognition ffmpeg-python
   ```

3. **For GPU acceleration** (optional):
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## 📦 Dependencies

| Category | Package | Purpose | Required |
|----------|---------|---------|----------|
| **UI** | `ttkbootstrap` | Modern Material Design interface | Recommended |
| **UI** | `tkinterdnd2` | Drag & drop functionality | Recommended |
| **AI** | `openai-whisper` | High-quality AI transcription | Optional |
| **AI** | `torch` + `torchaudio` | GPU acceleration | Optional |
| **Fallback** | `SpeechRecognition` | Backup transcription method | Recommended |
| **Audio** | `ffmpeg-python` | Audio processing | Required |

### Dependency Tiers

- **🎯 Core**: Works with just Python + FFmpeg
- **🎨 Enhanced**: + ttkbootstrap + tkinterdnd2 for modern UI
- **🧠 AI-Powered**: + openai-whisper for best transcription
- **⚡ GPU-Accelerated**: + torch + torchaudio for speed

## 🎮 Usage

### Basic Operation

1. **Launch** the application: `python main.py`
2. **Select** audio file via button or drag & drop
3. **Choose** export format (TXT, SRT, VTT)
4. **Click** transcribe and wait for results
5. **Find** output file saved next to original audio

### Supported Formats

- **Input**: WAV, MP3, M4A, FLAC, OGG, AAC, MP4, AVI, MOV
- **Output**:
  - **TXT**: Full text with metadata and timestamps
  - **SRT**: Standard subtitle format
  - **VTT**: WebVTT subtitle format

### Performance Tips

- **Preload AI** model for faster subsequent transcriptions
- **Use GPU** acceleration for 3-5x speed improvement
- **Convert to WAV** for best compatibility
- **16kHz mono** audio works best with the AI model

## 🔧 Development

### Code Style

The codebase follows professional Python standards:

- **PEP 8** compliant formatting
- **Type hints** where applicable
- **Docstrings** for all public functions
- **Modular design** with clear separation of concerns
- **Error handling** with graceful degradation

### Adding Features

1. **UI changes**: Modify `ui/layout.py`
2. **Transcription logic**: Update `logic/transcriber.py`
3. **File handling**: Enhance `utils/file_utils.py`
4. **Configuration**: Adjust `config/settings.py`

### Testing

```bash
# Run the application
python main.py

# Test specific modules (when test suite is added)
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the code style
4. Test thoroughly with different audio files
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg and ensure it's in your system PATH

**"No module named 'ttkbootstrap'"**
- Install with: `pip install ttkbootstrap`

**"Whisper model download fails"**
- Check internet connection and disk space
- Models are downloaded to `~/.cache/whisper/`

**"CUDA out of memory"**
- Use CPU mode or reduce audio file length
- Close other GPU-intensive applications

### Performance Issues

- **Slow transcription**: Install GPU acceleration or use smaller audio files
- **High memory usage**: Enable garbage collection in settings
- **UI freezing**: Ensure background processing is working correctly

---

**Built with ❤️ for Greek language transcription**
