-- =============================================================================
-- WORLD CUP DATA WAREHOUSE - STAR SCHEMA DDL
-- =============================================================================
-- This script creates the complete star schema for World Cup analytics
-- with temperature enrichment
-- =============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fact_matches;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_team;
DROP TABLE IF EXISTS dim_location;
DROP TABLE IF EXISTS dim_temperature;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- Date Dimension
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    is_weekend INTEGER DEFAULT 0,
    CONSTRAINT unique_date UNIQUE (full_date)
);

CREATE INDEX idx_date_year ON dim_date(year);
CREATE INDEX idx_date_month ON dim_date(year, month);

-- Team Dimension
CREATE TABLE dim_team (
    team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_code VARCHAR(3),
    confederation VARCHAR(20),
    CONSTRAINT unique_team UNIQUE (team_name)
);

CREATE INDEX idx_team_confederation ON dim_team(confederation);

-- Location Dimension
CREATE TABLE dim_location (
    location_id INTEGER PRIMARY KEY,
    city VARCHAR(100),
    country VARCHAR(100) NOT NULL,
    stadium VARCHAR(200),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6)
);

CREATE INDEX idx_location_country ON dim_location(country);
CREATE INDEX idx_location_city ON dim_location(city);

-- Temperature Dimension
CREATE TABLE dim_temperature (
    temperature_id INTEGER PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER,
    avg_temperature_celsius DECIMAL(5, 2),
    temperature_category VARCHAR(20)
);

CREATE INDEX idx_temp_country_year ON dim_temperature(country, year);
CREATE INDEX idx_temp_category ON dim_temperature(temperature_category);

-- =============================================================================
-- FACT TABLE
-- =============================================================================

CREATE TABLE fact_matches (
    match_id INTEGER PRIMARY KEY,
    date_id INTEGER,
    location_id INTEGER,
    home_team_id INTEGER,
    away_team_id INTEGER,
    temperature_id INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    attendance INTEGER,
    stage VARCHAR(50),
    
    -- Foreign Keys
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (home_team_id) REFERENCES dim_team(team_id),
    FOREIGN KEY (away_team_id) REFERENCES dim_team(team_id),
    FOREIGN KEY (temperature_id) REFERENCES dim_temperature(temperature_id)
);

-- Fact table indexes for query performance
CREATE INDEX idx_fact_date ON fact_matches(date_id);
CREATE INDEX idx_fact_location ON fact_matches(location_id);
CREATE INDEX idx_fact_home_team ON fact_matches(home_team_id);
CREATE INDEX idx_fact_away_team ON fact_matches(away_team_id);
CREATE INDEX idx_fact_temperature ON fact_matches(temperature_id);
CREATE INDEX idx_fact_scores ON fact_matches(home_score, away_score);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Complete match details view
CREATE VIEW vw_match_details AS
SELECT 
    fm.match_id,
    dd.full_date AS match_date,
    dd.year,
    dd.month,
    ht.team_name AS home_team,
    at.team_name AS away_team,
    fm.home_score,
    fm.away_score,
    (fm.home_score + fm.away_score) AS total_goals,
    dl.city,
    dl.country AS host_country,
    dt.avg_temperature_celsius AS temperature,
    dt.temperature_category,
    fm.attendance,
    fm.stage,
    CASE 
        WHEN fm.home_score > fm.away_score THEN ht.team_name
        WHEN fm.away_score > fm.home_score THEN at.team_name
        ELSE 'Draw'
    END AS winner
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
LEFT JOIN dim_location dl ON fm.location_id = dl.location_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id;

-- Temperature impact summary view
CREATE VIEW vw_temperature_impact AS
SELECT 
    dt.temperature_category,
    COUNT(*) AS match_count,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals,
    ROUND(AVG(dt.avg_temperature_celsius), 2) AS avg_temp,
    ROUND(100.0 * SUM(CASE WHEN fm.home_score > fm.away_score THEN 1 ELSE 0 END) / COUNT(*), 2) AS home_win_pct
FROM fact_matches fm
JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
GROUP BY dt.temperature_category;

-- =============================================================================
-- DATA QUALITY CONSTRAINTS
-- =============================================================================

-- Add check constraints
ALTER TABLE fact_matches ADD CONSTRAINT chk_scores_non_negative 
    CHECK (home_score >= 0 AND away_score >= 0);

ALTER TABLE dim_temperature ADD CONSTRAINT chk_temp_range 
    CHECK (avg_temperature_celsius BETWEEN -50 AND 60);

ALTER TABLE dim_date ADD CONSTRAINT chk_valid_month 
    CHECK (month BETWEEN 1 AND 12);

ALTER TABLE dim_date ADD CONSTRAINT chk_valid_day 
    CHECK (day BETWEEN 1 AND 31);