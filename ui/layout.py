"""
Enhanced Material Design UI for GreekDrop using ttkbootstrap.
Features drag-drop, dynamic hardware status, toast notifications, and clean design.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from pathlib import Path
from typing import Optional, List, Callable

# Try importing ttkbootstrap first
try:
    import ttkbootstrap as ttk_bs
    from ttkbootstrap.constants import *

    MODERN_UI_AVAILABLE = True
except ImportError:
    MODERN_UI_AVAILABLE = False

# Try importing drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False

from config.settings import (
    APP_NAME,
    VERSION,
    WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    EXPORT_FORMATS,
    DEFAULT_THEME,
    DEBUG_MODE,
    check_dependencies,
)
from utils.logger import get_logger, init_logger
from utils.file_utils import (
    validate_audio_file,
    normalize_file_path,
    save_transcription_to_file,
    extract_basic_audio_metadata,
    get_output_directory,
)
from logic.transcriber import get_transcription_engine, preload_default_model


class ToastNotification:
    """Simple toast notification system."""

    def __init__(self, parent):
        self.parent = parent
        self.toast_window = None

    def show(self, message: str, duration: int = 3000, toast_type: str = "info"):
        """Show a toast notification."""
        if self.toast_window:
            try:
                self.toast_window.destroy()
            except:
                pass

        # Create toast window
        self.toast_window = tk.Toplevel(self.parent)
        self.toast_window.withdraw()  # Hide initially

        # Configure window
        self.toast_window.title("")
        self.toast_window.overrideredirect(True)  # No window decorations

        # Colors based on type
        colors = {
            "info": ("#2196F3", "white"),
            "success": ("#4CAF50", "white"),
            "warning": ("#FF9800", "white"),
            "error": ("#F44336", "white"),
        }
        bg_color, fg_color = colors.get(toast_type, colors["info"])

        # Create frame and label
        frame = tk.Frame(self.toast_window, bg=bg_color, padx=20, pady=10)
        frame.pack()

        label = tk.Label(
            frame, text=message, bg=bg_color, fg=fg_color, font=("Segoe UI", 10)
        )
        label.pack()

        # Position toast at bottom-right of parent
        self.toast_window.update_idletasks()
        width = self.toast_window.winfo_reqwidth()
        height = self.toast_window.winfo_reqheight()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + parent_width - width - 20
        y = parent_y + parent_height - height - 50

        self.toast_window.geometry(f"{width}x{height}+{x}+{y}")
        self.toast_window.deiconify()

        # Auto-close after duration
        self.parent.after(duration, self._close_toast)

    def _close_toast(self):
        """Close the toast notification."""
        if self.toast_window:
            try:
                self.toast_window.destroy()
            except:
                pass
            self.toast_window = None


class GreekDropUI:
    """
    Enhanced GreekDrop UI with Material Design, proper error handling,
    and comprehensive functionality.
    """

    def __init__(self):
        self.logger = init_logger(DEBUG_MODE)
        self.logger.info(f"Initializing {APP_NAME} {VERSION} UI")

        # Initialize core components
        self.transcription_engine = get_transcription_engine()
        self.dependencies = check_dependencies()

        # UI state
        self.current_audio_file = None
        self.transcription_in_progress = False

        # Initialize UI
        self._setup_window()
        self._create_ui_components()
        self._setup_drag_drop()
        self._update_hardware_status()

        self.logger.info("UI initialization complete")

    def _setup_window(self):
        """Initialize the main window with proper styling."""
        if MODERN_UI_AVAILABLE:
            self.window = ttk_bs.Window(
                title=f"{APP_NAME} {VERSION}",
                themename=DEFAULT_THEME,
                size=WINDOW_SIZE.split("x"),
                minsize=MIN_WINDOW_SIZE,
            )
        else:
            # Fallback to standard tkinter
            self.window = TkinterDnD.Tk() if DRAG_DROP_AVAILABLE else tk.Tk()
            self.window.title(f"{APP_NAME} {VERSION}")
            self.window.geometry(WINDOW_SIZE)
            self.window.minsize(*MIN_WINDOW_SIZE)

        # Center window on screen
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Configure window
        self.window.configure(bg="#f0f2f5" if not MODERN_UI_AVAILABLE else None)

        # Initialize toast system
        self.toast = ToastNotification(self.window)

    def _create_ui_components(self):
        """Create all UI components with Material Design styling."""
        # Main container with padding
        if MODERN_UI_AVAILABLE:
            main_frame = ttk_bs.Frame(self.window, padding=30)
        else:
            main_frame = tk.Frame(self.window, bg="#f0f2f5", padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title section
        self._create_title_section(main_frame)

        # File selection section
        self._create_file_section(main_frame)

        # Settings section
        self._create_settings_section(main_frame)

        # Action buttons section
        self._create_action_section(main_frame)

        # Status section
        self._create_status_section(main_frame)

        # Output section
        self._create_output_section(main_frame)

    def _create_title_section(self, parent):
        """Create the title section."""
        if MODERN_UI_AVAILABLE:
            title_frame = ttk_bs.Frame(parent)
            title_label = ttk_bs.Label(
                title_frame,
                text=f"{APP_NAME} {VERSION}",
                font=("Segoe UI", 24, "bold"),
                bootstyle="primary",  # Blue color
            )
        else:
            title_frame = tk.Frame(parent, bg="#f0f2f5")
            title_label = tk.Label(
                title_frame,
                text=f"{APP_NAME} {VERSION}",
                font=("Segoe UI", 24, "bold"),
                fg="#1976d2",
                bg="#f0f2f5",
            )

        title_frame.pack(fill=tk.X, pady=(0, 20))
        title_label.pack()

    def _create_file_section(self, parent):
        """Create the file selection section."""
        if MODERN_UI_AVAILABLE:
            file_frame = ttk_bs.LabelFrame(
                parent, text="Audio File Selection", padding=20, bootstyle="primary"
            )
        else:
            file_frame = tk.LabelFrame(
                parent,
                text="Audio File Selection",
                font=("Segoe UI", 10, "bold"),
                fg="#1976d2",
                bg="#ffffff",
                padx=20,
                pady=20,
            )

        file_frame.pack(fill=tk.X, pady=(0, 15))

        # File selection button
        if MODERN_UI_AVAILABLE:
            select_btn = ttk_bs.Button(
                file_frame,
                text="📁 Select Audio File",
                command=self._select_audio_file,
                bootstyle="primary-outline",
                width=20,
            )
        else:
            select_btn = tk.Button(
                file_frame,
                text="📁 Select Audio File",
                command=self._select_audio_file,
                font=("Segoe UI", 10),
                bg="#2196F3",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                pady=8,
            )

        select_btn.pack(side=tk.LEFT, padx=(0, 15))

        # File info label
        if MODERN_UI_AVAILABLE:
            self.file_info_label = ttk_bs.Label(
                file_frame,
                text="No file selected",
                font=("Segoe UI", 9),
                bootstyle="secondary",
            )
        else:
            self.file_info_label = tk.Label(
                file_frame,
                text="No file selected",
                font=("Segoe UI", 9),
                fg="#666666",
                bg="#ffffff",
            )

        self.file_info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Drag & drop instructions
        if DRAG_DROP_AVAILABLE:
            drop_text = "💡 You can also drag & drop audio files here"
        else:
            drop_text = "💡 Drag & drop not available - use Select button"

        if MODERN_UI_AVAILABLE:
            drop_label = ttk_bs.Label(
                file_frame, text=drop_text, font=("Segoe UI", 8), bootstyle="info"
            )
        else:
            drop_label = tk.Label(
                file_frame,
                text=drop_text,
                font=("Segoe UI", 8),
                fg="#666666",
                bg="#ffffff",
            )

        drop_label.pack(fill=tk.X, pady=(10, 0))

    def _create_settings_section(self, parent):
        """Create the settings section."""
        if MODERN_UI_AVAILABLE:
            settings_frame = ttk_bs.LabelFrame(
                parent, text="Export Settings", padding=20, bootstyle="secondary"
            )
        else:
            settings_frame = tk.LabelFrame(
                parent,
                text="Export Settings",
                font=("Segoe UI", 10, "bold"),
                fg="#666666",
                bg="#ffffff",
                padx=20,
                pady=20,
            )

        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # Export format selection
        format_label_frame = tk.Frame(
            settings_frame, bg="#ffffff" if not MODERN_UI_AVAILABLE else None
        )
        format_label_frame.pack(fill=tk.X)

        if MODERN_UI_AVAILABLE:
            format_label = ttk_bs.Label(
                format_label_frame, text="Export Format:", font=("Segoe UI", 10)
            )
        else:
            format_label = tk.Label(
                format_label_frame,
                text="Export Format:",
                font=("Segoe UI", 10),
                bg="#ffffff",
            )

        format_label.pack(side=tk.LEFT)

        # Format dropdown
        self.format_var = tk.StringVar(value="All")

        if MODERN_UI_AVAILABLE:
            format_combo = ttk_bs.Combobox(
                format_label_frame,
                textvariable=self.format_var,
                values=EXPORT_FORMATS,
                state="readonly",
                width=15,
                bootstyle="primary",
            )
        else:
            format_combo = ttk.Combobox(
                format_label_frame,
                textvariable=self.format_var,
                values=EXPORT_FORMATS,
                state="readonly",
                width=15,
            )

        format_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Output directory info
        output_info = f"💾 Files saved to: {get_output_directory()}"

        if MODERN_UI_AVAILABLE:
            output_label = ttk_bs.Label(
                settings_frame, text=output_info, font=("Segoe UI", 8), bootstyle="info"
            )
        else:
            output_label = tk.Label(
                settings_frame,
                text=output_info,
                font=("Segoe UI", 8),
                fg="#666666",
                bg="#ffffff",
            )

        output_label.pack(fill=tk.X, pady=(10, 0))

    def _create_action_section(self, parent):
        """Create the action buttons section."""
        if MODERN_UI_AVAILABLE:
            action_frame = ttk_bs.Frame(parent)
        else:
            action_frame = tk.Frame(parent, bg="#f0f2f5")

        action_frame.pack(fill=tk.X, pady=(0, 15))

        # Preload model button
        if MODERN_UI_AVAILABLE:
            self.preload_btn = ttk_bs.Button(
                action_frame,
                text="🧠 Preload AI Model",
                command=self._preload_model,
                bootstyle="warning-outline",
                width=18,
            )
        else:
            self.preload_btn = tk.Button(
                action_frame,
                text="🧠 Preload AI Model",
                command=self._preload_model,
                font=("Segoe UI", 10),
                bg="#FF9800",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                pady=8,
            )

        self.preload_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Model info button
        if MODERN_UI_AVAILABLE:
            info_btn = ttk_bs.Button(
                action_frame,
                text="ℹ️ Info",
                command=self._show_info,
                bootstyle="info-outline",
                width=8,
            )
        else:
            info_btn = tk.Button(
                action_frame,
                text="ℹ️ Info",
                command=self._show_info,
                font=("Segoe UI", 10),
                bg="#2196F3",
                fg="white",
                relief=tk.FLAT,
                padx=15,
                pady=8,
            )

        info_btn.pack(side=tk.LEFT, padx=(0, 20))

        # Main transcribe button
        if MODERN_UI_AVAILABLE:
            self.transcribe_btn = ttk_bs.Button(
                action_frame,
                text="🚀 Start Transcription",
                command=self._start_transcription,
                bootstyle="success",
                width=20,
            )
        else:
            self.transcribe_btn = tk.Button(
                action_frame,
                text="🚀 Start Transcription",
                command=self._start_transcription,
                font=("Segoe UI", 11, "bold"),
                bg="#4CAF50",
                fg="white",
                relief=tk.FLAT,
                padx=25,
                pady=10,
            )

        self.transcribe_btn.pack(side=tk.RIGHT)
        self.transcribe_btn.configure(state=tk.DISABLED)

    def _create_status_section(self, parent):
        """Create the status section."""
        if MODERN_UI_AVAILABLE:
            status_frame = ttk_bs.LabelFrame(
                parent, text="System Status", padding=15, bootstyle="info"
            )
        else:
            status_frame = tk.LabelFrame(
                parent,
                text="System Status",
                font=("Segoe UI", 10, "bold"),
                fg="#2196F3",
                bg="#ffffff",
                padx=15,
                pady=15,
            )

        status_frame.pack(fill=tk.X, pady=(0, 15))

        # Hardware status line
        hardware_frame = tk.Frame(
            status_frame, bg="#ffffff" if not MODERN_UI_AVAILABLE else None
        )
        hardware_frame.pack(fill=tk.X)

        # Create separate labels for dynamic coloring
        if MODERN_UI_AVAILABLE:
            hw_prefix = ttk_bs.Label(hardware_frame, text="Hardware: ")
            self.cpu_label = ttk_bs.Label(hardware_frame, text="CPU")
            self.slash_label = ttk_bs.Label(hardware_frame, text=" / ")
            self.gpu_label = ttk_bs.Label(hardware_frame, text="GPU")
        else:
            hw_prefix = tk.Label(hardware_frame, text="Hardware: ", bg="#ffffff")
            self.cpu_label = tk.Label(hardware_frame, text="CPU", bg="#ffffff")
            self.slash_label = tk.Label(hardware_frame, text=" / ", bg="#ffffff")
            self.gpu_label = tk.Label(hardware_frame, text="GPU", bg="#ffffff")

        hw_prefix.pack(side=tk.LEFT)
        self.cpu_label.pack(side=tk.LEFT)
        self.slash_label.pack(side=tk.LEFT)
        self.gpu_label.pack(side=tk.LEFT)

        # AI Model status
        if MODERN_UI_AVAILABLE:
            self.model_status_label = ttk_bs.Label(
                status_frame, text="AI Model: Not loaded"
            )
        else:
            self.model_status_label = tk.Label(
                status_frame, text="AI Model: Not loaded", bg="#ffffff"
            )

        self.model_status_label.pack(fill=tk.X, pady=(5, 0))

    def _create_output_section(self, parent):
        """Create the output section."""
        if MODERN_UI_AVAILABLE:
            output_frame = ttk_bs.LabelFrame(
                parent,
                text="Transcription Output & Status",
                padding=15,
                bootstyle="dark",
            )
        else:
            output_frame = tk.LabelFrame(
                parent,
                text="Transcription Output & Status",
                font=("Segoe UI", 10, "bold"),
                fg="#333333",
                bg="#ffffff",
                padx=15,
                pady=15,
            )

        output_frame.pack(fill=tk.BOTH, expand=True)

        # Create text widget with scrollbar
        text_frame = tk.Frame(
            output_frame, bg="#ffffff" if not MODERN_UI_AVAILABLE else None
        )
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Text widget
        self.output_text = tk.Text(
            text_frame,
            font=("Consolas", 9),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#333333",
            wrap=tk.WORD,
            padx=10,
            pady=10,
        )

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.output_text.yview
        )
        self.output_text.configure(yscrollcommand=scrollbar.set)

        # Pack text and scrollbar
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Progress bar
        if MODERN_UI_AVAILABLE:
            self.progress_bar = ttk_bs.Progressbar(
                output_frame, mode="indeterminate", bootstyle="primary-striped"
            )
        else:
            self.progress_bar = ttk.Progressbar(output_frame, mode="indeterminate")

        self.progress_bar.pack(fill=tk.X, pady=(10, 0))

        # Initial message
        self._log_to_output("Welcome to GreekDrop - Greek Audio Transcription System")
        self._log_to_output("Select an audio file to begin transcription.")

    def _setup_drag_drop(self):
        """Setup drag and drop functionality with fallback."""
        if not DRAG_DROP_AVAILABLE:
            self.logger.warning("Drag & drop not available - tkinterdnd2 missing")
            return

        try:
            # Make window accept drops
            self.window.drop_target_register(DND_FILES)
            self.window.dnd_bind("<<Drop>>", self._handle_drop)

            self.logger.debug("Drag & drop enabled successfully")

        except Exception as e:
            self.logger.error(f"Failed to setup drag & drop: {str(e)}", exc_info=True)

    def _handle_drop(self, event):
        """Handle drag and drop events."""
        if not hasattr(event, "data") or not event.data:
            self.logger.warning("Drop event has no data")
            return

        try:
            # Parse dropped files
            files = self.window.tk.splitlist(event.data)
            if not files:
                self.logger.warning("No files in drop event")
                return

            # Take the first file
            file_path = normalize_file_path(files[0])
            self.logger.debug(f"File dropped: {file_path}")

            # Validate and load the file for transcription
            self._load_audio_file(file_path)

            # Show success message
            self.toast.show(
                "File dropped successfully - ready for transcription",
                toast_type="success",
            )

        except Exception as e:
            self.logger.error(f"Drag & drop handling failed: {str(e)}", exc_info=True)
            self._show_error(
                "Drag & Drop Error", f"Failed to process dropped file: {str(e)}"
            )

    def _update_hardware_status(self):
        """Update hardware status labels with dynamic coloring."""
        try:
            # Import hardware detection functions
            from utils.hardware import (
                is_gpu_available,
                get_active_compute_device,
                get_gpu_device_name,
            )

            # Get REAL-TIME hardware status (not cached)
            gpu_available = is_gpu_available()
            compute_device = get_active_compute_device()
            forced_mode = None  # Will be updated if forcing is detected

            # Colors
            if MODERN_UI_AVAILABLE:
                active_color = "success"
                inactive_color = "secondary"
            else:
                active_color = "#4CAF50"  # Green
                inactive_color = "#666666"  # Gray

            # Update CPU label
            if compute_device == "CPU":
                if MODERN_UI_AVAILABLE:
                    self.cpu_label.configure(bootstyle=active_color)
                else:
                    self.cpu_label.configure(
                        fg=active_color, font=("Segoe UI", 9, "bold")
                    )
            elif MODERN_UI_AVAILABLE:
                self.cpu_label.configure(bootstyle=inactive_color)
            else:
                self.cpu_label.configure(fg=inactive_color, font=("Segoe UI", 9))

            # Update GPU label
            if compute_device == "GPU":
                if MODERN_UI_AVAILABLE:
                    self.gpu_label.configure(bootstyle=active_color)
                else:
                    self.gpu_label.configure(
                        fg=active_color, font=("Segoe UI", 9, "bold")
                    )
            elif MODERN_UI_AVAILABLE:
                self.gpu_label.configure(bootstyle=inactive_color)
            else:
                self.gpu_label.configure(fg=inactive_color, font=("Segoe UI", 9))

            # Get device name for logging
            device_name = get_gpu_device_name() if gpu_available else "No GPU"

            # Log hardware detection with runtime status
            self.logger.log_hardware_detection(gpu_available, device_name)

            # Update forced mode info if applicable
            if forced_mode:
                status_text = f"Hardware: {compute_device} (FORCED)"
            else:
                status_text = f"Hardware: {compute_device}"

            self.logger.debug(status_text)

        except Exception as e:
            self.logger.error(f"Hardware status update failed: {str(e)}", exc_info=True)

    def _select_audio_file(self):
        """Open file dialog to select audio file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=[
                    ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.wma *.aac"),
                    ("All Files", "*.*"),
                ],
            )

            if file_path:
                self._load_audio_file(file_path)

        except Exception as e:
            self.logger.error(f"File selection failed: {str(e)}", exc_info=True)
            self._show_error("File Selection Error", f"Failed to select file: {str(e)}")

    def _load_audio_file(self, file_path: str):
        """Load and validate an audio file."""
        try:
            # Normalize path
            normalized_path = normalize_file_path(file_path)

            # Validate file
            is_valid, message = validate_audio_file(normalized_path)

            if not is_valid:
                self._show_error("Invalid Audio File", message)
                return

            # Update UI
            self.current_audio_file = normalized_path

            # Get file metadata
            metadata = extract_basic_audio_metadata(normalized_path)

            # Update file info label
            file_name = Path(normalized_path).name
            self.file_info_label.configure(text=f"✅ {file_name}")

            # Enable transcribe button
            self.transcribe_btn.configure(state=tk.NORMAL)

            # Log to output
            self._log_to_output(f"File loaded: {file_name}")
            self._log_to_output(metadata)

            # Show success toast
            self.toast.show(f"Audio file loaded: {file_name}", toast_type="success")

            self.logger.info(f"Audio file loaded successfully: {file_name}")

        except Exception as e:
            self.logger.error(f"Audio file loading failed: {str(e)}", exc_info=True)
            self._show_error(
                "File Loading Error", f"Failed to load audio file: {str(e)}"
            )

    def _preload_model(self):
        """Preload the AI model."""

        def preload_thread():
            try:
                self.preload_btn.configure(state=tk.DISABLED)
                self._log_to_output("Preloading AI model...")
                self.progress_bar.start()

                success = preload_default_model()

                if success:
                    self.model_status_label.configure(
                        text="AI Model: Ready (Whisper Base)"
                    )
                    self._log_to_output("✅ AI model preloaded successfully")
                    self.toast.show(
                        "AI model preloaded successfully", toast_type="success"
                    )
                else:
                    self._log_to_output("❌ AI model preload failed")
                    self.toast.show("AI model preload failed", toast_type="error")

            except Exception as e:
                self.logger.error(f"Model preload failed: {str(e)}", exc_info=True)
                self._log_to_output(f"❌ Model preload error: {str(e)}")
                self.toast.show("Model preload error", toast_type="error")

            finally:
                self.progress_bar.stop()
                self.preload_btn.configure(state=tk.NORMAL)

        threading.Thread(target=preload_thread, daemon=True).start()

    def _start_transcription(self):
        """Start the transcription process."""
        if not self.current_audio_file:
            self._show_error("No File Selected", "Please select an audio file first.")
            return

        if self.transcription_in_progress:
            self._show_error(
                "Transcription in Progress",
                "Please wait for current transcription to complete.",
            )
            return

        def transcription_thread():
            try:
                self.transcription_in_progress = True
                self.transcribe_btn.configure(state=tk.DISABLED)
                self.progress_bar.start()

                # Clear output
                self.output_text.delete(1.0, tk.END)

                # Progress callback
                def progress_callback(message: str):
                    self.window.after(0, lambda: self._log_to_output(f"🔄 {message}"))

                # Start transcription
                start_time = time.time()
                self._log_to_output(
                    f"Starting transcription of: {Path(self.current_audio_file).name}"
                )

                result = self.transcription_engine.transcribe(
                    self.current_audio_file, progress_callback=progress_callback
                )

                if result.get("success", False):
                    # Display transcription result
                    text = result.get("text", "")
                    processing_time = result.get("processing_time", 0)

                    self._log_to_output("✅ Transcription completed!")
                    self._log_to_output(
                        f"Processing time: {processing_time:.2f} seconds"
                    )
                    self._log_to_output("-" * 50)
                    self._log_to_output("TRANSCRIPTION RESULT:")
                    self._log_to_output("-" * 50)
                    self._log_to_output(text)

                    # Save to file(s)
                    format_type = self.format_var.get()
                    saved_files = save_transcription_to_file(
                        result, self.current_audio_file, format_type
                    )

                    if saved_files:
                        self._log_to_output("-" * 50)
                        self._log_to_output("FILES SAVED:")
                        for file_path in saved_files:
                            absolute_path = Path(file_path).resolve()
                            self._log_to_output(f"📄 {absolute_path}")

                        # Show toast notifications with full paths
                        for i, file_path in enumerate(saved_files):
                            file_name = Path(file_path).name
                            absolute_path = str(Path(file_path).resolve())

                            # Stagger the toast notifications
                            self.window.after(
                                (i + 1) * 1500,  # Stagger toasts by 1.5 seconds
                                lambda path=absolute_path, name=file_name: self.toast.show(
                                    f"Saved: {name}",
                                    duration=4000,
                                    toast_type="success",
                                ),
                            )

                        # Show summary toast
                        self.window.after(
                            len(saved_files) * 1500 + 500,
                            lambda: self.toast.show(
                                f"All files saved! ({len(saved_files)} files)",
                                toast_type="success",
                            ),
                        )
                    else:
                        self._log_to_output("❌ Failed to save transcription files")
                        self.toast.show("Failed to save files", toast_type="error")

                else:
                    error_msg = result.get("error", "Unknown error")
                    self._log_to_output(f"❌ Transcription failed: {error_msg}")
                    self.toast.show("Transcription failed", toast_type="error")

            except Exception as e:
                self.logger.error(
                    f"Transcription thread failed: {str(e)}", exc_info=True
                )
                self._log_to_output(f"❌ Transcription error: {str(e)}")
                self.toast.show("Transcription error", toast_type="error")

            finally:
                self.transcription_in_progress = False
                self.progress_bar.stop()
                self.transcribe_btn.configure(state=tk.NORMAL)

        threading.Thread(target=transcription_thread, daemon=True).start()

    def _show_info(self):
        """Show application information."""
        deps = check_dependencies()

        info_text = f"""
{APP_NAME} {VERSION}

DEPENDENCIES:
✅ Modern UI: {'Available' if deps.get('modern_ui', False) else 'Not Available'}
✅ Drag & Drop: {'Available' if deps.get('drag_drop', False) else 'Not Available'}
✅ Whisper AI: {'Available' if deps.get('whisper', False) else 'Not Available'}
✅ PyTorch: {'Available' if deps.get('torch', False) else 'Not Available'}

HARDWARE:
🖥️ Compute Device: {deps.get('compute_device', 'CPU')}
🔧 Forced Mode: {deps.get('forced_mode', 'None')}

OUTPUT FORMATS:
📄 TXT - Plain text transcription
📄 SRT - Subtitle format with timestamps
📄 VTT - WebVTT subtitle format
📄 All - Saves TXT, SRT, and VTT formats

SUPPORTED AUDIO:
🎵 WAV, MP3, M4A, FLAC, OGG, WMA, AAC

OUTPUT DIRECTORY:
📁 {get_output_directory()}
        """.strip()

        messagebox.showinfo("GreekDrop Information", info_text)

    def _log_to_output(self, message: str):
        """Log a message to the output text widget."""
        try:
            self.output_text.insert(tk.END, f"{message}\n")
            self.output_text.see(tk.END)
            self.window.update_idletasks()
        except Exception as e:
            self.logger.error(f"Failed to log to output: {str(e)}")

    def _show_error(self, title: str, message: str):
        """Show an error dialog and log the error."""
        self.logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def run(self):
        """Start the UI main loop."""
        try:
            self.logger.info("Starting UI main loop")
            self.window.mainloop()
        except Exception as e:
            self.logger.critical(f"UI main loop failed: {str(e)}", exc_info=True)
            raise
        finally:
            self.logger.info("UI main loop ended")


def create_and_run_ui():
    """Create and run the GreekDrop UI."""
    try:
        app = GreekDropUI()
        app.run()
    except Exception as e:
        print(f"CRITICAL ERROR: UI creation failed: {str(e)}")
        raise


if __name__ == "__main__":
    create_and_run_ui()
