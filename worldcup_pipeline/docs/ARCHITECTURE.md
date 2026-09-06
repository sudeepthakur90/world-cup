# World Cup Data Pipeline - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)
7. [Scalability Considerations](#scalability-considerations)

---

## System Overview

This data engineering pipeline implements a complete ETL/ELT workflow that:
- **Ingests** World Cup match data (1930-2014) and historical temperature data
- **Transforms** raw data into clean, standardized formats
- **Enriches** match data with temperature information based on date and location
- **Models** data using dimensional modeling (Star Schema)
- **Exposes** analytics-ready datasets for BI consumption

### Key Objectives
- Provide reliable, reproducible data pipeline
- Enable temperature impact analysis on match outcomes
- Support BI dashboards with pre-built queries
- Ensure data quality and AI-readiness

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  • World Cup Results (Excel)                                            │
│    https://public.tableau.com/...                                       │
│                                                                          │
│  • Temperature Data (CSV/ZIP)                                           │
│    https://ourworldindata.org/...                                       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Component: DataDownloader                                              │
│  • HTTP requests with retry logic                                       │
│  • ZIP extraction and file handling                                     │
│  • Data validation on download                                          │
│  Output: Raw files → data/raw/                                          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   TRANSFORMATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Component: DataCleaner                                                 │
│  • Column standardization                                               │
│  • Data type conversion                                                 │
│  • Missing value handling                                               │
│  • Duplicate removal                                                    │
│  • Country name standardization                                         │
│  • Outlier detection and filtering                                      │
│  Output: Cleaned data → data/processed/ (Parquet)                       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Component: DataEnricher                                                │
│  • Temperature data preparation                                         │
│  • Date/location matching logic                                         │
│  • Join strategies (exact + fuzzy)                                      │
│  • Temperature categorization                                           │
│  Output: Enriched dataset → data/processed/                             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA MODEL LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Component: StarSchemaBuilder                                           │
│                                                                          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │  dim_date    │      │  dim_team    │      │ dim_location │         │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘         │
│         │                     │                      │                  │
│         │                     ▼                      │                  │
│         │          ┌─────────────────────┐           │                  │
│         └─────────▶│   fact_matches      │◀──────────┘                  │
│                    │  (Grain: Match)     │                              │
│                    └──────────┬──────────┘                              │
│                               │                                          │
│                               ▼                                          │
│                    ┌──────────────────┐                                 │
│                    │ dim_temperature  │                                 │
│                    └──────────────────┘                                 │
│                                                                          │
│  Output: Star Schema → SQLite/PostgreSQL + Parquet files                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ANALYTICS LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Component: AnalyticsEngine                                             │
│  • Pre-built SQL queries                                                │
│  • Temperature impact analysis                                          │
│  • Historical trend analysis                                            │
│  • Geographic insights                                                  │
│  • Team performance metrics                                             │
│  Output: CSV reports + SQL views                                        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   BI / ANALYTICS TOOLS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  • Tableau / Power BI                                                   │
│  • SQL Clients                                                          │
│  • Jupyter Notebooks                                                    │
│  • ML/AI Platforms                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Ingestion Layer (`src/ingestion/`)

**Purpose**: Reliable data acquisition from external sources

**Components**:
- `DataDownloader`: HTTP client with retry logic
- Supports Excel (.xlsx) and ZIP files
- Streaming downloads for large files
- Automatic extraction and file management

**Error Handling**:
- Exponential backoff retry strategy
- Network timeout handling
- File validation post-download
- Graceful failure with detailed logging

---

### 2. Transformation Layer (`src/transformation/`)

**Purpose**: Convert raw data into clean, analysis-ready format

**DataCleaner Operations**:

1. **Column Standardization**
   - Lowercase, underscore-separated names
   - Consistent naming conventions

2. **Data Type Conversion**
   - Date parsing with error handling
   - Numeric conversion for scores
   - String cleaning (trim, title case)

3. **Data Quality**
   - Duplicate detection and removal
   - Outlier filtering (temperature range: -50 to 60°C)
   - Missing value analysis
   - Country name normalization

4. **Business Rules**
   - Year range filter (1930-2014)
   - Valid score ranges (non-negative)
   - Attendance data cleaning

---

### 3. Enrichment Layer (`src/enrichment/`)

**Purpose**: Enhance match data with temperature context

**Enrichment Strategy**:

1. **Primary Join**: Country + Year + Month
2. **Fallback Join**: Country + Year (annual average)
3. **Categorization**: Cold / Moderate / Warm / Hot

**Matching Logic**:
```python
Join Keys:
- Country (standardized names)
- Year (extracted from match date)
- Month (if available in both datasets)

Temperature Categories:
- Cold: < 10°C
- Moderate: 10-20°C
- Warm: 20-30°C
- Hot: > 30°C
```

---

### 4. Data Model Layer (`src/models/`)

**Star Schema Design**

#### Fact Table: `fact_matches`
**Grain**: One record per match

| Column | Type | Description |
|--------|------|-------------|
| match_id | PK | Unique match identifier |
| date_id | FK | Link to date dimension |
| location_id | FK | Link to location dimension |
| home_team_id | FK | Link to team dimension |
| away_team_id | FK | Link to team dimension |
| temperature_id | FK | Link to temperature dimension |
| home_score | Measure | Goals scored by home team |
| away_score | Measure | Goals scored by away team |
| attendance | Measure | Match attendance |
| stage | Attribute | Tournament stage |

#### Dimension Tables

**dim_date**: Date attributes for temporal analysis
- Supports year, month, quarter, day of week filtering
- Enables trend analysis over time

**dim_team**: Team master data
- Includes confederation mapping
- Enables team performance analysis

**dim_location**: Geographic information
- City and country details
- Supports geographic analysis
- Ready for geocoding (lat/long fields)

**dim_temperature**: Temperature context
- Monthly/yearly averages
- Pre-categorized for easy filtering
- Enables climate analysis

**Design Benefits**:
- ✅ Optimized for BI queries (denormalized)
- ✅ Slowly Changing Dimensions (SCD Type 1)
- ✅ Additive measures (scores, attendance)
- ✅ Conformed dimensions (date, location)

---

### 5. Analytics Layer (`src/analytics/`)

**Pre-built Queries**:

1. **Temperature Impact**
   - Goals by temperature range
   - Home advantage analysis by climate
   - Scoring patterns correlation

2. **Historical Trends**
   - Tournament evolution over decades
   - Seasonal patterns
   - Attendance trends

3. **Geographic Analysis**
   - Performance by host country
   - Climate zone comparisons
   - Continental trends

4. **Team Analytics**
   - All-time performance rankings
   - Head-to-head records
   - Goal scoring efficiency

---

## Data Flow

### End-to-End Pipeline Flow

```
1. INGEST
   ├─ Download World Cup Excel
   ├─ Download & Extract Temperature ZIP
   └─ Store in data/raw/

2. TRANSFORM
   ├─ Load raw files
   ├─ Clean & standardize
   ├─ Validate data quality
   └─ Save to data/processed/ (Parquet)

3. ENRICH
   ├─ Load cleaned datasets
   ├─ Prepare temperature data (aggregations)
   ├─ Join on country/year/month
   ├─ Categorize temperatures
   └─ Save enriched data

4. MODEL
   ├─ Build dimension tables
   ├─ Build fact table with FK relationships
   ├─ Save to database (SQLite/PostgreSQL)
   └─ Export to Parquet files

5. ANALYZE
   ├─ Execute SQL queries
   ├─ Generate CSV reports
   └─ Export for BI tools
```

---

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|----------|
| Language | Python 3.9+ | Primary development language |
| Data Processing | Pandas | Data manipulation and transformation |
| Database | SQLAlchemy | Database abstraction layer |
| Storage | SQLite / PostgreSQL | Relational data storage |
| File Format | Parquet | Efficient columnar storage |
| Validation | Pydantic | Data validation |
| Logging | Python logging | Centralized logging |
| Configuration | python-dotenv | Environment management |

### Libraries

**Data Processing**:
- `pandas`: DataFrame operations
- `numpy`: Numerical operations
- `pyarrow`: Parquet file handling

**Database**:
- `sqlalchemy`: ORM and database abstraction
- `psycopg2`: PostgreSQL driver

**HTTP & Files**:
- `requests`: HTTP client
- `openpyxl`: Excel file reading

**Quality & Testing**:
- `pytest`: Unit testing
- `mypy`: Type checking
- `black`: Code formatting

---

## Design Decisions

### 1. **Why Star Schema?**

**Rationale**:
- Optimized for analytical queries (OLAP)
- Simple for BI tools to understand
- Fast aggregations and joins
- Intuitive business logic representation

**Alternatives Considered**:
- Snowflake Schema: Rejected (over-normalization)
- Data Vault: Rejected (too complex for use case)

---

### 2. **Why Parquet Files?**

**Benefits**:
- Columnar format → fast analytical queries
- Efficient compression
- Type preservation
- Compatible with Spark, Pandas, BI tools

---

### 3. **Why Modular Architecture?**

**Benefits**:
- Each stage can run independently
- Easy to test individual components
- Facilitates debugging
- Supports incremental processing

---

### 4. **Temperature Enrichment Strategy**

**Challenge**: Temperature data may not have exact date matches

**Solution**:
1. Try exact match (country + year + month)
2. Fallback to year average if no monthly data
3. Mark unmatched records for investigation

---

## Scalability Considerations

### Current Scale
- **Matches**: ~1000 records (1930-2014)
- **Temperature**: ~100K records (monthly data)
- **Processing Time**: < 5 minutes end-to-end

### Future Scaling Strategies

#### For 10x Data Volume
- ✅ Current architecture supports (Pandas handles millions)
- Enable chunked processing (configurable chunk size)
- Use Parquet partitioning by year

#### For 100x Data Volume
- Migrate to PySpark for distributed processing
- Use cloud storage (S3, GCS)
- Implement data partitioning strategy

#### For Real-time Requirements
- Add streaming layer (Kafka, Kinesis)
- Implement incremental updates
- Use change data capture (CDC)

### Performance Optimizations

1. **Indexing Strategy**
   - Primary keys on all dimensions
   - Foreign keys on fact table
   - Composite indexes on common filters

2. **Query Optimization**
   - Pre-aggregated views for common queries
   - Materialized views for complex joins
   - Query result caching

3. **Storage Optimization**
   - Parquet compression (snappy)
   - Partitioning by year/month
   - Pruning unused columns

---

## Monitoring & Observability

### Logging Strategy
- **File Logs**: Detailed execution trace
- **Console Logs**: User-friendly progress
- **Log Levels**: DEBUG, INFO, WARNING, ERROR

### Data Quality Metrics
- Completeness rate per table
- Duplicate detection
- Outlier counts
- Match success rates (enrichment)

### Pipeline Metrics
- Execution time per stage
- Record counts (input/output)
- Error rates
- Data quality scores

---

## Security Considerations

### Data Protection
- No sensitive data in repository
- Environment variables for credentials
- .gitignore for data files

### Access Control
- Database user permissions
- File system permissions
- API authentication (if applicable)

---

## Deployment

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Production Deployment Options

1. **Scheduled Execution** (Cron, Task Scheduler)
2. **Orchestration** (Apache Airflow, Prefect)
3. **Containerization** (Docker)
4. **Cloud** (AWS Lambda, GCP Cloud Functions)

---

## Maintenance

### Regular Tasks
- Monitor data quality metrics
- Review logs for errors
- Update dependencies
- Refresh source data if updated

### Troubleshooting
- Check logs in `logs/pipeline.log`
- Verify data file existence
- Validate database connectivity
- Review data quality reports