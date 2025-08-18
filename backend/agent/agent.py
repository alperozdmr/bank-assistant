# agent.py
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# Adjust imports to your project structure if needed.
# If these modules live under packages (e.g., integrations/tools), update paths accordingly.
from llmadapter import LLMAdapter
from tools.schemas import get_tool_catalog
from dotenv import load_dotenv
load_dotenv()

USE_MCP = 0
MCP_URL = "http://127.0.0.1:8081/sse"# os.getenv("MCP_URL", "http://127.0.0.1:8001")

if USE_MCP:
    from integrations.fastmcp_client import call_mcp_tool
else:
    from tools.account_balance import InterApiClient, compose_balance_reply

# --- Rule-based helpers (still useful as a fast-path) ---
BALANCE_KEYWORDS = ["bakiye", "balance", "ne kadar var", "kalan para", "hesabımda ne kadar", "bakiyem"]
IBAN_RE  = re.compile(r"\bTR[0-9A-Z]{24}\b", re.IGNORECASE)
NUM_RE   = re.compile(r"\b\d{2,}\b")          # InterAPI üçlü için
ACCID_RE = re.compile(r"\b\d{1,10}\b")        # MCP için account_id


def _looks_like_balance_intent(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in BALANCE_KEYWORDS)


def _extract_triplet(text: str) -> Optional[Tuple[int, int, int]]:
    # very naive extraction: look for three numbers
    nums = [int(x) for x in NUM_RE.findall(text)]
    if len(nums) >= 3:
        return nums[0], nums[1], nums[2]
    return None


def _extract_iban(text: str) -> Optional[str]:
    m = IBAN_RE.search(text)
    return m.group(0) if m else None


def _extract_account_id(text: str) -> Optional[int]:
    # You can tighten this later if needed
    m = ACCID_RE.search(text)
    return int(m.group(0)) if m else None


def _build_user_message(user_text: str) -> List[Dict[str, str]]:
    adapter = LLMAdapter()
    msgs = adapter.system_messages()
    msgs.append({"role": "user", "content": user_text})
    return msgs


def _run_llm_tool_path(user_text: str) -> Dict[str, Any]:
    """
    Two-turn tool-calling flow:
      1) Ask LLM with tools=AccountBalanceTool_get_balance
      2) If tool call(s), execute them and feed results back
      3) Ask LLM again for final user-friendly message
    """
    adapter = LLMAdapter()
    catalog = get_tool_catalog()  # {"tools":[...]}
    messages = _build_user_message(user_text)

    # 1) First call
    first = adapter.generate(messages=messages, tools=catalog["tools"], tool_choice="auto")
    if "error" in first:
        return {"YANIT": "Üzgünüm, model şu anda yanıt veremiyor.", "error": first}

    calls = LLMAdapter.first_tool_calls(first)

    # If no tool call, just return model content
    if not calls:
        content = LLMAdapter.first_message_content(first) or "Tam anlayamadım, tekrar eder misiniz?"
        return {"YANIT": content, "toolOutputs": []}

    tool_outputs: List[Dict[str, Any]] = []

    # 2) Execute tool(s)
    for call in calls:
        name = (call.get("name") or "").strip()
        args = call.get("arguments") or {}

        # Accept both names for convenience
        if name in ("AccountBalanceTool_get_balance", "get_balance"):
            # Choose route
            if USE_MCP and "account_id" in args:
                res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": int(args["account_id"])})
                tool_outputs.append({"name": "get_balance", "args": {"account_id": int(args["account_id"])}, "result": res, "ok": res.get("ok", True)})
            else:
                # InterAPI path with IBAN or triplet
                iban = args.get("iban")
                if not iban:
                    # try triplet
                    triplet = {k: args.get(k) for k in ("account_suffix", "branch_code", "customer_no")}
                    if not all(isinstance(v, int) for v in triplet.values()):
                        # Can't execute
                        tool_outputs.append({"name": name, "args": args, "result": {"ok": False, "error": "missing_arguments"}, "ok": False})
                        continue
                # Execute
                try:
                    client = InterApiClient()
                    raw = client.get_account_detail(
                        account_suffix=args.get("account_suffix"),
                        branch_code=args.get("branch_code"),
                        customer_no=args.get("customer_no"),
                        iban=args.get("iban"),
                    )
                    # pretty text for UI; also include raw
                    reply = compose_balance_reply(raw)
                    tool_outputs.append({"name": "get_balance", "args": args, "result": {"ok": True, "raw": raw, "text": reply}, "ok": True})
                except Exception as e:
                    tool_outputs.append({"name": "get_balance", "args": args, "result": {"ok": False, "error": str(e)}, "ok": False})
        else:
            # Unknown tool name
            tool_outputs.append({"name": name, "args": args, "result": {"ok": False, "error": "unknown_tool"}, "ok": False})

    # 3) Second call with tool messages
    for out in tool_outputs:
        content = out["result"]
        messages.append({
            "role": "tool",
            "name": out["name"],
            "content": json.dumps(content, ensure_ascii=False)
        })

    second = adapter.generate(messages=messages)
    final_text = LLMAdapter.first_message_content(second) or (
        tool_outputs[0]["result"].get("text")
        if tool_outputs and isinstance(tool_outputs[0]["result"], dict)
        else "İstediğiniz bilgilere erişilemedi."
    )
    return {"YANIT": final_text, "toolOutputs": tool_outputs, "llmTime": {"first": first.get("_elapsed_sec"), "second": second.get("_elapsed_sec")}}


