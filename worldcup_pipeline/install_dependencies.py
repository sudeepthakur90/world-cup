#!/usr/bin/env python
"""
Dependency Installation Script

Installs required packages with progress tracking and error handling.
Works on Windows, Linux, and Mac.
"""

import subprocess
import sys
from pathlib import Path

# Core dependencies in order of installation
DEPENDENCIES = [
    ("pip", "pip", True),  # Upgrade pip first
    ("numpy", "numpy", False),
    ("pandas", "pandas", False),
    ("openpyxl", "openpyxl", False),
    ("pyarrow", "pyarrow", False),
    ("requests", "requests", False),
    ("sqlalchemy", "sqlalchemy", False),
    ("python-dotenv", "python-dotenv", False),
    ("psutil", "psutil", False),
]


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def install_package(name, package, upgrade=False):
    """
    Install a single package.
    
    Args:
        name: Display name
        package: Package name for pip
        upgrade: Whether to upgrade
    
    Returns:
        bool: Success status
    """
    try:
        if upgrade:
            print(f"Upgrading {name}...")
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package]
        else:
            print(f"Installing {name}...")
            cmd = [sys.executable, "-m", "pip", "install", package]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✓ {name} installed successfully")
            return True
        else:
            print(f"✗ Failed to install {name}")
            print(f"Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {name} installation timed out")
        return False
    except Exception as e:
        print(f"✗ Error installing {name}: {e}")
        return False


def verify_installation():
    """
    Verify all packages can be imported.
    
    Returns:
        bool: All imports successful
    """
    print_header("Verifying Installation")
    
    packages = [
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("openpyxl", "OpenPyXL"),
        ("requests", "Requests"),
        ("sqlalchemy", "SQLAlchemy"),
    ]
    
    all_ok = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"✓ {name} can be imported")
        except ImportError:
            print(f"✗ {name} cannot be imported")
            all_ok = False
    
    return all_ok


def main():
    """
    Main installation process.
    """
    print_header("World Cup Pipeline - Dependency Installation")
    
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Executable: {sys.executable}")
    
    # Install packages
    print_header("Installing Dependencies")
    
    failed = []
    for idx, (name, package, upgrade) in enumerate(DEPENDENCIES, 1):
        print(f"\n[{idx}/{len(DEPENDENCIES)}] ", end="")
        success = install_package(name, package, upgrade)
        if not success:
            failed.append(name)
        print()
    
    # Verify
    if verify_installation():
        print_header("✓ Installation Complete!")
        print("\nYou can now run:")
        print("  python test_download.py")
        print("  python run_ingestion.py")
        print("  python run_adaptive_pipeline.py")
        return True
    else:
        print_header("✗ Installation Issues Detected")
        if failed:
            print("\nFailed packages:")
            for pkg in failed:
                print(f"  - {pkg}")
        print("\nPlease check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
