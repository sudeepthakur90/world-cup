#!/usr/bin/env python
"""
Dependency Installation Script

Installs required packages from requirements.txt with progress tracking.
Works on Windows, Linux, and Mac.
"""

import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def upgrade_pip():
    """
    Upgrade pip to latest version.
    
    Returns:
        bool: Success status
    """
    try:
        print("Upgrading pip...")
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ pip upgraded successfully\n")
            return True
        else:
            print(f"✗ Failed to upgrade pip: {result.stderr[:200]}\n")
            return False
    except Exception as e:
        print(f"✗ Error upgrading pip: {e}\n")
        return False


def install_requirements():
    """
    Install all packages from requirements.txt.
    
    Returns:
        bool: Success status
    """
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"✗ requirements.txt not found at: {requirements_file}")
        return False
    
    try:
        print(f"Installing from {requirements_file.name}...\n")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        
        result = subprocess.run(
            cmd,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print("\n✓ All packages installed successfully")
            return True
        else:
            print(f"\n✗ Installation failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ Installation timed out")
        return False
    except Exception as e:
        print(f"\n✗ Error during installation: {e}")
        return False


def verify_installation():
    """
    Verify all packages can be imported.
    
    Returns:
        bool: All imports successful
    """
    print_header("Step 3: Verifying Installation")
    
    packages = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("openpyxl", "OpenPyXL"),
        ("pyarrow", "PyArrow"),
        ("requests", "Requests"),
        ("sqlalchemy", "SQLAlchemy"),
        ("dotenv", "Python-dotenv"),
        ("psutil", "PSUtil"),
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
    
    # Step 1: Upgrade pip
    print_header("Step 1: Upgrading pip")
    upgrade_pip()
    
    # Step 2: Install from requirements.txt
    print_header("Step 2: Installing Dependencies")
    if not install_requirements():
        print_header("✗ Installation Failed")
        print("\nPlease check the errors above.")
        return False
    
    # Step 3: Verify
    if verify_installation():
        print_header("✓ Installation Complete!")
        print("\nYou can now run:")
        print("  run_adaptive_pipeline.bat")
        print("  run_ingestion.bat")
        print("  run_analytics.bat")
        print("\nOr run Python scripts directly:")
        print("  python run_adaptive_pipeline.py")
        print("  python test_download.py")
        return True
    else:
        print_header("✗ Installation Issues Detected")
        print("\nSome packages could not be imported.")
        print("Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
