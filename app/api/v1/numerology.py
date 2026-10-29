from datetime import date

from fastapi import APIRouter, Header, Request

from app.ai.interpreter import DISCLAIMER, interpret_numerology
from app.api.v1.llm_errors import call_interpreter
from app.api.v1.reading_storage import (
    persist_reading_if_owned,
    resolve_optional_owner,
)
from app.engine.name_numerology import calculate_expression, calculate_soul_urge
from app.engine.numerology import calculate_life_path, calculate_personal_year
from app.schemas.numerology import (
    NumerologyInterpretRequest,
    NumerologyInterpretResponse,
    NumerologyRequest,
    NumerologyResponse,
)
from app.rate_limit import limiter

router = APIRouter()


def _calculate(req: NumerologyRequest) -> NumerologyResponse:
    year = req.target_year or date.today().year
    result = NumerologyResponse(
        life_path=calculate_life_path(req.dob),
        personal_year=calculate_personal_year(req.dob, year),
        target_year=year,
    )
    if req.full_name:
        result.soul_urge = calculate_soul_urge(req.full_name)
        result.expression = calculate_expression(req.full_name)
    return result


@router.post("/numerology", response_model=NumerologyResponse)
@limiter.limit("60/minute")
def numerology(
    request: Request,
    req: NumerologyRequest,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> NumerologyResponse:
    owner_id = resolve_optional_owner(reading_token)
    result = _calculate(req)
    persist_reading_if_owned(owner_id, "numerology", result.model_dump(mode="json"))
    return result


@router.post("/numerology/interpret", response_model=NumerologyInterpretResponse)
@limiter.limit("10/minute")
def numerology_interpret(
    request: Request,
    req: NumerologyInterpretRequest,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> NumerologyInterpretResponse:
    owner_id = resolve_optional_owner(reading_token)
    calculated = _calculate(req)
    text = call_interpreter(
        interpret_numerology,
        life_path=calculated.life_path,
        personal_year=calculated.personal_year,
        target_year=calculated.target_year,
        soul_urge=calculated.soul_urge,
        expression=calculated.expression,
        topic=req.topic,
    )
    result = NumerologyInterpretResponse(
        **calculated.model_dump(),
        interpretation=text,
        disclaimer=DISCLAIMER,
    )
    persist_reading_if_owned(owner_id, "numerology", result.model_dump(mode="json"))
    return result
