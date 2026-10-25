"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.api.v1.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database…")
    await init_db()
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Wind Forecast Intelligence API",
    description="UK National Wind Generation Forecast Accuracy Analytics — January 2026",
    version="1.0.0",
    lifespan=lifespan,
)

_allow_credentials = settings.CORS_ORIGINS != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Wind Forecast Intelligence API", "docs": "/docs"}
