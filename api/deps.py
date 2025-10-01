"""
FastAPI dependencies for authentication, database, and other services
"""

import os
import logging
from typing import Generator, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseSettings
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis
from rq import Queue

from persistence.db import get_db
from api.auth import verify_token, get_current_user
from api.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiter
rate_limiter = RateLimiter()


class Settings(BaseSettings):
    """Application settings"""
    # Application
    app_name: str = "Predictive Maintenance API"
    debug: bool = False
    environment: str = "local"
    
    # Security
    api_key: str = "dev-CHANGE-ME"
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Azure
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_key_vault_url: Optional[str] = None
    
    # Database
    database_url: str = "postgresql+psycopg2://user:pass@localhost:5432/pdm"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Azure AI Search
    azure_search_endpoint: Optional[str] = None
    azure_search_key: Optional[str] = None
    azure_search_index_name: str = "pdm-manuals"
    
    # ML
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_backend: str = "faiss"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # File upload
    max_file_size_mb: int = 100
    allowed_file_types: str = "csv,txt"
    upload_temp_dir: str = "./temp_uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Database dependency
def get_database() -> Generator[Session, None, None]:
    """Get database session"""
    db = get_db()
    try:
        yield db
    finally:
        db.close()


# Redis dependency
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Get Redis client"""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url)
    return _redis_client


# RQ Queue dependency
def get_queue() -> Queue:
    """Get RQ queue"""
    redis_client = get_redis()
    return Queue("pdm", connection=redis_client)


# Authentication dependencies
def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key"""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user_dependency(
    token_data: dict = Depends(verify_jwt_token)
) -> dict:
    """Get current user from token"""
    return get_current_user(token_data)


# Rate limiting dependency
def check_rate_limit(request: Request) -> bool:
    """Check rate limit for request"""
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True


# File upload validation
def validate_file_upload(
    file_size: int,
    content_type: str,
    settings: Settings = Depends(get_settings)
) -> bool:
    """Validate file upload"""
    max_size = settings.max_file_size_mb * 1024 * 1024
    allowed_types = settings.allowed_file_types.split(",")
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    if not any(content_type.startswith(t) for t in allowed_types):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    return True


# Machine ID validation
def validate_machine_id(machine_id: str) -> str:
    """Validate machine ID format"""
    if not machine_id or len(machine_id) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid machine ID"
        )
    return machine_id


# Optional authentication (for public endpoints)
def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Optional authentication for public endpoints"""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        return get_current_user(payload)
    except JWTError:
        return None


# Admin role check
def require_admin_role(user: dict = Depends(get_current_user_dependency)) -> dict:
    """Require admin role"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return user


# Machine access check
def check_machine_access(
    machine_id: str,
    user: dict = Depends(get_current_user_dependency)
) -> str:
    """Check if user has access to machine"""
    # In a real implementation, this would check user permissions
    # For now, we'll allow access to all machines
    return machine_id


# Database transaction dependency
@asynccontextmanager
async def get_db_transaction():
    """Get database session with transaction"""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Health check dependencies
def check_database_health(db: Session = Depends(get_database)) -> bool:
    """Check database health"""
    try:
        db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_redis_health(redis_client: redis.Redis = Depends(get_redis)) -> bool:
    """Check Redis health"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Service dependencies
def get_ml_service():
    """Get ML service instance"""
    from ai.model_infer import MLService
    return MLService()


def get_rag_service():
    """Get RAG service instance"""
    from rag.retrieve import RAGService
    return RAGService()


# Monitoring dependencies
def get_metrics_collector():
    """Get metrics collector"""
    from api.telemetry import MetricsCollector
    return MetricsCollector()


# Cache dependencies
def get_cache_service(redis_client: redis.Redis = Depends(get_redis)):
    """Get cache service"""
    from api.cache import CacheService
    return CacheService(redis_client)


# Background task dependencies
def get_background_tasks():
    """Get background task service"""
    from workers.tasks import BackgroundTaskService
    return BackgroundTaskService()


