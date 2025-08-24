# common/mcp_decorators.py
from __future__ import annotations
import inspect
import time
import uuid
from functools import wraps
from typing import Any, Dict

from common.logging_setup import get_logger
from common.pii import mask_args

# Bu logger yalnızca MCP server için kullanılır
log = get_logger("mcp_server", "mcp-server.log", service="mcp-server")


def _wrap_ok(data: Dict[str, Any], corr_id: str, tool: str, started_at: float) -> Dict[str, Any]:
    """Başarılı tool yanıtını standart biçime sarar ve loglar."""
    dur = int((time.perf_counter() - started_at) * 1000)
    log.info("tool_result", extra={
        "event": "tool_result",
        "corr_id": corr_id,
        "tool": tool,
        "ok": True,
        "duration_ms": dur,
    })
    return {"ok": True, "data": data}


def _wrap_err(msg: str, corr_id: str, tool: str, started_at: float) -> Dict[str, Any]:
    """Hata tool yanıtını standart biçime sarar ve loglar."""
    dur = int((time.perf_counter() - started_at) * 1000)
    log.error("tool_error", extra={
        "event": "tool_error",
        "corr_id": corr_id,
        "tool": tool,
        "ok": False,
        "error": msg,
        "duration_ms": dur,
    })
    return {"ok": False, "error": msg}


def log_tool(func):
    """
    MCP tool fonksiyonları için dekoratör:
    - corr_id üretir/alır
    - argümanları PII maskeleyip loglar
    - beklenmeyen hataları yakalar
    - çıktıyı {ok/error/data} tek sözleşmesine çevirir
    """
    sig = inspect.signature(func)

    @wraps(func)  # -> ad, docstring ve imzayı olabildiğince korur
    def wrapper(*args, **kwargs):
        corr_id = kwargs.pop("_corr_id", str(uuid.uuid4()))
        started = time.perf_counter()
        tool_name = func.__name__

        # Positional argümanları isimlendir (log için okunaklı olsun)
        try:
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            named_args = dict(bound.arguments)
        except Exception:
            named_args = {**kwargs}

        # Sadece log amaçlı olan _corr_id'yi dışarıda tut
        named_args.pop("_corr_id", None)

        # Tool çağrısını PII maskeli argümanlarla logla
        log.info("tool_call", extra={
            "event": "tool_call",
            "corr_id": corr_id,
            "tool": tool_name,
            "args_masked": mask_args(named_args),
        })

        try:
            # Orijinal işlevi çalıştır
            result = func(*args, **kwargs)

            # Eski tarz: {"error": "..."} dönmüşse hata say
            if isinstance(result, dict) and result.get("error"):
                return _wrap_err(str(result["error"]), corr_id, tool_name, started)

            # Başarı: dict değilse bile data içine koy
            if not isinstance(result, dict):
                result = {"value": result}

            return _wrap_ok(result, corr_id, tool_name, started)

        except Exception as e:
            # Beklenmeyen hata
            return _wrap_err(str(e), corr_id, tool_name, started)

    return wrapper
