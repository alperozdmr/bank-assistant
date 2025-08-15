# MINIMAL AGENT SADECE ACCOUNT BALANCE ÇAĞIRIR METİN OUTPUTU DÖNDÜRÜR

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from tools.account_balance import InterApiClient, compose_balance_reply

BALANCE_KEYWORDS = [
    "bakiye",
    "balance",
    "ne kadar var",
    "kalan para",
    "hesabımda ne kadar",
    "bakiyem",
]
IBAN_RE = re.compile(r"\bTR[0-9A-Z]{24}\b", re.IGNORECASE)
NUM_RE = re.compile(r"\b\d{2,}\b")  # branch/suffix/customer için kaba yakalama


def _extract_triplet(text: str) -> Optional[Dict[str, Any]]:
    nums = [int(x) for x in NUM_RE.findall(text)]
    if len(nums) < 3:
        return None
    uniq = []
    for n in nums:
        if n not in uniq:
            uniq.append(n)
        if len(uniq) == 3:
            break
    if len(uniq) < 3:
        return None
    # En uzun (>=6-7 hane) olanı customer_no kabul et
    strlens = [(n, len(str(n))) for n in uniq]
    customer_no = max(strlens, key=lambda t: (t[1], t[0]))[0]
    rest = [n for n in uniq if n != customer_no]
    branch_code = max(rest)
    account_suffix = min(rest)
    return {
        "account_suffix": account_suffix,
        "branch_code": branch_code,
        "customer_no": customer_no,
    }


def handle_message(user_message: str) -> Dict[str, Any]:
    lm = user_message.lower()
    if not any(k in lm for k in BALANCE_KEYWORDS):
        return {
            "YANIT": "Bakiye sormak istersen IBAN veya (şube, ek no, müşteri no) yaz."
        }

    m_iban = IBAN_RE.search(user_message)
    args: Dict[str, Any]
    if m_iban:
        args = {"iban": m_iban.group(0)}
    else:
        trip = _extract_triplet(user_message)
        if not trip:
            return {
                "YANIT": "Hangi hesabın bakiyesini istiyorsun? IBAN yazabilir veya sırayla 'şube kodu, hesap ek no, müşteri no' gönderebilirsin."
            }
        args = trip

    try:
        client = InterApiClient()
        raw = client.get_account_detail(**args)
        return {"YANIT": compose_balance_reply(raw)}
    except Exception as e:
        return {"YANIT": f"Bakiyeyi alırken bir sorun oluştu: {e}"}


if __name__ == "__main__":
    print("Minimal Agent (S3) — mesaj yaz (çıkış: Ctrl+C)")
    try:
        while True:
            msg = input("> ")
            out = handle_message(msg)
            print("YANIT:", out["YANIT"])
    except KeyboardInterrupt:
        pass
