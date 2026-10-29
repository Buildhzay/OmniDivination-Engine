from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.engine.name_numerology import normalize_name


class NumerologyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dob: date = Field(description="Ngày sinh dương lịch, định dạng YYYY-MM-DD")
    full_name: str | None = Field(
        default=None,
        max_length=100,
        description="Họ tên khai sinh (không bắt buộc)",
    )
    target_year: int | None = Field(
        default=None,
        ge=1900,
        le=2200,
        description="Năm cần xem; mặc định là năm hiện tại",
    )

    @field_validator("dob")
    @classmethod
    def dob_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Ngày sinh không được ở tương lai")
        if value.year < 1900:
            raise ValueError("Năm sinh phải từ 1900 trở đi")
        return value

    @field_validator("full_name")
    @classmethod
    def name_has_letters(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not normalize_name(value):
            raise ValueError("Họ tên phải có chữ cái")
        return value


class NumerologyResponse(BaseModel):
    life_path: int
    personal_year: int
    target_year: int
    soul_urge: int | None = None
    expression: int | None = None


class NumerologyInterpretRequest(NumerologyRequest):
    topic: Literal["general", "career"] = Field(
        default="general",
        description="Chủ đề quan tâm",
    )


class NumerologyInterpretResponse(NumerologyResponse):
    interpretation: str
    disclaimer: str
