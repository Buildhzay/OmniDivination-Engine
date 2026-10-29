from datetime import date

from fastapi import APIRouter

from app.ai.interpreter import DISCLAIMER, interpret_numerology
from app.api.v1.llm_errors import call_interpreter
from app.engine.name_numerology import calculate_expression, calculate_soul_urge
from app.engine.numerology import calculate_life_path, calculate_personal_year
from app.schemas.numerology import (
    NumerologyInterpretRequest,
    NumerologyInterpretResponse,
    NumerologyRequest,
    NumerologyResponse,
)

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
def numerology(req: NumerologyRequest) -> NumerologyResponse:
    return _calculate(req)


@router.post("/numerology/interpret", response_model=NumerologyInterpretResponse)
def numerology_interpret(
    req: NumerologyInterpretRequest,
) -> NumerologyInterpretResponse:
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
    return NumerologyInterpretResponse(
        **calculated.model_dump(),
        interpretation=text,
        disclaimer=DISCLAIMER,
    )
