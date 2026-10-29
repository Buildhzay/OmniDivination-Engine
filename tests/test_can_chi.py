from datetime import date

import pytest

from app.engine.can_chi import (
    branch_from_hour,
    day_can_chi,
    hour_can_chi,
    month_can_chi,
    year_can_chi,
)


def test_year_can_chi_examples() -> None:
    assert year_can_chi(2006) == "Bính Tuất"
    assert year_can_chi(1984) == "Giáp Tý"


def test_month_can_chi_uses_lunar_month_and_year_stem() -> None:
    assert month_can_chi(2006, 6) == "Ất Mùi"
    assert month_can_chi(2024, 1) == "Bính Dần"


def test_day_can_chi_uses_julian_day() -> None:
    assert day_can_chi(date(2006, 7, 3)) == "Quý Tỵ"
    assert day_can_chi(date(2024, 2, 10)) == "Giáp Thìn"


def test_branch_from_hour_uses_two_hour_intervals() -> None:
    assert branch_from_hour(15) == "Thân"
    assert branch_from_hour(23) == "Tý"
    assert branch_from_hour(0) == "Tý"
    assert branch_from_hour(1) == "Sửu"


def test_hour_can_chi_uses_civil_midnight_boundary() -> None:
    assert hour_can_chi(date(2006, 7, 3), 15) == "Canh Thân"
    assert hour_can_chi(date(2006, 7, 3), 23) == "Nhâm Tý"
    assert hour_can_chi(date(2006, 7, 4), 0) == "Giáp Tý"


@pytest.mark.parametrize("hour", [-1, 24])
def test_hour_functions_reject_invalid_hours(hour: int) -> None:
    with pytest.raises(ValueError, match="Giờ phải nằm trong khoảng"):
        branch_from_hour(hour)
    with pytest.raises(ValueError, match="Giờ phải nằm trong khoảng"):
        hour_can_chi(date(2006, 7, 3), hour)


@pytest.mark.parametrize("month", [0, 13])
def test_month_can_chi_rejects_invalid_lunar_month(month: int) -> None:
    with pytest.raises(ValueError, match="Tháng âm lịch"):
        month_can_chi(2024, month)
