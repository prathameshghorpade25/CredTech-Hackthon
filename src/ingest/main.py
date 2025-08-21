import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from src.ingest.structured import DataIngestionManager, CSVDataSource, DatabaseDataSource
from src.ingest.unstructured import NewsDataSource, SocialMediaDataSource

def run_ingestion(output_path: str = 'data/processed/combined_data.csv'):
    """Run the full ingestion pipeline"""
    import os
    from src.utils.logging import get_app_logger
    
    logger = get_app_logger(__name__)
    
    # Initialize the data ingestion manager
    manager = DataIngestionManager()
    
    # Add structured data sources
    # First try to use real financial data
    try:
        from src.ingest.financial_data import AlphaVantageClient, FinancialModelingPrepClient
        from src.utils.api_client import APIError
        
        logger.info("Attempting to fetch real financial data from APIs")
        
        # Get company financial data from APIs
        try:
            # Use Financial Modeling Prep for financial ratios
            fmp_client = FinancialModelingPrepClient()
            
            # Process financial data for multiple companies
            companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            financial_data = []
            
            for symbol in companies:
                try:
                    # Get financial ratios
                    ratios = fmp_client.get_financial_ratios(symbol)
                    metrics = fmp_client.get_key_metrics(symbol)
                    
                    # Process and combine the data
                    if ratios and metrics:
                        for ratio_data in ratios:
                            date = ratio_data.get('date')
                            # Find matching metrics for this date
                            matching_metrics = next((m for m in metrics if m.get('date') == date), {})
                            
                            # Extract key financial indicators
                            financial_data.append({
                                'issuer': symbol,
                                'asof_date': date,
                                'income': matching_metrics.get('revenue', 0),
                                'balance': matching_metrics.get('totalAssets', 0),
                                'transactions': matching_metrics.get('operatingCashFlow', 0),
                                'debt_to_equity': ratio_data.get('debtToEquityRatio', 0),
                                'current_ratio': ratio_data.get('currentRatio', 0),
                                'return_on_assets': ratio_data.get('returnOnAssets', 0),
                                'return_on_equity': ratio_data.get('returnOnEquity', 0),
                                'data_source': 'financial_modeling_prep'
                            })
                except APIError as e:
                    logger.error(f"Error fetching financial data for {symbol}: {str(e)}")
                    continue
            
            # If we got real financial data, create a DataFrame and add it as a source
            if financial_data:
                import pandas as pd
                financial_df = pd.DataFrame(financial_data)
                
                # Save to CSV for caching/reproducibility
                financial_csv = os.path.join('data', 'processed', 'financial_data.csv')
                Path(financial_csv).parent.mkdir(parents=True, exist_ok=True)
                financial_df.to_csv(financial_csv, index=False)
                
                # Add as a source
                manager.add_source(CSVDataSource(name="financial_data", file_path=financial_csv))
                logger.info(f"Added real financial data for {len(financial_data)} records")
        except Exception as e:
            logger.error(f"Failed to get financial data from APIs: {str(e)}")
    except ImportError:
        logger.warning("Financial data API clients not available, falling back to sample data")
    
    # Add fallback/sample data sources if needed
    if len(manager.sources) == 0:
        logger.warning("No real financial data sources available, using sample data")
        sample_csv = os.path.join('data', 'raw', 'sample.csv')
        if os.path.exists(sample_csv):
            manager.add_source(CSVDataSource(name="sample_data", file_path=sample_csv))
        
        # Try to use real database if available, otherwise use mock
        try:
            from src.utils.database import DatabaseConnector
            # Test database connection
            db = DatabaseConnector()
            db.connect()
            db.disconnect()
            
            # If connection successful, add as a source
            manager.add_source(DatabaseDataSource(
                name="credit_history", 
                connection_string="",  # Will use config from DATABASE_CONFIGS
                query="SELECT * FROM credit_history"
            ))
            logger.info("Added real database source for credit history")
        except Exception as e:
            logger.warning(f"Database connection failed, using mock data: {str(e)}")
            manager.add_source(DatabaseDataSource(
                name="credit_history", 
                connection_string="mock://credit_db", 
                query="SELECT * FROM credit_history"
            ))
    
    # Ingest structured data
    structured_df = manager.ingest_all()
    
    # Ingest news data (unstructured)
    news_source = NewsDataSource(name="news_data")
    news_df = news_source.load_data()
    
    # Save the raw ingested data
    manager.save_ingested_data(structured_df, output_path)
    
    # Save news data separately
    news_output_path = os.path.join('data', 'processed', 'news_data.csv')
    Path(news_output_path).parent.mkdir(parents=True, exist_ok=True)
    news_df.to_csv(news_output_path, index=False)
    
    print(f"Ingestion complete. Structured data: {structured_df.shape[0]} rows, News data: {news_df.shape[0]} rows")
    
    return {
        "structured_data": structured_df,
        "news_data": news_df
    }

if __name__ == "__main__":
    run_ingestion()