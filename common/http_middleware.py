# common/http_middleware.py
from __future__ import annotations

import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from common.logging_setup import get_logger


class CorrelationLoggingMiddleware(BaseHTTPMiddleware):
    """
    - Her HTTP isteğine corr_id ekler (yoksa üretir)
    - İstek süresini ölçer
    - JSON log yazar (dosya + stdout)
    - Yanıta X-Request-ID header'ını koyar
    """

    def __init__(self, app, logger=None):
        super().__init__(app)
        self.log = logger or get_logger("chat_backend", "chat-backend.log", service="chat-backend")

    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.corr_id = corr_id  # endpoint içinde erişim için

        t0 = time.perf_counter()
        response: Optional[Response] = None
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Beklenmeyen tüm HTTP hataları
            self.log.error("http_unhandled_error", extra={
                "event": "http_unhandled_error",
                "corr_id": corr_id,
                "error": str(e),
                "meta": {"path": str(request.url), "method": request.method},
            })
            raise
        finally:
            dur = int((time.perf_counter() - t0) * 1000)
            # Yanıta corr_id header'ı eklemeyi dene
            try:
                if response is not None and "X-Request-ID" not in response.headers:
                    response.headers["X-Request-ID"] = corr_id
            except Exception:
                # Yanıt akışı başlamış olabilir; kritik değil
                pass

            self.log.info("http_request", extra={
                "event": "http_request",
                "corr_id": corr_id,
                "meta": {"path": request.url.path, "method": request.method, "status": getattr(response, "status_code", None)},
                "duration_ms": dur,
            })


def install_http_logging(app, logger=None):
    """
    FastAPI/Starlette uygulamana bu middleware'i ekler.
    Not: Starlette'de middleware'ler **eklenme sırasıyla** sarılır. Bunu ilk eklemek genelde idealdir.
    """
    app.add_middleware(CorrelationLoggingMiddleware, logger=logger)
