# backend/src/main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from backend.src.api.endpoints import (
    auth, fraud_cases, detectors, dashboard, reports, admin
)
from backend.src.config.settings import Settings
from backend.src.infrastructure.middleware.auth_middleware import AuthMiddleware
from backend.src.infrastructure.middleware.error_handler import ErrorHandlerMiddleware
from backend.src.infrastructure.middleware.rate_limit import RateLimitMiddleware
from backend.src.infrastructure.persistence.db_context import init_database
from backend.src.infrastructure.tasks.scheduler import start_scheduler
from backend.src.infrastructure.websocket.manager import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Fraud Detection System...")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Start background scheduler
    if settings.FRAUD_DETECTION_ENABLED:
        start_scheduler()
        logger.info("Fraud detection scheduler started")
    
    # Initialize WebSocket manager
    if settings.WEBSOCKET_ENABLED:
        app.state.ws_manager = WebSocketManager()
        logger.info("WebSocket manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fraud Detection System...")
    
    # Cleanup resources
    if hasattr(app.state, "ws_manager"):
        await app.state.ws_manager.disconnect_all()


# Create FastAPI application
app = FastAPI(
    title="Fraud Detection System",
    description="Enterprise-grade fraud detection system with real-time monitoring",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE
    )

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuthMiddleware, exclude_paths=["/api/v1/auth/login", "/api/v1/health"])

# Add trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.petroecuador.com.ec"]
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(fraud_cases.router, prefix="/api/v1/fraud-cases", tags=["Fraud Cases"])
app.include_router(detectors.router, prefix="/api/v1/detectors", tags=["Detectors"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fraud Detection System API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    from backend.src.infrastructure.persistence.db_context import get_db_context
    from backend.src.infrastructure.persistence.firebird_connector import get_firebird_connector
    
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check SQL Server
    try:
        db_context = get_db_context()
        db_context.execute_query("SELECT 1")
        health_status["services"]["sql_server"] = "operational"
    except Exception as e:
        health_status["services"]["sql_server"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Firebird
    try:
        fb_connector = get_firebird_connector()
        fb_connector.test_connection()
        health_status["services"]["firebird"] = "operational"
    except Exception as e:
        health_status["services"]["firebird"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Application started on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Application shutting down...")
    
    # Cleanup database connections
    from backend.src.infrastructure.persistence.db_context import get_db_context
    db_context = get_db_context()
    db_context.cleanup()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )