import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.db.database import save_audit_event

logger = logging.getLogger("app.audit")

MAX_REQUEST_BODY_BYTES = 16 * 1024

_INTERPRETATION_MODULES = {
    "/api/v1/divination/numerology/interpret": "numerology",
    "/api/v1/divination/tarot/interpret": "tarot",
}


class _RequestBodyTooLarge(Exception):
    pass


class RequestAuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        path = str(scope.get("path", ""))
        module = _INTERPRETATION_MODULES.get(path)
        status_code: int | None = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        async def send_body_too_large() -> None:
            await send_with_request_id(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send_with_request_id(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Request body too large."}',
                }
            )

        content_length = next(
            (
                value
                for name, value in scope.get("headers", [])
                if name.lower() == b"content-length"
            ),
            None,
        )
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = 0
            if declared_length > MAX_REQUEST_BODY_BYTES:
                await send_body_too_large()
                if module is not None:
                    self._audit(module, path, request_id, status_code)
                return

        body_size = 0

        async def receive_with_body_limit() -> Message:
            nonlocal body_size
            message = await receive()
            if message["type"] == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > MAX_REQUEST_BODY_BYTES:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, receive_with_body_limit, send_with_request_id)
        except _RequestBodyTooLarge:
            await send_body_too_large()
        except Exception:
            if module is not None:
                self._audit(module, path, request_id, None)
            raise

        if module is not None:
            self._audit(module, path, request_id, status_code)

    @staticmethod
    def _audit(
        module: str,
        endpoint: str,
        request_id: str,
        status_code: int | None,
    ) -> None:
        accepted = status_code is not None and 200 <= status_code < 400
        if accepted:
            reason = None
        elif status_code == 422:
            reason = "validation_error"
        elif status_code == 429:
            reason = "rate_limited"
        elif status_code == 413:
            reason = "request_too_large"
        elif status_code == 502:
            reason = "interpretation_failed"
        elif status_code == 503:
            reason = "interpreter_unavailable"
        else:
            reason = "internal_error" if status_code is None else "request_failed"

        timestamp = datetime.now(timezone.utc).isoformat()
        event = {
            "timestamp": timestamp,
            "request_id": request_id,
            "module": module,
            "endpoint": endpoint,
            "accepted": accepted,
            "rejected": not accepted,
            "reason": reason,
        }
        logger.info(
            json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        )
        save_audit_event(
            timestamp=timestamp,
            request_id=request_id,
            module=module,
            endpoint=endpoint,
            accepted=accepted,
            reason=reason,
        )
