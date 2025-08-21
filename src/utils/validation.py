"""Data validation utilities for CredTech XScore

This module provides comprehensive validation utilities for input validation,
error handling, and data sanitization to ensure data integrity and security.
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

# Import the unified ValidationError from error_handling
from src.utils.error_handling import ValidationError

class BaseModel:
    """Simple base model to replace pydantic BaseModel"""
    
    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

def Field(default=None, **kwargs):
    """Simple field definition to replace pydantic Field"""
    return default

def validator(field_name):
    """Simple validator decorator to replace pydantic validator"""
    def decorator(func):
        return func
    return decorator

from src.utils.logging import get_app_logger

logger = get_app_logger(__name__)

class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {', '.join(self.errors)}"

class DataValidator:
    """Base class for data validators"""
    
    def validate(self, data: Any) -> ValidationResult:
        """Validate data and return result"""
        raise NotImplementedError("Subclasses must implement validate()")

class SchemaValidator(DataValidator):
    """Validator for checking data schema"""
    
    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        """
        Initialize with schema definition
        
        Args:
            schema: Dictionary mapping field names to their validation rules
                Each field should have:
                - type: The expected Python type
                - required: Whether the field is required
                - validators: Optional list of validation functions
        """
        self.schema = schema
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema"""
        errors = []
        
        # Check for required fields
        for field_name, field_rules in self.schema.items():
            if field_rules.get('required', False) and field_name not in data:
                errors.append(f"Missing required field: {field_name}")
        
        # Validate field types and run custom validators
        for field_name, field_value in data.items():
            if field_name in self.schema:
                field_rules = self.schema[field_name]
                
                # Type validation
                expected_type = field_rules.get('type')
                if expected_type and not isinstance(field_value, expected_type):
                    errors.append(f"Field {field_name} should be of type {expected_type.__name__}")
                
                # Custom validators
                validators = field_rules.get('validators', [])
                for validator_func in validators:
                    result = validator_func(field_value)
                    if not result[0]:
                        errors.append(f"Field {field_name}: {result[1]}")
        
        return ValidationResult(len(errors) == 0, errors)

class DataFrameValidator(DataValidator):
    """Validator for pandas DataFrames"""
    
    def __init__(self, required_columns: List[str], column_types: Optional[Dict[str, type]] = None,
                 custom_validators: Optional[Dict[str, List[Callable]]] = None):
        """
        Initialize DataFrame validator
        
        Args:
            required_columns: List of columns that must be present
            column_types: Optional mapping of column names to expected types
            custom_validators: Optional mapping of column names to validator functions
        """
        self.required_columns = required_columns
        self.column_types = column_types or {}
        self.custom_validators = custom_validators or {}
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate DataFrame structure and content"""
        errors = []
        
        # Check for required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check column types
        for col, expected_type in self.column_types.items():
            if col in df.columns:
                # Check if any values in the column are not of the expected type
                invalid_values = df[~df[col].apply(lambda x: isinstance(x, expected_type))]
                if not invalid_values.empty:
                    errors.append(f"Column {col} contains values of incorrect type. Expected {expected_type.__name__}")
        
        # Run custom validators
        for col, validators in self.custom_validators.items():
            if col in df.columns:
                for validator_func in validators:
                    try:
                        result = validator_func(df[col])
                        if not result[0]:
                            errors.append(f"Column {col}: {result[1]}")
                    except Exception as e:
                        errors.append(f"Error validating column {col}: {str(e)}")
        
        return ValidationResult(len(errors) == 0, errors)

# Common validation functions
def validate_range(min_val: Optional[float] = None, max_val: Optional[float] = None):
    """Create a validator function that checks if a value is within a range"""
    def validator(value):
        if min_val is not None and value < min_val:
            return False, f"Value {value} is less than minimum {min_val}"
        if max_val is not None and value > max_val:
            return False, f"Value {value} is greater than maximum {max_val}"
        return True, ""
    return validator

def validate_regex(pattern: str, error_message: str = "Invalid format"):
    """Create a validator function that checks if a string matches a regex pattern"""
    compiled_pattern = re.compile(pattern)
    def validator(value):
        if not isinstance(value, str):
            return False, "Value is not a string"
        if not compiled_pattern.match(value):
            return False, error_message
        return True, ""
    return validator

def validate_enum(allowed_values: List[Any]):
    """Create a validator function that checks if a value is in a set of allowed values"""
    def validator(value):
        if value not in allowed_values:
            return False, f"Value {value} is not one of the allowed values: {', '.join(map(str, allowed_values))}"
        return True, ""
    return validator

def validate_not_empty(value):
    """Validate that a value is not empty"""
    if isinstance(value, str) and not value.strip():
        return False, "Value cannot be empty"
    if hasattr(value, '__len__') and len(value) == 0:
        return False, "Value cannot be empty"
    return True, ""

# Credit score specific validators
def create_credit_score_validator():
    """Create a validator for credit score input data"""
    schema = {
        'issuer': {
            'type': str,
            'required': True,
            'validators': [validate_not_empty]
        },
        'income': {
            'type': (int, float),
            'required': True,
            'validators': [validate_range(min_val=0)]
        },
        'balance': {
            'type': (int, float),
            'required': True,
            'validators': [validate_range(min_val=0)]
        },
        'transactions': {
            'type': int,
            'required': True,
            'validators': [validate_range(min_val=0)]
        },
        'news_sentiment': {
            'type': (int, float),
            'required': False,
            'validators': [validate_range(min_val=-1, max_val=1)]
        }
    }
    
    return SchemaValidator(schema)

# Input sanitization functions
def sanitize_input(input_str: str) -> str:
    """Sanitize input string to prevent injection attacks"""
    if not isinstance(input_str, str):
        return str(input_str) if input_str is not None else ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\\\\]', '', input_str)
    return sanitized

def sanitize_dict(data: Dict) -> Dict:
    """Sanitize all string values in a dictionary"""
    sanitized_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_input(value)
        else:
            sanitized_data[key] = value
    
    return sanitized_data

# Password validation
def validate_password_strength(password: str) -> ValidationResult:
    """Validate password strength
    
    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return ValidationResult(len(errors) == 0, errors)

# Email validation
def validate_email(email: str) -> ValidationResult:
    """Validate email format"""
    if not email:
        return ValidationResult(False, ["Email cannot be empty"])
    
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return ValidationResult(False, ["Invalid email format"])
    
    return ValidationResult(True)

# Date validation
def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> ValidationResult:
    """Validate that a string is in the specified date format"""
    try:
        datetime.strptime(date_str, format_str)
        return ValidationResult(True)
    except ValueError:
        return ValidationResult(False, [f"Invalid date format. Expected format: {format_str}"])

# Example usage
def validate_credit_score_input(data: Dict[str, Any]) -> ValidationResult:
    """Validate credit score input data"""
    validator = create_credit_score_validator()
    return validator.validate(data)