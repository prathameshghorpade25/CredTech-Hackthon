# API Integration Guide

## Overview

The CredTech XScore project integrates with several external financial data APIs to gather information for credit scoring. This guide provides details on each API, its operational status, configuration requirements, and testing procedures.

## Integrated APIs

The following external APIs are integrated into the project:

1. **Alpha Vantage** - Financial market data including company overviews and time series data
2. **Financial Modeling Prep** - Financial statements, ratios, and metrics
3. **Marketstack** - Real-time and historical stock data
4. **News API** - News articles for sentiment analysis

## API Configuration

### Environment Variables

All API keys are configured through environment variables in the `.env` file. The project includes a `.env.example` file that you can copy and modify:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your API keys
```

Required API key environment variables:

```
ALPHA_VANTAGE_API_KEY=your_api_key_here
FMP_API_KEY=your_api_key_here
MARKETSTACK_API_KEY=your_api_key_here
NEWS_API_KEY=your_api_key_here
```

### Obtaining API Keys

1. **Alpha Vantage**
   - Visit: https://www.alphavantage.co/support/#api-key
   - Sign up for a free or premium API key
   - Free tier limitations: 5 API calls per minute, 500 calls per day

2. **Financial Modeling Prep**
   - Visit: https://financialmodelingprep.com/developer/docs/pricing
   - Sign up for an account and select a plan
   - Free tier available with limited endpoints

3. **Marketstack**
   - Visit: https://marketstack.com/product
   - Sign up for an account and select a plan
   - Free tier limitations: 1000 requests per month, limited endpoints

4. **News API**
   - Visit: https://newsapi.org/register
   - Sign up for an API key
   - Free tier limitations: 100 requests per day, no historical data

## Testing API Connections

The project includes a script to test the connection to each API and verify that your API keys are correctly configured.

### Using the Test Script

Run the following command from the project root directory:

```bash
python scripts/test_api_connections.py
```

This will test all integrated APIs and report their operational status.

To test a specific API:

```bash
python scripts/test_api_connections.py --api alpha_vantage
```

Replace `alpha_vantage` with any of: `financial_modeling_prep`, `marketstack`, or `news_api`.

### Interpreting Test Results

The test script will output the following information for each API:

- **API Key Configuration**: Whether the API key is configured in your `.env` file
- **Connection Status**: Whether the API is operational, has authentication errors, or other issues
- **Response Sample**: A sample of the data returned by the API

Possible status values:

- **OPERATIONAL**: The API is working correctly
- **AUTHENTICATION_ERROR**: The API key is invalid or missing
- **RATE_LIMITED**: You've exceeded the API's rate limits
- **ERROR**: Other errors occurred during the connection test

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify that your API key is correctly entered in the `.env` file
   - Check if your API key has expired or been revoked
   - Ensure you're using the correct API key for the service

2. **Rate Limiting**
   - Most APIs have rate limits, especially on free tiers
   - The application includes rate limiting logic to handle this
   - Consider upgrading to a paid plan if you need more requests

3. **Connection Errors**
   - Check your internet connection
   - Verify that the API service is not experiencing downtime
   - Check if your network blocks API requests

### API-Specific Troubleshooting

#### Alpha Vantage

- Free tier is limited to 5 requests per minute and 500 per day
- If you receive "Invalid API call" errors, check the symbol you're requesting

#### Financial Modeling Prep

- Different endpoints are available on different subscription tiers
- Check the documentation to ensure the endpoints you need are available on your plan

#### Marketstack

- Historical data may be limited on free plans
- Ensure you're using the correct date format (YYYY-MM-DD) in requests

#### News API

- Free tier only allows access to the last 30 days of news
- Developer plan doesn't allow commercial use

## Error Handling

The application includes robust error handling for API requests:

1. **Retry Logic**: Failed requests are automatically retried with exponential backoff
2. **Rate Limiting**: The application tracks request timestamps and respects API rate limits
3. **Error Classification**: Errors are classified as authentication errors, rate limit errors, or general API errors

## Fallback Mechanisms

If an API is unavailable or returns errors, the application has fallback mechanisms:

1. **Multiple Data Sources**: Critical data can often be obtained from multiple APIs
2. **Cached Data**: Previously fetched data is cached to reduce API calls
3. **Default Values**: The application can use default or estimated values when data is unavailable

## Monitoring and Alerts

The application logs all API interactions, including:

- Request timestamps
- Response status codes
- Error messages
- Rate limit information

These logs can be used to monitor API usage and troubleshoot issues.

## Adding New API Integrations

To add a new API integration:

1. Add the API configuration to `src/utils/api_config.py`
2. Create a client class in `src/ingest/financial_data.py`
3. Update the test script to include the new API
4. Add the necessary environment variables to `.env.example`

## API Documentation

For more information on the APIs used in this project, refer to their official documentation:

- [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)
- [Financial Modeling Prep Documentation](https://financialmodelingprep.com/developer/docs/)
- [Marketstack Documentation](https://marketstack.com/documentation)
- [News API Documentation](https://newsapi.org/docs)