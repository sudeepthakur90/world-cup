#!/usr/bin/env python
"""
AI Readiness Validation Runner

Validates whether the data is ready for AI/ML applications.
Performs comprehensive data quality checks, statistical profiling, and bias detection.
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
    Run AI-readiness validation.
    """
    parser = argparse.ArgumentParser(
        description='Validate AI-Readiness of World Cup Analytics Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ai_readiness.py                      # Run full validation
  python run_ai_readiness.py --output report.json # Custom output file
  python run_ai_readiness.py --verbose            # Show detailed output
        """
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: data/output/ai_readiness_report.json)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed validation output'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("  AI-READINESS VALIDATION")
    logger.info("="*70)
    
    # Check if database or files exist
    db_path = config.GOLD_PATH / "worldcup_analytics.db"
    has_database = db_path.exists()
    has_parquet = any(config.GOLD_PATH.glob("*.parquet"))
    
    if not has_database and not has_parquet:
        logger.error("\nNo data found for validation:")
        logger.error(f"  - Database: {db_path}")
        logger.error(f"  - Parquet files: {config.GOLD_PATH / '*.parquet'}")
        logger.error("\nPlease run the pipeline first:")
        logger.error("  python run_adaptive_pipeline.py")
        logger.error("\nOr at minimum:")
        logger.error("  python run_modeling.py")
        return False
    
    if has_database:
        logger.info("\n✓ Database found")
        logger.info(f"  - {db_path.name}")
        data_source = "Database"
    else:
        logger.info("\n✓ Parquet files found")
        logger.info(f"  - {config.GOLD_PATH}")
        data_source = "Parquet files"
    
    logger.info(f"\nData source: {data_source}")
    logger.info(f"Database URL: {get_database_url()}")
    
    # Initialize validator
    try:
        from src.analytics.validate_ai_readiness import AIReadinessValidator
        
        logger.info("\n" + "="*70)
        logger.info("Running validation checks...")
        logger.info("="*70)
        
        validator = AIReadinessValidator()
        
        # Run all validations
        logger.info("\n1. Loading data...")
        results = validator.validate_all()
        
        if not results:
            logger.error("\n✗ Validation failed: No results returned")
            return False
        
        # Display results
        logger.info("\n" + "="*70)
        logger.info("VALIDATION RESULTS")
        logger.info("="*70)
        
        # Overall score
        readiness_score = results.get('readiness_score', 0)
        logger.info(f"\n🎯 Overall AI-Readiness Score: {readiness_score:.2f}%")
        
        if readiness_score >= 90:
            logger.info("   ✓ Status: HIGHLY READY for AI/ML applications")
            status_emoji = "✅"
        elif readiness_score >= 70:
            logger.info("   ⚠  Status: MODERATELY READY for AI/ML applications")
            status_emoji = "⚠️"
        else:
            logger.warning("   ✗ Status: Needs SIGNIFICANT IMPROVEMENT")
            status_emoji = "❌"
        
        # Data completeness
        if 'data_completeness' in results:
            logger.info("\n📊 Data Completeness:")
            completeness = results['data_completeness']
            for table_name, metrics in completeness.items():
                logger.info(f"\n   {table_name}:")
                logger.info(f"     Records: {metrics['total_records']:,}")
                logger.info(f"     Completeness: {metrics['overall_completeness_percent']:.2f}%")
                if metrics['critical_missing']:
                    logger.warning(f"     ⚠  Critical missing columns: {', '.join(metrics['critical_missing'])}")
        
        # Data quality
        if 'data_quality' in results:
            logger.info("\n🔍 Data Quality:")
            quality = results['data_quality']
            total_duplicates = sum(q['duplicate_records'] for q in quality.values())
            if total_duplicates == 0:
                logger.info("   ✓ No duplicate records found")
            else:
                logger.warning(f"   ⚠  Duplicate records: {total_duplicates}")
            
            # Outliers
            total_outliers = sum(
                sum(outlier_info['count'] for outlier_info in q.get('outliers', {}).values())
                for q in quality.values()
            )
            if total_outliers > 0:
                logger.info(f"   ℹ  Outliers detected: {total_outliers} (expected for real-world data)")
        
        # Feature analysis
        if 'feature_analysis' in results:
            logger.info("\n🧮 Feature Analysis:")
            features = results['feature_analysis']
            logger.info(f"   Total features: {features.get('total_features', 0)}")
            logger.info(f"   Numeric features: {features.get('numeric_features', 0)}")
            logger.info(f"   Categorical features: {features.get('categorical_features', 0)}")
        
        # Correlation analysis
        if 'correlation_analysis' in results:
            correlations = results['correlation_analysis']
            strong_corrs = correlations.get('strong_correlations', [])
            if strong_corrs:
                logger.info("\n🔗 Strong Correlations (|r| > 0.7):")
                for corr in strong_corrs[:5]:  # Show top 5
                    logger.info(f"   {corr['feature1']} ↔ {corr['feature2']}: {corr['correlation']:.3f}")
                if len(strong_corrs) > 5:
                    logger.info(f"   ... and {len(strong_corrs) - 5} more")
            else:
                logger.info("\n🔗 Correlations: No strong correlations detected")
        
        # Bias detection
        if 'bias_detection' in results:
            logger.info("\n⚖️  Bias Detection:")
            bias = results['bias_detection']
            
            if 'temporal_distribution' in bias:
                temp_dist = bias['temporal_distribution']
                logger.info(f"   Temporal coverage: {temp_dist.get('coverage_years', 0)} years")
            
            if 'geographic_distribution' in bias:
                geo_dist = bias['geographic_distribution']
                logger.info(f"   Geographic coverage: {geo_dist.get('unique_countries', 0)} countries")
        
        # Verbose output
        if args.verbose:
            logger.info("\n" + "="*70)
            logger.info("DETAILED STATISTICS")
            logger.info("="*70)
            
            if 'statistical_profile' in results:
                logger.info("\nStatistical Profiles:")
                import json
                logger.info(json.dumps(results['statistical_profile'], indent=2))
        
        # Save report
        output_path = Path(args.output) if args.output else (config.GOLD_PATH / "ai_readiness_report.json")
        validator.save_report(output_path)
        
        logger.info("\n" + "="*70)
        logger.info(f"{status_emoji} AI-READINESS VALIDATION COMPLETE")
        logger.info("="*70)
        
        logger.info(f"\nReport saved to: {output_path}")
        logger.info(f"Overall score: {readiness_score:.2f}%")
        
        # Recommendations
        logger.info("\n📋 Recommendations:")
        
        if readiness_score >= 90:
            logger.info("   ✓ Data is ready for AI/ML model development")
            logger.info("   ✓ Proceed with feature engineering and model training")
            logger.info("   ✓ Consider A/B testing different algorithms")
        elif readiness_score >= 70:
            logger.info("   ⚠  Review and address critical missing columns")
            logger.info("   ⚠  Consider data imputation strategies")
            logger.info("   ✓ Can proceed with prototype models")
        else:
            logger.warning("   ✗ Improve data completeness (target >90%)")
            logger.warning("   ✗ Address duplicate records")
            logger.warning("   ✗ Enhance data quality before model development")
        
        logger.info("\n💡 Next steps:")
        logger.info("   - Review detailed report: ai_readiness_report.json")
        logger.info("   - Address any data quality issues")
        logger.info("   - Document data lineage and transformations")
        logger.info("   - Proceed with ML model development if score > 80%")
        
        # Return success if score is reasonable
        return readiness_score >= 50
        
    except Exception as e:
        logger.error(f"\nValidation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
