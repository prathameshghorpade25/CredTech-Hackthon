# CredTech XScore API Security Guide

This document provides guidelines for securing the CredTech XScore API in production environments.

## Security Features

The CredTech XScore API includes the following security features:

1. **JWT Authentication**: Secure token-based authentication for API access
2. **Password Hashing**: Secure storage of user credentials using bcrypt
3. **Data Encryption**: Encryption of sensitive data using Fernet symmetric encryption
4. **HTTPS Support**: TLS/SSL encryption for API communication
5. **Environment-based Configuration**: Separation of security settings from code

## Setup Instructions

### 1. Generate Security Keys

Use the provided script to generate secure keys:

```bash
python scripts/generate_keys.py
```

For production environments with proper SSL certificates:

```bash
python scripts/generate_keys.py --generate-ssl --common-name your-domain.com
```

This will create a `.env.security` file with the necessary security configuration.

### 2. Configure Environment Variables

Merge the generated `.env.security` file with your production `.env` file or set the environment variables directly in your production environment:

```
# JWT Authentication
JWT_SECRET_KEY=your_generated_jwt_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Data Encryption
ENCRYPTION_KEY=your_generated_encryption_key

# HTTPS Configuration (if using SSL)
SSL_KEYFILE=path/to/ssl_key.pem
SSL_CERTFILE=path/to/ssl_cert.pem
```

### 3. User Management

In production, replace the mock user database in `src/serve/api.py` with a proper database integration. Ensure that:

- User passwords are hashed using the `get_password_hash()` function from `src/utils/security.py`
- User authentication uses the `verify_password()` function
- Consider implementing rate limiting for authentication attempts

### 4. HTTPS Configuration

For production environments, obtain proper SSL certificates from a trusted certificate authority. Options include:

- Let's Encrypt (free)
- Commercial SSL providers
- Internal CA for enterprise environments

Update the SSL configuration in your environment variables:

```
SSL_KEYFILE=/path/to/your/keyfile.pem
SSL_CERTFILE=/path/to/your/certfile.pem
```

### 5. API Key Authentication

For machine-to-machine communication, consider implementing API key authentication:

1. Generate API keys using the `generate_api_key()` function in `src/utils/security.py`
2. Store API keys securely in your database
3. Implement API key validation middleware

## Security Best Practices

### Environment Variables

- Never commit `.env` files to version control
- Use different keys for development, staging, and production
- Rotate keys periodically

### Access Control

- Implement role-based access control for different API endpoints
- Limit access to sensitive endpoints
- Implement proper authorization checks

### Data Protection

- Encrypt sensitive data at rest using the provided encryption utilities
- Implement proper data retention policies
- Consider implementing field-level encryption for highly sensitive data

### Monitoring and Logging

- Monitor failed authentication attempts
- Log security-related events
- Implement alerts for suspicious activities

### Regular Updates

- Keep dependencies updated
- Apply security patches promptly
- Conduct regular security reviews

## Security Headers

Consider adding the following security headers to your API responses:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# In production, redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Restrict hosts that can connect to your API
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [Encryption Best Practices](https://cryptography.io/en/latest/)