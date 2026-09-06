# Pipeline Runners Guide - All Available Scripts

## 🎯 **Overview**

You now have **individual stage runners** for maximum flexibility!

---

## 📋 **Available Runners**

### **1. Full Pipeline Runners**

| Script | Description | When to Use |
|--------|-------------|-------------|
| `run_pipeline.py` | Standard full pipeline | Production run |
| `run_adaptive_pipeline.py` | Auto-selects Pandas/Spark | Adaptive execution |

### **2. Individual Stage Runners**

| Script | Stage | Description |
|--------|-------|-------------|
| `run_ingestion.py` | 1. Ingestion | Download raw data |
| `run_transformation.py` | 2. Transformation | Clean data (Pandas/Spark) |
| `run_enrichment.py` | 3. Enrichment | Add temperature data |
| *(future)* `run_modeling.py` | 4. Modeling | Build Star Schema |
| *(future)* `run_analytics.py` | 5. Analytics | Run SQL queries |

### **3. Windows-Specific Runners**

| Script | Description |
|--------|-------------|
| `run_transformation_spark_windows.py` | Spark without errors |
| `*.bat` files | Double-click versions |

### **4. Setup & Testing**

| Script | Purpose |
|--------|----------|
| `setup_spark_windows.py` | Install Hadoop winutils |
| `test_spark.py` | Verify Spark works |
| `test_transformation.py` | Test transformation |
| `test_download.py` | Test data sources |

---

## 🚀 **How to Use**

### **Option 1: Run Full Pipeline**

```bash
cd C:\Users\sudthaku3\AI\worldcup_pipeline
venv\Scripts\activate

# Adaptive (auto-selects engine)
python run_adaptive_pipeline.py

# Or standard
python run_pipeline.py
```

---

### **Option 2: Run Stage by Stage**

```bash
cd C:\Users\sudthaku3\AI\worldcup_pipeline
venv\Scripts\activate

# Stage 1: Download data
python run_ingestion.py

# Stage 2: Clean data
python run_transformation.py --engine pandas

# Stage 3: Enrich data
python run_enrichment.py

# Stage 4: Build model (future)
python run_modeling.py

# Stage 5: Run analytics (future)
python run_analytics.py
```

---

### **Option 3: Double-Click (Windows)**

```
Double-click any .bat file:
  - run.bat                  (Full adaptive pipeline)
  - run_ingestion.bat        (Download only)
  - run_transformation.bat   (Clean only)
  - run_enrichment.bat       (Enrich only)
```

---

## 📊 **Detailed Stage Runners**

### **1. Ingestion Runner**

**File**: `run_ingestion.py`

**What it does:**
- Downloads World Cup data (Excel + CSV)
- Downloads temperature data (ZIP → CSV)
- Validates downloads
- Cleans up temporary files

**Usage:**
```bash
python run_ingestion.py
```

**Output:**
```
data/raw/
├── WorldCupMatches.xlsx    ✅
├── WorldCupMatches.csv     ✅
└── temperature.csv          ✅
```

**When to use:**
- Need fresh data
- Data sources updated
- Testing download logic

---

### **2. Transformation Runner**

**File**: `run_transformation.py`

**What it does:**
- Reads raw data
- Cleans and validates
- Standardizes column names
- Saves to Parquet

**Usage:**
```bash
# Auto-detect engine
python run_transformation.py

# Force Pandas
python run_transformation.py --engine pandas

# Force Spark
python run_transformation.py --engine spark
```

**Output:**
```
data/processed/
├── worldcup_cleaned.parquet     ✅
└── temperature_cleaned.parquet   ✅
```

**When to use:**
- After ingestion
- Testing cleaning logic
- Comparing Pandas vs Spark
- Re-processing after schema changes

---

### **3. Enrichment Runner** ✨ NEW!

**File**: `run_enrichment.py`

**What it does:**
- Loads cleaned data
- Matches temperatures to matches
- Enriches with climate data
- Saves enriched dataset

**Usage:**
```bash
python run_enrichment.py
```

**Output:**
```
data/processed/
└── worldcup_enriched.parquet    ✅
```

**Statistics shown:**
```
Enrichment Statistics:
  Total matches: 900
  Matches with temperature: 750
  Match rate: 83.3%

Temperature Statistics:
  Mean: 18.5°C
  Min: -5.2°C
  Max: 35.8°C
```

**When to use:**
- After transformation
- Testing join logic
- Analyzing temperature coverage
- Re-enriching after temperature data updates

---

## 🔄 **Complete Workflow**

### **Full Pipeline (All Stages):**

