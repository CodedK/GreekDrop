#!/usr/bin/env python3
"""
GreekDrop Executable Builder
Creates optimized standalone executables for distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if build requirements are installed"""
    requirements = {
        'pyinstaller': 'pip install pyinstaller',
        'nuitka': 'pip install nuitka',
        'upx': 'Download from https://upx.github.io/'
    }

    missing = []
    for req, install_cmd in requirements.items():
        try:
            if req == 'upx':
                result = subprocess.run(['upx', '--version'], capture_output=True)
                if result.returncode != 0:
                    missing.append(f"{req}: {install_cmd}")
            else:
                __import__(req)
        except (ImportError, FileNotFoundError):
            missing.append(f"{req}: {install_cmd}")

    if missing:
        print("❌ Missing requirements:")
        for req in missing:
            print(f"   {req}")
        return False
    return True

def build_pyinstaller(source_file="optimized_main.py", optimization_level="standard"):
    """Build executable using PyInstaller"""
    print(f"🔨 Building with PyInstaller ({optimization_level})...")

    base_args = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "GreekDrop-Optimized",
        "--icon", "icon.ico" if os.path.exists("icon.ico") else None,
        "--add-data", "transcriptions;transcriptions",
        "--hidden-import", "torch",
        "--hidden-import", "torchaudio",
        "--hidden-import", "whisper",
        "--hidden-import", "tkinterdnd2",
        source_file
    ]

    # Remove None values
    base_args = [arg for arg in base_args if arg is not None]

    if optimization_level == "minimal":
        # Fastest build, larger size
        pass
    elif optimization_level == "standard":
        # Balanced optimization
        base_args.extend([
            "--strip",
            "--exclude-module", "matplotlib",
            "--exclude-module", "scipy",
            "--exclude-module", "pandas"
        ])
    elif optimization_level == "maximum":
        # Maximum optimization, slower build
        base_args.extend([
            "--strip",
            "--upx-dir", get_upx_path(),
            "--exclude-module", "matplotlib",
            "--exclude-module", "scipy",
            "--exclude-module", "pandas",
            "--exclude-module", "PIL",
            "--exclude-module", "cv2"
        ])

    try:
        result = subprocess.run(base_args, check=True, capture_output=True, text=True)
        print("✅ PyInstaller build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def build_nuitka(source_file="optimized_main.py"):
    """Build executable using Nuitka (fastest runtime performance)"""
    print("🚀 Building with Nuitka (maximum performance)...")

    args = [
        "python", "-m", "nuitka",
        "--onefile",
        "--windows-disable-console",
        "--enable-plugin=tk-inter",
        "--include-package=whisper",
        "--include-package=torch",
        "--include-package=torchaudio",
        "--include-package=tkinterdnd2",
        "--output-filename=GreekDrop-Ultra.exe",
        "--remove-output",
        source_file
    ]

    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print("✅ Nuitka build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def get_upx_path():
    """Try to find UPX executable path"""
    possible_paths = [
        "upx",
        "C:\\upx\\upx.exe",
        "/usr/bin/upx",
        "/usr/local/bin/upx"
    ]

    for path in possible_paths:
        if shutil.which(path):
            return os.path.dirname(path)
    return None

def create_installer_script():
    """Create a simple installer script"""
    installer_content = '''
@echo off
echo ========================================
echo GreekDrop Optimized Installation
echo ========================================
echo.

REM Create application directory
if not exist "%USERPROFILE%\\GreekDrop" mkdir "%USERPROFILE%\\GreekDrop"

REM Copy executable
copy "GreekDrop-Optimized.exe" "%USERPROFILE%\\GreekDrop\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\\Desktop\\GreekDrop.lnk'); $s.TargetPath = '%USERPROFILE%\\GreekDrop\\GreekDrop-Optimized.exe'; $s.Save()"

REM Create start menu entry
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GreekDrop" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GreekDrop"
powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GreekDrop\\GreekDrop.lnk'); $s.TargetPath = '%USERPROFILE%\\GreekDrop\\GreekDrop-Optimized.exe'; $s.Save()"

echo.
echo ✅ Installation completed!
echo.
echo Application installed to: %USERPROFILE%\\GreekDrop
echo Desktop shortcut created
echo Start menu entry created
echo.
pause
'''

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
        print("Please make sure optimized_main.py is in the current directory.")
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
                    size = os.path.getsize(os.path.join("dist", file)) / (1024*1024)
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