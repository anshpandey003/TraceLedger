from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.pool import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)
    yield
    pool.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence verification and investigation API.",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}