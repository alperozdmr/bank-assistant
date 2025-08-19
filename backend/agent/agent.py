# backend/agent/agent.py
# Minimal Agent — LLM tool-calling + MCP
from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from llmadapter import LLMAdapter
from tools.schemas import get_tool_catalog
from integrations.fastmcp_client import call_mcp_tool

USE_MCP = 1
MCP_URL = "http://127.0.0.1:8081/sse"

_BALANCE_WORDS = ("bakiye", "balance", "ne kadar var", "kalan para", "hesabımda ne kadar", "bakiyem")
_ACC_STRICT = re.compile(r"\b(hesap|account)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_CUST_RE    = re.compile(r"\b(müşteri|customer)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_ACC_RE = re.compile(r"\b\d{1,10}\b")

def _acc_id(txt: str) -> Optional[int]:
    m = _ACC_RE.search(txt)
    return int(m.group()) if m else None

def _cust_id(txt: str) -> Optional[int]:
    m = _CUST_RE.search(txt)
    return int(m.group(3)) if m else None

def _fmt_balance(res: Dict[str, Any], fallback_id: Optional[int] = None) -> str:
    if not isinstance(res, dict):
        return "Beklenmedik MCP yanıtı."
    if res.get("error"):
        return f"Hata: {res['error']}"
    d = res["data"] if isinstance(res.get("data"), dict) else res
    #burası customer id için eklendi
    if isinstance(d.get("accounts"), list):
        accs = d["accounts"]
        if not accs:
            return "Bu müşteri için hesap bulunamadı."
        if len(accs) == 1:
            # Tek hesap: normal akışa bırakmak için d'yi tek hesaba eşitle
            one = accs[0]
            d = {
                "account_id": one.get("account_id"),
                "currency": one.get("currency"),
                "balance": one.get("balance"),
            }
        else:
            preview = ", ".join(
                f"#{a.get('account_id')} {a.get('balance')} {a.get('currency')}"
                for a in accs[:3]
            )
            more = f" (+{len(accs)-3} daha)" if len(accs) > 3 else ""
            return f"{len(accs)} hesap bulundu: {preview}{more}. Lütfen bir account_id seçin."
        
    cur = (d.get("currency") or "").upper()
    bal = d.get("balance")
    try:
        # "12.345,67" / "12345.67" / "12345,67" toleransı
        s = str(bal).replace(" ", "")
        if s.count(".") > 1:            # binlik nokta + ondalık virgül
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        val = float(s)
    except Exception:
        return "Bakiye bilgisi okunamadı."
    amt = f"{val:,.2f}"
    if cur == "TRY":
        amt = amt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Hesap {d.get('account_id', fallback_id)} bakiyeniz: {amt} {cur}"

def _llm_flow(user_text: str) -> Dict[str, Any]:
    adapter = LLMAdapter()
    msgs: List[Dict[str, str]] = adapter.system_messages() + [{"role": "user", "content": user_text}]
    tools = get_tool_catalog()["tools"]

    first = adapter.generate(messages=msgs, tools=tools, tool_choice="auto")
    if "error" in first:
        return {"YANIT": "Üzgünüm, model şu anda yanıt veremiyor.", "error": first}

    calls = LLMAdapter.first_tool_calls(first)
    if not calls:
        txt = LLMAdapter.first_message_content(first) or "Lütfen sayısal account_id yazın (örn: 1)."
        return {"YANIT": txt, "toolOutputs": []}

    outs: List[Dict[str, Any]] = []
    for c in calls:
        name = c.get("name")
        args = c.get("arguments") or {}
        call_id = c.get("id")
        if name in ("AccountBalanceTool_get_balance", "get_balance") and "account_id" in args or "customer_id" in args:
            try:
                #customer_id için güncellendi
                payload: Dict[str, Any] = {}
                if args.get("account_id") is not None:
                    payload["account_id"] = int(args["account_id"])
                if args.get("customer_id") is not None:
                    payload["customer_id"] = int(args["customer_id"])
                res = call_mcp_tool(MCP_URL, "get_balance", payload)
                out = {"name": "get_balance", "args": payload, "result": res, "ok": res.get("ok", True)}
            except Exception as e:
                out = {"name": "get_balance", "args": args, "result": {"ok": False, "error": str(e)}, "ok": False}
        else:
            out = {"name": name, "args": args, "result": {"ok": False, "error": "missing_account_id"}, "ok": False}

        outs.append(out)
        msgs.append({
            "role": "tool",
            "tool_call_id": call_id,
            "name": out["name"],
            "content": json.dumps(out["result"], ensure_ascii=False),
        })

    second = adapter.generate(messages=msgs)
    final = LLMAdapter.first_message_content(second) or _fmt_balance(outs[0]["result"])
    return {"YANIT": final, "toolOutputs": outs,
            "llmTime": {"first": first.get("_elapsed_sec"), "second": second.get("_elapsed_sec")}}

def handle_message(user_text: str) -> Dict[str, Any]:
    low = user_text.lower()
    if USE_MCP and any(w in low for w in _BALANCE_WORDS):
        cid = _cust_id(user_text)
        if cid is not None:
            res = call_mcp_tool(MCP_URL, "get_balance", {"customer_id": cid})
            return {"YANIT": _fmt_balance(res), "toolOutputs": [{"name": "get_balance", "args": {"customer_id": cid}, "result": res, "ok": res.get("ok", True)}]}
        acc = _acc_id(user_text)
        if acc is not None:
            res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": acc})
            return {"YANIT": _fmt_balance(res, acc), "toolOutputs": [{"name": "get_balance", "args": {"account_id": acc}, "result": res, "ok": res.get("ok", True)}]}
    return _llm_flow(user_text)

if __name__ == "__main__":
    print("Minimal Agent — LLM tool-calling + MCP (Ctrl+C to exit)")
    try:
        while True:
            print("YANIT:", handle_message(input("> "))["YANIT"])
    except KeyboardInterrupt:
        pass
