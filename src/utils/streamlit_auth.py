"""Authentication utilities for Streamlit dashboard"""

import os
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from src.utils.enhanced_logging import get_app_logger, get_security_logger, log_with_context, get_session_context
from src.utils.streamlit_logging import log_authentication_attempt, log_authorization_check, log_security_event
from src.utils.secure_data import (
    secure_save_json,
    secure_load_json,
    secure_hash,
    verify_hash,
    sanitize_sensitive_data
)

# Set up logger
logger = get_app_logger(__name__)

# Constants
USER_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                           'data', 'users.json')

# Ensure the user database exists
def ensure_user_db_exists():
    """Create user database if it doesn't exist"""
    if not os.path.exists(USER_DB_PATH):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        
        # Create default admin user
        admin_hash = secure_hash("admin")  # Default password: admin
        users = {
            "admin": {
                "username": "admin",
                "password": admin_hash,  # This is now a dict with hash and salt
                "full_name": "Administrator",
                "email": "admin@credtech.com",
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
        }
        
        # Save to file securely
        secure_save_json(users, USER_DB_PATH, encrypt=True)
        
        logger.info(f"Created default user database at {USER_DB_PATH}")
        logger.info("Default admin user created with password 'admin'. Please change this password immediately.")

# Password hashing
def hash_password(password: str) -> Dict[str, str]:
    """Hash a password for storing using secure hash with salt"""
    return secure_hash(password)

# User management functions
def get_users() -> Dict:
    """Get all users from the database"""
    ensure_user_db_exists()
    
    try:
        return secure_load_json(USER_DB_PATH)
    except Exception as e:
        logger.error(f"Error loading user database: {str(e)}")
        return {}
        
def get_users_data() -> Dict:
    """Get all users from the database (alias for get_users)"""
    return get_users()

def save_users(users: Dict):
    """Save users to the database securely"""
    try:
        # Sanitize data for logging
        sanitized_users = sanitize_sensitive_data(users, ['password'])
        logger.debug(f"Saving user database with {len(users)} users: {sanitized_users.keys()}")
        
        # Save data securely with encryption
        secure_save_json(users, USER_DB_PATH, encrypt=True)
    except Exception as e:
        logger.error(f"Error saving user database: {str(e)}")

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user"""
    users = get_users()
    security_logger = get_security_logger()
    
    # Get session context for logging
    context = get_session_context()
    context['username'] = username
    
    if username in users:
        user = users[username]
        
        # Verify password against stored hash
        if verify_hash(password, user["password"]):
            # Update last login time
            users[username]["last_login"] = datetime.now().isoformat()
            save_users(users)
            
            # Log successful authentication
            log_authentication_attempt(username, True, {
                "role": user["role"],
                "last_login": user.get("last_login"),
                "ip_address": context.get("ip_address", "unknown")
            })
            
            log_with_context(security_logger, "info", f"User {username} authenticated successfully", {
                "role": user["role"],
                "authentication_method": "password"
            })
            
            return True
        else:
            # Log failed authentication - wrong password
            log_authentication_attempt(username, False, {
                "reason": "invalid_password",
                "ip_address": context.get("ip_address", "unknown")
            })
            
            log_with_context(security_logger, "warning", f"Failed authentication attempt for user {username}", {
                "reason": "invalid_password",
                "authentication_method": "password"
            })
    else:
        # Log failed authentication - user not found
        log_authentication_attempt(username, False, {
            "reason": "user_not_found",
            "ip_address": context.get("ip_address", "unknown")
        })
        
        log_with_context(security_logger, "warning", f"Failed authentication attempt for unknown user {username}", {
            "reason": "user_not_found",
            "authentication_method": "password"
        })
    
    logger.warning(f"Failed authentication attempt for user {username}")
    return False

def is_authenticated():
    """Check if user is authenticated"""
    is_auth = "user" in st.session_state and st.session_state["user"] is not None
    
    # Log authentication check
    context = get_session_context()
    log_authorization_check("session_check", is_auth, {
        "session_id": context.get("session_id", "unknown"),
        "ip_address": context.get("ip_address", "unknown")
    })
    
    return is_auth

def login_user(username: str):
    """Set user in session state"""
    users = get_users()
    if username in users:
        st.session_state["user"] = users[username]
        
        # Log user login
        context = get_session_context()
        context["username"] = username
        context["role"] = users[username].get("role", "user")
        
        log_security_event("user_login", {
            "username": username,
            "role": users[username].get("role", "user"),
            "session_id": context.get("session_id", "unknown"),
            "ip_address": context.get("ip_address", "unknown")
        })
        
        log_with_context(get_security_logger(), "info", f"User {username} logged in", {
            "role": users[username].get("role", "user")
        })

def logout_user():
    """Remove user from session state"""
    if "user" in st.session_state:
        username = st.session_state["user"].get("username", "Unknown")
        role = st.session_state["user"].get("role", "user")
        
        # Log user logout
        context = get_session_context()
        log_security_event("user_logout", {
            "username": username,
            "role": role,
            "session_id": context.get("session_id", "unknown"),
            "ip_address": context.get("ip_address", "unknown")
        })
        
        log_with_context(get_security_logger(), "info", f"User {username} logged out", {
            "role": role
        })
        
        del st.session_state["user"]

def get_current_user():
    """Get current user from session state"""
    return st.session_state.get("user", None)

def require_auth(page_func):
    """Decorator to require authentication for a page"""
    def wrapper(*args, **kwargs):
        # Get function name for logging
        func_name = page_func.__name__
        
        if not is_authenticated():
            # Log unauthorized access attempt
            context = get_session_context()
            log_authorization_check(func_name, False, {
                "page": func_name,
                "session_id": context.get("session_id", "unknown"),
                "ip_address": context.get("ip_address", "unknown")
            })
            
            log_with_context(get_security_logger(), "warning", f"Unauthorized access attempt to {func_name}", {
                "page": func_name,
                "session_id": context.get("session_id", "unknown")
            })
            
            st.warning("Please log in to access this page")
            display_login_form()
            return
        
        # User is authenticated, log access and call the page function
        current_user = get_current_user()
        context = get_session_context()
        
        log_authorization_check(func_name, True, {
            "page": func_name,
            "username": current_user.get("username", "unknown"),
            "role": current_user.get("role", "user"),
            "session_id": context.get("session_id", "unknown")
        })
        
        return page_func(*args, **kwargs)
    
    return wrapper

def display_login_form():
    """Display login form"""
    st.subheader("Login")
    
    # Log login form display
    context = get_session_context()
    log_security_event("login_form_displayed", {
        "session_id": context.get("session_id", "unknown"),
        "ip_address": context.get("ip_address", "unknown")
    })
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Log login attempt
            log_security_event("login_attempt", {
                "username": username,
                "session_id": context.get("session_id", "unknown"),
                "ip_address": context.get("ip_address", "unknown")
            })
            
            if authenticate(username, password):
                login_user(username)
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def create_user(username: str, password: str, full_name: str, email: str, role: str = "user") -> bool:
    """Create a new user with secure password hashing"""
    users = get_users()
    
    if username in users:
        logger.warning(f"Attempted to create duplicate user: {username}")
        return False
    
    # Create user with securely hashed password
    users[username] = {
        "username": username,
        "password": hash_password(password),  # Secure hash with salt
        "full_name": full_name,
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Log sanitized user data
    sanitized_user = sanitize_sensitive_data(users[username], ['password'])
    logger.info(f"Creating new user: {sanitized_user}")
    
    save_users(users)
    logger.info(f"Created new user: {username}")
    return True

def update_user(username: str, full_name: str = None, email: str = None, role: str = None) -> bool:
    """Update an existing user's information"""
    users = get_users()
    
    if username not in users:
        logger.warning(f"Attempted to update non-existent user: {username}")
        return False
    
    if full_name is not None:
        users[username]["full_name"] = full_name
    
    if email is not None:
        users[username]["email"] = email
    
    if role is not None:
        users[username]["role"] = role
    
    save_users(users)
    logger.info(f"Updated user: {username}")
    return True

def change_password(username: str, new_password: str) -> bool:
    """Change a user's password with secure hashing"""
    users = get_users()
    
    if username not in users:
        logger.warning(f"Attempted to change password for non-existent user: {username}")
        return False
    
    # Update with securely hashed password
    users[username]["password"] = hash_password(new_password)
    
    save_users(users)
    logger.info(f"Changed password for user: {username}")
    return True

def delete_user(username: str) -> bool:
    """Delete a user"""
    users = get_users()
    
    if username not in users:
        logger.warning(f"Attempted to delete non-existent user: {username}")
        return False
    
    # Don't allow deleting the last admin user
    if users[username]["role"] == "admin":
        admin_count = sum(1 for user in users.values() if user["role"] == "admin")
        if admin_count <= 1:
            logger.warning(f"Attempted to delete the last admin user: {username}")
            return False
    
    del users[username]
    
    save_users(users)
    logger.info(f"Deleted user: {username}")
    return True

def display_user_management():
    """Display user management interface with secure data handling"""
    st.subheader("User Management")
    
    # Get current user
    current_user = get_current_user()
    
    # Only allow admins to manage users
    if not current_user or current_user.get("role") != "admin":
        st.warning("You do not have permission to manage users")
        return
    
    # Display existing users with sanitized data
    users = get_users()
    user_df = pd.DataFrame([
        {
            "Username": user["username"],
            "Full Name": user["full_name"],
            "Email": user["email"],
            "Role": user["role"],
            "Created": user["created_at"],
            "Last Login": user["last_login"] or "Never"
        }
        for user in users.values()
    ])
    
    st.write("### Existing Users")
    st.dataframe(user_df)
    
    # Form to create new user with secure password handling
    st.write("### Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_password_confirm = st.text_input("Confirm Password", type="password")
        new_full_name = st.text_input("Full Name")
        new_email = st.text_input("Email")
        new_role = st.selectbox("Role", ["user", "admin"])
        
        submit = st.form_submit_button("Create User")
        
        if submit:
            if not new_username or not new_password:
                st.error("Username and password are required")
            elif new_username in users:
                st.error(f"User {new_username} already exists")
            elif new_password != new_password_confirm:
                st.error("Passwords do not match")
            else:
                # Sanitize inputs before creating user
                sanitized_username = sanitize_input(new_username)
                sanitized_full_name = sanitize_input(new_full_name)
                sanitized_email = sanitize_input(new_email)
                
                if create_user(sanitized_username, new_password, sanitized_full_name, sanitized_email, new_role):
                    st.success(f"User {sanitized_username} created successfully")
                    st.experimental_rerun()
                else:
                    st.error("Failed to create user")