#!/usr/bin/env python3
"""
Bundle the Python backend for Tauri sidecar deployment.

This script uses PyInstaller to create a standalone executable
that can be shipped with the Tauri application.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def create_executable():
    """Create a standalone executable using PyInstaller."""

    # Determine output name based on platform
    system = platform.system()
    if system == "Windows":
        output_name = "backend.exe"
    else:
        output_name = "backend"

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", output_name,
        "--distpath", "../src-tauri/binaries",
        "--workpath", "build",
        "--specpath", "build",
        "--noconfirm",
        "--clean",
        "--console",  # Keep console for debugging
        "--hidden-import", "lancedb",
        "--hidden-import", "sentence_transformers",
        "--hidden-import", "torch",
        "--hidden-import", "PyMuPDF",
        "--hidden-import", "PIL",
        "--hidden-import", "httpx",
        "--collect-data", "sentence_transformers",
        "--collect-data", "lancedb",
        "main.py"
    ]

    print(f"Building executable for {system}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    print(f"Successfully created {output_name}")

    # Set executable permissions on Unix-like systems
    if system != "Windows":
        exe_path = Path(f"../src-tauri/binaries/{output_name}")
        exe_path.chmod(0o755)

def install_pyinstaller():
    """Install PyInstaller if not present."""
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

if __name__ == "__main__":
    install_pyinstaller()
    create_executable()