"""Engine Thần số học: chỉ dùng toán, không gọi mạng, không gọi AI."""

from datetime import date

MASTER_NUMBERS = (11, 22, 33)


def reduce_number(n: int, keep_master: bool = True) -> int:
    """Rút gọn n về 1 chữ số bằng cách cộng các chữ số.

    Nếu keep_master=True, dừng lại khi gặp 11, 22, 33.
    """
    if n < 0:
        raise ValueError("n phải là số không âm")
    while n > 9:
        if keep_master and n in MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def calculate_life_path(dob: date) -> int:
    """Số chủ đạo: rút gọn ngày, tháng, năm RIÊNG, cộng lại rồi rút gọn."""
    day = reduce_number(dob.day)
    month = reduce_number(dob.month)
    year = reduce_number(dob.year)
    return reduce_number(day + month + year)


def calculate_personal_year(dob: date, year: int) -> int:
    """Năm cá nhân: ngày sinh + tháng sinh + năm đang xét, rút gọn về 1 chữ số."""
    total = reduce_number(dob.day) + reduce_number(dob.month) + reduce_number(year)
    return reduce_number(total, keep_master=False)
