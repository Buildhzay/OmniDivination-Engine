from fastapi import HTTPException

from app.db.database import get_user_id_for_token, save_reading


def resolve_optional_owner(token: str | None) -> str | None:
    if token is None:
        return None
    user_id = get_user_id_for_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Reading token không hợp lệ.",
        )
    return user_id


def persist_reading_if_owned(
    owner_id: str | None,
    module: str,
    result: dict,
) -> None:
    if owner_id is not None:
        save_reading(owner_id, module, result)
