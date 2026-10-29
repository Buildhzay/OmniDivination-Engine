import os
from datetime import date, time
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("OMNIDIVINATION_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 60


def _headers() -> dict[str, str]:
    token = st.session_state.get("reading_token", "").strip()
    return {"X-Reading-Token": token} if token else {}


def _request(method: str, path: str, **kwargs: Any) -> requests.Response | None:
    base_url = st.session_state.get("api_url", DEFAULT_API_URL).rstrip("/")
    try:
        response = requests.request(
            method,
            f"{base_url}{path}",
            headers={**_headers(), **kwargs.pop("headers", {})},
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException:
        st.error("Không kết nối được backend. Hãy kiểm tra API URL và trạng thái server.")
        return None

    if response.status_code >= 400:
        messages = {
            401: "Reading token không hợp lệ hoặc đã bị thiếu.",
            413: "Request vượt quá giới hạn kích thước.",
            422: "Dữ liệu nhập không hợp lệ.",
            429: "Đã vượt giới hạn yêu cầu. Vui lòng đợi rồi thử lại.",
            502: "Dịch vụ diễn giải tạm thời không xử lý được yêu cầu.",
            503: "Dịch vụ diễn giải chưa được cấu hình.",
        }
        st.error(messages.get(response.status_code, f"Backend trả về lỗi HTTP {response.status_code}."))
        return None
    return response


def _show_result(response: requests.Response | None) -> None:
    if response is None:
        return
    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Backend trả về phản hồi không đúng định dạng JSON.")
        return

    if "interpretation" in result:
        st.subheader("Kết quả")
        st.text(result["interpretation"])
        st.caption(result.get("disclaimer", ""))
        details = {
            key: value
            for key, value in result.items()
            if key not in {"interpretation", "disclaimer"}
        }
        with st.expander("Thông số đã tính"):
            st.json(details)
        if not st.session_state.get("reading_token"):
            st.info("Tạo hoặc nhập Reading Token để lưu kết quả vào lịch sử.")
    else:
        st.subheader("Kết quả tính toán / rút bài")
        st.json(result)


st.set_page_config(page_title="OmniDivination", page_icon="✦")
st.title("OmniDivination")
st.caption("Thần số học và Tarot để giải trí, tự suy ngẫm.")

with st.sidebar:
    st.header("Kết nối")
    st.text_input("Backend API URL", value=DEFAULT_API_URL, key="api_url")
    if st.button("Tạo Reading Token", use_container_width=True):
        response = _request("POST", "/api/v1/readings/session")
        if response is not None:
            session = response.json()
            st.session_state["reading_token"] = session["reading_token"]
            st.session_state["new_reading_token"] = session["reading_token"]
            st.success("Đã tạo token. Hãy sao chép và cất giữ an toàn.")
    st.text_input(
        "Reading Token",
        key="reading_token",
        type="password",
        help="Token cho phép lưu, xem và xóa lịch sử. Giữ bí mật token này.",
    )
    if st.session_state.get("new_reading_token"):
        st.code(st.session_state["new_reading_token"], language=None)
        st.caption("Token chỉ được backend trả lại một lần khi tạo.")
    st.caption("Token bị mất thì không thể khôi phục quyền truy cập lịch sử.")

tab_numerology, tab_tarot, tab_lunar, tab_history = st.tabs(
    ["Thần số học", "Tarot", "Lịch âm & Can Chi", "Lịch sử"]
)

with tab_numerology:
    with st.form("numerology_form"):
        birth_date = st.date_input(
            "Ngày sinh",
            value=date(2000, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        full_name = st.text_input("Họ tên (không bắt buộc)", max_chars=100)
        target_year = st.number_input(
            "Năm cần xem",
            min_value=1900,
            max_value=2200,
            value=date.today().year,
        )
        topic = st.selectbox(
            "Chủ đề",
            options=["general", "career"],
            format_func=lambda value: (
                "Tự khám phá bản thân" if value == "general" else "Sự nghiệp"
            ),
        )
        interpret_numerology = st.form_submit_button("Tính và diễn giải")

    if interpret_numerology:
        payload: dict[str, Any] = {
            "dob": birth_date.isoformat(),
            "target_year": target_year,
            "topic": topic,
        }
        if full_name.strip():
            payload["full_name"] = full_name.strip()
        _show_result(
            _request(
                "POST",
                "/api/v1/divination/numerology/interpret",
                json=payload,
            )
        )

with tab_tarot:
    with st.form("tarot_form"):
        count = st.number_input("Số lá bài", min_value=1, max_value=10, value=3)
        tarot_topic = st.selectbox(
            "Chủ đề Tarot",
            options=["general", "career"],
            format_func=lambda value: (
                "Tự khám phá bản thân" if value == "general" else "Sự nghiệp"
            ),
        )
        interpret_tarot = st.form_submit_button("Rút bài và diễn giải")

    if interpret_tarot:
        _show_result(
            _request(
                "POST",
                "/api/v1/divination/tarot/interpret",
                json={"count": count, "topic": tarot_topic},
            )
        )

with tab_lunar:
    with st.form("lunar_form"):
        lunar_birth_date = st.date_input(
            "Ngày sinh dương lịch",
            value=date(2000, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        has_birth_time = st.checkbox("Tôi biết giờ sinh")
        lunar_birth_time = st.time_input(
            "Giờ sinh (giờ Việt Nam)",
            value=time(15, 30),
            disabled=not has_birth_time,
        )
        calculate_lunar = st.form_submit_button("Đổi lịch và xem Can Chi")

    if calculate_lunar:
        payload: dict[str, Any] = {"dob": lunar_birth_date.isoformat()}
        if has_birth_time:
            payload["birth_time"] = lunar_birth_time.strftime("%H:%M")
        _show_result(_request("POST", "/api/v1/divination/lunar", json=payload))

with tab_history:
    if not st.session_state.get("reading_token"):
        st.info("Nhập Reading Token ở thanh bên để mở lịch sử.")
    elif st.button("Tải lịch sử"):
        response = _request("GET", "/api/v1/readings/history")
        if response is not None:
            history = response.json()
            if not history:
                st.info("Chưa có nội dung đã lưu cho token này.")
            for reading in history:
                title = f"{reading['module']} · {reading['created_at']}"
                with st.expander(title):
                    st.json(reading["result"])
                    if st.button("Xóa mục này", key=f"delete-{reading['id']}"):
                        deleted = _request(
                            "DELETE",
                            f"/api/v1/readings/history/{reading['id']}",
                        )
                        if deleted is not None:
                            st.success("Đã xóa mục lịch sử.")
                            st.rerun()

st.divider()
st.caption(
    "Kết quả chỉ mang tính tham khảo và giải trí; không thay thế tư vấn chuyên môn."
)
