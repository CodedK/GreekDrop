"""
Hardware detection and system diagnostics for GreekDrop.
Centralized runtime hardware status checking.
"""

import sys
from typing import Dict, Any


def get_runtime_hardware_status() -> Dict[str, Any]:
    """
    Get runtime hardware status including GPU availability.

    Returns:
        Dict with hardware status information:
        - gpu: bool - CUDA GPU availability
        - torch: bool - PyTorch installation
        - cuda: bool - CUDA toolkit availability
        - device: str - Primary compute device
    """
    status = {"gpu": False, "torch": False, "cuda": False, "device": "CPU"}

    try:
        import torch

        status["torch"] = True

        if torch.cuda.is_available():
            status["gpu"] = True
            status["cuda"] = True
            status["device"] = "GPU"

            # Additional GPU info for debugging
            status["gpu_name"] = torch.cuda.get_device_name(0)
            status["gpu_count"] = torch.cuda.device_count()
        else:
            status["device"] = "CPU"

    except ImportError:
        status["torch"] = False

    return status


def print_hardware_diagnostics(debug_mode: bool = False) -> None:
    """Print structured hardware diagnostics."""
    hardware = get_runtime_hardware_status()

    print("[GreekDrop] Hardware Status")
    print("─" * 30)
    print(f"- PyTorch:      {'AVAILABLE' if hardware['torch'] else 'NOT INSTALLED'}")
    print(f"- CUDA Support: {'AVAILABLE' if hardware['cuda'] else 'UNAVAILABLE'}")
    print(f"- Primary GPU:  {'AVAILABLE' if hardware['gpu'] else 'UNAVAILABLE'}")
    print(f"- Compute Mode: {hardware['device']}")

    if debug_mode and hardware["gpu"]:
        print(f"- GPU Device:   {hardware.get('gpu_name', 'Unknown')}")
        print(f"- GPU Count:    {hardware.get('gpu_count', 0)}")
        print(f"- Python:       {sys.version.split()[0]}")


def is_gpu_available() -> bool:
    """Simple runtime GPU availability check."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def get_active_compute_device() -> str:
    """Get the currently active compute device (CPU or GPU)."""
    try:
        import torch

        if torch.cuda.is_available():
            return "GPU"
        else:
            return "CPU"
    except ImportError:
        return "CPU"


def get_gpu_device_name() -> str:
    """Get the name of the GPU device if available."""
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        else:
            return "No GPU detected"
    except ImportError:
        return "PyTorch not available"