def handle_message(user_text: str) -> Dict[str, Any]:
    """
    Hybrid strategy:
      - If balance intent looks very obvious and we can extract arguments locally, short-circuit.
      - Otherwise, ask LLM with tool-calling enabled.
    """
    # 1) obvious fast-path
    if _looks_like_balance_intent(user_text):
        if USE_MCP:
            acc_id = _extract_account_id(user_text)
            if acc_id is not None:
                res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": acc_id})
                if res.get("ok", True):

                    return {"YANIT": f"Hesap {acc_id} bakiyeniz: {res.get("balance", 'N/A')} {res.get("currency", '')}", "toolOutputs": [{"name":"get_balance","args":{"account_id":acc_id},"result":res,"ok":res.get("ok",True)}]}
        else:
            iban = _extract_iban(user_text)
            triplet = _extract_triplet(user_text)
            if iban or triplet:
                try:
                    client = InterApiClient()
                    raw = client.get_account_detail(
                        account_suffix=triplet[0] if triplet else None,
                        branch_code=triplet[1] if triplet else None,
                        customer_no=triplet[2] if triplet else None,
                        iban=iban,
                    )
                    return {"YANIT": compose_balance_reply(raw), "toolOutputs": [{"name":"get_balance","args": {"iban":iban} if iban else {"account_suffix":triplet[0],"branch_code":triplet[1],"customer_no":triplet[2]}, "result":{"ok":True,"raw":raw,"text":compose_balance_reply(raw)},"ok":True}]}
                except Exception as e:
                    return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu: {e}"}

    # 2) LLM tool-calling path
    return _run_llm_tool_path(user_text)


if __name__ == "__main__":
    print("Minimal Agent — LLM tool-calling + rule-based short-circuit (Ctrl+C to exit)")
    try:
        while True:
            print("YANIT:", handle_message(input("> "))["YANIT"])
    except KeyboardInterrupt:
        pass

# from __future__ import annotations
# import os, re
# from typing import Dict, Any, Optional

# USE_MCP = os.getenv("USE_MCP") == "1"

# if USE_MCP:
#     from integrations.fastmcp_client import call_mcp_tool
# else:
#     from tools.account_balance import InterApiClient, compose_balance_reply

# BALANCE_KEYWORDS = ["bakiye", "balance", "ne kadar var", "kalan para", "hesabımda ne kadar", "bakiyem"]
# IBAN_RE  = re.compile(r"\bTR[0-9A-Z]{24}\b", re.IGNORECASE)
# NUM_RE   = re.compile(r"\b\d{2,}\b")          # InterAPI üçlü için
# ACCID_RE = re.compile(r"\b\d{1,10}\b")        # MCP için account_id

