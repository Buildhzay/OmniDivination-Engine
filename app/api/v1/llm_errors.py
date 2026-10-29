from fastapi import HTTPException

from app.ai.client import LLMNotConfigured, LLMUnavailable
from app.safety.output_filter import OutputRejected


def call_interpreter(fn, *args, **kwargs) -> str:
    """Đổi lỗi nội bộ thành lỗi HTTP chung, không tiết lộ chi tiết."""
    try:
        return fn(*args, **kwargs)
    except LLMNotConfigured:
        raise HTTPException(
            status_code=503,
            detail="Dịch vụ diễn giải chưa được cấu hình.",
        ) from None
    except LLMUnavailable:
        raise HTTPException(
            status_code=502,
            detail="Dịch vụ diễn giải tạm thời không phản hồi. Vui lòng thử lại sau.",
        ) from None
    except OutputRejected:
        raise HTTPException(
            status_code=502,
            detail="Không tạo được bản diễn giải đạt chuẩn an toàn. Vui lòng thử lại.",
        ) from None
