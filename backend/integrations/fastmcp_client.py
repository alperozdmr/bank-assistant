from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from fastmcp import Client


def _from_content(content: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(content, list):
        return None
    for b in content:
        # block pydantic veya dict olabilir
        btype = getattr(b, "type", None) or (isinstance(b, dict) and b.get("type"))
        if btype == "json":
            j = getattr(b, "json", None) or (isinstance(b, dict) and b.get("json"))
            if isinstance(j, dict):
                return j
        if btype == "text":
            t = getattr(b, "text", None) or (isinstance(b, dict) and b.get("text"))
            if isinstance(t, str):
                try:
                    return json.loads(t)
                except Exception:
                    pass
    return None


def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x.get("data") if isinstance(x.get("data"), dict) else x
    # result/data attribute’ı olan tipler
    for attr in ("data", "result"):
        val = getattr(x, attr, None)
        if isinstance(val, dict):
            return val
    # content içindeki json/text
    got = _from_content(getattr(x, "content", None))
    if isinstance(got, dict):
        return got
    # pydantic/dataclass/obj.dict()
    for meth in ("model_dump", "dict"):
        f = getattr(x, meth, None)
        if callable(f):
            try:
                d = f()
                if isinstance(d, dict):
                    return (
                        d.get("data")
                        if isinstance(d.get("data"), dict)
                        else d.get("result", d)
                    )
            except Exception:
                pass
    # string json olabilir
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            pass
    # debug fallback
    return {"_type": type(x).__name__, "_raw": str(x)}


async def _acall(url: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        async with Client(url) as client:
            res = await client.call_tool(tool, args)
            return _as_dict(res)
    except Exception as e:
        # Deterministic error object for caller
        return {
            "ok": False,
            "error": f"mcp_call_failed:{e.__class__.__name__}",
            "detail": str(e),
            "tool": tool,
            "args": args,
        }


def call_mcp_tool(url: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return asyncio.run(_acall(url, tool, args))
