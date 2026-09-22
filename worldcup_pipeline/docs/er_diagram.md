# Entity Relationship Diagram - Star Schema

## World Cup Analytics Database Schema

```
                           ┌──────────────────────┐
                           │    dim_date          │
                           ├──────────────────────┤
                           │ PK date_id           │
                           │    full_date         │
                           │    year              │
                           │    month             │
                           │    day               │
                           │    quarter           │
                           │    day_of_week       │
                           │    day_name          │
                           │    month_name        │
                           │    is_weekend        │
                           └──────────┬───────────┘
                                      │
                                      │ 1:N
                                      │
┌──────────────────┐        ┌────────┴─────────────┐        ┌──────────────────────┐
│    dim_team      │        │   fact_matches       │        │    dim_location      │
├──────────────────┤        ├──────────────────────┤        ├──────────────────────┤
│ PK team_id       │◄───N:1─│ FK home_team_id      │─1:N───►│ PK location_id       │
│    team_name     │        │ FK away_team_id      │        │    city              │
│    region        │        │ FK date_id           │        │    country           │
└──────────────────┘        │ FK location_id       │        │    stadium           │
                            │ FK temperature_id    │        └──────────────────────┘
                            │ PK match_id          │
                            │    home_goals        │
                            │    away_goals        │
                            │    round             │
                            │    year              │
                            └──────────┬───────────┘
                                       │
                                       │ 1:N
                                       │
                           ┌───────────┴──────────────────────┐
                           │  dim_temperature                 │
                           ├──────────────────────────────────┤
                           │ PK temperature_id                │
                           │    avg_temperature_celsius       │
                           │    temperature_category          │
                           └──────────────────────────────────┘
```

---

## Table Descriptions

### **Fact Table: fact_matches**
Central fact table containing World Cup match results (836 records).

**Grain:** One row per match

**Measures (Additive):**
- `home_goals` - Goals scored by home team (INTEGER)
- `away_goals` - Goals scored by away team (INTEGER)

**Foreign Keys:**
- `date_id` → dim_date
- `home_team_id` → dim_team
- `away_team_id` → dim_team
- `location_id` → dim_location
- `temperature_id` → dim_temperature (nullable, ~76% populated)

**Attributes:**
- `match_id` - Primary key (INTEGER)
- `round` - Tournament round (TEXT) - e.g., "Group Stage", "Quarter-final"
- `year` - Tournament year (INTEGER) - denormalized for performance

---

### **Dimension Tables:**

#### **1. dim_date** (~330 records)
Temporal dimension with date hierarchies.

**Attributes:**
- `date_id` (PK) - Surrogate key (INTEGER)
- `full_date` - Actual date (DATE) - YYYY-MM-DD format
- `year` - Year (INTEGER) - 1930-2014
- `month` - Month (INTEGER) - 1-12
- `day` - Day (INTEGER) - 1-31
- `quarter` - Quarter (INTEGER) - 1-4
- `day_of_week` - Day number (INTEGER) - 1-7
- `day_name` - Day name (TEXT) - "Monday", "Tuesday", etc.
- `month_name` - Month name (TEXT) - "January", "February", etc.
- `is_weekend` - Weekend flag (BOOLEAN) - True/False

**Purpose:** Enable time-based analysis and aggregations

---

#### **2. dim_team** (~82 records)
Team dimension with regional information.

**Attributes:**
- `team_id` (PK) - Surrogate key (INTEGER)
- `team_name` - Team name (TEXT) - e.g., "Brazil", "Germany", "Argentina"
- `region` - Geographic region (TEXT) - e.g., "South America", "Europe", "Africa"

**Purpose:** Team-level analysis and regional comparisons

**Note:** Uses SCD Type 1 (overwrite on change)

---

#### **3. dim_location** (~151 records)
Geographic dimension for match venues.

**Attributes:**
- `location_id` (PK) - Surrogate key (INTEGER)
- `city` - City name (TEXT) - e.g., "São Paulo", "Paris", "Mexico City"
- `country` - Host country (TEXT) - e.g., "Brazil", "France", "Mexico"
- `stadium` - Stadium name (TEXT) - e.g., "Maracanã", "Estadio Azteca"

**Purpose:** Geographic analysis and venue performance

---

#### **4. dim_temperature** (~26 records)
Temperature dimension with categorization.

**Attributes:**
- `temperature_id` (PK) - Surrogate key (INTEGER)
- `avg_temperature_celsius` - Average temperature (REAL) - in Celsius
- `temperature_category` - Category (TEXT) - "Cold", "Moderate", "Warm", "Hot"

**Temperature Categories:**
- **Cold**: < 10°C
- **Moderate**: 10-20°C
- **Warm**: 20-30°C
- **Hot**: > 30°C

**Purpose:** Climate impact analysis on match performance

**Note:** ~76% of matches have temperature data (635/836 enriched)

---

## Relationships

| From Table | To Table | Cardinality | Type | Description |
|------------|----------|-------------|------|-------------|
| fact_matches | dim_date | N:1 | Many-to-One | Many matches per date |
| fact_matches | dim_team (home) | N:1 | Many-to-One | Many matches per team |
| fact_matches | dim_team (away) | N:1 | Many-to-One | Many matches per team |
| fact_matches | dim_location | N:1 | Many-to-One | Many matches per location |
| fact_matches | dim_temperature | N:1 | Many-to-One | Many matches per temp (nullable) |

---
