# CredTech XScore API Documentation

## Overview

The CredTech XScore API provides credit scoring and financial data analysis capabilities. This RESTful API allows you to obtain credit scores for companies or individuals based on financial data and news sentiment analysis.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

In production environments, this would be replaced with your domain.

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints, you need to:

1. Obtain a token using the `/api/token` endpoint
2. Include the token in the Authorization header of subsequent requests

### Getting a Token

```
POST /api/token
```

**Request Body:**

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header of your requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### Health Check

```
GET /api/health
```

Checks if the API is running and if the credit scoring model is loaded.

**Response:**

```json
{
  "status": "OK",
  "version": "1.0.0",
  "model_loaded": true,
  "timestamp": "2025-08-20T14:30:15.123456"
}
```

### Credit Scoring

#### Score a Single Credit Profile

```
POST /api/score
```

**Request Body:**

```json
{
  "issuer": "Apple Inc.",
  "income": 365000000.0,
  "balance": 45000000.0,
  "transactions": 1250,
  "news_sentiment": 0.75
}
```

**Response:**

```json
{
  "issuer": "Apple Inc.",
  "score": 92.5,
  "rating": "AA",
  "risk_level": "Low",
  "explanation": {
    "income": 0.45,
    "balance": 0.25,
    "transactions": 0.15,
    "news_sentiment": 0.15
  },
  "timestamp": "2025-08-20T14:30:15.123456"
}
```

#### Score Multiple Credit Profiles (Batch)

```
POST /api/batch-score
```

**Request Body:**

```json
{
  "items": [
    {
      "issuer": "Apple Inc.",
      "income": 365000000.0,
      "balance": 45000000.0,
      "transactions": 1250,
      "news_sentiment": 0.75
    },
    {
      "issuer": "Microsoft Corp.",
      "income": 168000000.0,
      "balance": 32000000.0,
      "transactions": 980,
      "news_sentiment": 0.62
    }
  ]
}
```

**Response:**

```json
{
  "results": [
    {
      "issuer": "Apple Inc.",
      "score": 92.5,
      "rating": "AA",
      "risk_level": "Low",
      "explanation": {
        "income": 0.45,
        "balance": 0.25,
        "transactions": 0.15,
        "news_sentiment": 0.15
      },
      "timestamp": "2025-08-20T14:30:15.123456"
    },
    {
      "issuer": "Microsoft Corp.",
      "score": 88.3,
      "rating": "A",
      "risk_level": "Low",
      "explanation": {
        "income": 0.40,
        "balance": 0.30,
        "transactions": 0.15,
        "news_sentiment": 0.15
      },
      "timestamp": "2025-08-20T14:30:15.234567"
    }
  ],
  "count": 2,
  "timestamp": "2025-08-20T14:30:15.345678"
}
```

### Data Endpoints

#### Get Available Issuers

```
GET /api/issuers
```

Returns a list of issuers that can be used for credit scoring.

**Response:**

```json
[
  {
    "name": "Apple Inc.",
    "type": "Company",
    "sector": "Technology",
    "country": "USA"
  },
  {
    "name": "Microsoft Corp.",
    "type": "Company",
    "sector": "Technology",
    "country": "USA"
  },
  {
    "name": "Tesla Inc.",
    "type": "Company",
    "sector": "Automotive",
    "country": "USA"
  },
  {
    "name": "Amazon.com Inc.",
    "type": "Company",
    "sector": "Retail",
    "country": "USA"
  },
  {
    "name": "Google LLC",
    "type": "Company",
    "sector": "Technology",
    "country": "USA"
  }
]
```

### System Information

#### Get Model Information

```
GET /api/model-info
```

Returns information about the credit scoring model.

**Response:**

```json
{
  "name": "CredTech XScore Model",
  "version": "1.0.0",
  "features": ["income", "balance", "transactions", "news_sentiment"],
  "metrics": {
    "accuracy": 0.92,
    "precision": 0.94,
    "recall": 0.89,
    "f1": 0.91,
    "roc_auc": 0.95
  },
  "last_trained": "2025-07-15"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid or cannot be served
- `401 Unauthorized`: Authentication failed or token is invalid
- `403 Forbidden`: The authenticated user doesn't have permission
- `404 Not Found`: The requested resource doesn't exist
- `422 Unprocessable Entity`: Validation error in the request data
- `500 Internal Server Error`: An error occurred on the server
- `503 Service Unavailable`: The model is not available

Error responses include a JSON object with details about the error:

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors, the response includes more detailed information:

```json
{
  "detail": {
    "message": "Validation failed",
    "errors": [
      {
        "loc": ["body", "income"],
        "msg": "Income must be greater than 0",
        "type": "value_error"
      }
    ]
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Each client is limited to:

- 100 requests per minute for `/api/score` endpoint
- 10 requests per minute for `/api/batch-score` endpoint

When the rate limit is exceeded, the API returns a `429 Too Many Requests` status code.

## Environment Variables

The API requires several environment variables to be set:

- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `JWT_ALGORITHM`: Algorithm used for JWT (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes

See the `.env.example` file for a complete list of required environment variables.

## API Versioning

The current API version is `1.0.0`. The version is included in the response of the `/api/health` endpoint.

Future versions will be announced with appropriate deprecation notices for any breaking changes.

## Support

For questions or issues related to the API, please contact:

- Email: support@credtech.example.com
- Documentation: https://credtech.example.com/docs