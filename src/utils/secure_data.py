"""Secure data handling utilities for CredTech XScore"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.utils.logging import get_app_logger
from src.utils.error_handling import DataError

# Set up logger
logger = get_app_logger(__name__)

# Environment variable for encryption key
ENV_KEY_NAME = "CREDTECH_ENCRYPTION_KEY"

def get_encryption_key() -> bytes:
    """Get or generate encryption key
    
    Returns:
        bytes: Encryption key
    """
    # Try to get key from environment variable
    env_key = os.environ.get(ENV_KEY_NAME)
    
    if env_key:
        try:
            # Decode the base64 encoded key
            return base64.urlsafe_b64decode(env_key)
        except Exception as e:
            logger.error(f"Error decoding encryption key: {str(e)}")
    
    # If no key in environment or invalid key, generate a new one
    logger.warning(f"No valid encryption key found in environment variable {ENV_KEY_NAME}. Generating a new key.")
    
    # Generate a new key
    key = Fernet.generate_key()
    
    # Print instructions for setting the key
    logger.info(f"Generated new encryption key. Set the following environment variable:\n"
                f"  {ENV_KEY_NAME}={key.decode()}")
    
    return key

def get_cipher() -> Fernet:
    """Get Fernet cipher for encryption/decryption
    
    Returns:
        Fernet: Cipher for encryption/decryption
    """
    key = get_encryption_key()
    return Fernet(key)

def encrypt_data(data: Union[str, bytes, Dict, list]) -> str:
    """Encrypt data
    
    Args:
        data: Data to encrypt (string, bytes, dict, or list)
    
    Returns:
        str: Base64 encoded encrypted data
    """
    try:
        # Convert data to JSON string if it's a dict or list
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        
        # Convert to bytes if it's a string
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Encrypt the data
        cipher = get_cipher()
        encrypted_data = cipher.encrypt(data)
        
        # Return base64 encoded encrypted data
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting data: {str(e)}")
        raise DataError(f"Failed to encrypt data: {str(e)}")

def decrypt_data(encrypted_data: str) -> Union[str, Dict, list]:
    """Decrypt data
    
    Args:
        encrypted_data: Base64 encoded encrypted data
    
    Returns:
        Union[str, Dict, list]: Decrypted data
    """
    try:
        # Decode base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
        
        # Decrypt the data
        cipher = get_cipher()
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        
        # Convert to string
        decrypted_str = decrypted_bytes.decode('utf-8')
        
        # Try to parse as JSON
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            # If not valid JSON, return as string
            return decrypted_str
    except Exception as e:
        logger.error(f"Error decrypting data: {str(e)}")
        raise DataError(f"Failed to decrypt data: {str(e)}")

def secure_hash(data: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Create a secure hash of data with salt
    
    Args:
        data: Data to hash
        salt: Optional salt, generated if not provided
    
    Returns:
        Dict[str, str]: Dictionary with hash and salt
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Create hash
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode('utf-8'))
    hash_obj.update(data.encode('utf-8'))
    hash_value = hash_obj.hexdigest()
    
    return {
        'hash': hash_value,
        'salt': salt
    }

def verify_hash(data: str, hash_dict: Dict[str, str]) -> bool:
    """Verify data against a hash
    
    Args:
        data: Data to verify
        hash_dict: Dictionary with hash and salt
    
    Returns:
        bool: True if hash matches, False otherwise
    """
    # Extract hash and salt
    stored_hash = hash_dict.get('hash')
    salt = hash_dict.get('salt')
    
    if not stored_hash or not salt:
        return False
    
    # Create hash with the same salt
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode('utf-8'))
    hash_obj.update(data.encode('utf-8'))
    calculated_hash = hash_obj.hexdigest()
    
    # Compare hashes
    return secrets.compare_digest(calculated_hash, stored_hash)

def secure_save_json(data: Dict[str, Any], file_path: str, encrypt: bool = True) -> None:
    """Save data to a JSON file with optional encryption
    
    Args:
        data: Data to save
        file_path: Path to save the file
        encrypt: Whether to encrypt the data
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if encrypt:
            # Encrypt the data
            encrypted_data = encrypt_data(data)
            
            # Save encrypted data
            with open(file_path, 'w') as f:
                json.dump({'encrypted': True, 'data': encrypted_data}, f)
        else:
            # Save unencrypted data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {str(e)}")
        raise DataError(f"Failed to save data: {str(e)}")

def secure_load_json(file_path: str) -> Dict[str, Any]:
    """Load data from a JSON file with automatic decryption if needed
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dict[str, Any]: Loaded data
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return {}
        
        # Load the file
        with open(file_path, 'r') as f:
            file_data = json.load(f)
        
        # Check if data is encrypted
        if isinstance(file_data, dict) and file_data.get('encrypted', False):
            # Decrypt the data
            return decrypt_data(file_data.get('data', ''))
        else:
            # Data is not encrypted
            return file_data
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise DataError(f"Failed to load data: {str(e)}")

def sanitize_sensitive_data(data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
    """Sanitize sensitive data for logging or display
    
    Args:
        data: Data to sanitize
        sensitive_fields: List of sensitive field names
    
    Returns:
        Dict[str, Any]: Sanitized data
    """
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '********'
    
    return sanitized