```bash
# Method 1: One command (adaptive)
python run_adaptive_pipeline.py

# Method 2: Stage by stage
python run_ingestion.py
python run_transformation.py --engine pandas
python run_enrichment.py
# ... future stages
```

### **Selective Re-run:**

```bash
# Only re-download data
python run_ingestion.py

# Only re-clean (data exists)
python run_transformation.py

# Only re-enrich (cleaned data exists)
python run_enrichment.py
```

---

## 📁 **File Dependencies**

### **Ingestion:**
```
Input:  (none - downloads from internet)
Output: data/raw/*.{xlsx,csv}
```

### **Transformation:**
```
Input:  data/raw/*.{xlsx,csv}
Output: data/processed/*_cleaned.parquet
```

### **Enrichment:**
```
Input:  data/processed/*_cleaned.parquet
Output: data/processed/worldcup_enriched.parquet
```

### **Modeling (future):**
```
Input:  data/processed/worldcup_enriched.parquet
Output: data/output/worldcup_analytics.db
```

### **Analytics (future):**
```
Input:  data/output/worldcup_analytics.db
Output: Query results + visualizations
```

---

## ⚡ **Quick Reference**

### **Common Commands:**

```bash
# Fresh start (all stages)
python run_adaptive_pipeline.py

# Just download new data
python run_ingestion.py

# Re-clean with Pandas
python run_transformation.py --engine pandas

# Re-enrich
python run_enrichment.py

# Test Spark setup
python test_spark.py
```

---

## 🎓 **For Interview**

### **How to Explain:**

> *"I designed the pipeline with modular stage runners for maximum flexibility:*
>
> **Full Pipeline**:
> - *run_adaptive_pipeline.py - Auto-selects optimal engine*
>
> **Individual Stages**:
> - *run_ingestion.py - Downloads raw data*
> - *run_transformation.py - Cleans with Pandas or Spark*
> - *run_enrichment.py - Adds temperature data*
>
> **Benefits**:
> 1. *Selective re-execution (only re-run failed stages)*
> 2. *Testing individual components*
> 3. *Faster development iterations*
> 4. *Easy debugging (isolate issues)*
> 5. *Production flexibility (skip stages if data exists)*
>
> *This demonstrates:*
> - *Modular design principles*
> - *Separation of concerns*
> - *Developer experience optimization*
> - *Production-ready architecture"*

---

## 📊 **Stage Runners Comparison**

| Runner | Time | Output | Can Skip? |
|--------|------|--------|----------|
| **Ingestion** | ~5 sec | Raw files | If files exist ✅ |
| **Transformation** | 3-10 sec | Cleaned parquet | If cleaned exists ✅ |
| **Enrichment** | ~2 sec | Enriched parquet | If enriched exists ✅ |
| **Modeling** | ~1 sec | SQLite DB | If DB exists ✅ |
| **Analytics** | ~1 sec | Query results | Always run |

**Total**: ~10-20 seconds for full pipeline

---

## ✅ **Checklist: When to Use Each Runner**

### **Use Full Pipeline When:**
- [ ] First time setup
- [ ] Complete refresh needed
- [ ] Demonstrating end-to-end flow
- [ ] Production deployment

### **Use Ingestion When:**
- [ ] Data sources updated
- [ ] Need fresh download
- [ ] Testing download logic

### **Use Transformation When:**
- [ ] Changed cleaning logic
- [ ] Testing Pandas vs Spark
- [ ] Schema changes
- [ ] Data quality issues

### **Use Enrichment When:**
- [ ] Temperature data updated
- [ ] Changed matching logic
- [ ] Testing join strategies
- [ ] Analyzing coverage

---

## 🚀 **Try It Now**

### **Complete Example:**

```bash
# Navigate to project
cd C:\Users\sudthaku3\AI\worldcup_pipeline

# Activate environment
venv\Scripts\activate

# Run each stage
echo "Stage 1: Ingestion"
python run_ingestion.py

echo "Stage 2: Transformation"
python run_transformation.py --engine pandas

echo "Stage 3: Enrichment"
python run_enrichment.py

echo "Done!"
```

---

## 📚 **Related Documentation**

- [HOW_TO_RUN.md](../HOW_TO_RUN.md) - How to run the pipeline
- [TRANSFORMATION_FIXES.md](TRANSFORMATION_FIXES.md) - Column mappings
- [WINDOWS_SPARK_SETUP.md](WINDOWS_SPARK_SETUP.md) - Spark setup
- [ADAPTIVE_ARCHITECTURE.md](ADAPTIVE_ARCHITECTURE.md) - Engine selection

---

**Last Updated**: 2026-09-02  
**New Runners**: run_enrichment.py ✅  
**Status**: Complete  
**Version**: 11.0
