# pii.py
import re

IBAN_TR = re.compile(r"\bTR\d{2}[A-Z0-9]{20,26}\b", re.IGNORECASE)
CARD16  = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
LONG_DIGITS = re.compile(r"\b\d{10,}\b")

def mask_text(s: str) -> str:
    if not s:
        return s
    s = IBAN_TR.sub(lambda m: m.group(0)[:6] + "*"*(len(m.group(0))-10) + m.group(0)[-4:], s)
    s = CARD16.sub(lambda m: m.group(0)[:4] + "-****-****-" + m.group(0)[-4:], s)
    s = LONG_DIGITS.sub(lambda m: m.group(0)[:2] + "*"*(len(m.group(0))-4) + m.group(0)[-2:], s)
    return s

def mask_args(d: dict) -> dict:
    out = {}
    for k, v in (d or {}).items():
        if isinstance(v, str):
            out[k] = mask_text(v)
        else:
            out[k] = v
    return out
