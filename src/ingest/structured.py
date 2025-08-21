import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from src.utils.logging import get_app_logger

logger = get_app_logger(__name__)

class StructuredDataSource:
    """Base class for structured data sources"""
    
    def __init__(self, name: str):
        self.name = name
    
    def load_data(self) -> pd.DataFrame:
        """Load data from the source"""
        raise NotImplementedError("Subclasses must implement this method")

class CSVDataSource(StructuredDataSource):
    """Data source for CSV files"""
    
    def __init__(self, name: str, file_path: str):
        super().__init__(name)
        self.file_path = file_path
    
    def load_data(self) -> pd.DataFrame:
        """Load data from CSV file"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")
        
        df = pd.read_csv(self.file_path)
        # Add source column to identify the data source
        df['data_source'] = self.name
        return df

class DatabaseDataSource(StructuredDataSource):
    """Data source for database connections"""
    
    def __init__(self, name: str, connection_string: str, query: str, db_type: str = "postgres"):
        super().__init__(name)
        self.connection_string = connection_string
        self.query = query
        self.db_type = db_type
    
    def load_data(self) -> pd.DataFrame:
        """Load data from database"""
        from src.utils.database import DatabaseConnector, DatabaseError
        
        try:
            # Use the database connector to execute the query
            db = DatabaseConnector(self.db_type)
            df = db.execute_query(self.query)
            db.disconnect()
            
            # Add source column
            df['data_source'] = self.name
            return df
            
        except DatabaseError as e:
            logger.error(f"Error loading data from database: {str(e)}")
            # Fallback to mock data if available in development/testing
            if os.environ.get('ENVIRONMENT') in ['development', 'testing']:
                mock_path = os.path.join('data', 'raw', f"{self.name}_mock.csv")
                if os.path.exists(mock_path):
                    logger.warning(f"Using mock data from {mock_path} as fallback")
                    df = pd.read_csv(mock_path)
                    df['data_source'] = self.name
                    return df
            
            # Return empty dataframe with expected schema
            return pd.DataFrame({
                'issuer': [],
                'asof_date': [],
                'income': [],
                'balance': [],
                'transactions': [],
                'target': [],
                'data_source': []
            })

class DataIngestionManager:
    """Manager for ingesting data from multiple sources"""
    
    def __init__(self):
        self.sources: Dict[str, StructuredDataSource] = {}
    
    def add_source(self, source: StructuredDataSource):
        """Add a data source"""
        self.sources[source.name] = source
    
    def ingest_all(self) -> pd.DataFrame:
        """Ingest data from all sources and combine"""
        dfs = []
        
        for name, source in self.sources.items():
            try:
                df = source.load_data()
                dfs.append(df)
                print(f"Successfully ingested data from {name}")
            except Exception as e:
                print(f"Error ingesting data from {name}: {e}")
        
        if not dfs:
            raise ValueError("No data was successfully ingested")
        
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Convert date strings to datetime objects
        if 'asof_date' in combined_df.columns:
            combined_df['asof_date'] = pd.to_datetime(combined_df['asof_date'])
        
        return combined_df
    
    def save_ingested_data(self, df: pd.DataFrame, output_path: str):
        """Save ingested data to output path"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved ingested data to {output_path}")