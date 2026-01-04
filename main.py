from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logger import configure_application_logging, get_logger
from src.core.database import init_db
from src.core.auth_middleware import AuthMiddleware
from src.api.modules.video_upload.routers import router as video_upload_router
from src.api.modules.auth.routers import router as auth_router
from src.api.modules.user.routers import router as user_router

# Configure application-wide logging
configure_application_logging(level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize database connection on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    init_db()

# Configure CORS (must be added before authentication middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    AuthMiddleware,
    public_paths={"/", "/health", "/openapi.json", "/docs", "/redoc"},
    public_prefixes=("/auth",),
)

# Register routers
app.include_router(video_upload_router)
app.include_router(auth_router)
app.include_router(user_router)

@app.get("/health", tags=["Root"])
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - health check"""
    logger.info("Health check endpoint accessed")
    return {
        "status": "online",
        "message": f"{settings.PROJECT_NAME} server is running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
