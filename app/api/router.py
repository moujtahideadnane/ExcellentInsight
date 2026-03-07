from fastapi import APIRouter

from app.api import auth, dashboard, jobs, settings, upload, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(upload.router)
api_router.include_router(jobs.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(settings.router)
