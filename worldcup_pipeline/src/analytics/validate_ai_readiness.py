"""
AI-Readiness Validation Module

Validates whether the data is ready for AI/ML applications.
Performs data quality checks, statistical profiling, and bias detection.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from src.config import config, get_database_url
from src.utils import setup_logger

logger = setup_logger(__name__)


class AIReadinessValidator:
    """
    Validates data readiness for AI/ML applications.
    """
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or get_database_url()
        self.engine = create_engine(self.db_url)
        self.validation_results = {}
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Perform all AI-readiness validations.
        
        Returns:
            Dictionary containing all validation results
        """
        logger.info("Starting AI-readiness validation")
        
        # Load data
        tables = self._load_tables()
        
        if not tables:
            logger.error("No tables found for validation")
            return {}
        
        # Run validations
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'data_completeness': self._check_data_completeness(tables),
            'data_quality': self._check_data_quality(tables),
            'statistical_profile': self._generate_statistical_profile(tables),
            'feature_analysis': self._analyze_features(tables),
            'correlation_analysis': self._analyze_correlations(tables),
            'bias_detection': self._detect_bias(tables),
            'data_lineage': self._document_data_lineage(),
            'readiness_score': None  # Will be calculated
        }
        
        # Calculate overall readiness score
        self.validation_results['readiness_score'] = self._calculate_readiness_score()
        
        logger.info(f"AI-readiness validation complete. Score: {self.validation_results['readiness_score']:.2f}%")
        
        return self.validation_results
    
    def _load_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Load all tables from database or files.
        
        Returns:
            Dictionary of table name -> DataFrame
        """
        tables = {}
        
        # Try to load from database first
        try:
            with self.engine.connect() as conn:
                # Get table names
                table_names = ['fact_matches', 'dim_date', 'dim_team', 'dim_location', 'dim_temperature']
                
                for table_name in table_names:
                    try:
                        df = pd.read_sql_table(table_name, conn)
                        tables[table_name] = df
                        logger.info(f"Loaded {table_name}: {len(df)} records")
                    except Exception as e:
                        logger.warning(f"Could not load {table_name} from database: {e}")
        except Exception as e:
            logger.warning(f"Could not connect to database: {e}")
        
        # Fallback to files
        if not tables:
            logger.info("Loading from parquet files")
            for parquet_file in config.output_path.glob("*.parquet"):
                table_name = parquet_file.stem
                tables[table_name] = pd.read_parquet(parquet_file)
                logger.info(f"Loaded {table_name}: {len(tables[table_name])} records")
        
        return tables
    
    def _check_data_completeness(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Check data completeness across all tables.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Completeness metrics
        """
        logger.info("Checking data completeness")
        
        completeness = {}
        
        for table_name, df in tables.items():
            total_cells = df.size
            missing_cells = df.isnull().sum().sum()
            completeness_rate = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
            
            column_completeness = {}
            for col in df.columns:
                col_completeness = (df[col].notna().sum() / len(df) * 100) if len(df) > 0 else 0
                column_completeness[col] = round(col_completeness, 2)
            
            completeness[table_name] = {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'overall_completeness_percent': round(completeness_rate, 2),
                'missing_cells': int(missing_cells),
                'column_completeness': column_completeness,
                'critical_missing': [col for col, pct in column_completeness.items() if pct < 90]
            }
        
        return completeness
    
    def _check_data_quality(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Perform data quality checks.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Data quality metrics
        """
        logger.info("Checking data quality")
        
        quality = {}
        
        for table_name, df in tables.items():
            # Duplicates
            duplicate_count = df.duplicated().sum()
            
            # Data type consistency
            dtype_issues = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check if numeric values are stored as strings
                    try:
                        pd.to_numeric(df[col].dropna(), errors='raise')
                        dtype_issues.append(f"{col}: numeric stored as string")
                    except:
                        pass
            
            # Outliers (for numeric columns)
            outlier_info = {}
            for col in df.select_dtypes(include=[np.number]).columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)][col]
                if len(outliers) > 0:
                    outlier_info[col] = {
                        'count': len(outliers),
                        'percentage': round(len(outliers) / len(df) * 100, 2)
                    }
            
            quality[table_name] = {
                'duplicate_records': int(duplicate_count),
                'duplicate_percentage': round(duplicate_count / len(df) * 100, 2) if len(df) > 0 else 0,
                'data_type_issues': dtype_issues,
                'outliers': outlier_info
            }
        
        return quality
    
    def _generate_statistical_profile(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Generate statistical profiles for numeric columns.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Statistical profiles
        """
        logger.info("Generating statistical profiles")
        
        profiles = {}
        
        for table_name, df in tables.items():
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                continue
            
            stats = {}
            for col in numeric_cols:
                stats[col] = {
                    'count': int(df[col].count()),
                    'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    'std': float(df[col].std()) if not pd.isna(df[col].std()) else None,
                    'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    'median': float(df[col].median()) if not pd.isna(df[col].median()) else None,
                    'skewness': float(df[col].skew()) if not pd.isna(df[col].skew()) else None,
                    'kurtosis': float(df[col].kurtosis()) if not pd.isna(df[col].kurtosis()) else None
                }
            
            profiles[table_name] = stats
        
        return profiles
    
    def _analyze_features(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze feature characteristics for ML.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Feature analysis
        """
        logger.info("Analyzing features for ML")
        
        analysis = {}
        
        # Focus on fact table
        if 'fact_matches' in tables:
            df = tables['fact_matches']
            
            feature_types = {
                'numeric': list(df.select_dtypes(include=[np.number]).columns),
                'categorical': list(df.select_dtypes(include=['object', 'category']).columns),
                'temporal': [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            }
            
            # Cardinality for categorical features
            categorical_cardinality = {}
            for col in feature_types['categorical']:
                unique_count = df[col].nunique()
                categorical_cardinality[col] = {
                    'unique_values': int(unique_count),
                    'cardinality_ratio': round(unique_count / len(df), 4) if len(df) > 0 else 0
                }
            
            analysis['feature_types'] = feature_types
            analysis['categorical_cardinality'] = categorical_cardinality
            analysis['total_features'] = len(df.columns)
            analysis['numeric_features'] = len(feature_types['numeric'])
            analysis['categorical_features'] = len(feature_types['categorical'])
        
        return analysis
    
    def _analyze_correlations(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze correlations between numeric features.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Correlation analysis
        """
        logger.info("Analyzing feature correlations")
        
        correlations = {}
        
        if 'fact_matches' in tables:
            df = tables['fact_matches']
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) > 1:
                corr_matrix = numeric_df.corr()
                
                # Find strong correlations (> 0.7)
                strong_correlations = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            strong_correlations.append({
                                'feature1': corr_matrix.columns[i],
                                'feature2': corr_matrix.columns[j],
                                'correlation': round(float(corr_val), 3)
                            })
                
                correlations['strong_correlations'] = strong_correlations
                correlations['correlation_matrix_shape'] = list(corr_matrix.shape)
        
        return correlations
    
    def _detect_bias(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Detect potential biases in the dataset.
        
        Args:
            tables: Dictionary of DataFrames
        
        Returns:
            Bias detection results
        """
        logger.info("Detecting potential biases")
        
        bias_checks = {}
        
        # Temporal bias
        if 'dim_date' in tables:
            df = tables['dim_date']
            if 'year' in df.columns:
                year_dist = df['year'].value_counts().to_dict()
                bias_checks['temporal_distribution'] = {
                    'year_counts': {int(k): int(v) for k, v in year_dist.items()},
                    'coverage_years': int(df['year'].max() - df['year'].min()) if len(df) > 0 else 0
                }
        
        # Geographic bias
        if 'dim_location' in tables:
            df = tables['dim_location']
            if 'country' in df.columns:
                country_dist = df['country'].value_counts().head(10).to_dict()
                bias_checks['geographic_distribution'] = {
                    'top_10_countries': country_dist,
                    'unique_countries': int(df['country'].nunique())
                }
        
        # Team representation
        if 'dim_team' in tables:
            df = tables['dim_team']
            bias_checks['team_representation'] = {
                'total_teams': len(df),
                'confederation_distribution': df['confederation'].value_counts().to_dict() if 'confederation' in df.columns else {}
            }
        
        return bias_checks
    
    def _document_data_lineage(self) -> Dict[str, Any]:
        """
        Document data lineage and transformations.
        
        Returns:
            Data lineage documentation
        """
        return {
            'source_systems': [
                {
                    'name': 'World Cup Results',
                    'url': config.worldcup_url,
                    'type': 'Excel'
                },
                {
                    'name': 'Temperature Data',
                    'url': config.temperature_url,
                    'type': 'CSV (zipped)'
                }
            ],
            'transformation_stages': [
                'Data Ingestion',
                'Data Cleaning & Standardization',
                'Temperature Enrichment',
                'Dimensional Modeling (Star Schema)',
                'Aggregation & Analytics'
            ],
            'data_freshness': {
                'coverage_period': '1930-2014',
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _calculate_readiness_score(self) -> float:
        """
        Calculate overall AI-readiness score.
        
        Returns:
            Readiness score (0-100)
        """
        score = 100.0
        
        # Completeness penalty
        if 'data_completeness' in self.validation_results:
            avg_completeness = np.mean([
                v['overall_completeness_percent'] 
                for v in self.validation_results['data_completeness'].values()
            ])
            completeness_score = avg_completeness
        else:
            completeness_score = 0
        
        # Quality penalty
        if 'data_quality' in self.validation_results:
            total_duplicates = sum([
                v['duplicate_percentage'] 
                for v in self.validation_results['data_quality'].values()
            ])
            quality_penalty = min(total_duplicates, 20)
        else:
            quality_penalty = 0
        
        # Calculate final score
        final_score = (completeness_score * 0.7) + ((100 - quality_penalty) * 0.3)
        
        return round(final_score, 2)
    
    def save_report(self, output_path: Path = None):
        """
        Save validation report to JSON file.
        
        Args:
            output_path: Output file path
        """
        if not output_path:
            output_path = config.output_path / "ai_readiness_report.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"AI-readiness report saved to {output_path}")


def validate_ai_readiness() -> bool:
    """
    Run AI-readiness validation and generate report.
    
    Returns:
        bool: True if successful
    """
    try:
        validator = AIReadinessValidator()
        results = validator.validate_all()
        validator.save_report()
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("AI-READINESS VALIDATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Overall Readiness Score: {results['readiness_score']:.2f}%")
        
        if results['readiness_score'] >= 90:
            logger.info("✓ Data is HIGHLY READY for AI/ML applications")
        elif results['readiness_score'] >= 70:
            logger.info("⚠ Data is MODERATELY READY for AI/ML applications")
        else:
            logger.warning("✗ Data needs SIGNIFICANT IMPROVEMENT before AI/ML use")
        
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"AI-readiness validation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = validate_ai_readiness()
    exit(0 if success else 1)