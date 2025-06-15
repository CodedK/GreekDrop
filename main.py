#!/usr/bin/env python3
"""
GreekDrop - Greek Audio Transcription System
Professional audio transcription with AI-powered speech recognition.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import APP_NAME, VERSION, DEBUG_MODE, check_dependencies
from utils.logger import init_logger, get_logger
from utils.hardware import print_hardware_diagnostics
from ui.layout import create_and_run_ui


def print_header():
    """Print professional application header."""
    print(f"{APP_NAME} v{VERSION} - Audio Transcription System")
    print("=" * 50)


def print_dependencies_summary(deps: dict):
    """Print clean dependencies summary."""
    logger = get_logger()

    print(f"[{APP_NAME}] System Dependencies")
    print("─" * 30)

    dep_status = {
        "Modern UI": deps.get("modern_ui", False),
        "Drag & Drop": deps.get("drag_drop", False),
        "Whisper AI": deps.get("whisper", False),
        "PyTorch": deps.get("torch", False),
        "Audio Processing": deps.get("audio_processing", False),
    }

    for name, available in dep_status.items():
        status = "AVAILABLE" if available else "MISSING"
        print(f"- {name:<15} {status}")

        if not available:
            logger.warning(f"Dependency missing: {name}")

    print()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Greek Audio Transcription System"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with detailed logging"
    )

    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Force CPU mode (disable GPU acceleration)",
    )

    parser.add_argument(
        "--force-gpu",
        action="store_true",
        help="Force GPU mode (require GPU acceleration)",
    )

    parser.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")

    return parser.parse_args()


def validate_environment():
    """Validate the runtime environment."""
    logger = get_logger()

    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(
            f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}"
        )
        return False

    # Check dependencies
    deps = check_dependencies()

    # Check critical dependencies
    critical_deps = ["modern_ui", "whisper", "torch"]
    missing_critical = [dep for dep in critical_deps if not deps.get(dep, False)]

    if missing_critical:
        logger.error(f"Critical dependencies missing: {', '.join(missing_critical)}")
        print("\nCRITICAL ERROR: Missing required dependencies")
        print("Please install required packages:")
        print("  pip install ttkbootstrap openai-whisper torch")
        return False

    return True


def setup_environment_variables(args):
    """Setup environment variables based on command line arguments."""
    import os

    if args.debug:
        os.environ["GREEKDROP_DEBUG"] = "true"

    if args.force_cpu:
        os.environ["GREEKDROP_FORCE_CPU"] = "true"
        print("🔧 CPU mode forced via command line")

    if args.force_gpu:
        os.environ["GREEKDROP_FORCE_GPU"] = "true"
        print("🔧 GPU mode forced via command line")


def main():
    """Main application entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Setup environment
        setup_environment_variables(args)

        # Initialize logging
        logger = init_logger(args.debug or DEBUG_MODE)

        # Print header
        print_header()

        # Validate environment
        if not validate_environment():
            sys.exit(1)

        # Check dependencies
        logger.info("Checking system dependencies...")
        deps = check_dependencies()
        print_dependencies_summary(deps)

        # Hardware diagnostics
        logger.info("Analyzing hardware configuration...")
        print_hardware_diagnostics()

        # Log startup info
        logger.info(f"Starting {APP_NAME} {VERSION}")
        logger.info(f"Debug mode: {args.debug or DEBUG_MODE}")
        logger.info(f"Compute device: {deps.get('compute_device', 'CPU')}")

        if deps.get("forced_mode"):
            logger.info(f"Hardware mode forced: {deps.get('forced_mode')}")

        # Initialize and run UI
        logger.info("Launching user interface...")
        print(f"[{APP_NAME}] Launching application...")
        print()

        create_and_run_ui()

        logger.info("Application shutdown complete")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print(f"\n[{APP_NAME}] Application interrupted")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Application startup failed: {str(e)}", exc_info=True)
        print(f"\nCRITICAL ERROR: {str(e)}")

        if args.debug or DEBUG_MODE:
            import traceback

            print("\nFull traceback:")
            traceback.print_exc()
        else:
            print("Use --debug for detailed error information")

        sys.exit(1)


if __name__ == "__main__":
    main()
