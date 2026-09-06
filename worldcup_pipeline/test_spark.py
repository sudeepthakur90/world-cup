#!/usr/bin/env python
"""
Quick PySpark Test Script

Tests if PySpark is properly configured on Windows.
"""

import os
import sys

print("="*70)
print("  PYSPARK WINDOWS TEST")
print("="*70)

print("\n1. Checking environment variables...\n")

# Check HADOOP_HOME
hadoop_home = os.environ.get('HADOOP_HOME')
if hadoop_home:
    print(f"✓ HADOOP_HOME = {hadoop_home}")
else:
    print("✗ HADOOP_HOME not set")
    print("\nFix: Run setup script first:")
    print("  python setup_spark_windows.py")
    sys.exit(1)

# Check if winutils exists
from pathlib import Path
winutils_path = Path(hadoop_home) / "bin" / "winutils.exe"
if winutils_path.exists():
    print(f"✓ winutils.exe found at {winutils_path}")
else:
    print(f"✗ winutils.exe not found at {winutils_path}")
    print("\nFix: Run setup script first:")
    print("  python setup_spark_windows.py")
    sys.exit(1)

print("\n2. Testing PySpark import...\n")

try:
    from pyspark.sql import SparkSession
    from pyspark import __version__
    print(f"✓ PySpark imported successfully (version {__version__})")
except ImportError as e:
    print(f"✗ PySpark not installed: {e}")
    print("\nFix: Install PySpark:")
    print("  pip install pyspark")
    sys.exit(1)

print("\n3. Creating Spark session...\n")

try:
    spark = SparkSession.builder \
        .master('local[*]') \
        .appName('PySpark-Test') \
        .config('spark.driver.memory', '2g') \
        .getOrCreate()
    
    print(f"✓ Spark session created successfully")
    print(f"  Spark version: {spark.version}")
    print(f"  Master: {spark.sparkContext.master}")
    print(f"  App name: {spark.sparkContext.appName}")
    
    print("\n4. Testing DataFrame operations...\n")
    
    # Create test DataFrame
    data = [
        ("France", 4, "Mexico", 1),
        ("Brazil", 2, "Germany", 1),
        ("Argentina", 3, "Uruguay", 0)
    ]
    columns = ["home_team", "home_goals", "away_team", "away_goals"]
    
    df = spark.createDataFrame(data, columns)
    
    print("✓ Test DataFrame created:")
    df.show()
    
    print(f"\n✓ DataFrame operations work!")
    print(f"  Rows: {df.count()}")
    print(f"  Columns: {len(df.columns)}")
    
    # Stop Spark
    spark.stop()
    print("\n✓ Spark session stopped")
    
    print("\n" + "="*70)
    print("✅ PYSPARK IS WORKING CORRECTLY!")
    print("="*70)
    
    print("\nYou can now run:")
    print("  python run_transformation.py --engine spark")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n✗ Spark test failed: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    
    print("\n" + "="*70)
    print("TROUBLESHOOTING:")
    print("="*70)
    print("\n1. Make sure HADOOP_HOME is set:")
    print("   echo %HADOOP_HOME%")
    print("\n2. Verify winutils.exe exists:")
    print("   dir C:\\hadoop\\bin\\winutils.exe")
    print("\n3. Run setup script:")
    print("   python setup_spark_windows.py")
    print("\n4. Restart terminal after setup")
    
    sys.exit(1)
