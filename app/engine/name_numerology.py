"""Chỉ số từ họ tên: Linh hồn (nguyên âm) và Sức mạnh/Biểu đạt (mọi chữ cái)."""

import unicodedata

from app.engine.numerology import reduce_number

LETTER_VALUES = {
    letter: value
    for value, letters in {
        1: "AJS",
        2: "BKT",
        3: "CLU",
        4: "DMV",
        5: "ENW",
        6: "FOX",
        7: "GPY",
        8: "HQZ",
        9: "IR",
    }.items()
    for letter in letters
}

VOWELS = set("AEIOUY")


def normalize_name(full_name: str) -> str:
    """Bỏ dấu tiếng Việt, đổi Đ thành D, chỉ giữ chữ cái A-Z viết hoa."""
    text = full_name.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return "".join(c for c in text.upper() if "A" <= c <= "Z")


def calculate_soul_urge(full_name: str) -> int:
    """Chỉ số Linh hồn: cộng giá trị các nguyên âm."""
    letters = normalize_name(full_name)
    if not letters:
        raise ValueError("Họ tên không có chữ cái hợp lệ")
    total = sum(LETTER_VALUES[c] for c in letters if c in VOWELS)
    return reduce_number(total)


def calculate_expression(full_name: str) -> int:
    """Chỉ số Sức mạnh (Biểu đạt): cộng giá trị mọi chữ cái."""
    letters = normalize_name(full_name)
    if not letters:
        raise ValueError("Họ tên không có chữ cái hợp lệ")
    total = sum(LETTER_VALUES[c] for c in letters)
    return reduce_number(total)
