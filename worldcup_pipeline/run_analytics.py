#!/usr/bin/env python
"""
Analytics Stage Runner

Runs analytical queries against the Star Schema database.
Generates insights and saves results to CSV files.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
from src.config import config, get_database_url
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Run analytics stage.
    """
    parser = argparse.ArgumentParser(
        description='Run Analytics Stage (SQL Queries & Insights)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analytics.py                    # Run all queries
  python run_analytics.py --query temperature_impact  # Run specific query
  python run_analytics.py --list             # List available queries
  python run_analytics.py --no-save          # Don't save to CSV
        """
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Run specific query by name (default: all queries)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available queries and exit'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to CSV files'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for CSV files (default: data/output/analytics_results)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("  ANALYTICS STAGE (SQL Queries & Insights)")
    logger.info("="*70)
    
    # Check if database exists
    db_url = get_database_url()
    db_path = config.GOLD_PATH / "worldcup_analytics.db"
    
    if not db_path.exists():
        logger.error("\nDatabase not found:")
        logger.error(f"  - {db_path}")
        logger.error("\nPlease run modeling first:")
        logger.error("  python run_modeling.py")
        logger.error("\nOr run full pipeline:")
        logger.error("  python run_adaptive_pipeline.py")
        return False
    
    logger.info("\n✓ Database found")
    logger.info(f"  - {db_path.name}")
    logger.info(f"\nDatabase: {db_url}")
    
    # Initialize analytics engine
    try:
        from src.analytics.run_queries import AnalyticsEngine
        
        analytics = AnalyticsEngine(db_url)
        available_queries = list(analytics.queries.keys())
        
        # List queries if requested
        if args.list:
            logger.info("\nAvailable Queries:")
            logger.info("="*70)
            for i, query_name in enumerate(available_queries, 1):
                logger.info(f"  {i}. {query_name}")
            logger.info("\nTo run a specific query:")
            logger.info("  python run_analytics.py --query <query_name>")
            return True
        
        # Determine which queries to run
        if args.query:
            if args.query not in available_queries:
                logger.error(f"\nQuery '{args.query}' not found.")
                logger.error("\nAvailable queries:")
                for query_name in available_queries:
                    logger.error(f"  - {query_name}")
                logger.error("\nUse --list to see all queries")
                return False
            
            queries_to_run = {args.query: analytics.queries[args.query]}
            logger.info(f"\nRunning query: {args.query}")
        else:
            queries_to_run = analytics.queries
            logger.info(f"\nRunning all queries ({len(queries_to_run)} total)")
        
        logger.info("\n" + "="*70)
        
        # Execute queries
        results = {}
        for query_name, query_sql in queries_to_run.items():
            try:
                logger.info(f"\nExecuting: {query_name}")
                logger.info("-" * 70)
                
                result_df = analytics.execute_query(query_name)
                
                if result_df is not None and len(result_df) > 0:
                    results[query_name] = result_df
                    
                    logger.info(f"\u2713 Query completed: {len(result_df)} rows returned")
                    
                    # Display first few rows
                    logger.info("\nResults (first 10 rows):")
                    logger.info(result_df.head(10).to_string(index=False))
                    
                    if len(result_df) > 10:
                        logger.info(f"\n... and {len(result_df) - 10} more rows")
                    
                else:
                    logger.warning(f"No results returned for {query_name}")
                
            except Exception as e:
                logger.error(f"Error executing {query_name}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        logger.info("\n" + "="*70)
        
        if not results:
            logger.error("\n✗ No query results obtained")
            return False
        
        # Save results to CSV
        if not args.no_save:
            output_dir = args.output_dir or (config.GOLD_PATH / "analytics_results")
            output_path = Path(output_dir)
            
            logger.info("\nSaving results to CSV files...")
            logger.info(f"Output directory: {output_path}")
            
            analytics.save_results_to_csv(results, output_path)
            
            logger.info("\nCSV files created:")
            for query_name in results.keys():
                csv_file = output_path / f"{query_name}.csv"
                logger.info(f"  - {csv_file.name}")
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("✓ ANALYTICS STAGE COMPLETE")
        logger.info("="*70)
        
        logger.info("\nQuery Execution Summary:")
        logger.info(f"  Queries executed: {len(results)}")
        logger.info(f"  Total rows returned: {sum(len(df) for df in results.values())}")
        
        if not args.no_save:
            logger.info(f"\nResults saved to: {output_path}")
            logger.info(f"  CSV files: {len(results)}")
        
        logger.info("\nKey Insights:")
        
        # Show some key insights if available
        if 'goals_by_temperature_category' in results:
            df = results['goals_by_temperature_category']
            if not df.empty:
                logger.info("\n  Temperature Impact on Goals:")
                for _, row in df.iterrows():
                    logger.info(f"    {row['temperature_category']}: {row['avg_goals_per_match']:.2f} goals/match")
        
        if 'top_scoring_matches' in results:
            df = results['top_scoring_matches']
            if not df.empty:
                logger.info("\n  Highest Scoring Match:")
                top_match = df.iloc[0]
                logger.info(f"    {top_match.get('home_team', 'N/A')} vs {top_match.get('away_team', 'N/A')}")
                logger.info(f"    Score: {top_match.get('home_score', 0)}-{top_match.get('away_score', 0)}")
        
        logger.info("\nNext steps:")
        logger.info("  - Review CSV files for detailed insights")
        logger.info("  - Create visualizations from results")
        logger.info("  - Import into BI tools (Tableau, Power BI)")
        logger.info("\nQuery database directly:")
        logger.info(f"  sqlite3 {db_path}")
        logger.info("  SELECT * FROM fact_matches LIMIT 10;")
        
        return True
        
    except Exception as e:
        logger.error(f"\nAnalytics error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
