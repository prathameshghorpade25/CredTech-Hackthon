"""Database connection utilities"""

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Union, Any
import logging

from src.utils.api_config import DATABASE_CONFIGS
from src.utils.logging import get_app_logger

logger = get_app_logger(__name__)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

class DatabaseConnector:
    """Database connection manager"""
    
    def __init__(self, db_type: str = "postgres"):
        """Initialize database connector
        
        Args:
            db_type: Type of database (must be in DATABASE_CONFIGS)
        """
        if db_type not in DATABASE_CONFIGS:
            raise ValueError(f"Unknown database type: {db_type}. Available types: {list(DATABASE_CONFIGS.keys())}")
            
        self.db_type = db_type
        self.config = DATABASE_CONFIGS[db_type]
        self.engine = None
        self.connection = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            connection_string = self.config['connection_string']()
            logger.info(f"Connecting to {self.db_type} database at {self.config['host']}:{self.config['port']}")
            self.engine = create_engine(connection_string)
            self.connection = self.engine.connect()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise DatabaseError(f"Failed to connect to database: {str(e)}")
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
        
        if self.engine:
            self.engine.dispose()
            
        self.connection = None
        self.engine = None
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results as DataFrame
        """
        if not self.connection:
            self.connect()
            
        try:
            logger.debug(f"Executing query: {query}")
            result = pd.read_sql_query(text(query), self.connection, params=params)
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    def execute_statement(self, statement: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute SQL statement (INSERT, UPDATE, DELETE) and return affected rows
        
        Args:
            statement: SQL statement
            params: Statement parameters
            
        Returns:
            Number of affected rows
        """
        if not self.connection:
            self.connect()
            
        try:
            logger.debug(f"Executing statement: {statement}")
            result = self.connection.execute(text(statement), params or {})
            row_count = result.rowcount
            logger.info(f"Statement executed successfully, affected {row_count} rows")
            return row_count
        except Exception as e:
            logger.error(f"Statement execution failed: {str(e)}")
            raise DatabaseError(f"Statement execution failed: {str(e)}")
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = "append") -> int:
        """Insert DataFrame into database table
        
        Args:
            df: DataFrame to insert
            table_name: Target table name
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            
        Returns:
            Number of rows inserted
        """
        if not self.engine:
            self.connect()
            
        try:
            logger.info(f"Inserting {len(df)} rows into table {table_name}")
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            logger.info(f"Successfully inserted {len(df)} rows into {table_name}")
            return len(df)
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {str(e)}")
            raise DatabaseError(f"Failed to insert data into {table_name}: {str(e)}")