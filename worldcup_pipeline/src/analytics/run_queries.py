"""
Analytics Module

Provides pre-built SQL queries for BI insights.
Includes queries for temperature impact, trends, and geographic analysis.
"""

from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import config, get_database_url
from src.utils import setup_logger

logger = setup_logger(__name__)


class AnalyticsEngine:
    """
    Executes analytical queries against the star schema.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize analytics engine.
        
        Args:
            db_url: Database connection URL
        """
        self.db_url = db_url or get_database_url()
        self.engine = create_engine(self.db_url)
        self.queries = self._load_queries()
    
    def _load_queries(self) -> Dict[str, str]:
        """
        Load all analytical queries.
        
        Returns:
            Dictionary of query name -> SQL string
        """
        return {
            'temperature_impact_on_goals': self._query_temperature_impact_on_goals(),
            'goals_by_temperature_category': self._query_goals_by_temperature_category(),
            'home_advantage_by_temperature': self._query_home_advantage_by_temperature(),
            'tournament_trends_over_time': self._query_tournament_trends(),
            'matches_by_year_and_country': self._query_matches_by_year_country(),
            'top_scoring_matches': self._query_top_scoring_matches(),
            'team_performance_summary': self._query_team_performance(),
            'temperature_distribution': self._query_temperature_distribution(),
            'seasonal_patterns': self._query_seasonal_patterns(),
            'geographic_analysis': self._query_geographic_analysis(),
        }
    
    def _query_temperature_impact_on_goals(self) -> str:
        """
        Analyze correlation between temperature and goals scored.
        """
        return """
        -- Temperature Impact on Goals Scored
        SELECT 
            dt.temperature_category,
            dt.avg_temperature_celsius,
            COUNT(fm.match_id) as total_matches,
            AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)) as avg_total_goals,
            AVG(COALESCE(fm.home_goals, 0)) as avg_home_goals,
            AVG(COALESCE(fm.away_goals, 0)) as avg_away_goals,
            MAX(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)) as max_total_goals
        FROM fact_matches fm
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE dt.avg_temperature_celsius IS NOT NULL
        GROUP BY dt.temperature_category, dt.avg_temperature_celsius
        ORDER BY dt.avg_temperature_celsius;
        """
    
    def _query_goals_by_temperature_category(self) -> str:
        """
        Goals distribution by temperature category.
        """
        return """
        -- Goals by Temperature Category
        SELECT 
            dt.temperature_category,
            COUNT(fm.match_id) as match_count,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals_per_match,
            ROUND(MIN(dt.avg_temperature_celsius), 2) as min_temp,
            ROUND(MAX(dt.avg_temperature_celsius), 2) as max_temp,
            ROUND(AVG(dt.avg_temperature_celsius), 2) as avg_temp
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
                ELSE 5
            END;
        """
    
    def _query_home_advantage_by_temperature(self) -> str:
        """
        Analyze home team advantage across temperature ranges.
        """
        return """
        -- Home Advantage by Temperature
        SELECT 
            dt.temperature_category,
            COUNT(fm.match_id) as total_matches,
            SUM(CASE WHEN fm.home_goals > fm.away_goals THEN 1 ELSE 0 END) as home_wins,
            SUM(CASE WHEN fm.home_goals < fm.away_goals THEN 1 ELSE 0 END) as away_wins,
            SUM(CASE WHEN fm.home_goals = fm.away_goals THEN 1 ELSE 0 END) as draws,
            ROUND(100.0 * SUM(CASE WHEN fm.home_goals > fm.away_goals THEN 1 ELSE 0 END) / COUNT(fm.match_id), 2) as home_win_percent
        FROM fact_matches fm
        JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE fm.home_goals IS NOT NULL AND fm.away_goals IS NOT NULL
        GROUP BY dt.temperature_category
        ORDER BY 
            CASE dt.temperature_category
                WHEN 'Cold' THEN 1
                WHEN 'Moderate' THEN 2
                WHEN 'Warm' THEN 3
                WHEN 'Hot' THEN 4
                ELSE 5
            END;
        """
    
    def _query_tournament_trends(self) -> str:
        """
        Historical trends over time.
        """
        return """
        -- Tournament Trends Over Time
        SELECT 
            dd.year,
            COUNT(DISTINCT fm.match_id) as total_matches,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals_per_match,
            COUNT(DISTINCT dl.country) as host_countries,
            ROUND(AVG(dt.avg_temperature_celsius), 2) as avg_temperature
        FROM fact_matches fm
        JOIN dim_date dd ON fm.date_id = dd.date_id
        LEFT JOIN dim_location dl ON fm.location_id = dl.location_id
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        GROUP BY dd.year
        ORDER BY dd.year;
        """
    
    def _query_matches_by_year_country(self) -> str:
        """
        Matches grouped by year and host country.
        """
        return """
        -- Matches by Year and Host Country
        SELECT 
            dd.year,
            dl.country,
            COUNT(fm.match_id) as match_count,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals,
            ROUND(AVG(dt.avg_temperature_celsius), 2) as avg_temp
        FROM fact_matches fm
        JOIN dim_date dd ON fm.date_id = dd.date_id
        JOIN dim_location dl ON fm.location_id = dl.location_id
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE dl.country IS NOT NULL
        GROUP BY dd.year, dl.country
        ORDER BY dd.year, match_count DESC;
        """
    
    def _query_top_scoring_matches(self) -> str:
        """
        Top scoring matches with temperature context.
        """
        return """
        -- Top Scoring Matches
        SELECT 
            dd.full_date as match_date,
            ht.team_name as home_team,
            at.team_name as away_team,
            fm.home_goals,
            fm.away_goals,
            (COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)) as total_goals,
            dl.city,
            dl.country,
            dt.avg_temperature_celsius as temperature,
            dt.temperature_category
        FROM fact_matches fm
        JOIN dim_date dd ON fm.date_id = dd.date_id
        JOIN dim_team ht ON fm.home_team_id = ht.team_id
        JOIN dim_team at ON fm.away_team_id = at.team_id
        LEFT JOIN dim_location dl ON fm.location_id = dl.location_id
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE fm.home_goals IS NOT NULL AND fm.away_goals IS NOT NULL
        ORDER BY total_goals DESC, dd.full_date DESC
        LIMIT 20;
        """
    
    def _query_team_performance(self) -> str:
        """
        Team performance summary.
        """
        return """
        -- Team Performance Summary
        WITH team_matches AS (
            SELECT 
                team_id,
                team_name,
                SUM(matches) as total_matches,
                SUM(wins) as wins,
                SUM(losses) as losses,
                SUM(draws) as draws,
                SUM(goals_for) as goals_for,
                SUM(goals_against) as goals_against
            FROM (
                -- Home matches
                SELECT 
                    ht.team_id,
                    ht.team_name,
                    COUNT(*) as matches,
                    SUM(CASE WHEN fm.home_goals > fm.away_goals THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN fm.home_goals < fm.away_goals THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN fm.home_goals = fm.away_goals THEN 1 ELSE 0 END) as draws,
                    SUM(COALESCE(fm.home_goals, 0)) as goals_for,
                    SUM(COALESCE(fm.away_goals, 0)) as goals_against
                FROM fact_matches fm
                JOIN dim_team ht ON fm.home_team_id = ht.team_id
                WHERE fm.home_goals IS NOT NULL
                GROUP BY ht.team_id, ht.team_name
                
                UNION ALL
                
                -- Away matches
                SELECT 
                    at.team_id,
                    at.team_name,
                    COUNT(*) as matches,
                    SUM(CASE WHEN fm.away_goals > fm.home_goals THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN fm.away_goals < fm.home_goals THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN fm.away_goals = fm.home_goals THEN 1 ELSE 0 END) as draws,
                    SUM(COALESCE(fm.away_goals, 0)) as goals_for,
                    SUM(COALESCE(fm.home_goals, 0)) as goals_against
                FROM fact_matches fm
                JOIN dim_team at ON fm.away_team_id = at.team_id
                WHERE fm.away_goals IS NOT NULL
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
            ROUND(100.0 * wins / NULLIF(total_matches, 0), 2) as win_percentage,
            goals_for,
            goals_against,
            (goals_for - goals_against) as goal_difference,
            ROUND(CAST(goals_for AS FLOAT) / NULLIF(total_matches, 0), 2) as goals_per_match
        FROM team_matches
        WHERE total_matches > 0
        ORDER BY wins DESC, goal_difference DESC
        LIMIT 20;
        """
    
    def _query_temperature_distribution(self) -> str:
        """
        Temperature distribution across matches.
        """
        return """
        -- Temperature Distribution
        SELECT 
            ROUND(dt.avg_temperature_celsius / 5) * 5 as temp_range_start,
            COUNT(fm.match_id) as match_count,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals
        FROM fact_matches fm
        JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE dt.avg_temperature_celsius IS NOT NULL
        GROUP BY ROUND(dt.avg_temperature_celsius / 5)
        ORDER BY temp_range_start;
        """
    
    def _query_seasonal_patterns(self) -> str:
        """
        Seasonal patterns in matches.
        """
        return """
        -- Seasonal Patterns
        SELECT 
            dd.month,
            dd.month_name,
            COUNT(fm.match_id) as match_count,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals,
            ROUND(AVG(dt.avg_temperature_celsius), 2) as avg_temperature
        FROM fact_matches fm
        JOIN dim_date dd ON fm.date_id = dd.date_id
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        GROUP BY dd.month, dd.month_name
        ORDER BY dd.month;
        """
    
    def _query_geographic_analysis(self) -> str:
        """
        Geographic performance analysis.
        """
        return """
        -- Geographic Analysis
        SELECT 
            dl.country as host_country,
            COUNT(DISTINCT dd.year) as tournaments_hosted,
            COUNT(fm.match_id) as total_matches,
            ROUND(AVG(COALESCE(fm.home_goals, 0) + COALESCE(fm.away_goals, 0)), 2) as avg_goals_per_match,
            ROUND(AVG(dt.avg_temperature_celsius), 2) as avg_temperature,
            dt.temperature_category as typical_climate
        FROM fact_matches fm
        JOIN dim_location dl ON fm.location_id = dl.location_id
        JOIN dim_date dd ON fm.date_id = dd.date_id
        LEFT JOIN dim_temperature dt ON fm.temperature_id = dt.temperature_id
        WHERE dl.country IS NOT NULL
        GROUP BY dl.country, dt.temperature_category
        ORDER BY total_matches DESC;
        """
    
    def execute_query(self, query_name: str) -> Optional[pd.DataFrame]:
        """
        Execute a named query.
        
        Args:
            query_name: Name of the query to execute
        
        Returns:
            DataFrame with results or None if error
        """
        if query_name not in self.queries:
            logger.error(f"Query '{query_name}' not found")
            logger.info(f"Available queries: {list(self.queries.keys())}")
            return None
        
        try:
            logger.info(f"Executing query: {query_name}")
            
            with self.engine.connect() as conn:
                result = pd.read_sql(text(self.queries[query_name]), conn)
            
            logger.info(f"Query returned {len(result)} rows")
            return result
            
        except Exception as e:
            logger.error(f"Error executing query '{query_name}': {e}")
            return None
    
    def execute_all_queries(self) -> Dict[str, pd.DataFrame]:
        """
        Execute all queries and return results.
        
        Returns:
            Dictionary of query name -> result DataFrame
        """
        logger.info("Executing all analytical queries")
        
        results = {}
        for query_name in self.queries.keys():
            result = self.execute_query(query_name)
            if result is not None:
                results[query_name] = result
        
        logger.info(f"Executed {len(results)} queries successfully")
        return results
    
    def save_results_to_csv(self, results: Dict[str, pd.DataFrame], output_dir):
        """
        Save query results to CSV files.
        
        Args:
            results: Dictionary of query results
            output_dir: Output directory path
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for query_name, df in results.items():
            csv_path = output_path / f"{query_name}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {query_name} to {csv_path}")


def run_all_analytics() -> bool:
    """
    Run all analytical queries and save results.
    
    Returns:
        bool: True if successful
    """
    try:
        analytics = AnalyticsEngine()
        results = analytics.execute_all_queries()
        
        if not results:
            logger.error("No query results obtained")
            return False
        
        # Save results
        analytics.save_results_to_csv(results, config.GOLD_PATH / "analytics_results")
        
        logger.info("Analytics execution completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running analytics: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_all_analytics()
    exit(0 if success else 1)