"""Vietnamese lunar calendar conversion using the Ho Ngoc Duc algorithm."""

from dataclasses import dataclass
from datetime import date
from math import cos, floor, pi, sin

TIME_ZONE = 7
MIN_SUPPORTED_YEAR = 1800
MAX_SUPPORTED_YEAR = 2199
_SYNODIC_MONTH = 29.530588853
_EPOCH = 2415021.076998695
_DEG_TO_RAD = pi / 180


@dataclass(frozen=True)
class LunarDate:
    day: int
    month: int
    year: int
    is_leap_month: bool


def julian_day_number(day: int, month: int, year: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )
    if jd < 2299161:
        return day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083
    return jd


def _new_moon_day(k: int) -> int:
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    jd1 = (
        2415020.75933
        + 29.53058868 * k
        + 0.0001178 * t2
        - 0.000000155 * t3
    )
    jd1 += 0.00033 * sin((166.56 + 132.87 * t - 0.009173 * t2) * _DEG_TO_RAD)

    mean_sun = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    mean_moon = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    moon_argument = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3

    correction = (
        (0.1734 - 0.000393 * t) * sin(mean_sun * _DEG_TO_RAD)
        + 0.0021 * sin(2 * mean_sun * _DEG_TO_RAD)
        - 0.4068 * sin(mean_moon * _DEG_TO_RAD)
        + 0.0161 * sin(2 * mean_moon * _DEG_TO_RAD)
        - 0.0004 * sin(3 * mean_moon * _DEG_TO_RAD)
        + 0.0104 * sin(2 * moon_argument * _DEG_TO_RAD)
        - 0.0051 * sin((mean_sun + mean_moon) * _DEG_TO_RAD)
        - 0.0074 * sin((mean_sun - mean_moon) * _DEG_TO_RAD)
        + 0.0004 * sin((2 * moon_argument + mean_sun) * _DEG_TO_RAD)
        - 0.0004 * sin((2 * moon_argument - mean_sun) * _DEG_TO_RAD)
        - 0.0006 * sin((2 * moon_argument + mean_moon) * _DEG_TO_RAD)
        + 0.0010 * sin((2 * moon_argument - mean_moon) * _DEG_TO_RAD)
        + 0.0005 * sin((2 * mean_moon + mean_sun) * _DEG_TO_RAD)
    )
    if t < -11:
        delta_t = (
            0.001
            + 0.000839 * t
            + 0.0002261 * t2
            - 0.00000845 * t3
            - 0.000000081 * t2 * t2
        )
    else:
        delta_t = -0.000278 + 0.000265 * t + 0.000262 * t2

    return floor(jd1 + correction - delta_t + 0.5 + TIME_ZONE / 24)


def _sun_longitude_sector(julian_day: int) -> int:
    t = (julian_day - 0.5 - TIME_ZONE / 24 - 2451545.0) / 36525
    t2 = t * t
    mean_anomaly = (
        357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t2 * t
    )
    mean_longitude = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    equation_of_center = (
        (1.914600 - 0.004817 * t - 0.000014 * t2)
        * sin(mean_anomaly * _DEG_TO_RAD)
        + (0.019993 - 0.000101 * t) * sin(2 * mean_anomaly * _DEG_TO_RAD)
        + 0.000290 * sin(3 * mean_anomaly * _DEG_TO_RAD)
    )
    omega = 125.04 - 1934.136 * t
    longitude = (
        mean_longitude
        + equation_of_center
        - 0.00569
        - 0.00478 * sin(omega * _DEG_TO_RAD)
    )
    longitude = (longitude * _DEG_TO_RAD) % (2 * pi)
    return floor(longitude / pi * 6)


def _lunar_month_11(year: int) -> int:
    off = julian_day_number(31, 12, year) - 2415021
    k = floor(off / _SYNODIC_MONTH)
    new_moon = _new_moon_day(k)
    if _sun_longitude_sector(new_moon) >= 9:
        new_moon = _new_moon_day(k - 1)
    return new_moon


def _leap_month_offset(month_11: int) -> int:
    k = floor(0.5 + (month_11 - _EPOCH) / _SYNODIC_MONTH)
    last_sector = -1
    i = 1
    sector = _sun_longitude_sector(_new_moon_day(k + i))
    while sector != last_sector and i < 14:
        last_sector = sector
        i += 1
        sector = _sun_longitude_sector(_new_moon_day(k + i))
    return i - 1


def solar_to_lunar(solar_date: date) -> LunarDate:
    """Convert a Gregorian date to the Vietnamese lunar calendar (UTC+7).

    The implementation supports Gregorian years 1800 through 2199.
    """
    if not MIN_SUPPORTED_YEAR <= solar_date.year <= MAX_SUPPORTED_YEAR:
        raise ValueError(
            f"Năm phải nằm trong khoảng {MIN_SUPPORTED_YEAR}–{MAX_SUPPORTED_YEAR}"
        )

    day_number = julian_day_number(
        solar_date.day,
        solar_date.month,
        solar_date.year,
    )
    k = floor((day_number - _EPOCH) / _SYNODIC_MONTH)
    month_start = _new_moon_day(k + 1)
    if month_start > day_number:
        month_start = _new_moon_day(k)

    month_11 = _lunar_month_11(solar_date.year)
    next_month_11 = month_11
    if month_11 >= month_start:
        lunar_year = solar_date.year
        month_11 = _lunar_month_11(solar_date.year - 1)
    else:
        lunar_year = solar_date.year + 1
        next_month_11 = _lunar_month_11(solar_date.year + 1)

    lunar_day = day_number - month_start + 1
    month_difference = floor((month_start - month_11) / 29)
    lunar_month = month_difference + 11
    is_leap_month = False

    if next_month_11 - month_11 > 365:
        leap_offset = _leap_month_offset(month_11)
        if month_difference >= leap_offset:
            lunar_month = month_difference + 10
            is_leap_month = month_difference == leap_offset

    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and month_difference < 4:
        lunar_year -= 1

    return LunarDate(
        day=lunar_day,
        month=lunar_month,
        year=lunar_year,
        is_leap_month=is_leap_month,
    )
