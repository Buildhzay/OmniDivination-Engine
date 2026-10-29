from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1 import lunar, numerology, readings, tarot
from app.rate_limit import limiter
from app.request_middleware import RequestAuditMiddleware

app = FastAPI(title="OmniDivination Engine", version="0.2.0")
app.state.limiter = limiter
app.add_middleware(RequestAuditMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau."},
    )


app.include_router(numerology.router, prefix="/api/v1/divination", tags=["divination"])
app.include_router(tarot.router, prefix="/api/v1/divination", tags=["divination"])
app.include_router(lunar.router, prefix="/api/v1/divination", tags=["divination"])
app.include_router(readings.router, prefix="/api/v1/readings", tags=["readings"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
