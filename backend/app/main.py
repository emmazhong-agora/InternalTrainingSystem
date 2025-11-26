from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, videos, progress, materials, chat, agora, prompts, users, categories, statistics, exams
from app.db.session import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered training platform for technical support teams",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["User Management"])
app.include_router(videos.router, prefix=f"{settings.API_V1_STR}/videos", tags=["Videos"])
app.include_router(progress.router, prefix=f"{settings.API_V1_STR}/progress", tags=["Progress"])
app.include_router(materials.router, prefix=f"{settings.API_V1_STR}", tags=["Materials"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["AI Chat"])
app.include_router(agora.router, prefix=f"{settings.API_V1_STR}/agora", tags=["Agora Voice AI"])
app.include_router(prompts.router, prefix=f"{settings.API_V1_STR}/prompts", tags=["Prompt Management"])
app.include_router(categories.router, prefix=f"{settings.API_V1_STR}/categories", tags=["Category Management"])
app.include_router(statistics.router, prefix=f"{settings.API_V1_STR}/statistics", tags=["Statistics"])
app.include_router(exams.router, prefix=f"{settings.API_V1_STR}/exams", tags=["Exam Management"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Internal Training System API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
