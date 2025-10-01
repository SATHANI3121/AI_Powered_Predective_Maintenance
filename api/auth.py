"""
Authentication and authorization utilities
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# Azure Key Vault client
_key_vault_client: Optional[SecretClient] = None


def get_key_vault_client() -> Optional[SecretClient]:
    """Get Azure Key Vault client"""
    global _key_vault_client
    if _key_vault_client is None:
        try:
            vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            if vault_url:
                credential = DefaultAzureCredential()
                _key_vault_client = SecretClient(vault_url=vault_url, credential=credential)
                logger.info("Azure Key Vault client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Key Vault client: {e}")
    return _key_vault_client


def get_secret(secret_name: str, default_value: str = None) -> str:
    """Get secret from Azure Key Vault or environment"""
    try:
        client = get_key_vault_client()
        if client:
            secret = client.get_secret(secret_name)
            return secret.value
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_name} from Key Vault: {e}")
    
    # Fallback to environment variable
    return os.getenv(secret_name, default_value)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Get secret from Key Vault or environment
    secret_key = get_secret("JWT_SECRET_KEY", JWT_SECRET_KEY)
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        # Get secret from Key Vault or environment
        secret_key = get_secret("JWT_SECRET_KEY", JWT_SECRET_KEY)
        
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(token_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get current user from token data"""
    user_id = token_data.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # In a real implementation, you would fetch user from database
    # For now, return basic user info from token
    return {
        "id": user_id,
        "username": token_data.get("username", "unknown"),
        "email": token_data.get("email", ""),
        "role": token_data.get("role", "user"),
        "permissions": token_data.get("permissions", [])
    }


def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check if user has specific permission"""
    user_permissions = user.get("permissions", [])
    user_role = user.get("role", "user")
    
    # Admin has all permissions
    if user_role == "admin":
        return True
    
    # Check specific permission
    return permission in user_permissions


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used in a more complex auth system
            # For now, we'll implement this in the dependency injection
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AzureADAuth:
    """Azure AD authentication helper"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get Azure AD authorization URL"""
        if not all([self.tenant_id, self.client_id]):
            raise ValueError("Azure AD configuration missing")
        
        return (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
            f"?client_id={self.client_id}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid profile email"
            f"&response_mode=query"
        )
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        # This would implement the OAuth2 flow
        # For now, return a mock response
        return {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }


def create_user_token(
    user_id: str,
    username: str,
    email: str,
    role: str = "user",
    permissions: list = None
) -> str:
    """Create a user token with specified claims"""
    if permissions is None:
        permissions = []
    
    token_data = {
        "sub": user_id,
        "username": username,
        "email": email,
        "role": role,
        "permissions": permissions,
        "iat": datetime.utcnow()
    }
    
    return create_access_token(token_data)


def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    expected_key = get_secret("API_KEY", "dev-CHANGE-ME")
    return api_key == expected_key


def get_machine_permissions(user: Dict[str, Any], machine_id: str) -> list:
    """Get user permissions for specific machine"""
    user_role = user.get("role", "user")
    user_permissions = user.get("permissions", [])
    
    # Base permissions
    permissions = ["read"]
    
    # Role-based permissions
    if user_role in ["admin", "operator"]:
        permissions.extend(["write", "predict", "alert"])
    
    if user_role == "admin":
        permissions.extend(["delete", "configure"])
    
    # Machine-specific permissions (would be fetched from database)
    # For now, return all permissions for demo
    return permissions


def can_access_machine(user: Dict[str, Any], machine_id: str, action: str = "read") -> bool:
    """Check if user can perform action on machine"""
    permissions = get_machine_permissions(user, machine_id)
    return action in permissions


# Mock user database (in production, this would be a real database)
MOCK_USERS = {
    "admin": {
        "id": "admin-001",
        "username": "admin",
        "email": "admin@company.com",
        "role": "admin",
        "permissions": ["read", "write", "delete", "configure", "predict", "alert"]
    },
    "operator": {
        "id": "operator-001", 
        "username": "operator",
        "email": "operator@company.com",
        "role": "operator",
        "permissions": ["read", "write", "predict", "alert"]
    },
    "viewer": {
        "id": "viewer-001",
        "username": "viewer", 
        "email": "viewer@company.com",
        "role": "viewer",
        "permissions": ["read"]
    }
}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password"""
    # In production, this would query a real database
    if username in MOCK_USERS:
        user = MOCK_USERS[username]
        # For demo, accept any password
        return user
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    for user in MOCK_USERS.values():
        if user["id"] == user_id:
            return user
    return None



