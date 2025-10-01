"""
FastAPI main application for Predictive Maintenance Platform
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from api.routes import ingest, predict, alerts, chat
from api.deps import get_settings
from api.telemetry import setup_telemetry
from persistence.db import init_db

# Prometheus metrics
REQUEST_COUNT = Counter(
    'pdm_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'pdm_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Predictive Maintenance API...")
    setup_telemetry()
    await init_db()
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Predictive Maintenance API",
        description="AI-powered predictive maintenance platform for industrial equipment",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else ["yourdomain.com"]
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response
    
    # Include routers
    app.include_router(ingest.router, prefix="/api/v1", tags=["ingestion"])
    app.include_router(predict.router, prefix="/api/v1", tags=["prediction"])
    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    
    # Health check endpoint
    @app.get("/healthz", tags=["health"])
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "timestamp": time.time()}
    
    # Metrics endpoint
    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Root endpoint
    @app.get("/", tags=["info"])
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Predictive Maintenance API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An error occurred"
            }
        )
    
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )



