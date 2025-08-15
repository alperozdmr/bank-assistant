from __future__ import annotations
import os, re
from typing import Dict, Any, Optional

USE_MCP = os.getenv("USE_MCP") == "1"

if USE_MCP:
    from integrations.fastmcp_client import call_mcp_tool
else:
    from tools.account_balance import InterApiClient, compose_balance_reply

BALANCE_KEYWORDS = ["bakiye", "balance", "ne kadar var", "kalan para", "hesabımda ne kadar", "bakiyem"]
IBAN_RE  = re.compile(r"\bTR[0-9A-Z]{24}\b", re.IGNORECASE)
NUM_RE   = re.compile(r"\b\d{2,}\b")          # InterAPI üçlü için
ACCID_RE = re.compile(r"\b\d{1,10}\b")        # MCP için account_id

def _extract_triplet(text: str) -> Optional[Dict[str, Any]]:
    nums = [int(x) for x in NUM_RE.findall(text)]
    uniq = []
    for n in nums:
        if n not in uniq:
            uniq.append(n)
        if len(uniq) == 3:
            break
    if len(uniq) < 3:
        return None
    # en uzun -> customer, kalanın büyüğü -> branch, küçüğü -> suffix
    customer_no = max(uniq, key=lambda n: (len(str(n)), n))
    rest = [n for n in uniq if n != customer_no]
    return {"account_suffix": min(rest), "branch_code": max(rest), "customer_no": customer_no}

def _extract_account_id(text: str) -> Optional[int]:
    m = ACCID_RE.search(text)
    return int(m.group(0)) if m else None

def _format_try(n: float) -> str:
    s = f"{n:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def _compose_mcp_balance_reply(raw: Dict[str, Any]) -> str:
    if not isinstance(raw, dict):
        return "Beklenmedik MCP yanıtı (dict değil)."
    if "error" in raw:
        return f"Hata: {raw.get('error')}"
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    acc_id = data.get("account_id")
    bal    = data.get("balance")
    cur    = data.get("currency", "TRY")
    st     = data.get("status", "")
    if isinstance(bal, str):
        try: bal = float(bal.replace(",", "."))
        except Exception: pass
    if isinstance(bal, (int, float)):
        return f"Hesap {acc_id} için güncel bakiye: {_format_try(float(bal))} {cur}. (durum: {st})"
    return f"Bakiye bilgisi alınamadı. (alanlar: {', '.join(sorted(map(str, data.keys())) )})"

def handle_message(user_message: str) -> Dict[str, Any]:
    lm = user_message.lower()
    if not any(k in lm for k in BALANCE_KEYWORDS):
        return {"YANIT": ("Bakiye için lütfen 'account_id' yaz (örn: 'hesap 1 bakiyem')." if USE_MCP
                          else "Bakiye sormak istersen IBAN veya (şube, ek no, müşteri no) yaz.")}

    if USE_MCP:
        acc_id = _extract_account_id(user_message)
        if acc_id is None:
            return {"YANIT": "Hangi hesabın bakiyesini istiyorsun? Sayısal account_id gönder (örn: 'hesap 1 bakiyem')."}
        try:
            url  = os.getenv("MCP_SSE_URL", "http://127.0.0.1:8081/sse")
            tool = os.getenv("MCP_BALANCE_TOOL", "get_balance")
            raw  = call_mcp_tool(url, tool, {"account_id": acc_id})
            return {"YANIT": _compose_mcp_balance_reply(raw)}
        except Exception as e:
            return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu (MCP): {e}"}

    # InterAPI yolu (opsiyonel şimdilik mcp server kullanıyoruz)
    m_iban = IBAN_RE.search(user_message)
    args: Dict[str, Any]
    if m_iban:
        args = {"iban": m_iban.group(0)}
    else:
        trip = _extract_triplet(user_message)
        if not trip:
            return {"YANIT": "Hangi hesabın bakiyesini istiyorsun? IBAN ya da 'şube, ek no, müşteri no' ver."}
        args = trip
    try:
        client = InterApiClient()
        raw = client.get_account_detail(**args)
        return {"YANIT": compose_balance_reply(raw)}
    except Exception as e:
        return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu: {e}"}

if __name__ == "__main__":
    print("Minimal Agent — MCP(HTTP) veya InterAPI modunda çalışır (çıkış: Ctrl+C)")
    try:
        while True:
            print("YANIT:", handle_message(input("> "))["YANIT"])
    except KeyboardInterrupt:
        pass
