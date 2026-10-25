from contextlib import asynccontextmanager
from backend.app.api.investigation_analysis import (
    router as investigation_analysis_router,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.claims import router as claims_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.investigations import router as investigations_router
from backend.app.api.investigation_results import (
    router as investigation_results_router,
)
from backend.app.api.result_citations import (
    router as result_citations_router,
)
from backend.app.api.investigation_runs import (
    router as investigation_runs_router,
)
from backend.app.core.config import settings
from backend.app.db.pool import pool


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations_router)
app.include_router(claims_router)
app.include_router(evidence_router)
app.include_router(investigation_results_router)
app.include_router(result_citations_router)
app.include_router(investigation_runs_router)
app.include_router(investigation_analysis_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}