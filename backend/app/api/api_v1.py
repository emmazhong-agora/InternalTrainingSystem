from fastapi import APIRouter

from app.api.routes import auth, chat, folders, progress, videos

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(folders.router)
api_router.include_router(videos.router)
api_router.include_router(progress.router)
api_router.include_router(chat.router)
