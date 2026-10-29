import unicodedata

from app.safety.output_filter import (
    check_numerology_output,
    check_safety,
    check_tarot_output,
)


def test_numerology_accepts_valid_output():
    errors = check_numerology_output(
        """
        Số chủ đạo 9 cho thấy khuynh hướng nhân văn.
        Năm cá nhân 2 gợi ý sự kiên nhẫn và hợp tác.
        """,
        life_path=9,
        personal_year=2,
    )

    assert errors == []


def test_numerology_rejects_unknown_number():
    errors = check_numerology_output(
        "Số chủ đạo 9 và số 5.",
        life_path=9,
        personal_year=2,
    )

    assert any("số 5" in error for error in errors)


def test_numerology_rejects_mismatched_labeled_number():
    errors = check_numerology_output(
        "Số chủ đạo 5.",
        life_path=9,
        personal_year=2,
    )

    assert any("phải là 9" in error for error in errors)


def test_numerology_accepts_reduced_master_number():
    errors = check_numerology_output(
        "Số chủ đạo 22/4.",
        life_path=22,
        personal_year=2,
    )

    assert errors == []


def test_numerology_rejects_optional_value_without_calculated_data():
    errors = check_numerology_output(
        "Số Linh hồn 8.",
        life_path=9,
        personal_year=2,
    )

    assert any("không có dữ liệu này" in error for error in errors)


def test_numerology_rejects_safety_violations():
    errors = check_numerology_output(
        "Bạn chắc chắn sẽ mua vàng và sẽ gặp vận hạn.",
        life_path=9,
        personal_year=2,
    )

    assert any("khẳng định tuyệt đối" in error for error in errors)
    assert any("khuyên đầu tư cụ thể" in error for error in errors)
    assert any("đe dọa hoặc gây sợ hãi" in error for error in errors)


def test_safety_normalizes_decomposed_unicode():
    text = unicodedata.normalize("NFD", "Bạn có thể mắc bệnh.")

    errors = check_safety(text)

    assert any("chẩn đoán hoặc nói về bệnh tật" in error for error in errors)


def test_safety_detects_personal_data_without_echoing_it():
    email = "private.user@example.com"
    phone = "0912345678"
    birth_date = "04/11/2005"

    errors = check_safety(f"Email {email}, số {phone}, ngày sinh {birth_date}.")

    assert any("lộ email" in error for error in errors)
    assert any("lộ số điện thoại" in error for error in errors)
    assert any("lộ ngày tháng năm" in error for error in errors)
    assert all(value not in " ".join(errors) for value in (email, phone, birth_date))


def test_tarot_accepts_drawn_cards_and_rejects_undrawn_cards():
    errors = check_tarot_output(
        "Mặt Trời gợi ý sự rõ ràng. Cái Chết biểu tượng cho chuyển hóa.",
        ["Mặt Trời"],
    )

    assert len(errors) == 1
    assert "Cái Chết" in errors[0]


def test_tarot_accepts_all_drawn_card_names():
    errors = check_tarot_output(
        "Mặt Trời mang niềm vui; Cái Chết gợi sự chuyển hóa.",
        ["Mặt Trời", "Cái Chết"],
    )

    assert errors == []


def test_tarot_also_applies_safety_checks():
    errors = check_tarot_output(
        "Mặt Trời cho thấy bạn chắc chắn sẽ thành công.",
        ["Mặt Trời"],
    )

    assert any("khẳng định tuyệt đối" in error for error in errors)
