# PySpark Setup for Windows - Complete Guide

## ⚠️ **The Windows Problem**

PySpark requires Hadoop native libraries (winutils) on Windows. Without them, you'll get errors like:

```
java.io.IOException: Could not locate executable null\bin\winutils.exe
```

or

```
ERROR Shell: Failed to locate the winutils binary in the hadoop binary path
```

---

## ✅ **Solution: Install Hadoop Winutils**

### **Method 1: Automated Setup** (Recommended)

We've created a setup script that does everything automatically:

```bash
cd C:\Users\sudthaku3\AI\worldcup_pipeline
venv\Scripts\activate
python setup_spark_windows.py
```

**What it does:**
1. ✅ Downloads Hadoop winutils (3.3.1)
2. ✅ Creates `C:\hadoop\bin` directory
3. ✅ Copies `winutils.exe` and `hadoop.dll`
4. ✅ Sets `HADOOP_HOME` environment variable
5. ✅ Adds to PATH
6. ✅ Verifies installation

---

### **Method 2: Manual Setup**

#### **Step 1: Download Winutils**

Download from one of these sources:

**Option A: GitHub (Recommended)**
```
https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.1/bin
```

Download these files:
- `winutils.exe`
- `hadoop.dll`

**Option B: Alternative Mirror**
```
https://github.com/steveloughran/winutils/tree/master/hadoop-3.0.0/bin
```

#### **Step 2: Create Hadoop Directory**

```bash
# Open PowerShell as Administrator
mkdir C:\hadoop\bin
```

#### **Step 3: Copy Files**

Copy `winutils.exe` and `hadoop.dll` to:
```
C:\hadoop\bin\
```

#### **Step 4: Set Environment Variables**

**Option A: Via PowerShell (Current Session)**
```powershell
$env:HADOOP_HOME = "C:\hadoop"
$env:PATH += ";C:\hadoop\bin"
```

**Option B: Via System Settings (Permanent)**

1. Open **System Properties** → **Advanced** → **Environment Variables**
2. Under **System Variables**, click **New**:
   - Variable name: `HADOOP_HOME`
   - Variable value: `C:\hadoop`
3. Edit **Path** variable, add:
   - `C:\hadoop\bin`
4. Click **OK** and restart terminal

#### **Step 5: Verify Installation**

```bash
# Check HADOOP_HOME
echo %HADOOP_HOME%
# Should show: C:\hadoop

# Check if winutils exists
dir C:\hadoop\bin\winutils.exe

# Test winutils
C:\hadoop\bin\winutils.exe
# Should show usage info
```

---

## 🚀 **Quick Test**

After setup, test PySpark:

```bash
cd C:\Users\sudthaku3\AI\worldcup_pipeline
venv\Scripts\activate
python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.master('local[*]').getOrCreate(); print('Spark works!'); spark.stop()"
```

**Expected output:**
```
Spark works!
```

---

## 🧪 **Test Transformation**

Once Spark is working:

```bash
python run_transformation.py --engine spark
```

---

## 📁 **Expected Directory Structure**

```
C:\hadoop\                    <-- HADOOP_HOME
└── bin\                      <-- Must be in PATH
    ├── winutils.exe          <-- Required
    └── hadoop.dll            <-- Required
```

---

## ⚠️ **Common Issues**

### **Issue 1: Permission Denied**

```
ERROR: Permission denied creating C:\hadoop
```

**Fix**: Run PowerShell as Administrator

---

### **Issue 2: Winutils Not Found**

```
ERROR: Could not locate executable null\bin\winutils.exe
```

**Fix**: 
1. Verify HADOOP_HOME is set:
   ```bash
   echo %HADOOP_HOME%
   ```
2. If not set, add to environment variables
3. Restart terminal

---

### **Issue 3: DLL Not Found**

```
ERROR: hadoop.dll is missing
```

**Fix**: Download both `winutils.exe` AND `hadoop.dll`

---

### **Issue 4: Version Mismatch**

```
WARNING: Hadoop version mismatch
```

**Fix**: Use Hadoop 3.3.1 winutils (matches PySpark 3.5.x)

---

## 🔧 **Troubleshooting Commands**

### **Check Environment:**
```bash
# PowerShell
$env:HADOOP_HOME
$env:PATH

# CMD
echo %HADOOP_HOME%
echo %PATH%
```

### **Verify Files:**
```bash
dir C:\hadoop\bin
# Should show:
# - winutils.exe
# - hadoop.dll
```

### **Test Winutils:**
```bash
C:\hadoop\bin\winutils.exe
# Should print usage info
```

### **Test PySpark:**
```python
import os
print(f"HADOOP_HOME: {os.environ.get('HADOOP_HOME')}")

from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[*]').getOrCreate()
print("Spark version:", spark.version)
spark.stop()
```

---

## 💡 **Alternative: Skip Spark Setup**

If Spark setup is too complex, just use Pandas:

```bash
python run_transformation.py --engine pandas
```

For your current data size (150 KB), Pandas is actually **faster** and requires no Hadoop setup!

---

## 📊 **Comparison: Pandas vs Spark on Windows**

| Aspect | Pandas | PySpark |
|--------|--------|----------|
| **Setup Time** | 0 minutes | 5-10 minutes |
| **Dependencies** | None | Hadoop winutils |
| **For 150 KB** | 3 seconds ⚡ | 10 seconds |
| **For 10 GB** | Won't work ❌ | Works ✅ |
| **Windows Issues** | None | Needs winutils |
| **Production** | Same as dev | Linux: no issues |

**Recommendation**: Use Pandas for current data, Spark for scale.

---

## 🔗 **Download Links**

### **Winutils GitHub Repos:**

1. **Primary (Hadoop 3.3.1)**:
   ```
   https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.1/bin
   ```

2. **Alternative (Hadoop 3.0.0)**:
   ```
   https://github.com/steveloughran/winutils/tree/master/hadoop-3.0.0/bin
   ```

3. **Another Mirror**:
   ```
   https://github.com/kontext-tech/winutils/tree/master/hadoop-3.3.1/bin
   ```

### **Required Files:**
- `winutils.exe` (~120 KB)
- `hadoop.dll` (~30 KB)

---

## ✅ **Quick Setup Checklist**

- [ ] Download `winutils.exe` and `hadoop.dll`
- [ ] Create `C:\hadoop\bin` directory
- [ ] Copy files to `C:\hadoop\bin`
- [ ] Set `HADOOP_HOME=C:\hadoop`
- [ ] Add `C:\hadoop\bin` to PATH
- [ ] Restart terminal
- [ ] Verify with `echo %HADOOP_HOME%`
- [ ] Test with `python test_spark.py`
- [ ] Run `python run_transformation.py --engine spark`

---

## 🎓 **Production Recommendation**

For production deployment:

1. **Use Docker** with official Spark images (no Windows issues)
2. **Use Linux servers** (Hadoop is native)
3. **Use cloud services** (Databricks, EMR, Dataproc)
4. **Keep Pandas option** for small data

**Windows Spark is mainly for:**
- Development
- Testing
- Demos
- Learning

---

**Last Updated**: 2026-09-02  
**Platform**: Windows 10/11  
**Spark Version**: 3.5.x  
**Hadoop Version**: 3.3.1  
**Status**: Complete Guide  
**Version**: 9.0
