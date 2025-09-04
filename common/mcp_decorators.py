# common/mcp_decorators.py (yalnızca log_tool'u güncelliyoruz)
from __future__ import annotations
import inspect
import time,os
import uuid
from functools import wraps
from typing import Any, Dict, Optional
from pathlib import Path
from common.logging_setup import get_logger
from common.pii import mask_args

log = get_logger("mcp_server", "mcp-server.log", service="mcp-server")

def _wrap_ok(data: Dict[str, Any], corr_id: str, tool: str, started_at: float) -> Dict[str, Any]:
    dur = int((time.perf_counter() - started_at) * 1000)
    log.info(f"tool_result:{tool}", extra={
        "event": "tool_result",
        "corr_id": corr_id,
        "tool": tool,
        "ok": True,
        "duration_ms": dur,
    })
    return {"ok": True, "data": data}


def _wrap_err(msg: str, corr_id: str, tool: str, started_at: float) -> Dict[str, Any]:
    dur = int((time.perf_counter() - started_at) * 1000)
    log.error(f"tool_error:{tool}", extra={
        "event": "tool_error",
        "corr_id": corr_id,
        "tool": tool,
        "ok": False,
        "error": msg,
        "duration_ms": dur,
    })
    return {"ok": False, "error": msg}


def log_tool(_func=None, *, name: Optional[str] = None):
    """
    MCP tool fonksiyonları için dekoratör.

    Kullanım:
      @log_tool
      def my_tool(...): ...

      @log_tool(name="Accounts.get_balance")
      def get_balance(...): ...

    Not: name verilirse log'larda bu ad görünür.
    """
    def _decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            corr_id = kwargs.pop("_corr_id", str(uuid.uuid4()))
            started = time.perf_counter()
            tool_name = name or func.__name__

            # positional argümanları isimlendir + PII maskele
            try:
                bound = sig.bind_partial(*args, **kwargs)
                bound.apply_defaults()
                named_args = dict(bound.arguments)
            except Exception:
                named_args = {**kwargs}
            named_args.pop("_corr_id", None)

            log.info(f"{tool_name}", extra={
                "event": "tool_call",
                "corr_id": corr_id,
                "tool": tool_name,
                "args_masked": mask_args(named_args),
            })

            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and result.get("error"):
                    return _wrap_err(str(result["error"]), corr_id, tool_name, started)
                if not isinstance(result, dict):
                    result = {"value": result}
                return _wrap_ok(result, corr_id, tool_name, started)
            except Exception as e:
                return _wrap_err(str(e), corr_id, tool_name, started)

        return wrapper

    # Hem @log_tool hem de @log_tool(name="...") desteği:
    if _func is not None and callable(_func):
        return _decorator(_func)
    return _decorator

