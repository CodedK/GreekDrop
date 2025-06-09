#!/usr/bin/env python3
"""
GreekDrop Executable Builder
Creates optimized standalone executables for distribution
"""

import os
import subprocess
import shutil
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

EXCLUDED_MODULES = [
    "matplotlib",
    "scipy",
    "pandas",
    "PIL",
    "cv2",
    "selenium",
    "jax",
    "expecttest",
    "keras",
    "tensorflow",
    "nltk",
    "transformers",
    "jupyterlab",
    "IPython",
    "botocore",
    "skimage",
    "sklearn",
    "pyarrow",
    "sqlalchemy",
    "bokeh",
    "spacy",
    "plotly",
    "notebook",
    "onnxruntime",
    "numpy",
    "sympy",
    "llvmlite",
    "pywt",
    "pyproj",
    "numba",
    "statsmodels",
    "mpl_toolkits",
]


def build_pyinstaller(source_file="optimized_main.py", optimization_level="standard"):
    print(f"🔨 Building with PyInstaller ({optimization_level})...")

    base_args = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "GreekDrop-Optimized",
        "--icon",
        "greekDrop.ico" if os.path.exists("greekDrop.ico") else None,
        "--add-data",
        "transcriptions;transcriptions",
        "--hidden-import",
        "torch",
        "--hidden-import",
        "torchaudio",
        "--hidden-import",
        "whisper",
        "--hidden-import",
        "tkinterdnd2",
        source_file,
    ]
    base_args = [arg for arg in base_args if arg is not None]

    if optimization_level in ("standard", "maximum"):
        if optimization_level == "maximum":
            upx_dir = get_upx_path()
            if shutil.which("strip"):
                base_args.append("--strip")
            else:
                logging.warning("Skipping --strip: 'strip' not found.")
            if upx_dir:
                base_args.extend(["--upx-dir", upx_dir])
            else:
                logging.warning("UPX not available; skipping --upx-dir")
            base_args.append("--noupx")
        else:
            base_args.append("--strip")

        for module in EXCLUDED_MODULES:
            base_args.extend(["--exclude-module", module])

    try:
        subprocess.run(base_args, check=True, capture_output=True, text=True)
        print("✅ PyInstaller build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def build_nuitka(source_file="optimized_main.py"):
    print("🚀 Building with Nuitka (maximum performance)...")

    args = [
        "python",
        "-m",
        "nuitka",
        "--onefile",
        "--windows-console-mode=disable",
        "--enable-plugin=tk-inter",
        "--include-package=whisper",
        "--include-package=torch",
        "--include-package=torchaudio",
        "--include-package=tkinterdnd2",
        "--output-filename=GreekDrop-Ultra.exe",
        "--remove-output",
        source_file,
    ]

    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
        print("✅ Nuitka build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def get_upx_path():
    env_upx = os.environ.get("UPX_PATH")
    if env_upx and shutil.which(env_upx):
        logging.info(f"UPX found via UPX_PATH: {env_upx}")
        return os.path.dirname(env_upx)
    for path in ["upx", "C:\\upx\\upx.exe", "/usr/bin/upx", "/usr/local/bin/upx"]:
        if shutil.which(path):
            upx_full_path = shutil.which(path)
            logging.info(f"UPX found at: {upx_full_path}")
            return os.path.dirname(upx_full_path)
    logging.warning("UPX not found in standard paths or environment.")
    return None


def check_requirements():
    """Check if essential build tools are present"""
    logging.info("Checking build requirements...")

    requirements = {
        "pyinstaller": "pip install pyinstaller",
        "nuitka": "pip install nuitka",
    }

    missing = []

    for req, install_cmd in requirements.items():
        if shutil.which(req) or shutil.which(f"{req}.exe"):
            logging.info(f"{req} is available.")
        else:
            logging.warning(f"{req} not found.")
            missing.append(f"{req}: {install_cmd}")

    if upx_path := get_upx_path():
        logging.info(f"UPX available at: {upx_path}")
    else:
        logging.warning("UPX not found. You can set UPX_PATH or install UPX manually.")
    if missing:
        logging.error("Missing required components:")
        for item in missing:
            logging.error(f"   {item}")
        return False
    return True


def create_installer_script():
    installer_content = """@echo off
echo ========================================
echo GreekDrop Optimized Installation
echo ========================================
echo.
if not exist "%USERPROFILE%\\GreekDrop" mkdir "%USERPROFILE%\\GreekDrop"
copy "GreekDrop-Optimized.exe" "%USERPROFILE%\\GreekDrop\\"
echo Creating desktop shortcut...
powershell "$ws = New-Object -ComObject WScript.Shell; ^
$s = $ws.CreateShortcut('%USERPROFILE%\\Desktop\\GreekDrop.lnk'); ^
$s.TargetPath = '%USERPROFILE%\\GreekDrop\\GreekDrop-Optimized.exe'; ^
$s.Save()"
set STARTMENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GreekDrop
if not exist "%STARTMENU%" mkdir "%STARTMENU%"
powershell "$ws = New-Object -ComObject WScript.Shell; ^
$s = $ws.CreateShortcut('%STARTMENU%\\GreekDrop.lnk'); ^
$s.TargetPath = '%USERPROFILE%\\GreekDrop\\GreekDrop-Optimized.exe'; ^
$s.Save()"
echo.
echo ✅ Installation completed!
echo.
echo Application installed to: %USERPROFILE%\\GreekDrop
echo Desktop shortcut created
echo Start menu entry created
echo.
pause
"""
    with open("installer.bat", "w") as f:
        f.write(installer_content)
    print("📦 Installer script created: installer.bat")


def main():
    print("🚀 GreekDrop Executable Builder")
    print("=" * 40)
    if not check_requirements():
        print("\n❌ Please install missing requirements first.")
        return
    # Check if source file exists
    source_file = "optimized_main.py"
    if not os.path.exists(source_file):
        print(f"❌ Source file '{source_file}' not found!")
        return
    print("\n📋 Build Options:")
    print("1. PyInstaller - Standard (Recommended)")
    print("2. PyInstaller - Maximum Optimization")
    print("3. Nuitka - Ultra Performance")
    print("4. Build All Versions")
    choice = input("\nSelect build option (1-4): ").strip()
    success = False
    if choice == "1":
        success = build_pyinstaller(source_file, "standard")
    elif choice == "2":
        success = build_pyinstaller(source_file, "maximum")
    elif choice == "3":
        success = build_nuitka(source_file)
    elif choice == "4":
        print("🔨 Building all versions...")
        success1 = build_pyinstaller(source_file, "standard")
        success2 = build_nuitka(source_file)
        success = success1 or success2
    else:
        print("❌ Invalid choice!")
        return
    if success:
        create_installer_script()
        print("\n🎉 Build completed successfully!")
        print("\n📁 Generated files:")
        if os.path.exists("dist"):
            for file in os.listdir("dist"):
                if file.endswith(".exe"):
                    size = os.path.getsize(os.path.join("dist", file)) / (1024 * 1024)
                    print(f"   📄 {file} ({size:.1f} MB)")
        print("\n💡 Next steps:")
        print("1. Test the executable on a clean system")
        print("2. Run installer.bat to install system-wide")
        print("3. Distribute the executable to users")
        print("\n⚡ Performance Tips:")
        print("- First run will be slower due to model loading")
        print("- Use 'Preload AI' button for instant subsequent processing")
        print("- Ensure NVIDIA GPU drivers for maximum speed")


if __name__ == "__main__":
    main()
