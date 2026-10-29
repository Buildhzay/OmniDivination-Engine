"""Vietnamese Can Chi calculations for lunar dates and local birth times."""

from datetime import date

from app.engine.lunar_calendar import julian_day_number

HEAVENLY_STEMS = (
    "Giáp",
    "Ất",
    "Bính",
    "Đinh",
    "Mậu",
    "Kỷ",
    "Canh",
    "Tân",
    "Nhâm",
    "Quý",
)
EARTHLY_BRANCHES = (
    "Tý",
    "Sửu",
    "Dần",
    "Mão",
    "Thìn",
    "Tỵ",
    "Ngọ",
    "Mùi",
    "Thân",
    "Dậu",
    "Tuất",
    "Hợi",
)


def _combine(stem_index: int, branch_index: int) -> str:
    return f"{HEAVENLY_STEMS[stem_index % 10]} {EARTHLY_BRANCHES[branch_index % 12]}"


def year_can_chi(year: int) -> str:
    """Return the sexagenary year name for a lunar-calendar year."""
    return _combine(year + 6, year + 8)


def month_can_chi(lunar_year: int, lunar_month: int) -> str:
    """Return the Can Chi name for lunar month 1 through 12."""
    if not 1 <= lunar_month <= 12:
        raise ValueError("Tháng âm lịch phải nằm trong khoảng 1 đến 12")
    year_stem = (lunar_year + 6) % 10
    stem = (year_stem % 5) * 2 + lunar_month + 1
    branch = lunar_month + 1
    return _combine(stem, branch)


def day_can_chi(solar_date: date) -> str:
    """Return the Can Chi day name using the Gregorian date's Julian day."""
    julian_day = julian_day_number(
        solar_date.day,
        solar_date.month,
        solar_date.year,
    )
    return _combine(julian_day + 9, julian_day + 1)


def branch_from_hour(hour: int) -> str:
    """Return the two-hour Earthly Branch for a local 24-hour clock hour."""
    if not 0 <= hour <= 23:
        raise ValueError("Giờ phải nằm trong khoảng 0 đến 23")
    return EARTHLY_BRANCHES[((hour + 1) // 2) % 12]


def hour_can_chi(solar_date: date, hour: int) -> str:
    """Return the Can Chi hour, using civil midnight as the day boundary."""
    if not 0 <= hour <= 23:
        raise ValueError("Giờ phải nằm trong khoảng 0 đến 23")
    julian_day = julian_day_number(
        solar_date.day,
        solar_date.month,
        solar_date.year,
    )
    day_stem = (julian_day + 9) % 10
    branch_index = ((hour + 1) // 2) % 12
    hour_stem = (day_stem % 5) * 2 + branch_index
    return _combine(hour_stem, branch_index)
