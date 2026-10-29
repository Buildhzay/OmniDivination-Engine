import pytest

from app.engine.name_numerology import (
    calculate_expression,
    calculate_soul_urge,
    normalize_name,
)


def test_normalize_removes_vietnamese_marks():
    assert normalize_name("Nguyễn Văn Đạt") == "NGUYENVANDAT"
    assert normalize_name("  lê  thị-hoa ") == "LETHIHOA"


def test_accents_do_not_change_result():
    assert calculate_expression("Nguyễn Văn Đạt") == calculate_expression(
        "Nguyen Van Dat"
    )
    assert calculate_soul_urge("Trần Thúy") == calculate_soul_urge("Tran Thuy")


def test_expression_hand_calculated():
    assert calculate_expression("Ba") == 3
    assert calculate_expression("Hoa") == 6


def test_soul_urge_hand_calculated():
    assert calculate_soul_urge("Ba") == 1
    assert calculate_soul_urge("Hoa") == 7


def test_master_number_kept():
    assert calculate_expression("Bi") == 11


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        calculate_expression("123 !!!")
    with pytest.raises(ValueError):
        calculate_soul_urge("")