# def _extract_triplet(text: str) -> Optional[Dict[str, Any]]:
#     nums = [int(x) for x in NUM_RE.findall(text)]
#     uniq = []
#     for n in nums:
#         if n not in uniq:
#             uniq.append(n)
#         if len(uniq) == 3:
#             break
#     if len(uniq) < 3:
#         return None
#     # en uzun -> customer, kalanın büyüğü -> branch, küçüğü -> suffix
#     customer_no = max(uniq, key=lambda n: (len(str(n)), n))
#     rest = [n for n in uniq if n != customer_no]
#     return {"account_suffix": min(rest), "branch_code": max(rest), "customer_no": customer_no}

# def _extract_account_id(text: str) -> Optional[int]:
#     m = ACCID_RE.search(text)
#     return int(m.group(0)) if m else None

# def _format_try(n: float) -> str:
#     s = f"{n:,.2f}"
#     return s.replace(",", "X").replace(".", ",").replace("X", ".")

# def _compose_mcp_balance_reply(raw: Dict[str, Any]) -> str:
#     if not isinstance(raw, dict):
#         return "Beklenmedik MCP yanıtı (dict değil)."
#     if "error" in raw:
#         return f"Hata: {raw.get('error')}"
#     data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
#     acc_id = data.get("account_id")
#     bal    = data.get("balance")
#     cur    = data.get("currency", "TRY")
#     st     = data.get("status", "")
#     if isinstance(bal, str):
#         try: bal = float(bal.replace(",", "."))
#         except Exception: pass
#     if isinstance(bal, (int, float)):
#         return f"Hesap {acc_id} için güncel bakiye: {_format_try(float(bal))} {cur}. (durum: {st})"
#     return f"Bakiye bilgisi alınamadı. (alanlar: {', '.join(sorted(map(str, data.keys())) )})"

# def handle_message(user_message: str) -> Dict[str, Any]:
#     lm = user_message.lower()
#     if not any(k in lm for k in BALANCE_KEYWORDS):
#         return {"YANIT": ("Bakiye için lütfen 'account_id' yaz (örn: 'hesap 1 bakiyem')." if USE_MCP
#                           else "Bakiye sormak istersen IBAN veya (şube, ek no, müşteri no) yaz.")}

#     if USE_MCP:
#         acc_id = _extract_account_id(user_message)
#         if acc_id is None:
#             return {"YANIT": "Hangi hesabın bakiyesini istiyorsun? Sayısal account_id gönder (örn: 'hesap 1 bakiyem')."}
#         try:
#             url  = os.getenv("MCP_SSE_URL", "http://127.0.0.1:8081/sse")
#             tool = os.getenv("MCP_BALANCE_TOOL", "get_balance")
#             raw  = call_mcp_tool(url, tool, {"account_id": acc_id})
#             return {"YANIT": _compose_mcp_balance_reply(raw)}
#         except Exception as e:
#             return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu (MCP): {e}"}

#     # InterAPI yolu (opsiyonel şimdilik mcp server kullanıyoruz)
#     m_iban = IBAN_RE.search(user_message)
#     args: Dict[str, Any]
#     if m_iban:
#         args = {"iban": m_iban.group(0)}
#     else:
#         trip = _extract_triplet(user_message)
#         if not trip:
#             return {"YANIT": "Hangi hesabın bakiyesini istiyorsun? IBAN ya da 'şube, ek no, müşteri no' ver."}
#         args = trip
#     try:
#         client = InterApiClient()
#         raw = client.get_account_detail(**args)
#         return {"YANIT": compose_balance_reply(raw)}
#     except Exception as e:
#         return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu: {e}"}

# if __name__ == "__main__":
#     print("Minimal Agent — MCP(HTTP) veya InterAPI modunda çalışır (çıkış: Ctrl+C)")
#     try:
#         while True:
#             print("YANIT:", handle_message(input("> "))["YANIT"])
#     except KeyboardInterrupt:
#         pass
