import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from models.database import create_db_and_tables
from api import reports_router, admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RESQ - Disaster Relief Platform",
    description="A high-performance backend for disaster relief operations where victims report disasters and NGOs manage rescue operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "RESQ Team",
        "email": "expirify2k24@gmail.com"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router)
app.include_router(admin_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RESQ API"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to RESQ Disaster Relief Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database and tables on startup"""
    try:
        create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )