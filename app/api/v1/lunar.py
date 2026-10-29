from fastapi import APIRouter, Header, Request

from app.api.v1.reading_storage import (
    persist_reading_if_owned,
    resolve_optional_owner,
)
from app.engine.can_chi import (
    day_can_chi,
    hour_can_chi,
    month_can_chi,
    year_can_chi,
)
from app.engine.lunar_calendar import solar_to_lunar
from app.rate_limit import limiter
from app.schemas.lunar import (
    CanChiResponse,
    LunarDateResponse,
    LunarRequest,
    LunarResponse,
)

router = APIRouter()


@router.post("/lunar", response_model=LunarResponse)
@limiter.limit("60/minute")
def lunar(
    request: Request,
    req: LunarRequest,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> LunarResponse:
    owner_id = resolve_optional_owner(reading_token)
    lunar_date = solar_to_lunar(req.dob)
    can_chi = CanChiResponse(
        year=year_can_chi(lunar_date.year),
        month=month_can_chi(lunar_date.year, lunar_date.month),
        day=day_can_chi(req.dob),
        hour=hour_can_chi(req.dob, req.birth_time.hour)
        if req.birth_time is not None
        else None,
    )
    result = LunarResponse(
        solar_date=req.dob,
        lunar_date=LunarDateResponse(
            day=lunar_date.day,
            month=lunar_date.month,
            year=lunar_date.year,
            is_leap_month=lunar_date.is_leap_month,
        ),
        can_chi=can_chi,
    )
    if owner_id is not None:
        history_result = result.model_dump(mode="json", exclude={"solar_date"})
        persist_reading_if_owned(owner_id, "lunar", history_result)
    return result
