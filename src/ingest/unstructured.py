import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class UnstructuredDataSource:
    """Base class for unstructured data sources"""
    
    def __init__(self, name: str):
        self.name = name
    
    def load_data(self) -> pd.DataFrame:
        """Load data from the source"""
        raise NotImplementedError("Subclasses must implement this method")

class NewsDataSource(UnstructuredDataSource):
    """Data source for news articles"""
    
    def __init__(self, name: str, file_path: Optional[str] = None):
        super().__init__(name)
        self.file_path = file_path
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def load_data(self) -> pd.DataFrame:
        """Load news data and extract sentiment features"""
        from src.ingest.financial_data import NewsAPIClient
        from src.utils.api_client import APIError
        
        try:
            # Try to get real news data from the API
            news_client = NewsAPIClient()
            company_data = []
            
            # Get news for a list of companies
            # In production, this would be dynamically generated based on the companies we're analyzing
            companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla"]
            
            for company in companies:
                try:
                    # Map company name to ticker symbol (simplified mapping for now)
                    symbol_map = {"Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", 
                                 "Amazon": "AMZN", "Tesla": "TSLA"}
                    symbol = symbol_map.get(company, company)
                    
                    # Get news for this company
                    news_response = news_client.get_company_news(company, days=30)
                    
                    # Process articles
                    if 'articles' in news_response:
                        for article in news_response['articles']:
                            company_data.append({
                                "issuer": symbol,
                                "date": article.get('publishedAt', '').split('T')[0],  # Extract date part
                                "text": article.get('title', '') + ". " + article.get('description', '')
                            })
                            
                except APIError as e:
                    logger.error(f"Error fetching news for {company}: {str(e)}")
                    continue
                    
            # If we got data from the API, use it
            if company_data:
                logger.info(f"Successfully retrieved {len(company_data)} news articles from API")
                news_data = company_data
            else:
                # Fallback to file or mock data
                if self.file_path and os.path.exists(self.file_path):
                    # Load from provided JSON file
                    with open(self.file_path, 'r') as f:
                        news_data = json.load(f)
                        logger.info(f"Using news data from file: {self.file_path}")
                else:
                    # Generate mock news data as last resort
                    news_data = self._generate_mock_news_data()
                    logger.warning("Using generated mock news data as fallback")
                    
        except Exception as e:
            logger.error(f"Error loading news data: {str(e)}")
            # Fallback to file or mock data
            if self.file_path and os.path.exists(self.file_path):
                # Load from provided JSON file
                with open(self.file_path, 'r') as f:
                    news_data = json.load(f)
                    logger.info(f"Using news data from file: {self.file_path}")
            else:
                # Generate mock news data as last resort
                news_data = self._generate_mock_news_data()
                logger.warning("Using generated mock news data as fallback")
            
        # Process news data into a dataframe with sentiment analysis
        records = []
        for item in news_data:
            issuer = item.get('issuer')
            date = item.get('date')
            text = item.get('text', '')
            
            # Perform sentiment analysis
            sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
            
            records.append({
                'issuer': issuer,
                'asof_date': date,
                'news_text': text[:100] + '...' if len(text) > 100 else text,  # Truncate long text
                'news_sentiment_neg': sentiment_scores['neg'],
                'news_sentiment_neu': sentiment_scores['neu'],
                'news_sentiment_pos': sentiment_scores['pos'],
                'news_sentiment_compound': sentiment_scores['compound'],
                'data_source': self.name
            })
        
        df = pd.DataFrame(records)
        if 'asof_date' in df.columns:
            df['asof_date'] = pd.to_datetime(df['asof_date'])
            
        return df
    
    def _generate_mock_news_data(self) -> List[Dict]:
        """Generate mock news data for demonstration purposes"""
        mock_data = [
            {
                "issuer": "ABC",
                "date": "2024-01-08",
                "text": "ABC Corporation announces strong quarterly results, exceeding analyst expectations. The company reported a 15% increase in revenue."
            },
            {
                "issuer": "XYZ",
                "date": "2024-01-09",
                "text": "XYZ Inc. faces challenges as new regulations impact their core business. Stock price dropped 5% following the announcement."
            },
            {
                "issuer": "LMN",
                "date": "2024-01-10",
                "text": "LMN Group acquires smaller competitor to expand market share. The acquisition is expected to be completed by end of quarter."
            },
            {
                "issuer": "QRS",
                "date": "2024-01-11",
                "text": "QRS Technologies unveils innovative new product line that could revolutionize the industry. Early customer feedback has been very positive."
            }
        ]
        
        # Save mock data to file for reproducibility
        mock_path = os.path.join('data', 'raw', 'mock_news.json')
        Path(mock_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(mock_path, 'w') as f:
            json.dump(mock_data, f, indent=2)
            
        return mock_data

class SocialMediaDataSource(UnstructuredDataSource):
    """Data source for social media content (placeholder for future implementation)"""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        super().__init__(name)
        self.api_key = api_key
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def load_data(self) -> pd.DataFrame:
        """Load social media data (mock implementation)"""
        # This would be implemented with actual API calls in a real system
        # For now, return empty dataframe with expected schema
        return pd.DataFrame({
            'issuer': [],
            'asof_date': [],
            'social_text': [],
            'social_sentiment_neg': [],
            'social_sentiment_neu': [],
            'social_sentiment_pos': [],
            'social_sentiment_compound': [],
            'data_source': []
        })