#!/usr/bin/env python
"""
Utility script to generate secure keys for CredTech XScore API

This script generates:
1. A JWT secret key for token authentication
2. A Fernet encryption key for sensitive data
3. Optional self-signed SSL certificates for development HTTPS
"""

import os
import secrets
import argparse
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta

def generate_jwt_key():
    """Generate a secure random key for JWT signing"""
    return secrets.token_hex(32)

def generate_encryption_key():
    """Generate a Fernet encryption key"""
    return Fernet.generate_key().decode()

def generate_self_signed_cert(common_name="localhost", days_valid=365):
    """Generate a self-signed certificate for development HTTPS"""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CredTech Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days_valid)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(common_name)]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write private key and certificate to files
    with open("ssl_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    
    with open("ssl_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    return "ssl_key.pem", "ssl_cert.pem"

def create_env_file(jwt_key, encryption_key, ssl_key=None, ssl_cert=None):
    """Create a .env file with the generated keys"""
    env_content = f"""# CredTech XScore API Security Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# WARNING: Keep this file secure and never commit to version control

# JWT Authentication
JWT_SECRET_KEY={jwt_key}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Data Encryption
ENCRYPTION_KEY={encryption_key}
"""
    
    if ssl_key and ssl_cert:
        env_content += f"""
# HTTPS Configuration
SSL_KEYFILE={ssl_key}
SSL_CERTFILE={ssl_cert}
"""
    
    with open(".env.security", "w") as f:
        f.write(env_content)
    
    print("Security configuration written to .env.security")
    print("IMPORTANT: Keep this file secure and never commit to version control")

def main():
    parser = argparse.ArgumentParser(description="Generate security keys for CredTech XScore API")
    parser.add_argument("--generate-ssl", action="store_true", help="Generate self-signed SSL certificates")
    parser.add_argument("--common-name", default="localhost", help="Common name for SSL certificate (default: localhost)")
    parser.add_argument("--days-valid", type=int, default=365, help="Days the SSL certificate is valid (default: 365)")
    
    args = parser.parse_args()
    
    print("Generating security keys for CredTech XScore API...")
    
    jwt_key = generate_jwt_key()
    encryption_key = generate_encryption_key()
    
    ssl_key = None
    ssl_cert = None
    
    if args.generate_ssl:
        print(f"Generating self-signed SSL certificate for {args.common_name} (valid for {args.days_valid} days)...")
        ssl_key, ssl_cert = generate_self_signed_cert(args.common_name, args.days_valid)
        print(f"SSL certificate generated: {ssl_cert}")
        print(f"SSL private key generated: {ssl_key}")
    
    create_env_file(jwt_key, encryption_key, ssl_key, ssl_cert)

if __name__ == "__main__":
    main()