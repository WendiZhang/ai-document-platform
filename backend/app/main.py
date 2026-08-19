from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from dotenv import load_dotenv

from app.api import api_router
from app.api.routes.chat import router as chat_router
from app.api.routes.search import router as search_router
from app.core.config import settings
from app.core.database import get_db


load_dotenv()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Upload documents and ask AI questions "
        "about their content."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(
    chat_router,
    prefix="/api",
)
app.include_router(
    search_router,
    prefix="/api",
)

@app.get("/")
def root():
    return {
        "message": "AI Document Intelligence API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health_check(
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))

        vector_result = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_extension
                    WHERE extname = 'vector'
                )
                """
            )
        )

        vector_enabled = bool(vector_result.scalar())

        return {
            "status": "healthy",
            "database": "connected",
            "pgvector": (
                "enabled"
                if vector_enabled
                else "not enabled"
            ),
        }

    except SQLAlchemyError as error:
        print("DATABASE HEALTH CHECK ERROR:", error)

        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from error
