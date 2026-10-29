"""Bộ lọc đầu ra: kiểm tra văn bản AI trả về BẰNG CODE trước khi đưa cho người dùng.

Prompt chỉ là lời dặn; file này mới là rào chắn thật.
Hai loại kiểm tra:
  1. Số liệu: con số và lá bài AI nhắc tới phải khớp với kết quả engine đã tính.
  2. An toàn: không dự đoán tử vong, chẩn đoán bệnh, khuyên đầu tư, đe dọa,
     chào bán dịch vụ, hoặc lộ dữ liệu cá nhân.
"""

import re
import unicodedata

from app.engine.tarot import load_deck


class OutputRejected(RuntimeError):
    """Văn bản AI không đạt kiểm tra (sai số liệu hoặc vi phạm an toàn)."""


# Số chủ đạo 11/22/33 thường được nhắc kèm dạng rút gọn (11/2, 22/4, 33/6).
REDUCED_MASTER = {11: 2, 22: 4, 33: 6}

_LABELS = {
    "số chủ đạo": "life_path",
    "số linh hồn": "soul_urge",
    "số sức mạnh": "expression",
    "số biểu đạt": "expression",
    "năm cá nhân": "personal_year",
}
_LABELED = re.compile(
    r"(số chủ đạo|số linh hồn|số sức mạnh|số biểu đạt|năm cá nhân)"
    r"(?:\s+của\s+bạn)?(?:\s+(?:19|20|21)\d{2})?\s*(?:là|:|=|-|–)?\s*(?:số\s+)?(\d{1,2})\b",
    re.IGNORECASE,
)
_BARE_NUMBER = re.compile(r"\bsố\s+(\d{1,2})\b", re.IGNORECASE)

_UNSAFE_PATTERNS = {
    "dự đoán tử vong hoặc tuổi thọ": r"tuổi thọ|sẽ (?:chết|qua đời|tử vong)|sắp (?:chết|qua đời)",
    "chẩn đoán hoặc nói về bệnh tật": r"ung thư|mắc bệnh|bị bệnh|chẩn đoán|đột quỵ|bệnh nan y",
    "khuyên đầu tư cụ thể": r"cổ phiếu|chứng khoán|tiền mã hóa|bitcoin|crypto|đầu tư vào|bất động sản|lướt sóng|mua vàng",
    "khẳng định tuyệt đối": r"chắc chắn sẽ|nhất định sẽ|không thể tránh khỏi|định mệnh đã an bài|chắc chắn rằng",
    "đe dọa hoặc gây sợ hãi": r"tai họa|đại họa|vận hạn|lời nguyền|bị nguyền|nguy hiểm đến tính mạng|giải hạn",
    "chào bán dịch vụ": r"mua (?:bùa|vật phẩm|đá phong thủy)|liên hệ thầy|đặt lễ|cúng giải",
    "lộ email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "lộ số điện thoại": r"(?<!\d)(?:\+?84|0)\d{9,10}(?!\d)",
    "lộ ngày tháng năm": r"(?<!\d)\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)\d{2}(?!\d)",
}
_UNSAFE_COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in _UNSAFE_PATTERNS.items()}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def check_safety(text: str) -> list[str]:
    """Trả về danh sách lý do vi phạm (rỗng nếu đạt). Không trả lại nguyên văn đoạn vi phạm."""
    t = _nfc(text)
    return [f"vi phạm an toàn: {reason}" for reason, rx in _UNSAFE_COMPILED.items() if rx.search(t)]


def check_numerology_output(
    text: str,
    *,
    life_path: int,
    personal_year: int,
    soul_urge: int | None = None,
    expression: int | None = None,
) -> list[str]:
    t = _nfc(text)
    expected = {
        "life_path": life_path,
        "personal_year": personal_year,
        "soul_urge": soul_urge,
        "expression": expression,
    }
    problems: list[str] = []

    for m in _LABELED.finditer(t):
        label = m.group(1).lower()
        value = int(m.group(2))
        want = expected[_LABELS[label]]
        if want is None:
            problems.append(f"sai số liệu: nhắc '{label}' nhưng hệ thống không có dữ liệu này")
        elif value != want and value != REDUCED_MASTER.get(want):
            problems.append(f"sai số liệu: '{label}' phải là {want}, AI viết {value}")

    allowed = {v for v in expected.values() if v is not None}
    allowed |= {REDUCED_MASTER[v] for v in allowed if v in REDUCED_MASTER}
    for m in _BARE_NUMBER.finditer(t):
        n = int(m.group(1))
        if n not in allowed:
            problems.append(f"sai số liệu: nhắc 'số {n}' không nằm trong kết quả đã tính")

    return problems + check_safety(t)


def check_tarot_output(text: str, drawn_names: list[str]) -> list[str]:
    t = _nfc(text)
    problems: list[str] = []

    remaining = t
    for name in sorted(drawn_names, key=len, reverse=True):
        remaining = remaining.replace(name, " ")
    for card in load_deck().values():
        if card["name_vi"] in remaining:
            problems.append(f"sai số liệu: nhắc lá bài không có trong lần rút ({card['name_vi']})")

    return problems + check_safety(t)
