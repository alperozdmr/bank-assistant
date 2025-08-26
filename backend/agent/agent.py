# backend/agent/agent.py
# Minimal Agent — LLM tool-calling + MCP
from __future__ import annotations

import json
import re
import os
from typing import Any, Dict, List, Optional

from integrations.fastmcp_client import call_mcp_tool
from llmadapter import LLMAdapter
from tools.schemas import get_tool_catalog


USE_MCP = 0
MCP_URL = "http://127.0.0.1:8082/sse"

def _default_customer_id() -> Optional[int]:
    v = os.getenv("DEFAULT_CUSTOMER_ID")
    if not v:
        return None
    try:
        return int(v)
    except Exception:
        return None

# MCP ayarları, default müşteri kimliği
import os
DEFAULT_CUSTOMER_ID = None
try:
    _dc = os.getenv("DEFAULT_CUSTOMER_ID")
    if _dc:
        DEFAULT_CUSTOMER_ID = int(_dc)
except Exception:
    DEFAULT_CUSTOMER_ID = None

_BALANCE_WORDS = (
    "bakiye",
    "balance",
    "ne kadar var",
    "kalan para",
    "hesabımda ne kadar",
    "bakiyem"
)
_CARD_WORDS = ("kart", "kredi kartı", "kartım", "kart bilgisi", "kart detayı", 
               "limit", "borç", "son ödeme", "kesim", "kullanılabilir limit", "kart borcu"
)
_FX_WORDS   = ("kur", "döviz", "doviz", "usd", "eur", "dolar", "euro", "sterlin", "rate")
_INT_WORDS  = ("faiz", "oran", "interest", "yatırım", "mevduat", "kredi faizi", "kredi")
_CARD_DEBT_TRIGGERS = ("kart borcu", "kart borcum", "kredi kartı borcu", "kredi karti borcu", "ekstre", "borç")
_FEE_WORDS  = ("ücret", "ucret", "masraf", "komisyon", "aidat", "fee")
_ALL_FEES_TRIGGERS = ("tüm ücret", "tüm ücretler", "tum ucret", "ucretler", "ücretler", "all fees")
_ACC_STRICT = re.compile(r"\b(hesap|account)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_CUST_RE = re.compile(r"\b(müşteri|customer)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_ACC_RE = re.compile(r"\b\d{1,10}\b")
_SRV_RE = re.compile(r"\b(eft|fast|havale|kart[_\s]?aidat[ıi]|kredi[_\s]?tahsis)\b", re.IGNORECASE)


def _acc_id(txt: str) -> Optional[int]:
    m = _ACC_RE.search(txt)
    return int(m.group()) if m else None


def _cust_id(txt: str) -> Optional[int]:
    m = _CUST_RE.search(txt)
    return int(m.group(3)) if m else None

def _service_code(txt: str) -> Optional[str]:
    m = _SRV_RE.search(txt or "")
    if not m: return None
    s = m.group(1).upper().replace(" ", "_")
    if s.startswith("KART"): s = "KART_AIDATI"
    if s.startswith("KREDI"): s = "KREDI_TAHSIS"
    return s

def _fmt_try_amount(x: Any) -> str:
    try:
        v = float(str(x).replace(",", "."))
    except Exception:
        return str(x)
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_balance(res: Dict[str, Any], fallback_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Balance response'unu hem text hem de UI component data olarak döndürür
    """
    if not isinstance(res, dict):
        return {
            "text": "Beklenmedik MCP yanıtı.",
            "ui_component": None
        }
    if res.get("error"):
        return {
            "text": f"Hata: {res['error']}",
            "ui_component": None
        }
    
    d = res["data"] if isinstance(res.get("data"), dict) else res
    
    # UI component data varsa onu kullan
    ui_component = d.get("ui_component")
    
    # burası customer id için eklendi
    if isinstance(d.get("accounts"), list):
        accs = d["accounts"]
        if not accs:
            return {
                "text": "Bu müşteri için hesap bulunamadı.",
                "ui_component": None
            }
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
                f"#{a.get('account_id')} {a.get('balance_formatted', a.get('balance'))} {a.get('currency')}"
                for a in accs[:3]
            )
            more = f" (+{len(accs)-3} daha)" if len(accs) > 3 else ""
            return {
                "text": f"{len(accs)} hesap bulundu: {preview}{more}. Lütfen bir account_id seçin.",
                "ui_component": ui_component
            }

    cur = (d.get("currency") or "").upper()
    bal = d.get("balance")
    try:
        # "12.345,67" / "12345.67" / "12345,67" toleransı
        s = str(bal).replace(" ", "")
        if s.count(".") > 1:  # binlik nokta + ondalık virgül
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        val = float(s)
    except Exception:
        return {
            "text": "Bakiye bilgisi okunamadı.",
            "ui_component": None
        }
    amt = f"{val:,.2f}"
    if cur == "TRY":
        amt = amt.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return {
        "text": f"Hesap {d.get('account_id', fallback_id)} bakiyeniz: {amt} {cur}",
        "ui_component": ui_component
    }


def _fmt_fx(res: Dict[str, Any], requested_currency: str = None) -> Dict[str, Any]:
    """
    Exchange rates response'unu hem text hem de UI component data olarak döndürür
    """
    d = res.get("data") if isinstance(res.get("data"), dict) else res
    rates = d.get("rates") or []
    ui_component = d.get("ui_component")
    
    if not rates:
        return {
            "text": "Kur bilgisi bulunamadı.",
            "ui_component": None
        }
    
    # Belirli bir kur istendiyse sadece onu filtrele
    if requested_currency:
        currency_map = {
            'usd': 'USD/TRY', 'dolar': 'USD/TRY',
            'eur': 'EUR/TRY', 'euro': 'EUR/TRY',
            'gbp': 'GBP/TRY', 'sterlin': 'GBP/TRY', 'pound': 'GBP/TRY',
            'jpy': 'JPY/TRY', 'yen': 'JPY/TRY',
            'chf': 'CHF/TRY', 'frank': 'CHF/TRY',
            'cny': 'CNY/TRY', 'yuan': 'CNY/TRY',
            'ruble': 'RUB/TRY', 'rub': 'RUB/TRY',
            'sar': 'SAR/TRY', 'riyal': 'SAR/TRY',
            'aed': 'AED/TRY', 'dirhem': 'AED/TRY',
            'cad': 'CAD/TRY', 'kanada': 'CAD/TRY'
        }
        
        target_code = currency_map.get(requested_currency.lower())
        if target_code:
            filtered_rates = [r for r in rates if r.get("code") == target_code]
            if filtered_rates:
                rates = filtered_rates
                ui_component = {
                    "type": "exchange_rates_card",
                    "rates": filtered_rates
                }
    
    # UI component yoksa kendimiz oluşturalım
    if not ui_component and rates:
        ui_component = {
            "type": "exchange_rates_card",
            "rates": rates
        }
    
    head = []
    for r in rates[:5]:
        code = r.get("code"); buy = r.get("buy"); sell = r.get("sell")
        head.append(f"{code}: alış {buy}, satış {sell}")
    
    return {
        "text": "Güncel kurlardan örnekler:\n- " + "\n- ".join(head),
        "ui_component": ui_component
    }

def _fmt_interest(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interest rates response'unu hem text hem de UI component data olarak döndürür
    """
    d = res.get("data") if isinstance(res.get("data"), dict) else res
    rates = d.get("rates") or []
    ui_component = d.get("ui_component")
    
    if not rates:
        return {
            "text": "Faiz oranı bulunamadı.",
            "ui_component": None
        }
    
    # UI component yoksa kendimiz oluşturalım
    if not ui_component and rates:
        ui_component = {
            "type": "interest_rates_card",
            "rates": rates
        }
    
    head = []
    for r in rates[:5]:
        prod = r.get("product"); apy = r.get("rate_apy")
        head.append(f"{prod}: yıllık {round(100*float(apy),2)}% APY")
    
    return {
        "text": "Güncel faiz oranları (örnek):\n- " + "\n- ".join(head),
        "ui_component": ui_component
    }

def _fmt_fees(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fees response'unu hem text hem de UI component data olarak döndürür.
    - get_fee (tek kayıt) ve list_fees (liste) ikisini de destekler.
    Return: {"text": str, "ui_component": {...} | None}
    """
    d = res.get("data") if isinstance(res.get("data"), dict) else res
    if not isinstance(d, dict) or d.get("error"):
        return {"text": "Ücret bilgisi bulunamadı.", "ui_component": None}

    # liste desteği
    if isinstance(d.get("fees"), list):
        fees = d.get("fees") or []

        def fmt_try(x: float) -> str:
            s = f"{float(x):,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        def one_line(item: Dict[str, Any]) -> str:
            desc = item.get("description") or item.get("service_code") or "Bilinmeyen"
            pr = item.get("pricing") or {}
            t = (pr.get("type") or "").lower() if isinstance(pr, dict) else ""
            cur = (pr.get("currency") or "TRY").upper() if isinstance(pr, dict) else "TRY"

            if t == "flat" and pr.get("amount") is not None:
                return f"{desc}: {fmt_try(pr['amount'])} {cur}"

            if t == "percent" and pr.get("rate") is not None:
                extras = []
                if pr.get("min") is not None:
                    extras.append(f"min {fmt_try(pr['min'])} {cur}")
                if pr.get("max") is not None:
                    extras.append(f"max {fmt_try(pr['max'])} {cur}")
                tail = f" ({'; '.join(extras)})" if extras else ""
                return f"{desc}: %{round(100*float(pr['rate']), 2)}{tail}"

            if t == "tiered" and isinstance(pr.get("tiers"), list):
                parts = []
                for tier in pr["tiers"][:4]:
                    thr = tier.get("threshold")
                    fee = tier.get("fee")
                    if fee is None:
                        continue
                    if thr is None:
                        parts.append(f"{fmt_try(fee)} {cur}")
                    else:
                        parts.append(f"≤{int(thr):,}".replace(",", ".") + f": {fmt_try(fee)} {cur}")
                if parts:
                    return f"{desc}: " + "; ".join(parts)

            return f"{desc}: (detay yok)"

        lines = ["- " + one_line(f) for f in fees[:20]]
        if len(fees) > 20:
            lines.append(f"... (+{len(fees)-20} diğer)")

        # UI component — liste
        ui_component = {
            "type": "fees_list",
            "items": fees,  # Dilersen map'leyip sadeleştirebilirsin
        }
        return {
            "text": "Güncel ücretlerden özet:\n" + "\n".join(lines),
            "ui_component": ui_component,
        }

    # ---------- TEK KAYIT (get_fee) DESTEĞİ ----------
    if "service_code" not in d:
        return {"text": "Ücret bilgisi bulunamadı.", "ui_component": None}

    desc = (d.get("description") or d.get("service_code") or "").strip()
    pr = d.get("pricing") or {}

    # UI component - MCP'den gelen varsa onu kullan, yoksa oluştur
    ui_component = d.get("ui_component")
    if not ui_component:
        ui_component = {
            "type": "fees_card",
            "service_code": d.get("service_code"),
            "description": desc,
            "pricing": pr,
            "updated_at": d.get("updated_at"),
        }

    def fmt_try(x: float) -> str:
        s = f"{float(x):,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    t = (pr.get("type") or "").lower() if isinstance(pr, dict) else ""

    # 1) Sabit tutar
    if t == "flat" and pr.get("amount") is not None:
        cur = (pr.get("currency") or "TRY").upper()
        text = f"Güncel {desc} ücreti: {fmt_try(pr['amount'])} {cur}."
    # 2) Yüzde
    elif t == "percent" and pr.get("rate") is not None:
        cur = (pr.get("currency") or "TRY").upper()
        extras = []
        if pr.get("min") is not None:
            extras.append(f"min {fmt_try(pr['min'])} {cur}")
        if pr.get("max") is not None:
            extras.append(f"max {fmt_try(pr['max'])} {cur}")
        tail = f" ({'; '.join(extras)})" if extras else ""
        text = f"Güncel {desc} ücreti: %{round(100*float(pr['rate']), 2)}{tail}."
    # 3) Dilimli
    elif t == "tiered" and isinstance(pr.get("tiers"), list):
        parts = []
        for tier in pr["tiers"][:4]:
            thr = tier.get("threshold")
            fee = tier.get("fee")
            if fee is None:
                continue
            if thr is None:
                parts.append(f"{fmt_try(fee)} TRY")
            else:
                parts.append(f"≤{int(thr):,}".replace(",", ".") + f": {fmt_try(fee)} TRY")
        if parts:
            text = f"Güncel {desc} ücreti (dilimler): " + "; ".join(parts) + "."
        else:
            text = f"{desc} ücreti için detay bulunamadı."
    else:
        text = f"{desc} ücreti için detay bulunamadı."

    return {"text": text, "ui_component": ui_component}

def _fmt_card_info(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Card info response'unu hem text hem de UI component data olarak döndürür
    """
    if not isinstance(res, dict) or res.get("error"):
        return {
            "text": "Kart bilgisi bulunamadı.",
            "ui_component": None
        }
    
    # UI component oluştur
    ui_component = {
        "type": "card_info_card",
        "card_id": res.get("card_id"),
        "limit": res.get("limit"),
        "borc": res.get("borc"),
        "kesim_tarihi": res.get("kesim_tarihi"),
        "son_odeme_tarihi": res.get("son_odeme_tarihi")
    }
    
    # Text oluştur
    card_id = res.get("card_id", "N/A")
    limit = res.get("limit", 0)
    borc = res.get("borc", 0)
    available = limit - borc
    
    text = f"Kart #{card_id} bilgileri:\n"
    text += f"• Kredi Limiti: {limit:,.2f} TRY\n"
    text += f"• Güncel Borç: {borc:,.2f} TRY\n"
    text += f"• Kullanılabilir: {available:,.2f} TRY\n"
    text += f"• Kesim: {res.get('kesim_tarihi', 'N/A')}. gün\n"
    text += f"• Son Ödeme: {res.get('son_odeme_tarihi', 'N/A')}. gün"
    
    return {
        "text": text,
        "ui_component": ui_component
    }

def _fmt_card_summary(res: Dict[str, Any]) -> str:
    d = res.get("data") if isinstance(res.get("data"), dict) else res
    if not isinstance(d, dict):
        return "Kart bilgisi okunamadı."
    if d.get("error") == "no_cards":
        return "Bu müşteri için kayıtlı kart bulunamadı."
    if isinstance(d.get("summary"), dict) and isinstance(d.get("card"), dict):
        s, c = d["summary"], d["card"]
        debt = s.get("current_debt")
        cur  = (c.get("currency") or "TRY").upper()
        try:
            val = float(debt or 0.0)
        except Exception:
            return "Kart borcu okunamadı."
        amt = f"{abs(val):,.2f}"
        if cur == "TRY":
            amt = amt.replace(",", "X").replace(".", ",").replace("X", ".")
        tail = f" Son ödeme günü: {s.get('due_day')}" if s.get("due_day") else ""
        return f"Kart borcunuz: {amt} {cur}{tail}"
    cards = d.get("cards") or []
    if cards:
        head = []
        for c in cards[:5]:
            cur = (c.get("currency") or "TRY").upper()
            try:
                val = float(c.get("current_debt") or 0.0)
            except Exception:
                val = 0.0
            amt = f"{abs(val):,.2f}"
            if cur == "TRY":
                amt = amt.replace(",", "X").replace(".", ",").replace("X", ".")
            head.append(f"#{c.get('card_id')} → borç {amt} {cur}")
        more = f" (+{len(cards)-5} daha)" if len(cards) > 5 else ""
        return "Birden fazla kart bulundu:\n- " + "\n- ".join(head) + more + "\nLütfen bir card_id seçin."
    return "Kart bilgisi bulunamadı."

def _fmt_atm_search(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    ATM/Branch search response'unu hem text hem de UI component data olarak döndürür
    """
    if not isinstance(res, dict) or not res.get("ok"):
        return {
            "text": "ATM/Şube arama başarısız oldu.",
            "ui_component": None
        }
    
    # MCP response'unda çift data katmanı var
    data = res.get("data", {})
    if isinstance(data, dict) and data.get("ok"):
        data = data.get("data", {})
    
    items = data.get("items", [])
    ui_component = data.get("ui_component")
    query = data.get("query", {})
    
    if not items:
        city = query.get("city", "")
        district = query.get("district", "")
        location = f"{city}{f' {district}' if district else ''}"
        return {
            "text": f"{location} bölgesinde ATM/şube bulunamadı.",
            "ui_component": None
        }
    
    # UI component yoksa kendimiz oluşturalım
    if not ui_component and items:
        ui_component = {
            "type": "atm_card",
            "query": query,
            "items": items,
            "count": len(items)
        }
    
    # Text oluştur
    city = query.get("city", "")
    district = query.get("district", "")
    search_type = query.get("type")
    location = f"{city}{f' {district}' if district else ''}"
    
    type_text = ""
    if search_type == "atm":
        type_text = "ATM"
    elif search_type == "branch":
        type_text = "şube"
    else:
        type_text = "ATM/şube"
    
    count = len(items)
    text = f"{location} bölgesinde {count} {type_text} bulundu."
    
    return {
        "text": text,
        "ui_component": ui_component
    }


def _llm_flow(user_text: str) -> Dict[str, Any]:
    adapter = LLMAdapter()
    msgs: List[Dict[str, str]] = adapter.system_messages() + [
        {"role": "user", "content": user_text}
    ]
    tools = get_tool_catalog()["tools"]

    first = adapter.generate(messages=msgs, tools=tools, tool_choice="auto")
    if "error" in first:
        return {"YANIT": "Üzgünüm, model şu anda yanıt veremiyor.", "error": first}

    calls = LLMAdapter.first_tool_calls(first)
    if not calls:
        txt = (
            LLMAdapter.first_message_content(first)
            or "Lütfen sayısal account_id yazın (örn: 1)."
        )
        return {"YANIT": txt, "toolOutputs": []}

    outs: List[Dict[str, Any]] = []
    for c in calls:
        name = c.get("name")
        args = c.get("arguments") or {}
        call_id = c.get("id")
        if name == "get_balance" and "account_id" in args:
            try:
                payload = {"account_id": int(args["account_id"])}
                res = call_mcp_tool(MCP_URL, "get_balance", payload)
                out = {
                    "name": "get_balance",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_balance",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "get_accounts" and "customer_id" in args:
            try:
                payload = {"customer_id": int(args["customer_id"])}
                res = call_mcp_tool(MCP_URL, "get_accounts", payload)
                out = {
                    "name": "get_accounts",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_accounts",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "get_fee" and "service_code" in args:
            try:
                payload = {"service_code": args["service_code"]}
                res = call_mcp_tool(MCP_URL, "get_fee", payload)
                out = {
                    "name": "get_fee",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_fee",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "get_exchange_rates":
            try:
                payload = {}
                res = call_mcp_tool(MCP_URL, "get_exchange_rates", payload)
                out = {
                    "name": "get_exchange_rates",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_exchange_rates",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "get_interest_rates":
            try:
                payload = {}
                res = call_mcp_tool(MCP_URL, "get_interest_rates", payload)
                out = {
                    "name": "get_interest_rates",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_interest_rates",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "branch_atm_search" and "city" in args:
            try:
                payload = {
                    "city": args["city"],
                    "district": args.get("district"),
                    "type": args.get("type"),
                    "limit": args.get("limit", 3)
                }
                res = call_mcp_tool(MCP_URL, "branch_atm_search", payload)
                out = {
                    "name": "branch_atm_search",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "branch_atm_search",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        else:
            out = {
                "name": name,
                "args": args,
                "result": {"ok": False, "error": "missing_account_id"},
                "ok": False,
            }

        outs.append(out)
        msgs.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "name": out["name"],
                "content": json.dumps(out["result"], ensure_ascii=False),
            }
        )

    second = adapter.generate(messages=msgs)
    
    # Balance response'u handle et - sadece balance tool'ları için
    ui_component = None
    final_text = ""
    
    # Eğer balance tool kullanıldıysa UI component'i çıkar
    if outs and outs[0].get("name") in ("get_balance", "get_accounts", "AccountBalanceTool_get_balance"):
        balance_result = _fmt_balance(outs[0]["result"])
        ui_component = balance_result.get("ui_component")
        
        # UI component varsa text boş, yoksa balance text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = balance_result["text"]
    elif outs and outs[0].get("name") == "get_exchange_rates":
        # Kullanıcı mesajında belirli bir kur var mı kontrol et
        import re
        currency_match = re.search(r'\b(usd|dolar|euro|eur|gbp|sterlin|pound|jpy|yen|chf|frank|cny|yuan|ruble|rub|sar|riyal|aed|dirhem|cad|kanada)\b', user_text.lower())
        requested_currency = currency_match.group(1) if currency_match else None
        
        fx_result = _fmt_fx(outs[0]["result"], requested_currency)
        ui_component = fx_result.get("ui_component")
        
        # UI component varsa text boş, yoksa fx text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = fx_result["text"]
    elif outs and outs[0].get("name") == "get_interest_rates":
        interest_result = _fmt_interest(outs[0]["result"])
        ui_component = interest_result.get("ui_component")
        
        # UI component varsa text boş, yoksa interest text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = interest_result["text"]
    elif outs and outs[0].get("name") == "get_fee":
        fees_result = _fmt_fees(outs[0]["result"])
        ui_component = fees_result.get("ui_component")
        
        # UI component varsa text boş, yoksa fees text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = fees_result["text"]
    elif outs and outs[0].get("name") == "get_card_info":
        card_result = _fmt_card_info(outs[0]["result"])
        ui_component = card_result.get("ui_component")
        
        # UI component varsa text boş, yoksa card text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = card_result["text"]
    elif outs and outs[0].get("name") == "branch_atm_search":
        atm_result = _fmt_atm_search(outs[0]["result"])
        ui_component = atm_result.get("ui_component")
        
        # UI component varsa text boş, yoksa atm text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = atm_result["text"]
    else:
        # Diğer tool'lar için LLM response'unu kullan
        final_text = LLMAdapter.first_message_content(second)
    
    # Fallback text
    if not final_text and not ui_component:
        final_text = "Lütfen sayısal account_id yazın (örn: 1)."
    
    result = {
        "YANIT": final_text,
        "toolOutputs": outs,
        "llmTime": {
            "first": first.get("_elapsed_sec"),
            "second": second.get("_elapsed_sec"),
        },
    }
    
    # UI component varsa ekle
    if ui_component:
        result["ui_component"] = ui_component
        
    return result


def handle_message(user_text: str) -> Dict[str, Any]:
    low = user_text.lower()

    # --- TÜM ÜCRETLER ---
    if any(k in low for k in ("tüm ücret", "tum ucret", "ücretler", "ucretler", "all fees", "tüm ücretler", "tum ucretler")):
        res = call_mcp_tool(MCP_URL, "list_fees", {"limit": 200})
        try:
            fees_out = _fmt_fees(res)
        except Exception:
            fees_out = None
        if isinstance(fees_out, dict) and ("text" in fees_out or "ui_component" in fees_out):
            ui_component = fees_out.get("ui_component")
            result = {
                "YANIT": "" if ui_component else fees_out.get("text", "Ücret bilgisi bulunamadı."),
                "toolOutputs": [{"name": "list_fees", "args": {"limit": 200}, "result": res, "ok": res.get("ok", True)}],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result

        d = res.get("data") if isinstance(res.get("data"), dict) else res
        fees = (d or {}).get("fees") or []
        if not fees:
            return {
                "YANIT": "Ücret bilgisi bulunamadı.",
                "toolOutputs": [{"name": "list_fees", "args": {"limit": 200}, "result": res, "ok": res.get("ok", True)}],
            }

        def _fmt_try(x: float) -> str:
            s = f"{float(x):,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        def _one_line(desc: str, pr: Dict[str, Any]) -> str:
            t = (pr.get("type") or "").lower()
            cur = (pr.get("currency") or "TRY").upper()
            if t == "flat" and pr.get("amount") is not None:
                return f"{desc}: {_fmt_try(pr['amount'])} {cur}"
            if t == "percent" and pr.get("rate") is not None:
                extras = []
                if pr.get("min") is not None:
                    extras.append(f"min {_fmt_try(pr['min'])} {cur}")
                if pr.get("max") is not None:
                    extras.append(f"max {_fmt_try(pr['max'])} {cur}")
                tail = f" ({'; '.join(extras)})" if extras else ""
                return f"{desc}: %{round(100*float(pr['rate']), 2)}{tail}"
            if t == "tiered" and isinstance(pr.get("tiers"), list):
                parts = []
                for tier in pr["tiers"][:4]:
                    thr = tier.get("threshold")
                    fee = tier.get("fee")
                    if fee is None:
                        continue
                    if thr is None:
                        parts.append(f"{_fmt_try(fee)} TRY")
                    else:
                        parts.append(f"≤{int(thr):,}".replace(",", ".") + f": {_fmt_try(fee)} TRY")
                if parts:
                    return f"{desc}: " + "; ".join(parts)
            return f"{desc}: (detay bulunamadı)"

        lines = []
        for f in fees[:20]:
            desc = f.get("description") or f.get("service_code") or "Bilinmeyen"
            pr = f.get("pricing") or {}
            if isinstance(pr, str):
                try:
                    import json as _json
                    pr = _json.loads(pr)
                except Exception:
                    pr = {}
            lines.append("- " + _one_line(desc, pr if isinstance(pr, dict) else {}))
        if len(fees) > 20:
            lines.append(f"... (+{len(fees)-20} diğer)")

        return {
            "YANIT": "Güncel ücretlerden özet:\n" + "\n".join(lines),
            "toolOutputs": [{"name": "list_fees", "args": {"limit": 200}, "result": res, "ok": res.get("ok", True)}],
        }

    # --- Tek hizmet kodu varsa: get_fee ---
    code = _service_code(user_text)
    if code:
        res = call_mcp_tool(MCP_URL, "get_fee", {"service_code": code})
        if res.get("error") and res.get("available_codes"):
            opts = ", ".join(res["available_codes"])
            return {"YANIT": f"'{code}' bulunamadı. Desteklenenler: {opts}. Hangisini istersiniz?"}
        fees_result = _fmt_fees(res)
        ui_component = fees_result.get("ui_component") if isinstance(fees_result, dict) else None
        result = {
            "YANIT": "" if ui_component else (fees_result.get("text") if isinstance(fees_result, dict) else str(fees_result)),
            "toolOutputs": [{"name":"get_fee","args":{"service_code": code}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result

    # === YENİ: Doğrudan "hesap <id>" yazıldıysa → get_balance ===
    m = _ACC_STRICT.search(user_text)
    if m:
        acc = int(m.group(3))
        res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": acc})
        bal_out = _fmt_balance(res, acc)
        ui_component = bal_out.get("ui_component") if isinstance(bal_out, dict) else None
        text = (bal_out.get("text") if isinstance(bal_out, dict) else str(bal_out)) or ""
        out = {
            "YANIT": "" if ui_component else text,
            "toolOutputs": [{"name": "get_balance", "args": {"account_id": acc}, "result": res, "ok": res.get("ok", True)}],
        }
        if ui_component:
            out["ui_component"] = ui_component
        return out

    # (kur ve döviz)
    if any(w in low for w in _FX_WORDS):
        import re
        currency_match = re.search(r'\b(usd|dolar|euro|eur|gbp|sterlin|pound|jpy|yen|chf|frank|cny|yuan|ruble|rub|sar|riyal|aed|dirhem|cad|kanada)\b', low)
        res = call_mcp_tool(MCP_URL, "get_exchange_rates", {})
        requested_currency = currency_match.group(1) if currency_match else None
        fx_result = _fmt_fx(res, requested_currency)
        ui_component = fx_result.get("ui_component") if isinstance(fx_result, dict) else None
        result = {
            "YANIT": "" if ui_component else (fx_result.get("text") if isinstance(fx_result, dict) else str(fx_result)),
            "toolOutputs": [{"name":"get_exchange_rates","args":{}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result

    # Interest (faiz)
    if any(w in low for w in _INT_WORDS):
        res = call_mcp_tool(MCP_URL, "get_interest_rates", {})
        interest_result = _fmt_interest(res)
        ui_component = interest_result.get("ui_component") if isinstance(interest_result, dict) else None
        result = {
            "YANIT": "" if ui_component else (interest_result.get("text") if isinstance(interest_result, dict) else str(interest_result)),
            "toolOutputs": [{"name":"get_interest_rates","args":{}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result

    # Ücret kelimesi geçti ama kod belirtilmedi
    if any(w in low for w in _FEE_WORDS):
        return {"YANIT": "Hangi hizmetin ücreti? Örnek: EFT, FAST, HAVALE, KART_AIDATI, KREDI_TAHSIS"}

    # === YENİ: Basit ATM/Şube tetikleyici ===
    if any(k in low for k in ("atm", "şube", "sube", "branch")):
        import re
        city = district = None

        # "izmir atm" / "istanbul kadıköy atm"
        m = re.search(r'([a-zçğıöşü]+)(?:\s+([a-zçğıöşü]+))?\s+(atm|şube|sube)\b', low)
        if not m:
            # "atm izmir" / "şube ankara çankaya"
            m = re.search(r'(atm|şube|sube)\s+([a-zçğıöşü]+)(?:\s+([a-zçğıöşü]+))?', low)

        def _title(s): 
            return s.capitalize() if s else None

        if m:
            g = m.groups()
            if g[0] in ("atm","şube","sube"):
                city, district = _title(g[1]), _title(g[2] if len(g) > 2 else None)
            else:
                city, district = _title(g[0]), _title(g[1])

        if not city:
            return {"YANIT": "Lütfen şehir adıyla birlikte sorar mısınız? Örn: 'İzmir ATM' ya da 'Şube Ankara Çankaya'."}

        payload = {"city": city}
        if district:
            payload["district"] = district
        if "atm" in low:
            payload["type"] = "atm"

        res = call_mcp_tool(MCP_URL, "branch_atm_search", payload)
        atm_out = _fmt_atm_search(res)
        ui_component = atm_out.get("ui_component") if isinstance(atm_out, dict) else None
        text = (atm_out.get("text") if isinstance(atm_out, dict) else str(atm_out)) or ""
        ret = {
            "YANIT": "" if ui_component else text,
            "toolOutputs": [{"name":"branch_atm_search","args": payload, "result": res, "ok": res.get("ok", True)}],
        }
        if ui_component:
            ret["ui_component"] = ui_component
        return ret

    # Kart borcu / ekstre (müşteri kimliği fallback ile)
    import re as _re
    wants_card_debt = bool(_re.search(r"(kredi\s*kart[ıi]|kart).*(bor[cç]|borcu|borcum|ekstre|son\s*ödeme)", low))
    if wants_card_debt:
        cid = _cust_id(user_text) or _default_customer_id()
        if not cid:
            return {"YANIT": "Kart borcunuzu gösterebilmem için müşteri numaranızı yazın (örn: müşteri 24)."}
        res = call_mcp_tool(MCP_URL, "get_primary_card_summary", {"customer_id": int(cid)})
        summary_text = _fmt_card_summary(res) if 'error' not in res else "Kart bilgisi bulunamadı."
        return {
            "YANIT": summary_text,
            "toolOutputs": [{"name":"get_primary_card_summary","args":{"customer_id": int(cid)}, "result":res, "ok":res.get("ok", True)}]
        }

    # Kart bilgileri (card_id verildiyse)
    if any(w in low for w in _CARD_WORDS):
        import re
        card_match = re.search(r'\b(\d{1,3})\b', user_text)
        if not card_match:
            return {"YANIT": "Hangi kartın bilgilerini istiyorsunuz? Örnek: Kart 101 bilgilerini göster"}
        card_id = int(card_match.group(1))
        res = call_mcp_tool(MCP_URL, "get_card_info", {"card_id": card_id})
        card_result = _fmt_card_info(res)
        if isinstance(card_result, dict):
            ui_component = card_result.get("ui_component")
            text = card_result.get("text", "Kart bilgisi alınamadı.")
        else:
            ui_component, text = None, (str(card_result) if card_result else "Kart bilgisi alınamadı.")
        result = {
            "YANIT": "" if ui_component else text,
            "toolOutputs": [{"name":"get_card_info","args":{"card_id": card_id}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result

    # Hesap bakiyesi (genel tetikleyiciler)
    if USE_MCP and any(w in low for w in _BALANCE_WORDS):
        cid = _cust_id(user_text)
        if cid is not None:
            res = call_mcp_tool(MCP_URL, "get_accounts", {"customer_id": cid})
            balance_result = _fmt_balance(res)
            if isinstance(balance_result, dict):
                ui_component = balance_result.get("ui_component")
                text = balance_result.get("text") or "Bakiye bilgisi bulunamadı."
            else:
                ui_component, text = None, str(balance_result)
            result = {
                "YANIT": "" if ui_component else text,
                "toolOutputs": [{"name": "get_balance","args": {"customer_id": cid},"result": res,"ok": res.get("ok", True)}],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result

        acc = _acc_id(user_text)
        if acc is not None:
            res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": acc})
            balance_result = _fmt_balance(res, acc)
            if isinstance(balance_result, dict):
                ui_component = balance_result.get("ui_component")
                text = balance_result.get("text") or "Bakiye bilgisi bulunamadı."
            else:
                ui_component, text = None, str(balance_result)
            result = {
                "YANIT": "" if ui_component else text,
                "toolOutputs": [{"name": "get_balance","args": {"account_id": acc},"result": res,"ok": res.get("ok", True)}],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result
        def_cid = _default_customer_id()
    if def_cid is not None:
        res = call_mcp_tool(MCP_URL, "get_accounts", {"customer_id": def_cid})
        balance_result = _fmt_balance(res)
        if isinstance(balance_result, dict):
            ui_component = balance_result.get("ui_component")
            text = balance_result.get("text") or "Bakiye bilgisi bulunamadı."
        else:
            ui_component, text = None, str(balance_result)

        out = {
            "YANIT": "" if ui_component else text,
            "toolOutputs": [{
                "name": "get_balance",
                "args": {"customer_id": def_cid},
                "result": res,
                "ok": res.get("ok", True),
            }],
        }
        if ui_component:
            out["ui_component"] = ui_component
        return out

    # Fallback → LLM
    return _llm_flow(user_text)

if __name__ == "__main__":
    print("Minimal Agent — LLM tool-calling + MCP (Ctrl+C to exit)")
    try:
        while True:
            user_inp = input("> ")
            out = handle_message(user_inp)

            msg = out.get("YANIT") or ""
            if not msg:
                try:
                    outs = out.get("toolOutputs") or []
                    if outs:
                        name = outs[0].get("name")
                        res0 = outs[0].get("result")

                        if name in ("get_balance", "get_accounts", "AccountBalanceTool_get_balance"):
                            msg = (_fmt_balance(res0) or {}).get("text", "")
                        elif name == "get_exchange_rates":
                            msg = (_fmt_fx(res0) or {}).get("text", "")
                        elif name == "get_interest_rates":
                            msg = (_fmt_interest(res0) or {}).get("text", "")
                        elif name == "get_fee":
                            msg = (_fmt_fees(res0) or {}).get("text", "")
                        elif name == "list_fees":
                            msg = (_fmt_fees(res0) or {}).get("text", "")
                        elif name == "get_card_info":
                            card = _fmt_card_info(res0) or {}
                            msg = card.get("text", "")
                        elif name == "branch_atm_search":
                            msg = (_fmt_atm_search(res0) or {}).get("text", "")
                except Exception:
                    pass

            if not msg:
                msg = "(UI bileşeni üretildi; CLI için metin özeti yok.)"

            print("YANIT:", msg)
    except KeyboardInterrupt:
        pass
