-- =============================================================================
-- ANALYTICAL QUERIES FOR BI DASHBOARD
-- =============================================================================
-- Pre-built queries for extracting key insights from World Cup data
-- with temperature enrichment
-- =============================================================================

-- =============================================================================
-- 1. TEMPERATURE IMPACT ANALYSIS
-- =============================================================================

-- Query 1.1: Goals scored by temperature range
SELECT 
    CASE 
        WHEN dt.avg_temperature_celsius < 10 THEN 'Cold (< 10°C)'
        WHEN dt.avg_temperature_celsius < 20 THEN 'Moderate (10-20°C)'
        WHEN dt.avg_temperature_celsius < 30 THEN 'Warm (20-30°C)'
        ELSE 'Hot (> 30°C)'
    END AS temperature_range,
    COUNT(fm.match_id) AS total_matches,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals_per_match,
    ROUND(MIN(dt.avg_temperature_celsius), 1) AS min_temp,
    ROUND(MAX(dt.avg_temperature_celsius), 1) AS max_temp
FROM fact_matches fm
JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
GROUP BY 
    CASE 
        WHEN dt.avg_temperature_celsius < 10 THEN 'Cold (< 10°C)'
        WHEN dt.avg_temperature_celsius < 20 THEN 'Moderate (10-20°C)'
        WHEN dt.avg_temperature_celsius < 30 THEN 'Warm (20-30°C)'
        ELSE 'Hot (> 30°C)'
    END
ORDER BY min_temp;

-- Query 1.2: Correlation between temperature and scoring
SELECT 
    dt.temperature_category,
    COUNT(*) AS matches,
    ROUND(AVG(fm.home_score), 2) AS avg_home_goals,
    ROUND(AVG(fm.away_score), 2) AS avg_away_goals,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_total_goals,
    MAX(fm.home_score + fm.away_score) AS highest_scoring_match
FROM fact_matches fm
JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE dt.temperature_category IS NOT NULL
GROUP BY dt.temperature_category
ORDER BY 
    CASE dt.temperature_category
        WHEN 'Cold' THEN 1
        WHEN 'Moderate' THEN 2
        WHEN 'Warm' THEN 3
        WHEN 'Hot' THEN 4
    END;

-- Query 1.3: Home advantage by temperature
SELECT 
    dt.temperature_category,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN fm.home_score > fm.away_score THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN fm.home_score < fm.away_score THEN 1 ELSE 0 END) AS away_wins,
    SUM(CASE WHEN fm.home_score = fm.away_score THEN 1 ELSE 0 END) AS draws,
    ROUND(100.0 * SUM(CASE WHEN fm.home_score > fm.away_score THEN 1 ELSE 0 END) / COUNT(*), 2) AS home_win_percentage,
    ROUND(AVG(fm.home_score - fm.away_score), 2) AS avg_goal_difference
FROM fact_matches fm
JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
GROUP BY dt.temperature_category;

-- =============================================================================
-- 2. HISTORICAL TRENDS
-- =============================================================================

-- Query 2.1: Tournament evolution over time
SELECT 
    dd.year,
    COUNT(DISTINCT fm.match_id) AS total_matches,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals_per_match,
    ROUND(AVG(CAST(fm.attendance AS FLOAT)), 0) AS avg_attendance,
    MAX(fm.attendance) AS max_attendance,
    COUNT(DISTINCT CASE WHEN fm.home_score + fm.away_score >= 5 THEN fm.match_id END) AS high_scoring_matches,
    ROUND(AVG(dt.avg_temperature_celsius), 1) AS avg_temperature
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
GROUP BY dd.year
ORDER BY dd.year;

-- Query 2.2: Decade-wise comparison
SELECT 
    FLOOR(dd.year / 10) * 10 AS decade,
    COUNT(*) AS total_matches,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals,
    ROUND(AVG(fm.attendance), 0) AS avg_attendance,
    COUNT(DISTINCT ht.team_id) + COUNT(DISTINCT at.team_id) AS unique_teams_participated
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
GROUP BY FLOOR(dd.year / 10) * 10
ORDER BY decade;

