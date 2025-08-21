"""Tests for security utilities"""

import os
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

# Import the security module
from src.utils.security import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, encrypt_sensitive_data, decrypt_sensitive_data,
    generate_encryption_key, setup_https_config
)


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_password_verification(self):
        """Test that a password can be verified against its hash"""
        password = "secure_password123"
        hashed = get_password_hash(password)
        
        # Verify the password matches its hash
        assert verify_password(password, hashed)
        
        # Verify incorrect password fails
        assert not verify_password("wrong_password", hashed)
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test that the same password produces different hashes due to salt"""
        password = "same_password"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Due to different salts


class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key"})
    def test_create_and_decode_token(self):
        """Test creating and decoding a JWT token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Decode the token
        payload = decode_access_token(token)
        
        # Check the subject matches
        assert payload.get("sub") == "testuser"
    
    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key"})
    def test_token_expiration(self):
        """Test that an expired token raises an exception"""
        # Create a token that expires immediately
        data = {"sub": "testuser"}
        expires = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires)
        
        # Attempt to decode the expired token
        with pytest.raises(HTTPException) as excinfo:
            decode_access_token(token)
        
        # Check the exception details
        assert excinfo.value.status_code == 401
        assert "expired" in excinfo.value.detail.lower()
    
    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key"})
    def test_invalid_token(self):
        """Test that an invalid token raises an exception"""
        # Attempt to decode an invalid token
        with pytest.raises(HTTPException) as excinfo:
            decode_access_token("invalid.token.string")
        
        # Check the exception details
        assert excinfo.value.status_code == 401
        assert "invalid" in excinfo.value.detail.lower()


class TestEncryption:
    """Test data encryption and decryption"""
    
    @patch.dict(os.environ, {"ENCRYPTION_KEY": generate_encryption_key()})
    def test_encrypt_decrypt(self):
        """Test encrypting and decrypting data"""
        sensitive_data = "This is sensitive information"
        
        # Encrypt the data
        encrypted = encrypt_sensitive_data(sensitive_data)
        
        # Verify encrypted data is different from original
        assert encrypted != sensitive_data
        
        # Decrypt the data
        decrypted = decrypt_sensitive_data(encrypted)
        
        # Verify decrypted data matches original
        assert decrypted == sensitive_data
    
    def test_missing_encryption_key(self):
        """Test that missing encryption key raises an error"""
        # Ensure ENCRYPTION_KEY is not set
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                encrypt_sensitive_data("test data")
            
            assert "ENCRYPTION_KEY" in str(excinfo.value)


class TestHTTPSConfig:
    """Test HTTPS configuration"""
    
    def test_https_config_with_ssl_files(self):
        """Test HTTPS config with SSL files"""
        with patch.dict(os.environ, {
            "SSL_KEYFILE": "/path/to/keyfile.pem",
            "SSL_CERTFILE": "/path/to/certfile.pem"
        }):
            config = setup_https_config()
            
            assert config["ssl_keyfile"] == "/path/to/keyfile.pem"
            assert config["ssl_certfile"] == "/path/to/certfile.pem"
    
    def test_https_config_without_ssl_files(self):
        """Test HTTPS config without SSL files"""
        with patch.dict(os.environ, {}, clear=True):
            config = setup_https_config()
            
            assert config == {}