#!/usr/bin/env python
"""
Simple script to check the current operational status of all integrated APIs.
This script provides a quick overview of which APIs are working and which need attention.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.utils.api_client import BaseAPIClient, APIError, AuthenticationError
from src.utils.api_config import FINANCIAL_DATA_PROVIDERS

# Load environment variables
load_dotenv()

def check_api_status() -> List[Dict]:
    """
    Check the operational status of all integrated APIs.
    
    Returns:
        List of dictionaries with API status information
    """
    results = []
    
    for provider_name, config in FINANCIAL_DATA_PROVIDERS.items():
        result = {
            'provider': provider_name,
            'name': provider_name.replace('_', ' ').title(),
            'api_key_configured': bool(config.get('api_key')) and config.get('api_key') != 'demo_key',
            'status': 'unknown',
            'error': None
        }
        
        # Skip detailed testing if API key is not configured
        if not result['api_key_configured']:
            result['status'] = 'not_configured'
            results.append(result)
            continue
        
        # Create a client and make a simple request
        try:
            client = BaseAPIClient(provider_name)
            
            # Different test endpoints for different providers
            if provider_name == 'alpha_vantage':
                response = client.request('', params={'function': 'GLOBAL_QUOTE', 'symbol': 'AAPL'})
                if response and isinstance(response, dict) and 'Global Quote' in response:
                    result['status'] = 'operational'
            
            elif provider_name == 'financial_modeling_prep':
                response = client.request('quote/AAPL')
                if response and isinstance(response, list) and len(response) > 0:
                    result['status'] = 'operational'
            
            elif provider_name == 'marketstack':
                response = client.request('eod', params={'symbols': 'AAPL', 'limit': 1})
                if response and isinstance(response, dict) and 'data' in response:
                    result['status'] = 'operational'
            
            elif provider_name == 'news_api':
                response = client.request('everything', params={'q': 'Apple', 'pageSize': 1})
                if response and isinstance(response, dict) and 'articles' in response:
                    result['status'] = 'operational'
            
        except AuthenticationError as e:
            result['status'] = 'authentication_error'
            result['error'] = str(e)
        except APIError as e:
            result['status'] = 'error'
            result['error'] = str(e)
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f"Unexpected error: {str(e)}"
        
        results.append(result)
    
    return results

def print_status_table(results: List[Dict]):
    """
    Print a formatted table of API status results.
    
    Args:
        results: List of API status dictionaries
    """
    # Define colors for terminal output
    colors = {
        'operational': '\033[92m',  # Green
        'authentication_error': '\033[91m',  # Red
        'error': '\033[91m',  # Red
        'not_configured': '\033[93m',  # Yellow
        'unknown': '\033[90m',  # Gray
        'reset': '\033[0m'
    }
    
    # Print header
    print("\n===== API Status =====\n")
    print(f"{'API Name':<25} {'API Key':<15} {'Status':<20} {'Error':<30}")
    print("-" * 90)
    
    # Print each API's status
    for result in results:
        api_key_status = "Configured" if result['api_key_configured'] else "Not Configured"
        status_color = colors.get(result['status'], colors['reset'])
        status_display = f"{status_color}{result['status'].upper()}{colors['reset']}"
        error_display = result['error'] if result['error'] else ""
        if len(error_display) > 30:
            error_display = error_display[:27] + "..."
            
        print(f"{result['name']:<25} {api_key_status:<15} {status_display:<20} {error_display:<30}")
    
    print("\n")

def main():
    """
    Main function to check and display API status.
    """
    print("Checking API status...")
    results = check_api_status()
    print_status_table(results)
    
    # Print summary and recommendations
    operational_count = sum(1 for r in results if r['status'] == 'operational')
    not_configured_count = sum(1 for r in results if r['status'] == 'not_configured')
    error_count = len(results) - operational_count - not_configured_count
    
    print(f"Summary: {operational_count} operational, {not_configured_count} not configured, {error_count} with errors")
    
    if not_configured_count > 0 or error_count > 0:
        print("\nRecommendations:")
        if not_configured_count > 0:
            print("- Configure missing API keys in your .env file")
        if error_count > 0:
            print("- Check API key validity for APIs with authentication errors")
            print("- Run the full test script for detailed diagnostics: python scripts/test_api_connections.py")
    
    print("\nFor more information, see docs/api_integration_guide.md")

if __name__ == "__main__":
    main()