from datetime import date

from fastapi import APIRouter

from app.engine.name_numerology import calculate_expression, calculate_soul_urge
from app.engine.numerology import calculate_life_path, calculate_personal_year
from app.schemas.numerology import NumerologyRequest, NumerologyResponse

router = APIRouter()


@router.post("/numerology", response_model=NumerologyResponse)
def numerology(req: NumerologyRequest) -> NumerologyResponse:
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
