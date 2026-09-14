from fastapi import FastAPI

app = FastAPI(
    title="TraceLedger API",
    version="0.1.0",
    description="Evidence verification and investigation API.",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}