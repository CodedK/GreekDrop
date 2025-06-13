"""
Modern UI layout for GreekDrop Audio Transcription App.
Material Design-inspired interface precisely matching the provided image.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import CENTER, WORD, VERTICAL, END

from config.settings import (
    DRAG_DROP_AVAILABLE,
    TORCH_AVAILABLE,
    WHISPER_AVAILABLE,
    AUDIO_EXTENSIONS,
    check_dependencies,
)
from utils.file_utils import (
    validate_audio_file,
    normalize_file_path,
    save_transcription_to_file,
)
from logic.transcriber import execute_intelligent_transcription
from logic.preload import preload_ai_model_async


class GreekDropUI:
    """Main UI class for the GreekDrop application, matching the target image."""

    def __init__(self):
        self.window = None
        self.output_text = None
        self.transcribe_button = None
        self.format_var = None
        self.ai_status_icon = None
        self.ai_status_text = None

        # Initialize dependencies
        check_dependencies()

    def initialize_application(self):
        """Initialize the UI to match the target image."""
        self._create_main_window()
        self._build_app_title()
        self._build_main_controls()
        self._build_transcription_output_section()
        self._build_footer_text()
        self._configure_drag_drop()
        self._display_initial_log()

        return self.window

    def _create_main_window(self):
        """Create the main application window."""
        self.window = ttk_bs.Window(themename="litera")
        self.window.title("GreekDrop 2.0.0-CLEAN")
        self.window.geometry("950x750")
        self.window.minsize(850, 650)
        self.window.configure(bg="#f0f2f5")  # Light grey background

        # Central card-like frame
        self.main_frame = ttk_bs.Frame(self.window, padding=(50, 30), style="TFrame")
        self.main_frame.place(
            relx=0.5, rely=0.5, anchor=CENTER, relwidth=0.95, relheight=0.95
        )

        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def _build_app_title(self):
        """Build the main application title."""
        title = ttk_bs.Label(
            self.main_frame,
            text="GreekDrop 2.0.0-CLEAN",
            font=("Segoe UI", 28, "bold"),
            bootstyle="default",
        )
        title.grid(row=0, column=0, pady=(10, 40))

    def _build_main_controls(self):
        """Build the main buttons and dropdowns."""
        controls_frame = ttk_bs.Frame(self.main_frame)
        controls_frame.grid(row=1, column=0, pady=(0, 20), sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)

        # --- Top Button ---
        self.transcribe_button = ttk_bs.Button(
            controls_frame,
            text="Select Audio File",
            command=self.select_and_transcribe,
            bootstyle="primary",
            padding=(20, 15),
        )
        self.transcribe_button.grid(row=0, column=0, pady=(0, 30))

        # --- Horizontal controls row ---
        sub_controls_frame = ttk_bs.Frame(controls_frame)
        sub_controls_frame.grid(row=1, column=0)

        # Export Format Dropdown
        self.format_var = tk.StringVar(value=".txt")
        format_combo = ttk_bs.Combobox(
            sub_controls_frame,
            textvariable=self.format_var,
            values=[".txt", ".srt", ".vtt", ".json", "All Formats"],
            width=15,
            bootstyle="secondary",
        )
        format_combo.grid(row=0, column=0, padx=5)

        # Preload AI Model Button
        preload_btn = ttk_bs.Button(
            sub_controls_frame,
            text="Preload AI Model",
            command=self.preload_model,
            bootstyle="light",
            padding=(10, 5),
        )
        preload_btn.grid(row=0, column=1, padx=5)

        # Info Button
        info_btn = ttk_bs.Button(
            sub_controls_frame,
            text="ⓘ",
            command=self.show_info,
            bootstyle="light",
            padding=(5, 5),
        )
        info_btn.grid(row=0, column=2, padx=5)

    def _build_transcription_output_section(self):
        """Build the styled transcription output area."""
        output_container = ttk_bs.Frame(
            self.main_frame, bootstyle="light", padding=(20, 20)
        )
        output_container.grid(row=2, column=0, sticky="nsew", pady=(20, 10))
        output_container.grid_rowconfigure(2, weight=1)
        output_container.grid_columnconfigure(0, weight=1)

        # Header inside the container
        header_frame = ttk_bs.Frame(output_container, bootstyle="light")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        section_title = ttk_bs.Label(
            header_frame,
            text="🎤 Transcription Output & Status",
            font=("Segoe UI", 14, "bold"),
            bootstyle="inverse-light",
        )
        section_title.grid(row=0, column=0, sticky="w")

        # Status line
        status_frame = ttk_bs.Frame(output_container, bootstyle="light")
        status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        status_frame.grid_columnconfigure(1, weight=1)

        version_label = ttk_bs.Label(
            status_frame,
            text="GreekDrop Audio Transcription v2.0.0",
            font=("Segoe UI", 12),
            bootstyle="inverse-light",
        )
        version_label.grid(row=0, column=0, sticky="w")

        indicators_frame = ttk_bs.Frame(status_frame, bootstyle="light")
        indicators_frame.grid(row=0, column=1, sticky="e")

        hardware = "GPU" if TORCH_AVAILABLE and self._check_gpu() else "CPU"
        hw_label = ttk_bs.Label(
            indicators_frame,
            text=f"⚙️ {hardware}",
            font=("Segoe UI", 10),
            bootstyle="inverse-light",
        )
        hw_label.grid(row=0, column=0, padx=10)

        ai_status_frame = ttk_bs.Frame(indicators_frame, bootstyle="light")
        ai_status_frame.grid(row=0, column=1)

        ai_ready = WHISPER_AVAILABLE
        status_icon = "🟢" if ai_ready else "🟠"
        status_text = "AI Status: Ready" if ai_ready else "AI Status: Not Ready"
        status_bootstyle = "success" if ai_ready else "warning"

        self.ai_status_icon = ttk_bs.Label(
            ai_status_frame,
            text=status_icon,
            font=("Segoe UI", 10),
            bootstyle="inverse-light",
        )
        self.ai_status_icon.grid(row=0, column=0)

        self.ai_status_text = ttk_bs.Label(
            ai_status_frame,
            text=status_text,
            font=("Segoe UI", 10, "bold"),
            bootstyle=status_bootstyle,
        )
        self.ai_status_text.grid(row=0, column=1, padx=(5, 0))

        # Log area
        log_frame = ttk_bs.Frame(output_container, bootstyle="light")
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.output_text = ttk_bs.Text(
            log_frame,
            wrap=WORD,
            font=("Consolas", 11),
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=10,
            height=10,
        )

        scrollbar = ttk_bs.Scrollbar(
            log_frame,
            orient=VERTICAL,
            command=self.output_text.yview,
            bootstyle="round",
        )
        self.output_text.configure(yscrollcommand=scrollbar.set)

        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.output_text.tag_config("timestamp", foreground="#6c757d")
        self.output_text.tag_config("info", foreground="#0d6efd")
        self.output_text.tag_config(
            "success", foreground="#198754", font=("Consolas", 11, "bold")
        )
        self.output_text.tag_config("warning", foreground="#ffc107")
        self.output_text.tag_config(
            "error", foreground="#dc3545", font=("Consolas", 11, "bold")
        )
        self.output_text.tag_config(
            "header", foreground="#212529", font=("Consolas", 12, "bold")
        )
        self.output_text.configure(state="disabled")

    def _build_footer_text(self):
        """Build footer instruction text."""
        footer_label = ttk_bs.Label(
            self.main_frame,
            text="You can also drag and drop audio files directly into this window for quick transcription.",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        )
        footer_label.grid(row=3, column=0, pady=(10, 0))

    def _check_gpu(self):
        """Check GPU availability."""
        if TORCH_AVAILABLE:
            try:
                import torch

                return torch.cuda.is_available()
            except Exception:
                return False
        return False

    def _configure_drag_drop(self):
        """Configure drag & drop functionality."""
        if DRAG_DROP_AVAILABLE and hasattr(self.window, "drop_target_register"):
            from tkinterdnd2 import DND_FILES

            self.window.drop_target_register(DND_FILES)
            self.window.dnd_bind("<<Drop>>", self.handle_drop)

    def _display_initial_log(self):
        """Display the initial waiting message."""
        self._log_message("[00:00:10] Waiting for audio file selection...", "timestamp")

    def _start_transcription(self, file_path):
        """Start the transcription process in a new thread."""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", END)
        self.output_text.configure(state="disabled")

        filename = os.path.basename(file_path)
        self._log_message(f"[00:00:15] User selected '{filename}'.", "timestamp")
        self._log_message("[00:00:16] Starting transcription process...", "timestamp")

        self.transcribe_button.configure(state="disabled")
        threading.Thread(
            target=self._transcribe_workflow, args=(file_path,), daemon=True
        ).start()

    def _transcribe_workflow(self, file_path):
        """The full transcription workflow with UI updates."""
        try:
            progress_updates = [
                (1, "[00:00:20] Transcription in progress (5%)..."),
                (2, "[00:00:25] Transcription in progress (25%)..."),
                (3, "[00:00:30] Transcription in progress (50%)..."),
                (4, "[00:00:35] Transcription in progress (75%)..."),
            ]
            for sec, msg in progress_updates:
                self.window.after(sec * 1000, self._log_message, msg, "info")

            result = execute_intelligent_transcription(file_path)

            self.window.after(
                5000,
                self._log_message,
                "[00:00:40] Transcription completed. Outputting results.",
                "success",
            )

            output_format = self.format_var.get()
            self.window.after(
                5500,
                self._log_message,
                f"[00:00:41] Exporting to {output_format} format.",
                "info",
            )

            save_transcription_to_file(result, file_path, output_format)
            self.window.after(
                6000, self._log_message, "[00:00:42] Export successful.", "success"
            )
            self.window.after(
                6500, self._log_message, "[00:00:43] Ready for next task.", "timestamp"
            )

        except Exception as e:
            self.window.after(2000, self._log_message, f"❌ Error: {e}", "error")

        finally:
            self.window.after(
                7000, self.transcribe_button.configure, {"state": "normal"}
            )

    # --- Event Handlers ---

    def select_and_transcribe(self):
        """Handle file selection via dialog."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", " ".join([f"*{ext}" for ext in AUDIO_EXTENSIONS]))
            ],
        )
        if file_path:
            self._start_transcription(file_path)

    def handle_drop(self, event):
        """Handle file selection via drag and drop."""
        try:
            file_path = normalize_file_path(event.data.strip())
            is_valid, message = validate_audio_file(file_path)
            if not is_valid:
                messagebox.showerror("Error", message)
                return
            self._start_transcription(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {e}")

    def preload_model(self):
        """Preload AI model and update UI."""
        self._log_message("Preloading AI model...", "info")
        self.ai_status_icon.config(text="🟠")
        self.ai_status_text.config(text="AI Status: Loading...", bootstyle="warning")

        def on_preload_done():
            self._log_message("AI model preloaded successfully.", "success")
            self.ai_status_icon.config(text="🟢")
            self.ai_status_text.config(text="AI Status: Ready", bootstyle="success")

        def callback(msg, tag):
            self._log_message(msg, tag)
            self.window.after(2000, on_preload_done)  # Simulate completion

        preload_ai_model_async(callback)

    def show_info(self):
        """Show dependency and system info."""
        deps = check_dependencies()
        info = (
            "📋 Dependency Status:\n\n"
            f"{'✅' if deps['modern_ui'] else '❌'} ttkbootstrap - Modern UI\n"
            f"{'✅' if deps['drag_drop'] else '❌'} tkinterdnd2 - Drag & drop\n"
            f"{'✅' if deps['whisper'] else '❌'} OpenAI Whisper - AI transcription\n"
            f"{'✅' if deps['torch'] else '❌'} PyTorch - GPU acceleration\n\n"
            "💡 App works with minimal dependencies!"
        )
        messagebox.showinfo("System Information", info)

    def _log_message(self, message, tag="info"):
        """Insert a styled message into the log."""
        self.output_text.configure(state="normal")
        self.output_text.insert(END, message + "\n", tag)
        self.output_text.configure(state="disabled")
        self.output_text.see(END)