-- Query 2.3: Seasonal patterns (month-wise)
SELECT 
    dd.month,
    dd.month_name,
    COUNT(*) AS matches_played,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals,
    ROUND(AVG(dt.avg_temperature_celsius), 1) AS avg_temp,
    COUNT(DISTINCT dd.year) AS years_active
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
GROUP BY dd.month, dd.month_name
ORDER BY dd.month;

-- =============================================================================
-- 3. GEOGRAPHIC ANALYSIS
-- =============================================================================

-- Query 3.1: Performance by host country
SELECT 
    dl.country AS host_country,
    COUNT(DISTINCT dd.year) AS tournaments_hosted,
    COUNT(*) AS total_matches,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals_per_match,
    ROUND(AVG(fm.attendance), 0) AS avg_attendance,
    MAX(fm.attendance) AS highest_attendance,
    ROUND(AVG(dt.avg_temperature_celsius), 1) AS avg_temperature,
    dt.temperature_category AS typical_climate
FROM fact_matches fm
JOIN dim_location dl ON fm.location_id = dl.location_id
JOIN dim_date dd ON fm.date_id = dd.date_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE dl.country IS NOT NULL
GROUP BY dl.country, dt.temperature_category
HAVING COUNT(*) >= 5
ORDER BY total_matches DESC;

-- Query 3.2: Climate zone win rates
WITH climate_zones AS (
    SELECT 
        CASE 
            WHEN dt.avg_temperature_celsius < 15 THEN 'Temperate'
            WHEN dt.avg_temperature_celsius < 25 THEN 'Subtropical'
            ELSE 'Tropical'
        END AS climate_zone,
        fm.*
    FROM fact_matches fm
    JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
)
SELECT 
    climate_zone,
    COUNT(*) AS total_matches,
    ROUND(AVG(home_score + away_score), 2) AS avg_goals,
    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) AS away_wins,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws
FROM climate_zones
WHERE climate_zone IS NOT NULL
GROUP BY climate_zone
ORDER BY total_matches DESC;

-- =============================================================================
-- 4. TEAM ANALYTICS
-- =============================================================================

-- Query 4.1: Top performing teams (all-time)
WITH team_stats AS (
    SELECT 
        team_id,
        team_name,
        SUM(matches) AS total_matches,
        SUM(wins) AS wins,
        SUM(losses) AS losses,
        SUM(draws) AS draws,
        SUM(goals_for) AS goals_for,
        SUM(goals_against) AS goals_against
    FROM (
        -- Home matches
        SELECT 
            ht.team_id,
            ht.team_name,
            COUNT(*) AS matches,
            SUM(CASE WHEN fm.home_score > fm.away_score THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN fm.home_score < fm.away_score THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN fm.home_score = fm.away_score THEN 1 ELSE 0 END) AS draws,
            SUM(fm.home_score) AS goals_for,
            SUM(fm.away_score) AS goals_against
        FROM fact_matches fm
        JOIN dim_team ht ON fm.home_team_id = ht.team_id
        WHERE fm.home_score IS NOT NULL
        GROUP BY ht.team_id, ht.team_name
        
        UNION ALL
        
        -- Away matches
        SELECT 
            at.team_id,
            at.team_name,
            COUNT(*) AS matches,
            SUM(CASE WHEN fm.away_score > fm.home_score THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN fm.away_score < fm.home_score THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN fm.away_score = fm.home_score THEN 1 ELSE 0 END) AS draws,
            SUM(fm.away_score) AS goals_for,
            SUM(fm.home_score) AS goals_against
        FROM fact_matches fm
        JOIN dim_team at ON fm.away_team_id = at.team_id
        WHERE fm.away_score IS NOT NULL
        GROUP BY at.team_id, at.team_name
    ) combined
    GROUP BY team_id, team_name
)
SELECT 
    team_name,
    total_matches,
    wins,
    draws,
    losses,
    ROUND(100.0 * wins / total_matches, 2) AS win_percentage,
    goals_for,
    goals_against,
    (goals_for - goals_against) AS goal_difference,
    ROUND(CAST(goals_for AS FLOAT) / total_matches, 2) AS goals_per_match,
    ROUND(CAST(goals_against AS FLOAT) / total_matches, 2) AS conceded_per_match
