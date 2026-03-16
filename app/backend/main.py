from fastapi import FastAPI, HTTPException
import time
import logging
from .core.database import db
from .core.neural import engine
from .routers import films, users

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("edge-cine-api")

from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Infrastructure
    db.initialize()
    logger.info("EdgeCine Infrastructure (Database Pool & Neural Engine) Ready.")
    yield
    # Shutdown
    db.close_all()

app = FastAPI(
    title="EdgeCine Neural Search API",
    version="2.0.0-pro",
    description="High-performance Local Inference Movie Discovery Engine",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

# Add CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080", 
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:8081", 
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(films.router)
app.include_router(users.router)

@app.get("/health")
def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "neural_engine": "online" if engine.onnx_session else "offline",
            "database": "unknown"
        }
    }
    
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        health_status["services"]["database"] = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = "disconnected"
    finally:
        if conn: db.return_connection(conn)
        
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    return health_status

@app.get("/")
def read_root():
    return {
        "app": "EdgeCine Neural Search",
        "status": "active",
        "engine": engine.model_variant
    }