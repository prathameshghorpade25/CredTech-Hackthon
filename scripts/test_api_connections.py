#!/usr/bin/env python
"""
Test script to verify connections to external APIs used in the CredTech XScore project.

This script tests the connection to each external API integrated in the project:
- Alpha Vantage
- Financial Modeling Prep
- Marketstack
- News API

It verifies API key configuration and reports the operational status of each API.
"""

import os
import sys
import time
from pathlib import Path
import argparse
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.utils.api_client import BaseAPIClient, APIError, AuthenticationError, RateLimitExceeded
from src.utils.api_config import FINANCIAL_DATA_PROVIDERS
from src.ingest.financial_data import AlphaVantageClient, FinancialModelingPrepClient, NewsAPIClient

# Load environment variables
load_dotenv()

def test_api_key_configuration() -> Dict[str, bool]:
    """
    Test if API keys are configured in environment variables.
    
    Returns:
        Dictionary with API provider names as keys and boolean values indicating if keys are configured
    """
    results = {}
    
    for provider, config in FINANCIAL_DATA_PROVIDERS.items():
        api_key = config.get('api_key')
        results[provider] = bool(api_key) and api_key != 'demo_key'
        
    return results

def test_alpha_vantage_connection() -> Dict[str, Any]:
    """
    Test connection to Alpha Vantage API.
    
    Returns:
        Dictionary with test results
    """
    client = AlphaVantageClient()
    result = {
        'provider': 'alpha_vantage',
        'name': 'Alpha Vantage',
        'status': 'unknown',
        'error': None,
        'response': None
    }
    
    try:
        # Test with a simple request for Apple Inc. overview
        response = client.get_company_overview('AAPL')
        
        # Check if we got a valid response
        if response and isinstance(response, dict) and 'Symbol' in response:
            result['status'] = 'operational'
            result['response'] = {
                'Symbol': response.get('Symbol'),
                'Name': response.get('Name'),
                'Description': response.get('Description', '')[:100] + '...' if response.get('Description') else None
            }
        else:
            result['status'] = 'error'
            result['error'] = 'Invalid response format'
            result['response'] = response
            
    except AuthenticationError as e:
        result['status'] = 'authentication_error'
        result['error'] = str(e)
    except RateLimitExceeded as e:
        result['status'] = 'rate_limited'
        result['error'] = str(e)
    except APIError as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Unexpected error: {str(e)}"
        
    return result

def test_financial_modeling_prep_connection() -> Dict[str, Any]:
    """
    Test connection to Financial Modeling Prep API.
    
    Returns:
        Dictionary with test results
    """
    client = FinancialModelingPrepClient()
    result = {
        'provider': 'financial_modeling_prep',
        'name': 'Financial Modeling Prep',
        'status': 'unknown',
        'error': None,
        'response': None
    }
    
    try:
        # Test with a simple request for Apple Inc. financial ratios
        response = client.get_financial_ratios('AAPL')
        
        # Check if we got a valid response
        if response and isinstance(response, list) and len(response) > 0:
            result['status'] = 'operational'
            # Just show a sample of the data
            sample_data = response[0] if response else {}
            result['response'] = {
                'date': sample_data.get('date'),
                'ratios_available': list(sample_data.keys())[:5] if sample_data else []
            }
        else:
            result['status'] = 'error'
            result['error'] = 'Invalid response format'
            result['response'] = response
            
    except AuthenticationError as e:
        result['status'] = 'authentication_error'
        result['error'] = str(e)
    except RateLimitExceeded as e:
        result['status'] = 'rate_limited'
        result['error'] = str(e)
    except APIError as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Unexpected error: {str(e)}"
        
    return result

def test_marketstack_connection() -> Dict[str, Any]:
    """
    Test connection to Marketstack API.
    
    Returns:
        Dictionary with test results
    """
    # Create a custom client since we don't have a specific class for Marketstack
    client = BaseAPIClient('marketstack')
    result = {
        'provider': 'marketstack',
        'name': 'Marketstack',
        'status': 'unknown',
        'error': None,
        'response': None
    }
    
    try:
        # Test with a simple request for Apple Inc. end-of-day data
        response = client.request('eod', params={'symbols': 'AAPL', 'limit': 1})
        
        # Check if we got a valid response
        if response and isinstance(response, dict) and 'data' in response:
            result['status'] = 'operational'
            data_sample = response.get('data', [])[0] if response.get('data') else {}
            result['response'] = {
                'pagination': response.get('pagination'),
                'data_sample': {
                    'symbol': data_sample.get('symbol'),
                    'date': data_sample.get('date'),
                    'close': data_sample.get('close')
                } if data_sample else None
            }
        else:
            result['status'] = 'error'
            result['error'] = 'Invalid response format'
            result['response'] = response
            
    except AuthenticationError as e:
        result['status'] = 'authentication_error'
        result['error'] = str(e)
    except RateLimitExceeded as e:
        result['status'] = 'rate_limited'
        result['error'] = str(e)
    except APIError as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Unexpected error: {str(e)}"
        
    return result

