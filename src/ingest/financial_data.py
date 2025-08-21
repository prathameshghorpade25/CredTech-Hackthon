"""Financial data sources for production use"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import time

from src.utils.api_client import BaseAPIClient, APIError
from src.utils.logging import get_app_logger

logger = get_app_logger(__name__)

class AlphaVantageClient(BaseAPIClient):
    """Client for Alpha Vantage financial data API"""
    
    def __init__(self):
        super().__init__("alpha_vantage")
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company overview data
        """
        params = {
            "function": "OVERVIEW",
            "symbol": symbol
        }
        
        return self.request("", params=params)
    
    def get_income_statement(self, symbol: str, quarterly: bool = False) -> Dict[str, Any]:
        """Get income statement data
        
        Args:
            symbol: Stock ticker symbol
            quarterly: If True, get quarterly statements, else annual
            
        Returns:
            Income statement data
        """
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": symbol
        }
        
        return self.request("", params=params)
    
    def get_balance_sheet(self, symbol: str, quarterly: bool = False) -> Dict[str, Any]:
        """Get balance sheet data
        
        Args:
            symbol: Stock ticker symbol
            quarterly: If True, get quarterly statements, else annual
            
        Returns:
            Balance sheet data
        """
        params = {
            "function": "BALANCE_SHEET",
            "symbol": symbol
        }
        
        return self.request("", params=params)
    
    def get_cash_flow(self, symbol: str, quarterly: bool = False) -> Dict[str, Any]:
        """Get cash flow statement data
        
        Args:
            symbol: Stock ticker symbol
            quarterly: If True, get quarterly statements, else annual
            
        Returns:
            Cash flow statement data
        """
        params = {
            "function": "CASH_FLOW",
            "symbol": symbol
        }
        
        return self.request("", params=params)
        
    def get_time_series_daily(self, symbol: str, full: bool = False) -> Dict[str, Any]:
        """Get daily time series data
        
        Args:
            symbol: Stock ticker symbol
            full: If True, get full history, else compact (100 data points)
            
        Returns:
            Time series data
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full" if full else "compact"
        }
        
        return self.request("", params=params)

class FinancialModelingPrepClient(BaseAPIClient):
    """Client for Financial Modeling Prep API"""
    
    def __init__(self):
        super().__init__("financial_modeling_prep")
    
    def get_financial_ratios(self, symbol: str, period: str = "annual") -> List[Dict[str, Any]]:
        """Get financial ratios
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            
        Returns:
            List of financial ratios
        """
        endpoint = f"ratios/{symbol}"
        params = {"period": period}
        
        return self.request(endpoint, params=params)
    
    def get_key_metrics(self, symbol: str, period: str = "annual") -> List[Dict[str, Any]]:
        """Get key financial metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            
        Returns:
            List of key metrics
        """
        endpoint = f"key-metrics/{symbol}"
        params = {"period": period}
        
        return self.request(endpoint, params=params)
    
    def get_financial_growth(self, symbol: str, period: str = "annual") -> List[Dict[str, Any]]:
        """Get financial growth metrics
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            
        Returns:
            List of growth metrics
        """
        endpoint = f"financial-growth/{symbol}"
        params = {"period": period}
        
        return self.request(endpoint, params=params)

class NewsAPIClient(BaseAPIClient):
    """Client for News API"""
    
    def __init__(self):
        super().__init__("news_api")
    
    def get_company_news(self, company_name: str, days: int = 30) -> Dict[str, Any]:
        """Get news articles about a company
        
        Args:
            company_name: Name of the company
            days: Number of days to look back
            
        Returns:
            News articles data
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "q": company_name,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "pageSize": 100
        }
        
        return self.request("everything", params=params)