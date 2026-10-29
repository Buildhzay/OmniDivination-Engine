from datetime import date

import pytest

from app.engine.numerology import (
    calculate_life_path,
    calculate_personal_year,
    reduce_number,
)


def test_reduce_basic():
    assert reduce_number(5) == 5
    assert reduce_number(18) == 9
    assert reduce_number(2006) == 8


def test_reduce_keeps_master_numbers():
    assert reduce_number(11) == 11
    assert reduce_number(22) == 22
    assert reduce_number(29) == 11
    assert reduce_number(11, keep_master=False) == 2


def test_reduce_rejects_negative():
    with pytest.raises(ValueError):
        reduce_number(-1)


def test_life_path_from_design_doc_example():
    assert calculate_life_path(date(2006, 7, 3)) == 9


def test_life_path_master_number_edge_case():
    assert calculate_life_path(date(2005, 11, 4)) == 22


def test_life_path_result_is_valid():
    valid = set(range(1, 10)) | {11, 22, 33}
    for y in range(1950, 2011):
        for m in (1, 5, 11, 12):
            for d in (1, 11, 22, 29, 31 if m != 11 else 30):
                assert calculate_life_path(date(y, m, d)) in valid


def test_personal_year_from_design_doc_example():
    assert calculate_personal_year(date(2006, 7, 3), 2026) == 2


def test_personal_year_never_master():
    for y in range(2020, 2040):
        assert 1 <= calculate_personal_year(date(2006, 7, 3), y) <= 9
