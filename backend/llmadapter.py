from __future__ import annotations
import json, time, requests
from typing import Any, Dict, List, Optional

# İsteğe bağlı yerel ayarlar
try:
    from config_local import (
        LLM_API_BASE as _BASE,
        LLM_CHAT_PATH as _CHAT_PATH,
        LLM_MODEL as _MODEL,
        LLM_API_KEY as _KEY,
    )
except Exception:
    _BASE = "https://router.huggingface.co/v1"  # Hugging Face Router varsayılanı
    _CHAT_PATH = "/chat/completions"            # Hugging Face API yolu
    _MODEL = "openai/gpt-oss-20b"               # Hugging Face modeli
    _KEY = "REPLACE_ME"                         # HF kullanıyorsan değiştir

REQUEST_TIMEOUT = 60
SYSTEM_POLICY = (
    "You are a banking assistant for a PoC. "
    "Never fabricate personal data. Do not perform payments or transfers. "
    "For account balances, always call the provided tool; if account_id is missing, ask for it. "
    "Keep answers concise."
)

def _safe_json(x: str) -> Optional[Dict[str, Any]]:
    try:
        v = json.loads(x)
        return v if isinstance(v, dict) else None
    except Exception:
        return None

class LLMAdapter:
    def __init__(self, model: Optional[str] = None, api_url: Optional[str] = None,
                 default_temperature: float = 0.2, default_top_p: float = 0.9, default_max_tokens: int = 512,
                 api_key: Optional[str] = None):
        self.model = model or _MODEL
        base = (api_url or _BASE).rstrip("/")
        self.api_base = base
        self.api_url = f"{base}{_CHAT_PATH}"
        self.api_key = api_key if api_key is not None else _KEY
        self.t, self.p, self.mx = default_temperature, default_top_p, default_max_tokens

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if "localhost:11434" in self.api_base or "127.0.0.1:11434" in self.api_base:
            return h  # Ollama: auth yok
        if not self.api_key or self.api_key == "REPLACE_ME":
            raise RuntimeError("LLM_API_KEY eksik: HF/benzeri için anahtar verin veya Ollama kullanın.")
        h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def system_messages(self, extra_system: Optional[str] = None) -> List[Dict[str, str]]:
        msgs = [{"role": "system", "content": SYSTEM_POLICY}]
        if extra_system: msgs.append({"role": "system", "content": extra_system})
        return msgs

    def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None,
                 tool_choice: str = "auto", temperature: Optional[float] = None, top_p: Optional[float] = None,
                 max_tokens: Optional[int] = None, timeout_sec: Optional[int] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.t if temperature is None else float(temperature),
            "top_p": self.p if top_p is None else float(top_p),
            "max_tokens": self.mx if max_tokens is None else int(max_tokens),
        }
        if tools: payload.update({"tools": tools, "tool_choice": tool_choice})

        t0 = time.time()
        try:
            r = requests.post(self.api_url, headers=self._headers(), json=payload, timeout=(timeout_sec or REQUEST_TIMEOUT))
            r.raise_for_status()
            data = r.json(); data["_elapsed_sec"] = round(time.time() - t0, 3)
            return data
        except requests.exceptions.Timeout:
            return {"error": "timeout", "_elapsed_sec": round(time.time() - t0, 3)}
        except requests.exceptions.HTTPError as e:
            return {"error": f"http_error:{e.response.status_code}", "detail": r.text if 'r' in locals() else "",
                    "_elapsed_sec": round(time.time() - t0, 3)}
        except Exception as e:
            return {"error": f"request_failed:{e.__class__.__name__}", "detail": str(e),
                    "_elapsed_sec": round(time.time() - t0, 3)}

    @staticmethod
    def first_message_content(resp: Dict[str, Any]) -> Optional[str]:
        try: return resp["choices"][0]["message"].get("content")
        except Exception: return None

    @staticmethod
    def first_tool_calls(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        calls: List[Dict[str, Any]] = []
        try:
            raw = resp["choices"][0]["message"].get("tool_calls") or []
            for c in raw:
                f = c.get("function") or {}
                args = f.get("arguments")
                if isinstance(args, str): args = _safe_json(args) or {}
                elif not isinstance(args, dict): args = {}
                calls.append({"id": c.get("id"), "name": f.get("name") or c.get("name"), "arguments": args})
            if calls: return calls
        except Exception:
            pass
        # içerikte gömülü {name, arguments}
        content = LLMAdapter.first_message_content(resp) or ""
        s, e = content.find("{"), content.rfind("}")
        if s != -1 and e > s:
            obj = _safe_json(content[s:e+1])
            if isinstance(obj, dict) and "name" in obj and "arguments" in obj:
                args = obj["arguments"]; 
                if isinstance(args, str): args = _safe_json(args) or {}
                calls.append({"id": None, "name": obj["name"], "arguments": args if isinstance(args, dict) else {}})
        return calls
