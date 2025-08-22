#!/usr/bin/env python
"""
API Status Dashboard - A simple web-based dashboard to monitor API status.

This script creates a Streamlit dashboard that displays the current status
of all integrated APIs and provides troubleshooting information.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import time
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import streamlit
import streamlit as st

# Import project modules
from src.utils.api_client import BaseAPIClient, APIError, AuthenticationError, RateLimitExceeded
from src.utils.api_config import FINANCIAL_DATA_PROVIDERS
from src.ingest.financial_data import AlphaVantageClient, FinancialModelingPrepClient, NewsAPIClient

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
            'error': None,
            'response': None
        }
        
        # Skip detailed testing if API key is not configured
        if not result['api_key_configured']:
            result['status'] = 'not_configured'
            results.append(result)
            continue
        
        # Create a client and make a simple request
        try:
            if provider_name == 'alpha_vantage':
                client = AlphaVantageClient()
                response = client.get_company_overview('AAPL')
                if response and isinstance(response, dict) and 'Symbol' in response:
                    result['status'] = 'operational'
                    result['response'] = {
                        'Symbol': response.get('Symbol'),
                        'Name': response.get('Name')
                    }
            
            elif provider_name == 'financial_modeling_prep':
                client = FinancialModelingPrepClient()
                response = client.get_financial_ratios('AAPL')
                if response and isinstance(response, list) and len(response) > 0:
                    result['status'] = 'operational'
                    result['response'] = {'data_available': True}
            
            elif provider_name == 'marketstack':
                client = BaseAPIClient('marketstack')
                response = client.request('eod', params={'symbols': 'AAPL', 'limit': 1})
                if response and isinstance(response, dict) and 'data' in response:
                    result['status'] = 'operational'
                    result['response'] = {'data_available': True}
            
            elif provider_name == 'news_api':
                client = NewsAPIClient()
                response = client.get_company_news('Apple', days=7)
                if response and isinstance(response, dict) and 'articles' in response:
                    result['status'] = 'operational'
                    result['response'] = {'articles_count': len(response.get('articles', []))}
            
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
        
        results.append(result)
    
    return results

def main():
    """
    Main function to create the Streamlit dashboard.
    """
    st.set_page_config(
        page_title="CredTech API Status Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 CredTech API Status Dashboard")
    st.write("Monitor the operational status of all integrated APIs")
    
    # Add last updated timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Last updated: {current_time}")
    
    # Add refresh button
    if st.button("Refresh Status"):
        st.experimental_rerun()
    
    # Get API status
    with st.spinner("Checking API status..."):
        results = check_api_status()
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    operational_count = sum(1 for r in results if r['status'] == 'operational')
    not_configured_count = sum(1 for r in results if r['status'] == 'not_configured')
    error_count = sum(1 for r in results if r['status'] in ['authentication_error', 'error'])
    rate_limited_count = sum(1 for r in results if r['status'] == 'rate_limited')
    
    col1.metric("Operational", operational_count)
    col2.metric("Not Configured", not_configured_count)
    col3.metric("Rate Limited", rate_limited_count)
    col4.metric("Errors", error_count)
    
    # Display detailed status for each API
    st.subheader("API Status Details")
    
    for result in results:
        # Create a color-coded status indicator
        status_colors = {
            'operational': 'green',
            'not_configured': 'orange',
            'authentication_error': 'red',
            'rate_limited': 'orange',
            'error': 'red',
            'unknown': 'gray'
        }
        
        status_color = status_colors.get(result['status'], 'gray')
        
        # Create an expander for each API
        with st.expander(f"{result['name']} - {result['status'].upper()}", expanded=result['status'] != 'operational'):
            cols = st.columns([3, 2])
            
            # Left column - Status information
            with cols[0]:
                st.markdown(f"**Status:** <span style='color:{status_color};'>{result['status'].upper()}</span>", unsafe_allow_html=True)
                st.write(f"**API Key:** {'Configured' if result['api_key_configured'] else 'Not Configured'}")
                
                if result['error']:
                    st.error(f"**Error:** {result['error']}")
                
                if result['status'] == 'not_configured':
                    st.info("To configure this API, add the appropriate API key to your .env file.")
                elif result['status'] == 'authentication_error':
                    st.warning("Authentication failed. Please check your API key.")
                elif result['status'] == 'rate_limited':
                    st.warning("Rate limit exceeded. Consider upgrading your API plan or implementing better rate limiting.")
            
            # Right column - Response data and troubleshooting
            with cols[1]:
                if result['response']:
                    st.write("**Sample Response:**")
                    st.json(result['response'])
                
                st.write("**Troubleshooting:**")
                if result['status'] == 'not_configured':
                    st.write("1. Add your API key to the .env file")
                    st.write(f"2. Set {result['provider'].upper()}_API_KEY=your_key_here")
                elif result['status'] == 'authentication_error':
                    st.write("1. Verify your API key is correct")
                    st.write("2. Check if your API key has expired")
                    st.write("3. Ensure you're using the right API key for this service")
                elif result['status'] == 'rate_limited':
                    st.write("1. Wait and try again later")
                    st.write("2. Reduce the frequency of API calls")
                    st.write("3. Consider upgrading your API plan")
                elif result['status'] == 'error':
                    st.write("1. Check the error message for details")
                    st.write("2. Verify your internet connection")
                    st.write("3. Check if the API service is experiencing downtime")
    
    # Documentation and resources
    st.subheader("Documentation & Resources")
    st.markdown("""
    - **API Integration Guide:** See `docs/api_integration_guide.md` for detailed configuration instructions
    - **Test Scripts:** Run `scripts/test_api_connections.py` for more detailed testing
    - **API Documentation:**
        - [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)
        - [Financial Modeling Prep Documentation](https://financialmodelingprep.com/developer/docs/)
        - [Marketstack Documentation](https://marketstack.com/documentation)
        - [News API Documentation](https://newsapi.org/docs)
    """)

if __name__ == "__main__":
    main()