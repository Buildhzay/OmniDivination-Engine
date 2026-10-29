from datetime import date

import pytest

from app.engine.lunar_calendar import (
    MAX_SUPPORTED_YEAR,
    MIN_SUPPORTED_YEAR,
    LunarDate,
    solar_to_lunar,
)


@pytest.mark.parametrize(
    ("solar_date", "expected"),
    [
        (date(2006, 7, 3), LunarDate(9, 6, 2006, False)),
        (date(2024, 2, 10), LunarDate(1, 1, 2024, False)),
        (date(2025, 1, 29), LunarDate(1, 1, 2025, False)),
        (date(2024, 9, 17), LunarDate(15, 8, 2024, False)),
        (date(2024, 6, 10), LunarDate(5, 5, 2024, False)),
    ],
)
def test_solar_to_lunar_known_dates(solar_date: date, expected: LunarDate) -> None:
    assert solar_to_lunar(solar_date) == expected


def test_solar_to_lunar_leap_month_boundaries() -> None:
    assert solar_to_lunar(date(2023, 3, 22)) == LunarDate(1, 2, 2023, True)
    assert solar_to_lunar(date(2023, 4, 19)) == LunarDate(29, 2, 2023, True)
    assert solar_to_lunar(date(2023, 4, 20)) == LunarDate(1, 3, 2023, False)


@pytest.mark.parametrize(
    "year",
    [MIN_SUPPORTED_YEAR - 1, MAX_SUPPORTED_YEAR + 1],
)
def test_solar_to_lunar_rejects_unsupported_year(year: int) -> None:
    with pytest.raises(ValueError, match="Năm phải nằm trong khoảng"):
        solar_to_lunar(date(year, 6, 15))
