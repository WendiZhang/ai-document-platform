from fastapi import APIRouter

from app.api.routes import (
    auth_router,
    documents_router,
)

api_router = APIRouter(
    prefix="/api",
)

api_router.include_router(auth_router)
api_router.include_router(documents_router)