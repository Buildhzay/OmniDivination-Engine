from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LunarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dob: date = Field(description="Ngày sinh dương lịch, định dạng YYYY-MM-DD")
    birth_time: time | None = Field(
        default=None,
        description="Giờ sinh theo giờ địa phương Việt Nam, định dạng HH:MM",
    )

    @field_validator("dob")
    @classmethod
    def dob_in_supported_range(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Ngày sinh không được ở tương lai")
        if value.year < 1900:
            raise ValueError("Năm sinh phải từ 1900 trở đi")
        return value

    @field_validator("birth_time")
    @classmethod
    def birth_time_is_local(cls, value: time | None) -> time | None:
        if value is not None and value.tzinfo is not None:
            raise ValueError("Giờ sinh phải là giờ địa phương, không kèm múi giờ")
        return value


class LunarDateResponse(BaseModel):
    day: int
    month: int
    year: int
    is_leap_month: bool


class CanChiResponse(BaseModel):
    year: str
    month: str
    day: str
    hour: str | None


class LunarResponse(BaseModel):
    solar_date: date
    lunar_date: LunarDateResponse
    can_chi: CanChiResponse