FROM team_stats
WHERE total_matches >= 10
ORDER BY win_percentage DESC, goal_difference DESC
LIMIT 20;

-- Query 4.2: Head-to-head records (top rivalries)
SELECT 
    ht.team_name AS team1,
    at.team_name AS team2,
    COUNT(*) AS matches_played,
    SUM(CASE WHEN fm.home_score > fm.away_score THEN 1 ELSE 0 END) AS team1_wins,
    SUM(CASE WHEN fm.away_score > fm.home_score THEN 1 ELSE 0 END) AS team2_wins,
    SUM(CASE WHEN fm.home_score = fm.away_score THEN 1 ELSE 0 END) AS draws,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_total_goals
FROM fact_matches fm
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
GROUP BY ht.team_name, at.team_name
HAVING COUNT(*) >= 3
ORDER BY matches_played DESC, avg_total_goals DESC
LIMIT 20;

-- =============================================================================
-- 5. SPECIAL INSIGHTS
-- =============================================================================

-- Query 5.1: Highest scoring matches with context
SELECT 
    dd.full_date AS match_date,
    ht.team_name AS home_team,
    fm.home_score,
    at.team_name AS away_team,
    fm.away_score,
    (fm.home_score + fm.away_score) AS total_goals,
    dl.city,
    dl.country,
    ROUND(dt.avg_temperature_celsius, 1) AS temperature,
    dt.temperature_category,
    fm.stage
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
LEFT JOIN dim_location dl ON fm.location_id = dl.location_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
ORDER BY total_goals DESC, dd.full_date DESC
LIMIT 20;

-- Query 5.2: Upset analysis (biggest score differentials)
SELECT 
    dd.year,
    ht.team_name AS winning_team,
    at.team_name AS losing_team,
    fm.home_score,
    fm.away_score,
    ABS(fm.home_score - fm.away_score) AS goal_difference,
    dl.country AS host_country,
    dt.avg_temperature_celsius AS temperature
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
LEFT JOIN dim_location dl ON fm.location_id = dl.location_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
WHERE fm.home_score IS NOT NULL AND fm.away_score IS NOT NULL
  AND fm.home_score != fm.away_score
ORDER BY goal_difference DESC, dd.year DESC
LIMIT 20;

-- Query 5.3: Tournament statistics by year
SELECT 
    dd.year AS tournament_year,
    dl.country AS host_country,
    COUNT(*) AS total_matches,
    COUNT(DISTINCT ht.team_id) + COUNT(DISTINCT at.team_id) AS teams_participated,
    SUM(fm.home_score + fm.away_score) AS total_goals,
    ROUND(AVG(fm.home_score + fm.away_score), 2) AS avg_goals_per_match,
    MAX(fm.home_score + fm.away_score) AS highest_scoring_match,
    ROUND(AVG(fm.attendance), 0) AS avg_attendance,
    SUM(fm.attendance) AS total_attendance,
    ROUND(AVG(dt.avg_temperature_celsius), 1) AS avg_tournament_temp
FROM fact_matches fm
JOIN dim_date dd ON fm.date_id = dd.date_id
JOIN dim_team ht ON fm.home_team_id = ht.team_id
JOIN dim_team at ON fm.away_team_id = at.team_id
JOIN dim_location dl ON fm.location_id = dl.location_id
LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
GROUP BY dd.year, dl.country
ORDER BY dd.year;