def test_news_api_connection() -> Dict[str, Any]:
    """
    Test connection to News API.
    
    Returns:
        Dictionary with test results
    """
    client = NewsAPIClient()
    result = {
        'provider': 'news_api',
        'name': 'News API',
        'status': 'unknown',
        'error': None,
        'response': None
    }
    
    try:
        # Test with a simple request for Apple Inc. news
        response = client.get_company_news('Apple', days=7)
        
        # Check if we got a valid response
        if response and isinstance(response, dict) and 'articles' in response:
            result['status'] = 'operational'
            articles = response.get('articles', [])
            result['response'] = {
                'totalResults': response.get('totalResults'),
                'article_count': len(articles),
                'sample_article': {
                    'title': articles[0].get('title'),
                    'source': articles[0].get('source', {}).get('name'),
                    'publishedAt': articles[0].get('publishedAt')
                } if articles else None
            }
        else:
            result['status'] = 'error'
            result['error'] = 'Invalid response format'
            result['response'] = response
            
    except AuthenticationError as e:
        result['status'] = 'authentication_error'
        result['error'] = str(e)
    except RateLimitExceeded as e:
        result['status'] = 'rate_limited'
        result['error'] = str(e)
    except APIError as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Unexpected error: {str(e)}"
        
    return result

def format_result(result: Dict[str, Any]) -> str:
    """
    Format a test result for display.
    
    Args:
        result: Test result dictionary
        
    Returns:
        Formatted string representation
    """
    status_colors = {
        'operational': '\033[92m',  # Green
        'authentication_error': '\033[91m',  # Red
        'rate_limited': '\033[93m',  # Yellow
        'error': '\033[91m',  # Red
        'unknown': '\033[90m'   # Gray
    }
    
    reset_color = '\033[0m'
    status_color = status_colors.get(result['status'], reset_color)
    
    output = f"\n{'-' * 80}\n"
    output += f"API: {result['name']} ({result['provider']})\n"
    output += f"Status: {status_color}{result['status'].upper()}{reset_color}\n"
    
    if result['error']:
        output += f"Error: {result['error']}\n"
    
    if result['response']:
        output += "Response Sample:\n"
        for key, value in result['response'].items():
            output += f"  {key}: {value}\n"
    
    return output

def main():
    """
    Main function to run API connection tests.
    """
    parser = argparse.ArgumentParser(description='Test external API connections for CredTech XScore')
    parser.add_argument('--api', choices=['all', 'alpha_vantage', 'financial_modeling_prep', 'marketstack', 'news_api'],
                        default='all', help='Specify which API to test')
    args = parser.parse_args()
    
    print("\n===== CredTech XScore API Connection Test =====\n")
    
    # Test API key configuration
    print("Checking API key configuration...")
    key_config = test_api_key_configuration()
    
    for provider, configured in key_config.items():
        status = "\033[92mConfigured\033[0m" if configured else "\033[91mNot Configured\033[0m"
        print(f"  {provider}: {status}")
    
    print("\nTesting API connections...")
    
    # Run the tests based on the specified API
    results = []
    
    if args.api in ['all', 'alpha_vantage']:
        results.append(test_alpha_vantage_connection())
        
    if args.api in ['all', 'financial_modeling_prep']:
        results.append(test_financial_modeling_prep_connection())
        
    if args.api in ['all', 'marketstack']:
        results.append(test_marketstack_connection())
        
    if args.api in ['all', 'news_api']:
        results.append(test_news_api_connection())
    
    # Display results
    for result in results:
        print(format_result(result))
    
    # Summary
    operational_count = sum(1 for r in results if r['status'] == 'operational')
    print(f"\n===== Summary =====")
    print(f"Total APIs tested: {len(results)}")
    print(f"Operational: {operational_count}")
    print(f"Non-operational: {len(results) - operational_count}")
    
    if operational_count < len(results):
        print("\nSome APIs are not operational. Please check the following:")
        print("1. Ensure all API keys are correctly configured in your .env file")
        print("2. Verify that your API keys are valid and not expired")
        print("3. Check if you've exceeded rate limits for any of the APIs")
        print("4. Ensure you have internet connectivity")
        print("\nFor more information, refer to the API documentation in the docs folder.")

if __name__ == "__main__":
    main()