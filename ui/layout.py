"""
Modern UI layout for GreekDrop Audio Transcription App.
Material Design-inspired interface with responsive components.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os

from config.settings import *
from utils.file_utils import (
    validate_audio_file,
    normalize_file_path,
    save_transcription_to_file,
    extract_basic_audio_metadata,
)
from logic.transcriber import (
    execute_intelligent_transcription,
    validate_system_dependencies,
)
from logic.preload import preload_ai_model_async


class GreekDropUI:
    """Main UI class for the GreekDrop application."""

    def __init__(self):
        self.window = None
        self.output_text = None
        self.transcribe_button = None
        self.format_var = None
        self.progress_bar = None

        # Initialize dependencies
        check_dependencies()

    def initialize_application(self):
        """Initialize the complete modern application UI."""
        self._create_main_window()
        self._build_header_section()
        self._build_control_panel()
        self._build_output_section()
        self._build_footer_section()
        self._configure_drag_drop()
        self._display_welcome_message()

        return self.window

    def _create_main_window(self):
        """Create the main application window."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            self.window = ttk_bs.Window(themename=DEFAULT_THEME)
        elif DRAG_DROP_AVAILABLE:
            from tkinterdnd2 import TkinterDnD

            self.window = TkinterDnD.Tk()
            self.window.configure(bg=COLORS["light"])
        else:
            self.window = tk.Tk()
            self.window.configure(bg=COLORS["light"])

        self.window.title(f"🎯 {APP_NAME} {VERSION}")
        self.window.geometry(DEFAULT_WINDOW_SIZE)
        self.window.minsize(*MIN_WINDOW_SIZE)

        # Configure responsive layout
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

    def _build_header_section(self):
        """Build modern header with title and status."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            header = ttk_bs.Frame(self.window, bootstyle="primary")
        else:
            header = tk.Frame(self.window, bg=COLORS["primary"], height=90)

        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Title
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            title = ttk_bs.Label(
                header,
                text=f"🎯 {APP_NAME}",
                font=("Segoe UI", 22, "bold"),
                bootstyle="inverse-primary",
            )
        else:
            title = tk.Label(
                header,
                text=f"🎯 {APP_NAME}",
                font=("Segoe UI", 22, "bold"),
                bg=COLORS["primary"],
                fg="white",
            )

        title.grid(row=0, column=0, padx=25, pady=20, sticky="w")

        # Status indicators
        self._create_status_frame(header)

    def _create_status_frame(self, parent):
        """Create hardware and AI status indicators."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            status_frame = ttk_bs.Frame(parent, bootstyle="primary")
        else:
            status_frame = tk.Frame(parent, bg=COLORS["primary"])

        status_frame.grid(row=0, column=2, padx=25, pady=20, sticky="e")

        hardware = "GPU" if TORCH_AVAILABLE and self._check_gpu() else "CPU"
        ai_status = "🧠 AI Ready" if WHISPER_AVAILABLE else "⚠️ Basic Mode"

        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            hw_label = ttk_bs.Label(
                status_frame,
                text=f"🖥️ {hardware}",
                bootstyle="inverse-success" if "GPU" in hardware else "inverse-warning",
            )
            ai_label = ttk_bs.Label(
                status_frame,
                text=ai_status,
                bootstyle="inverse-success" if WHISPER_AVAILABLE else "inverse-warning",
            )
        else:
            hw_label = tk.Label(
                status_frame,
                text=f"🖥️ {hardware}",
                bg=COLORS["primary"],
                fg="white",
                font=("Segoe UI", 10),
            )
            ai_label = tk.Label(
                status_frame,
                text=ai_status,
                bg=COLORS["primary"],
                fg="white",
                font=("Segoe UI", 10),
            )

        hw_label.grid(row=0, column=0, sticky="e", pady=3)
        ai_label.grid(row=1, column=0, sticky="e", pady=3)

    def _check_gpu(self):
        """Check GPU availability."""
        if TORCH_AVAILABLE:
            try:
                import torch

                return torch.cuda.is_available()
            except:
                return False
        return False

    def _build_control_panel(self):
        """Build control panel with buttons and options."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            control = ttk_bs.Frame(self.window, bootstyle="light")
        else:
            control = tk.Frame(self.window, bg=COLORS["light"])

        control.grid(row=1, column=0, sticky="ew", padx=25, pady=25)
        control.grid_columnconfigure(0, weight=1)

        # Main button
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            self.transcribe_button = ttk_bs.Button(
                control,
                text="📂  Select Audio File",
                command=self.select_and_transcribe,
                bootstyle="success-outline",
                width=30,
            )
        else:
            self.transcribe_button = tk.Button(
                control,
                text="📂  Select Audio File",
                command=self.select_and_transcribe,
                font=("Segoe UI", 14, "bold"),
                bg=COLORS["success"],
                fg="white",
                relief="flat",
                padx=25,
                pady=12,
            )

        self.transcribe_button.grid(row=0, column=0, pady=15)

        # Format options
        self._create_format_options(control)
        self._create_action_buttons(control)
        self._create_progress_bar(control)

    def _create_format_options(self, parent):
        """Create format selection dropdown."""
        options_frame = tk.Frame(parent, bg=COLORS["light"])
        options_frame.grid(row=1, column=0, pady=15)

        label = tk.Label(
            options_frame,
            text="Export Format:",
            font=("Segoe UI", 11),
            bg=COLORS["light"],
        )
        self.format_var = tk.StringVar(value="txt")

        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            combo = ttk_bs.Combobox(
                options_frame,
                textvariable=self.format_var,
                values=EXPORT_FORMATS,
                width=15,
                bootstyle="primary",
            )
        else:
            combo = ttk.Combobox(
                options_frame,
                textvariable=self.format_var,
                values=EXPORT_FORMATS,
                width=15,
            )

        label.grid(row=0, column=0, padx=(0, 15))
        combo.grid(row=0, column=1, padx=15)

    def _create_action_buttons(self, parent):
        """Create secondary action buttons."""
        buttons_frame = tk.Frame(parent, bg=COLORS["light"])
        buttons_frame.grid(row=2, column=0, pady=15)

        col = 0
        if WHISPER_AVAILABLE:
            if MODERN_UI_AVAILABLE:
                import ttkbootstrap as ttk_bs

                preload_btn = ttk_bs.Button(
                    buttons_frame,
                    text="🚀 Preload AI",
                    command=self.preload_model,
                    bootstyle="info-outline",
                    width=15,
                )
            else:
                preload_btn = tk.Button(
                    buttons_frame,
                    text="🚀 Preload AI",
                    command=self.preload_model,
                    font=("Segoe UI", 11),
                    bg=COLORS["info"],
                    fg="white",
                    relief="flat",
                )
            preload_btn.grid(row=0, column=col, padx=8)
            col += 1

        # Info button
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            info_btn = ttk_bs.Button(
                buttons_frame,
                text="ℹ️ Info",
                command=self.show_info,
                bootstyle="warning-outline",
                width=15,
            )
        else:
            info_btn = tk.Button(
                buttons_frame,
                text="ℹ️ Info",
                command=self.show_info,
                font=("Segoe UI", 11),
                bg=COLORS["warning"],
                fg="black",
                relief="flat",
            )
        info_btn.grid(row=0, column=col, padx=8)

    def _create_progress_bar(self, parent):
        """Create progress bar."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            self.progress_bar = ttk_bs.Progressbar(
                parent, mode="indeterminate", bootstyle="success-striped"
            )
        else:
            self.progress_bar = ttk.Progressbar(parent, mode="indeterminate")

        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=25, pady=15)
        self.progress_bar.grid_remove()

    def _build_output_section(self):
        """Build output text area."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            output_frame = ttk_bs.Frame(self.window, bootstyle="secondary")
        else:
            output_frame = tk.Frame(self.window, bg="#e9ecef")

        output_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 25))
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # Label
        label = tk.Label(
            output_frame,
            text="📝 Transcription Output & Status",
            font=("Segoe UI", 13, "bold"),
            bg="#e9ecef",
        )
        label.grid(row=0, column=0, sticky="w", padx=15, pady=15)

        # Text area with scrollbar
        text_frame = tk.Frame(output_frame)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="white",
            fg="#212529",
            relief="flat",
            padx=20,
            pady=20,
        )

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.output_text.yview
        )
        self.output_text.configure(yscrollcommand=scrollbar.set)

        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure text tags
        self.output_text.tag_config(
            "header", foreground=COLORS["primary"], font=("Consolas", 13, "bold")
        )
        self.output_text.tag_config("info", foreground=COLORS["info"])
        self.output_text.tag_config(
            "success", foreground=COLORS["success"], font=("Consolas", 11, "bold")
        )
        self.output_text.tag_config("warning", foreground=COLORS["warning"])
        self.output_text.tag_config(
            "error", foreground=COLORS["error"], font=("Consolas", 11, "bold")
        )
        self.output_text.tag_config("stats", foreground="#6f42c1")

    def _build_footer_section(self):
        """Build footer with drag & drop info."""
        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            footer = ttk_bs.Frame(self.window, bootstyle="dark")
        else:
            footer = tk.Frame(self.window, bg=COLORS["dark"])

        footer.grid(row=3, column=0, sticky="ew")

        text = (
            "📁 Drag & drop audio files anywhere to transcribe"
            if DRAG_DROP_AVAILABLE
            else "💡 Install tkinterdnd2 for drag & drop"
        )

        if MODERN_UI_AVAILABLE:
            import ttkbootstrap as ttk_bs

            label = ttk_bs.Label(
                footer, text=text, font=("Segoe UI", 10), bootstyle="inverse-dark"
            )
        else:
            label = tk.Label(
                footer, text=text, font=("Segoe UI", 10), bg=COLORS["dark"], fg="white"
            )

        label.pack(pady=12)

    def _configure_drag_drop(self):
        """Configure drag & drop functionality."""
        if DRAG_DROP_AVAILABLE and hasattr(self.window, "drop_target_register"):
            from tkinterdnd2 import DND_FILES

            self.window.drop_target_register(DND_FILES)
            self.window.dnd_bind("<<Drop>>", self.handle_drop)

    def _display_welcome_message(self):
        """Display welcome message."""
        self.output_text.insert(
            tk.END, f"🎯 {APP_NAME} Audio Transcription\n", "header"
        )
        self.output_text.insert(tk.END, f"Version {VERSION}\n\n", "info")

        hardware = "GPU" if TORCH_AVAILABLE and self._check_gpu() else "CPU"
        self.output_text.insert(tk.END, f"🖥️ Hardware: {hardware}\n", "info")

        if WHISPER_AVAILABLE:
            self.output_text.insert(tk.END, "🧠 AI Transcription: Ready\n", "success")
        else:
            self.output_text.insert(
                tk.END, "⚠️ AI Transcription: Install openai-whisper\n", "warning"
            )

        self.output_text.insert(tk.END, "\n🚀 Ready to transcribe!\n\n", "success")

    # Event handlers
    def select_and_transcribe(self):
        """File selection and transcription."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", " ".join([f"*{ext}" for ext in AUDIO_EXTENSIONS]))
            ],
        )
        if file_path:
            self._start_transcription(file_path)

    def handle_drop(self, event):
        """Handle drag & drop."""
        try:
            file_path = normalize_file_path(event.data.strip())
            is_valid, message = validate_audio_file(file_path)
            if not is_valid:
                messagebox.showerror("Error", message)
                return
            self._start_transcription(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {e}")

    def _start_transcription(self, file_path):
        """Start transcription process."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END, f"📂 Processing: {os.path.basename(file_path)}\n", "info"
        )

        # Show progress
        self.transcribe_button.configure(state="disabled")
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=25, pady=15)
        self.progress_bar.start()

        # Background transcription
        threading.Thread(
            target=self._transcribe_workflow, args=(file_path,), daemon=True
        ).start()

    def _transcribe_workflow(self, file_path):
        """Transcription workflow."""
        try:
            audio_info = extract_basic_audio_metadata(file_path)
            self.output_text.insert(tk.END, f"{audio_info}\n", "info")

            result = execute_intelligent_transcription(file_path)

            # Display results
            self.output_text.insert(tk.END, "\n📝 RESULT:\n", "header")
            self.output_text.insert(tk.END, f"{result['text']}\n\n", "success")
            self.output_text.insert(
                tk.END, f"⏱️ Time: {result['processing_time']:.1f}s\n", "stats"
            )
            self.output_text.insert(
                tk.END, f"⚡ Speed: {result['speedup']:.2f}x\n", "stats"
            )

            # Save file
            output_path = save_transcription_to_file(
                result, file_path, self.format_var.get()
            )
            if output_path:
                self.output_text.insert(
                    tk.END, f"💾 Saved: {os.path.basename(output_path)}\n", "success"
                )

            self.output_text.insert(tk.END, "\n✅ Completed!\n\n", "success")

        except Exception as e:
            self.output_text.insert(tk.END, f"\n❌ Error: {e}\n\n", "error")

        finally:
            self.transcribe_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.output_text.see(tk.END)

    def preload_model(self):
        """Preload AI model."""

        def callback(msg, tag):
            self.output_text.insert(tk.END, f"{msg}\n", tag)

        preload_ai_model_async(callback)

    def show_info(self):
        """Show dependency info."""
        deps = check_dependencies()
        info = "📋 Dependencies:\n\n"
        info += f"{'✅' if deps['modern_ui'] else '❌'} ttkbootstrap - Modern UI\n"
        info += f"{'✅' if deps['drag_drop'] else '❌'} tkinterdnd2 - Drag & drop\n"
        info += (
            f"{'✅' if deps['whisper'] else '❌'} OpenAI Whisper - AI transcription\n"
        )
        info += f"{'✅' if deps['torch'] else '❌'} PyTorch - GPU acceleration\n\n"
        info += "💡 App works with minimal dependencies!"
        messagebox.showinfo("Dependency Status", info)
