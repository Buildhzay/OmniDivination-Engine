from fastapi import FastAPI

from app.api.v1 import numerology, tarot

app = FastAPI(title="OmniDivination Engine", version="0.2.0")

app.include_router(numerology.router, prefix="/api/v1/divination", tags=["divination"])
app.include_router(tarot.router, prefix="/api/v1/divination", tags=["divination"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
