# backend/agent/agent.py
# Minimal Agent — LLM tool-calling + MCP
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from integrations.fastmcp_client import call_mcp_tool
from llmadapter import LLMAdapter
from tools.schemas import get_tool_catalog

USE_MCP = 0
MCP_URL = "http://127.0.0.1:8081/sse"

_BALANCE_WORDS = ("bakiye", "balance", "ne kadar var", "kalan para", "hesabımda ne kadar", 
                  "bakiyem", "hesaplarım", "hesap", "hesabım", "hesaplarımda ne kadar")
_CARD_WORDS = ("kart", "kredi kartı", "kartım", "kart bilgisi", "kart detayı", 
               "limit", "borç", "son ödeme", "kesim", "kullanılabilir limit")
_FX_WORDS   = ("kur", "döviz", "doviz", "usd", "eur", "dolar", "euro", "sterlin", "rate")
_INT_WORDS  = ("faiz", "oran", "interest", "yatırım", "mevduat", "kredi faizi", "kredi")
_FEE_WORDS  = ("ücret", "ucret", "masraf", "komisyon", "aidat", "fee")
_ACC_STRICT = re.compile(r"\b(hesap|account)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_CUST_RE = re.compile(r"\b(müşteri|customer)\s*(no|id)?\s*(\d{1,10})\b", re.IGNORECASE)
_ACC_RE = re.compile(r"\b\d{1,10}\b")
_SRV_RE = re.compile(r"\b(eft|fast|havale|kart[_\s]?aidat[ıi]|kredi[_\s]?tahsis)\b", re.IGNORECASE)
_TRANSACTION_WORDS = (
    "işlem", "transaction", "hesap hareketi", "geçmiş",
    "past transactions", "transaction history",
    "son işlem", "son işlemler", "hesap hareketleri", "ekstre"
)


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
            "text": str(res["error"]),
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
    Fees response'unu hem text hem de UI component data olarak döndürür
    """
    d = res.get("data") if isinstance(res.get("data"), dict) else res
    if not isinstance(d, dict) or d.get("error"):
        return {
            "text": "Ücret bilgisi bulunamadı.",
            "ui_component": None
        }

    if "service_code" not in d:
        return {
            "text": "Ücret bilgisi bulunamadı.",
            "ui_component": None
        }

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
            "updated_at": d.get("updated_at")
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
    # 3) Tierli
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

    return {
        "text": text,
        "ui_component": ui_component
    }


def _fmt_card_info(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Card info response'unu hem text hem de UI component data olarak döndürür
    """
    if not isinstance(res, dict) or res.get("error"):
        return {
            "text": "Kart bilgisi bulunamadı.",
            "ui_component": None
        }
    
    # Bazı MCP cevapları {ok, data:{...}} şeklinde gelebilir → aç
    d = res.get("data") if isinstance(res, dict) and isinstance(res.get("data"), dict) else res

    # UI component oluştur
    ui_component = {
        "type": "card_info_card",
        "card_id": d.get("card_id"),
        "limit": d.get("limit"),
        "borc": d.get("borc"),
        "kesim_tarihi": d.get("kesim_tarihi"),
        "son_odeme_tarihi": d.get("son_odeme_tarihi")
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


def _fmt_cards_list(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Müşteriye ait kartların listesi response'unu hem text hem de UI component data olarak döndürür.
    """
    if not isinstance(res, dict) or res.get("error"):
        return {
            "text": res.get("error", "Kart bilgileri bulunamadı."),
            "ui_component": None
        }
    
    d = res["data"] if isinstance(res.get("data"), dict) else res
    
    ui_component = d.get("ui_component")
    cards = d.get("cards")

    if not cards:
        return {
            "text": "Bu müşteri için kart bulunamadı.",
            "ui_component": None
        }
    
    if len(cards) == 1:
        # Tek kart: list_customer_cards formatını get_card_info formatına çevir
        one = cards[0]
        converted_card = {
            "card_id": one.get("card_id"),
            "limit": one.get("credit_limit"),
            "borc": one.get("current_debt"),
            "kesim_tarihi": one.get("statement_day"),
            "son_odeme_tarihi": one.get("due_day")
        }
        return _fmt_card_info(converted_card) # Tek kart için mevcut formatlama fonksiyonunu kullan
    else:
        # Birden fazla kart: özet metin ve UI component oluştur
        preview_texts = []
        for c in cards[:3]: # İlk 3 kartı göster
            card_id = c.get("card_id", "N/A")
            available = c.get("credit_limit", 0) - c.get("current_debt", 0)
            preview_texts.append(f"Kart #{card_id} (Kullanılabilir: {available:,.2f} TRY)")
        
        more_text = f" (+{len(cards)-3} daha)" if len(cards) > 3 else ""
        text = f"{len(cards)} kart bulundu: {'; '.join(preview_texts)}{more_text}."

        if not ui_component:
            ui_component = {
                "type": "card_info_card",
                "card_type": "multiple_cards",
                "total_count": len(cards),
                "cards": [
                    {
                        "card_id": card["card_id"],
                        "limit": card["credit_limit"],
                        "borc": card["current_debt"],
                        "kesim_tarihi": card["statement_day"],
                        "son_odeme_tarihi": card["due_day"],
                    }
                    for card in cards
                ]
            }
        
        return {
            "text": text,
            "ui_component": ui_component
        }

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

# -------- transactions_list yardımcıları --------

def _parse_iso_or_none(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None

def _extract_txn_params(user_text: str) -> Dict[str, Any]:
    txt = user_text.lower()
    acc = None
    acc_span = None

    # account_id
    m = _ACC_STRICT.search(user_text)
    if m:
        acc = int(m.group(3))
        acc_span = m.span(3)
    else:
        m2 = _ACC_RE.search(user_text)
        if m2:
            acc = int(m2.group())
            acc_span = m2.span()

    now = datetime.utcnow()
    start = None
    end = None
    invalid_date=False

    # kısa yollar
    if "bugün" in txt or "bugun" in txt or "today" in txt:
        start = datetime(now.year, now.month, now.day)
        end = now
    elif "dün" in txt or "dun" in txt or "yesterday" in txt:
        d = datetime(now.year, now.month, now.day) - timedelta(days=1)
        start = d
        end = d + timedelta(hours=23, minutes=59, seconds=59)
    else:
        m7 = re.search(r"\bson\s+(\d{1,3})\s*gün\b", txt)
        if m7:
            days = int(m7.group(1))
            end = now
            start = now - timedelta(days=days)
        elif "bu ay" in txt:
            start = datetime(now.year, now.month, 1)
            end = now
        elif "geçen ay" in txt or "gecen ay" in txt:
            first_this = datetime(now.year, now.month, 1)
            last_month_end = first_this - timedelta(seconds=1)
            start = datetime(last_month_end.year, last_month_end.month, 1)
            end = datetime(last_month_end.year, last_month_end.month, last_month_end.day, 23, 59, 59)

    # açık tarih biçimleri
    date_tokens = re.findall(r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?", user_text)
    if date_tokens:
        parsed_any=False
        if len(date_tokens) >= 1:
            p=_parse_iso_or_none(date_tokens[0])
            if p is not None:
                start=p
                parsed_any=True
            else:
                invalid_date=True
        if len(date_tokens) >= 2:
            p=_parse_iso_or_none(date_tokens[1])
            if p is not None:
                end=p
                parsed_any=True
            else:
                invalid_date=True
            
        if not parsed_any:
            invalid_date=True
    
    else:
        # Desteklemediğimiz ama tarihe benzeyen biçimleri yakala
        # 1) İki haneli yıl: 25-07-15, 25/07/15, 25.07.15
        if re.search(r"\b\d{2}[-/.]\d{2}[-/.]\d{2}\b", user_text):
            invalid_date = True

        # 2) Gün-Ay-YYYY veya YYYY-Ay-Gün: 01/02/2025, 01.02.2025, 2025/02/01, 2025.02.01
        if re.search(r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b", user_text):
            invalid_date = True

        # 3) Türkçe ay isimli biçimler (yıl olsun olmasın): 7 temmuz 18 ağustos, 2 Ocak 2025
        month_names = r"(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)"
        if re.search(rf"\b\d{{1,2}}\s+{month_names}(?:\s+\d{{4}})?\b", user_text, re.I):
            invalid_date = True

        # 4) Saniyesiz ISO saat: 2025-08-28 12:00
        if re.search(r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\b", user_text):
            invalid_date = True

    if start and end and start > end:
        start, end = end, start

    def _fmt(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    # limit
    limit = None
    time_pat = re.compile(r"\b(?:son|geçen)?\s*(\d{1,3})\s*(?:gün|hafta|ay|day|week|month)\b", re.I)
    time_spans = [m.span(1) for m in time_pat.finditer(txt)]

    def spans_overlap(a, b):
        return not (a[1] <= b[0] or b[1] <= a[0])

    limit_pats = [
        re.compile(r"\blimit\s*(?:=|:)?\s*(\d{1,3})\b", re.I),
        re.compile(r"\b(?:son|ilk)\s*(\d{1,3})\s*(?:işlem|islem|kayıt|kayit|adet)\b", re.I),
        re.compile(r"\b(\d{1,3})\s*(?:işlem|islem|kayıt|kayit|adet)\b", re.I),
    ]

    for pat in limit_pats:
        for lm in pat.finditer(txt):
            s = lm.span(1)
            if acc_span and spans_overlap(s, acc_span):
                continue
            if any(spans_overlap(s, t) for t in time_spans):
                continue
            v = int(lm.group(1))
            if 1 <= v <= 500:
                limit = v
                break
        if limit is not None:
            break

    ALL_WORDS = ("tüm", "tum", "bütün", "hepsi", "hepsini", "tamamı", "tamamını")
    if limit is None and any(w in txt for w in ALL_WORDS):
        limit = 500

    return {
        "account_id": acc,
        "from_date": _fmt(start) if start else None,
        "to_date": _fmt(end) if end else None,
        "limit": limit,   # burada None kalabilir
        "invalid_date": invalid_date,
    }

def _fmt_transactions(res: Dict[str, Any], fallback_acc_id: Optional[int] = None) -> Dict[str, Any]:
    """
    transactions_list çıktısını kullanıcıya uygun metin ve (varsa) UI bileşenine çevirir.
    Tarih aralığı verilmezse “tüm zamanlar” yazar. Metin her zaman dolu döner.
    """
    if not isinstance(res, dict):
        return {"text": "İşlemler alınamadı.", "ui_component": None}

    d = res.get("data") if isinstance(res.get("data"), dict) else res
    if d.get("error"):
        return {"text": str(d.get("error")), "ui_component": None}

    acc_id = d.get("account_id", fallback_acc_id)
    rng = d.get("range") or {}
    fr = rng.get("from") or d.get("from_date")
    to = rng.get("to") or d.get("to_date")
    rows = d.get("transactions") or []

    def _parse_iso_or_none_local(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        s = str(s).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def _fmt_amt(x: Any) -> str:
        try:
            return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return str(x)

    # metin başlığı
    if fr and to:
        head = f"Hesap {acc_id} için {fr} - {to} aralığında {len(rows)} işlem bulundu."
    else:
        head = f"Hesap {acc_id} için tüm zamanlarda {len(rows)} işlem bulundu."

    if len(rows) == 0:
        return {"text": head, "ui_component": None}
    
    # Eğer tüm işlemler metinde de listelensin isteniyorsa:
    details = []
    for r in rows:
        dt = r.get("txn_date") or r.get("date") or r.get("created_at")
        amt = _fmt_amt(r.get("amount"))
        desc = r.get("description") or ""
        ttype = r.get("txn_type") or ""
        details.append(f"{dt} | {ttype} {amt} | {desc}")

    details_text = "\n".join(details)

    # satırların özetini oluştur (ilk 5)
    lines = []
    for r in rows[:5]:
        dt = r.get("txn_date") or r.get("created_at") or r.get("date")
        dt_s = (_parse_iso_or_none_local(dt).strftime("%Y-%m-%d %H:%M:%S") if _parse_iso_or_none_local(dt) else str(dt))
        typ = r.get("txn_type") or ""
        desc = r.get("description") or ""
        amt = _fmt_amt(r.get("amount"))
        lines.append(f"{dt_s} {typ} {amt} — {desc}".replace("—", " - "))

    text = head + "\n- " + "\n- ".join(lines)

    # opsiyonel UI
    ui_items = []
    for r in rows:
        dt = r.get("txn_date") or r.get("created_at") or r.get("date")
        dt_iso = _parse_iso_or_none_local(dt)
        ui_items.append({
            "id": r.get("txn_id") or r.get("id"),
            "date": dt_iso.strftime("%Y-%m-%dT%H:%M:%SZ") if dt_iso else None,
            "datetime": dt_iso.strftime("%Y-%m-%dT%H:%M:%SZ") if dt_iso else None,
            "amount": r.get("amount"),
            "amount_formatted": _fmt_amt(r.get("amount")),
            "currency": r.get("currency") or "TRY",
            "type": r.get("txn_type"),
            "description": r.get("description"),
            "account_id": r.get("account_id", acc_id),
        })

    ui_component = {
        "type": "transactions_list",
        "account_id": acc_id,
        "count": len(rows),
        "items": ui_items
    }
    if fr or to:
        # UI’a ISO range ver
        fr_dt = _parse_iso_or_none_local(fr)
        to_dt = _parse_iso_or_none_local(to)
        ui_component["range"] = {
            "from": fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if fr_dt else None,
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if to_dt else None,
        }

    return {"text": head + "\n" + details_text, "ui_component": ui_component}

def _llm_flow(user_text: str, customer_id: int) -> Dict[str, Any]: # customer_id eklendi
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
                payload = {"account_id": int(args["account_id"]), "customer_id": customer_id} # customer_id eklendi
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
        elif name == "get_accounts": # customer_id in args kontrolü kaldırıldı
            try:
                # LLM'den gelen customer_id'yi tamamen yoksay ve doğru customer_id'yi kullan
                payload = {"customer_id": customer_id}
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
        elif name == "get_card_info" and "card_id" in args:
            try:
                payload = {"card_id": int(args["card_id"]), "customer_id": customer_id} # customer_id eklendi
                res = call_mcp_tool(MCP_URL, "get_card_info", payload)
                out = {
                    "name": "get_card_info",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "get_card_info",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }
        elif name == "list_customer_cards":
            try:
                payload = {"customer_id": customer_id}
                res = call_mcp_tool(MCP_URL, "list_customer_cards", payload)
                out = {
                    "name": "list_customer_cards",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "list_customer_cards",
                    "args": args,
                    "result": {"ok": False, "error": str(e)},
                    "ok": False,
                }

        elif name == "transactions_list":
            try:
                lim = args.get("limit")
                fd=args.get("from_date")
                td=args.get("to_date")
                has_range = bool(fd or td)

                payload = {
                    "account_id": int(args["account_id"]),
                    "from_date": fd,
                    "to_date": td,
                }
                if isinstance(lim, int):
                    payload["limit"]=lim
                elif not has_range:
                    payload["limit"]=1_000_000
                    
                res = call_mcp_tool(MCP_URL, "transactions_list", payload)
                out = {
                    "name": "transactions_list",
                    "args": payload,
                    "result": res,
                    "ok": res.get("ok", True),
                }
            except Exception as e:
                out = {
                    "name": "transactions_list",
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
    elif outs and outs[0].get("name") == "list_customer_cards": # Yeni eklenen kısım
        cards_list_result = _fmt_cards_list(outs[0]["result"])
        ui_component = cards_list_result.get("ui_component")

        if ui_component:
            final_text = ""
        else:
            final_text = cards_list_result["text"]
    elif outs and outs[0].get("name") == "branch_atm_search":
        atm_result = _fmt_atm_search(outs[0]["result"])
        ui_component = atm_result.get("ui_component")
        
        # UI component varsa text boş, yoksa atm text'ini kullan
        if ui_component:
            final_text = ""
        else:
            final_text = atm_result["text"]

    elif outs and outs[0].get("name") == "transactions_list":
        tx_result = _fmt_transactions(outs[0]["result"])
        ui_component = tx_result.get("ui_component")
        final_text = tx_result["text"]  # UI olsa bile metni göster

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


def handle_message(user_text: str, customer_id: int) -> Dict[str, Any]: # customer_id: int olarak güncellendi
    low = user_text.lower()

    if any(w in low for w in _TRANSACTION_WORDS):
        params = _extract_txn_params(user_text)
        if params.get("invalid_date"):
            return {"YANIT": "Geçerli bir tarih formatı girin. Desteklenen biçimler: YYYY-MM-DD"}
        acc = params.get("account_id")
        if acc is None:
            return {"YANIT": "Hangi hesap için işlem listeleyelim? Lütfen account_id belirtin. Örnek: hesap 12 son 30 gün işlemleri"}

        # Güvenlik - hesap gerçekten bu müşteriye mi ait kontrolü
        try:
            accs_res = call_mcp_tool(MCP_URL, "get_accounts", {"customer_id": customer_id})
            data = accs_res.get("data") or accs_res or {}
            allowed_ids = set()

            if isinstance(data, dict):
                # çoklu hesap
                if isinstance(data.get("accounts"), list):
                    for a in data["accounts"]:
                        if isinstance(a, dict) and "account_id" in a:
                            allowed_ids.add(a["account_id"])
                # tek hesap
                if "account_id" in data and isinstance(data.get("account_id"), int):
                    allowed_ids.add(data["account_id"])

            # allowed_ids boşsa (biçim tanınmadıysa) engelleme yapma
            if allowed_ids and acc not in allowed_ids:
                return {"YANIT": f"Hesap bulunamadı. Lütfen geçerli bir hesap numarası girin.", "status_code": 403}
            
        except Exception:
            # general_tools.list_transactions içinde de müşteri doğrulaması var
            pass

        # payload'ı sadece dolu alanlarla kur
        payload: Dict[str, Any] = {"account_id": acc}

        fd = params.get("from_date")
        td = params.get("to_date")
        if fd is not None:
            payload["from_date"] = fd
        if td is not None:
            payload["to_date"] = td

        raw_limit = params.get("limit") 
        has_range = bool(fd or td)

        if isinstance(raw_limit, int):
            payload["limit"]=raw_limit
        elif not has_range:
            payload["limit"] = 1_000_000
        #payload["limit"] = raw_limit if isinstance(raw_limit, int) else 1_000_000
        res = call_mcp_tool(MCP_URL, "transactions_list", payload)
        tx_result = _fmt_transactions(res, fallback_acc_id=acc)
        ui_component = tx_result.get("ui_component")

        out_item = {"name": "transactions_list", "args": payload, "result": res, "ok": res.get("ok", True)}
        result = {
            "YANIT": tx_result["text"],  # UI yoksa metni göster
            "toolOutputs": [out_item],
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result

    code = _service_code(user_text)
    if code:
        res = call_mcp_tool(MCP_URL, "get_fee", {"service_code": code})
        if res.get("error") and res.get("available_codes"):
            opts = ", ".join(res["available_codes"])
            return {"YANIT": f"'{code}' bulunamadı. Desteklenenler: {opts}. Hangisini istersiniz?"}
        
        fees_result = _fmt_fees(res)
        ui_component = fees_result.get("ui_component")
        
        result = {
            "YANIT": "" if ui_component else fees_result["text"],
            "toolOutputs": [{"name":"get_fee","args":{"service_code": code}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result
    
    # (kur ve döviz için)
    if any(w in low for w in _FX_WORDS):
        # Belirli bir kur sorulup sorulmadığını kontrol et
        import re
        currency_match = re.search(r'\b(usd|dolar|euro|eur|gbp|sterlin|pound|jpy|yen|chf|frank|cny|yuan|ruble|rub|sar|riyal|aed|dirhem|cad|kanada)\b', low)
        
        res = call_mcp_tool(MCP_URL, "get_exchange_rates", {})
        
        # Eğer belirli bir kur istendiyse sadece onu filtrele
        requested_currency = currency_match.group(1) if currency_match else None
        fx_result = _fmt_fx(res, requested_currency)
        ui_component = fx_result.get("ui_component")
        
        result = {
            "YANIT": "" if ui_component else fx_result["text"],
            "toolOutputs": [{"name":"get_exchange_rates","args":{}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result
    
   
     # Interest (faiz)
    if any(w in low for w in _INT_WORDS):
        res = call_mcp_tool(MCP_URL, "get_interest_rates", {})
        interest_result = _fmt_interest(res)
        ui_component = interest_result.get("ui_component")
        
        result = {
            "YANIT": "" if ui_component else interest_result["text"],
            "toolOutputs": [{"name":"get_interest_rates","args":{}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result
    
    # Ücretler
    if any(w in low for w in _FEE_WORDS):
        code = _service_code(user_text)
        if not code:
            return {"YANIT": "Hangi hizmetin ücreti? Örnek: EFT, FAST, HAVALE, KART_AIDATI, KREDI_TAHSIS"}
        res = call_mcp_tool(MCP_URL, "get_fee", {"service_code": code})
        # bilinmiyorsa desteklenenleri listele ve tekrar sor
        if res.get("error") and res.get("supported"):
            opts = ", ".join(res["supported"])
            return {"YANIT": f"'{code}' tanınmadı. Desteklenenler: {opts}. Hangisini istersiniz?"}
        
        fees_result = _fmt_fees(res)
        ui_component = fees_result.get("ui_component")
        
        result = {
            "YANIT": "" if ui_component else fees_result["text"],
            "toolOutputs": [{"name":"get_fee","args":{"service_code": code}, "result":res, "ok":res.get("ok", True)}]
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result
    
    # Kart bilgileri
    if any(w in low for w in _CARD_WORDS):
        # Kart ID'sini çıkar
        import re
        card_match = re.search(r'\b(\d{1,3})\b', user_text)
        if not card_match:
            # Kart ID'si belirtilmediğinde tüm kartları listele
            res = call_mcp_tool(MCP_URL, "list_customer_cards", {"customer_id": customer_id})
            cards_list_result = _fmt_cards_list(res)
            ui_component = cards_list_result.get("ui_component")

            result = {
                "YANIT": "" if ui_component else cards_list_result["text"],
                "toolOutputs": [
                    {
                        "name": "list_customer_cards",
                        "args": {"customer_id": customer_id},
                        "result": res,
                        "ok": res.get("ok", True),
                    }
                ],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result
        
        card_id = int(card_match.group(1))
        
        res = call_mcp_tool(MCP_URL, "get_card_info", {
            "card_id": card_id,
            "customer_id": customer_id # customer_id eklendi
        })
        
        card_result = _fmt_card_info(res)
        ui_component = card_result.get("ui_component")
        
        result = {
            "YANIT": "" if ui_component else card_result["text"],
            "toolOutputs": [{"name":"get_card_info","args":{"card_id": card_id, "customer_id": customer_id}, "result":res, "ok":res.get("ok", True)}],
        }
        if ui_component:
            result["ui_component"] = ui_component
        return result
    
    # Hesap bakiyesi
    if USE_MCP and any(w in low for w in _BALANCE_WORDS):
        cid_from_text = _cust_id(user_text)
        if cid_from_text is not None:
            # LLM'in yanlış bir müşteri ID'si döndürmesini engelle
            if cid_from_text != customer_id:
                return {"YANIT": f"Bu müşteri numarasına ({cid_from_text}) erişim izniniz yok.", "status_code": 403}

            res = call_mcp_tool(MCP_URL, "get_accounts", {"customer_id": cid_from_text})
            balance_result = _fmt_balance(res)
            ui_component = balance_result.get("ui_component")
            
            result = {
                "YANIT": "" if ui_component else balance_result["text"],
                "toolOutputs": [
                    {
                        "name": "get_balance",
                        "args": {"customer_id": cid_from_text},
                        "result": res,
                        "ok": res.get("ok", True),
                    }
                ],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result
            
        acc = _acc_id(user_text)
        if acc is not None:
            res = call_mcp_tool(MCP_URL, "get_balance", {"account_id": acc, "customer_id": customer_id}) # customer_id doğrudan iletildi
            balance_result = _fmt_balance(res, acc)
            ui_component = balance_result.get("ui_component")
            
            result = {
                "YANIT": "" if ui_component else balance_result["text"],
                "toolOutputs": [
                    {
                        "name": "get_balance",
                        "args": {"account_id": acc, "customer_id": customer_id},
                        "result": res,
                        "ok": res.get("ok", True),
                    }
                ],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result
        else: # Hesap ID'si belirtilmediğinde tüm hesapları listele
            res = call_mcp_tool(MCP_URL, "get_accounts", {"customer_id": customer_id})
            balance_result = _fmt_balance(res)
            ui_component = balance_result.get("ui_component")

            result = {
                "YANIT": "" if ui_component else balance_result["text"],
                "toolOutputs": [
                    {
                        "name": "get_accounts",
                        "args": {"customer_id": customer_id},
                        "result": res,
                        "ok": res.get("ok", True),
                    }
                ],
            }
            if ui_component:
                result["ui_component"] = ui_component
            return result
    return _llm_flow(user_text, customer_id)


if __name__ == "__main__":
    print("Minimal Agent — LLM tool-calling + MCP (Ctrl+C to exit)")
    try:
        while True:
            print("YANIT:", handle_message(input("> "), 1)["YANIT"])
    except KeyboardInterrupt:
        pass
