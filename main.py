#!/usr/bin/env python3
"""
GreekDrop Audio Transcription Application
Modern, modular Python application for transcribing Greek audio files.

Entry Point: Clean main launcher that initializes the modular application.
"""

from config.settings import check_dependencies
from ui.layout import GreekDropUI


def main():
    """Main application entry point."""
    print("🚀 Starting GreekDrop Audio Transcription App...")

    # Initialize dependencies
    print("📋 Checking dependencies...")
    deps = check_dependencies()

    # Create and initialize the UI
    print("🎨 Initializing modern UI...")
    app = GreekDropUI()
    window = app.initialize_application()

    # Show startup status
    print("✅ Application initialized successfully!")
    print(f"   Modern UI: {'✅' if deps['modern_ui'] else '❌'}")
    print(f"   AI Ready: {'✅' if deps['whisper'] else '❌'}")
    print(f"   Drag & Drop: {'✅' if deps['drag_drop'] else '❌'}")

    # Start the application
    print("🏃 Starting main event loop...")
    try:
        window.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        print("🛑 Application terminated")


if __name__ == "__main__":
    main()
