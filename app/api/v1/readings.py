from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel
from slowapi.util import get_remote_address

from app.db.database import (
    create_reading_session,
    delete_reading,
    get_user_id_for_token,
    list_readings,
)
from app.rate_limit import limiter

router = APIRouter()


class ReadingSessionResponse(BaseModel):
    user_id: str
    reading_token: str
    warning: str = "Lưu token an toàn; token chỉ được trả về khi tạo phiên."


class ReadingHistoryItem(BaseModel):
    id: str
    module: str
    created_at: str
    result: dict[str, Any]


@router.post("/session", response_model=ReadingSessionResponse, status_code=201)
@limiter.limit("5/minute", key_func=get_remote_address)
def create_session(request: Request) -> ReadingSessionResponse:
    user_id, token = create_reading_session()
    return ReadingSessionResponse(user_id=user_id, reading_token=token)


def _required_owner_id(reading_token: str | None) -> str:
    if reading_token is None:
        raise HTTPException(
            status_code=401,
            detail="Cần cung cấp X-Reading-Token.",
        )
    user_id = get_user_id_for_token(reading_token)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Reading token không hợp lệ.",
        )
    return user_id


@router.get("/history", response_model=list[ReadingHistoryItem])
@limiter.limit("60/minute", key_func=get_remote_address)
def reading_history(
    request: Request,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReadingHistoryItem]:
    user_id = _required_owner_id(reading_token)
    return [
        ReadingHistoryItem(**reading)
        for reading in list_readings(user_id, limit=limit, offset=offset)
    ]


@router.delete("/history/{reading_id}", status_code=204)
@limiter.limit("60/minute", key_func=get_remote_address)
def delete_reading_history(
    request: Request,
    reading_id: UUID,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> Response:
    user_id = _required_owner_id(reading_token)
    if not delete_reading(user_id, str(reading_id)):
        raise HTTPException(status_code=404, detail="Reading không tồn tại.")
    return Response(status_code=204)
