#!/usr/bin/env python
"""
Automated PySpark Windows Setup

Downloads and configures Hadoop winutils for PySpark on Windows.
Sets up HADOOP_HOME and PATH automatically.
"""

import os
import sys
import urllib.request
import shutil
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def download_file(url, destination):
    """Download file with progress."""
    try:
        print(f"Downloading: {url}")
        print(f"To: {destination}")
        
        urllib.request.urlretrieve(url, destination)
        
        if destination.exists():
            size_kb = destination.stat().st_size / 1024
            print(f"✓ Downloaded successfully ({size_kb:.1f} KB)")
            return True
        else:
            print("✗ Download failed")
            return False
    except Exception as e:
        print(f"✗ Error downloading: {e}")
        return False


def setup_hadoop_home():
    """Set up Hadoop directory and download winutils."""
    print_header("PYSPARK WINDOWS SETUP - HADOOP WINUTILS")
    
    # Define paths
    hadoop_home = Path("C:/hadoop")
    hadoop_bin = hadoop_home / "bin"
    
    print("Step 1: Creating Hadoop directory...")
    try:
        hadoop_bin.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {hadoop_bin}")
    except Exception as e:
        print(f"✗ Error creating directory: {e}")
        print("\nTry running as Administrator:")
        print("  Right-click PowerShell → Run as Administrator")
        print("  Then run this script again")
        return False
    
    print("\nStep 2: Downloading winutils.exe...")
    
    # Winutils download URLs (try multiple sources)
    winutils_urls = [
        "https://github.com/cdarlint/winutils/raw/master/hadoop-3.3.1/bin/winutils.exe",
        "https://github.com/steveloughran/winutils/raw/master/hadoop-3.0.0/bin/winutils.exe",
        "https://github.com/kontext-tech/winutils/raw/master/hadoop-3.3.1/bin/winutils.exe"
    ]
    
    hadoop_dll_urls = [
        "https://github.com/cdarlint/winutils/raw/master/hadoop-3.3.1/bin/hadoop.dll",
        "https://github.com/steveloughran/winutils/raw/master/hadoop-3.0.0/bin/hadoop.dll",
        "https://github.com/kontext-tech/winutils/raw/master/hadoop-3.3.1/bin/hadoop.dll"
    ]
    
    winutils_path = hadoop_bin / "winutils.exe"
    hadoop_dll_path = hadoop_bin / "hadoop.dll"
    
    # Download winutils.exe
    winutils_success = False
    for url in winutils_urls:
        print(f"\nTrying: {url}")
        if download_file(url, winutils_path):
            winutils_success = True
            break
    
    if not winutils_success:
        print("\n✗ Failed to download winutils.exe from all sources")
        print("\nManual download:")
        print("1. Go to: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.1/bin")
        print("2. Download winutils.exe")
        print(f"3. Save to: {winutils_path}")
        return False
    
    # Download hadoop.dll
    print("\nStep 3: Downloading hadoop.dll...")
    hadoop_dll_success = False
    for url in hadoop_dll_urls:
        print(f"\nTrying: {url}")
        if download_file(url, hadoop_dll_path):
            hadoop_dll_success = True
            break
    
    if not hadoop_dll_success:
        print("\n✗ Failed to download hadoop.dll from all sources")
        print("\nManual download:")
        print("1. Go to: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.1/bin")
        print("2. Download hadoop.dll")
        print(f"3. Save to: {hadoop_dll_path}")
        return False
    
    print("\nStep 4: Setting environment variables...")
    
    # Set environment variables for current session
    os.environ['HADOOP_HOME'] = str(hadoop_home)
    os.environ['PATH'] = os.environ.get('PATH', '') + f";{hadoop_bin}"
    
    print(f"✓ HADOOP_HOME = {hadoop_home}")
    print(f"✓ Added to PATH: {hadoop_bin}")
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANT: Set permanent environment variables")
    print("="*70)
    print("\nThe variables are set for THIS SESSION only.")
    print("\nFor PERMANENT setup:")
    print("\n1. Open 'System Properties' → 'Environment Variables'")
    print("2. Under 'System Variables', click 'New':")
    print(f"   - Variable name: HADOOP_HOME")
    print(f"   - Variable value: C:\\hadoop")
    print("3. Edit 'Path' variable, add:")
    print(f"   - C:\\hadoop\\bin")
    print("4. Click OK and restart terminal")
    print("\nOR run this PowerShell command as Administrator:")
    print("")
    print("[System.Environment]::SetEnvironmentVariable('HADOOP_HOME', 'C:\\hadoop', 'Machine')")
    print("[System.Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';C:\\hadoop\\bin', 'Machine')")
    print("")
    
    return True


def verify_setup():
    """Verify Spark installation."""
    print("\nStep 5: Verifying setup...\n")
    
    # Check HADOOP_HOME
    hadoop_home = os.environ.get('HADOOP_HOME')
    if hadoop_home:
        print(f"✓ HADOOP_HOME = {hadoop_home}")
    else:
        print("✗ HADOOP_HOME not set")
        return False
    
    # Check winutils
    winutils_path = Path(hadoop_home) / "bin" / "winutils.exe"
    if winutils_path.exists():
        print(f"✓ winutils.exe exists")
    else:
        print(f"✗ winutils.exe not found at {winutils_path}")
        return False
    
    # Check hadoop.dll
    hadoop_dll_path = Path(hadoop_home) / "bin" / "hadoop.dll"
    if hadoop_dll_path.exists():
        print(f"✓ hadoop.dll exists")
    else:
        print(f"✗ hadoop.dll not found at {hadoop_dll_path}")
        return False
    
    # Test PySpark import
    print("\nTesting PySpark...")
    try:
        from pyspark.sql import SparkSession
        print("✓ PySpark imported successfully")
        
        # Try to create Spark session
        print("Creating Spark session...")
        spark = SparkSession.builder \
            .master('local[*]') \
            .appName('TestSpark') \
            .getOrCreate()
        
        print(f"✓ Spark session created (version {spark.version})")
        spark.stop()
        print("✓ Spark works!")
        
        return True
        
    except Exception as e:
        print(f"✗ PySpark test failed: {e}")
        return False


def main():
    """Main setup function."""
    print_header("AUTOMATED PYSPARK SETUP FOR WINDOWS")
    
    print("This script will:")
    print("  1. Create C:\\hadoop\\bin directory")
    print("  2. Download winutils.exe and hadoop.dll")
    print("  3. Set HADOOP_HOME environment variable")
    print("  4. Add Hadoop bin to PATH")
    print("  5. Test PySpark")
    
    input("\nPress Enter to continue...")
    
    # Setup Hadoop
    if not setup_hadoop_home():
        print("\n✗ Setup failed")
        return False
    
    # Verify
    if not verify_setup():
        print("\n✗ Verification failed")
        return False
    
    print_header("SETUP COMPLETE!")
    
    print("✅ PySpark is ready to use!\n")
    print("Next steps:")
    print("\n1. Close and reopen terminal (for permanent env vars)")
    print("2. Test transformation:")
    print("   python run_transformation.py --engine spark")
    print("\n3. Or test directly:")
    print("   python -c 'from pyspark.sql import SparkSession; spark = SparkSession.builder.getOrCreate(); print(\"Spark works!\"); spark.stop()'")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
