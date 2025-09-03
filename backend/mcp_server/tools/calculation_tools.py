# backend/app/tools/calculation_tools.py
from __future__ import annotations
import base64
import csv
import io
import math
import sqlite3

from typing import Dict, Any, List, Optional, Tuple, Literal

# ---- interest helpers (module-level) ----
Compounding = Literal["annual","semiannual","quarterly","monthly","weekly","daily","continuous"]

def _normalize_compounding(value: str) -> Compounding:
    v = (value or "").strip().lower()
    aliases = {
        "annual":"annual","a":"annual","annually":"annual",
        "semiannual":"semiannual","semi-annual":"semiannual","sa":"semiannual",
        "quarterly":"quarterly","quarter":"quarterly","q":"quarterly",
        "monthly":"monthly","month":"monthly","m":"monthly","mo":"monthly",
        "weekly":"weekly","week":"weekly","w":"weekly",
        "daily":"daily","day":"daily","d":"daily",
        "continuous":"continuous","cont":"continuous","c":"continuous",
    }
    if v not in aliases:
        raise ValueError("Unsupported compounding. Use: annual|semiannual|quarterly|monthly|weekly|daily|continuous")
    return aliases[v]  # type: ignore[return-value]

def _periods_per_year(c: Compounding) -> Optional[int]:
    return {
        "annual":1, "semiannual":2, "quarterly":4,
        "monthly":12, "weekly":52, "daily":365,
        "continuous":None,
    }[c]




class CalculationTools:
    """
    S4–S6: Hesaplama araçları (DB erişimi yok; saf hesap).
    Dönüş şekli general_tools.py ile uyumludur:
      - Başarı: normalize edilmiş sözlük (ör. {"summary": {...}, "schedule": [...]})
      - Hata:   {"error": "mesaj"}
    """
    def __init__(self, repo):
        self.repo = repo

    # ------------- helpers -------------
    @staticmethod
    def _err(msg: str) -> Dict[str, Any]:
        return {"error": msg}
    @staticmethod
    def _round2(x: float) -> float:
        if x is None or isinstance(x, bool):
            return 0.0
        xf = float(x)
        if math.isnan(xf) or math.isinf(xf):
            return 0.0
        return round(xf, 2)


    # ------------- S5: LoanAmortizationTool -------------
    def loan_amortization_schedule(
        self,
        principal: float,
        rate: Optional[float],
        term: int,
        method: str = "annuity",
        currency: Optional[str] = None,
        export: str = "none",  # "csv" | "none"
    ) -> Dict[str, Any]:
        """
        installment = P * [ i(1+i)^n / ((1+i)^n - 1) ], i = r/12
        her ay: interest = remaining * i; principal_part = installment - interest
        """
        try:
            if principal is None or principal <= 0:
                return self._err("principal must be > 0")
            # Faiz oranı verilmemişse repo/DB'den 'ihtiyaç kredisi' ürünü ile çöz
            resolved_rate = None
            if rate is None:
                try:
                    # InterestCalculatorTool'daki mantıkla eş: loan için 'ihtiyaç kredisi'
                    product_mapping = {
                        "savings": "mevduat",
                        "loan": "ihtiyaç kredisi",
                        "credit_card": "kredi kartı",
                    }
                    mapped_product = product_mapping.get("loan", "loan")
                    resolved_rate, _meta = self.repo._resolve_rate_via_repo_or_db(
                        provided_rate=None,
                        product=mapped_product,
                        product_fallback=mapped_product,
                        currency=currency or "TRY",
                        as_of=None,
                    )
                except Exception as e:
                    return self._err(f"rate resolution failed: {e}")
            else:
                resolved_rate = float(rate)

            if resolved_rate is None or resolved_rate < 0:
                return self._err("annual rate must be >= 0")
            if term is None or int(term) < 1:
                return self._err("term (months) must be >= 1")
            term = int(term)

            m = (method or "annuity").lower()
            if m != "annuity":
                return self._err("only 'annuity' method is supported")

            i = resolved_rate / 12.0
            n = term
            if i == 0:
                installment = principal / n
            else:
                factor = (1.0 + i) ** n
                installment = principal * (i * factor) / (factor - 1.0)

            remaining = float(principal)
            rows: List[Dict[str, Any]] = []
            total_interest = 0.0

            for month in range(1, n + 1):
                interest = remaining * i
                principal_part = installment - interest
                if month == n:
                    principal_part = remaining  # yuvarlama farkını son ayda kapat
                    installment_eff = principal_part + interest
                else:
                    installment_eff = installment

                remaining = max(0.0, remaining - principal_part)
                total_interest += interest

                rows.append({
                    "month": month,
                    "installment": self._round2(installment_eff),
                    "interest": self._round2(interest),
                    "principal": self._round2(principal_part),
                    "remaining": self._round2(remaining),
                })

            total_payment = sum(r["installment"] for r in rows)

            data: Dict[str, Any] = {
                "summary": {
                    "principal": self._round2(principal),
                    "annual_rate": resolved_rate,
                    "monthly_rate": round(resolved_rate / 12.0, 10),
                    "term_months": n,
                    "installment": self._round2(installment),
                    "total_interest": self._round2(total_interest),
                    "total_payment": self._round2(total_payment),
                    "currency": currency or "",
                    "method": "annuity_monthly",
                },
                "schedule": rows,
                "ui_component": {
                    "type": "amortization_table_card",
                    "summary": {
                        "installment": self._round2(installment),
                        "total_interest": self._round2(total_interest),
                        "total_payment": self._round2(total_payment),
                        "principal": self._round2(principal),
                        "annual_rate": resolved_rate,
                        "monthly_rate": round(resolved_rate / 12.0, 10),
                        "term_months": n,
                        "currency": currency or "",
                    },
                },
            }

            if (export or "none").lower() == "csv":
                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow(["month", "installment", "interest", "principal", "remaining"])
                for r in rows:
                    writer.writerow([r["month"], r["installment"], r["interest"], r["principal"], r["remaining"]])
                csv_bytes = buf.getvalue().encode("utf-8")
                data["csv_base64"] = base64.b64encode(csv_bytes).decode("ascii")

            return data

        except Exception as e:
            return self._err(f"loan_amortization_schedule_error: {str(e)}")
        
    # ------------- S6: InterestCalculatorTool (deposit|loan) -------------
    def interest_compute(
        self,
        type: Literal["deposit","loan"],
        principal: float,
        term: float,
        compounding: str,
        # Oran çözümleme
        rate: Optional[float] = None,       # Manuel oran (0.30 = %30)
        product: Optional[str] = None,      # Repo/DB ürün anahtarı (ör: "savings", "loan")
        currency: str = "TRY",
        term_unit: Literal["years","months"] = "years",
        as_of: Optional[str] = None,        # "YYYY-MM-DD"
        # UI/çıktı
        schedule: bool = False,             # (ileride detay tablo istersen açarız)
        schedule_limit: int = 24,
        rounding: Optional[int] = None,
    ) -> Dict[str, Any]:
        
        """
        InterestCalculatorTool (mevduat / kredi)

        type='deposit'  → Bileşik mevduat getirisi hesaplar:
            FV = P * (1 + r/m)^(m*t),  i = r/m, n = m*t
            Sürekli bileşik için: FV = P * e^(r*t)
            Getiri = FV - P

        type='loan'     → Eşit taksitli (annuity) kredi ödemesi hesaplar:
            installment = P * [ i(1+i)^n / ((1+i)^n - 1) ],  i = r/m, n = m*t
            Her dönem: interest = remaining * i
                        principal_part = installment - interest
            Toplam ödeme = installment * n
            Toplam faiz  = toplam ödeme - P

        Parametreler:
            principal   : Anapara (>0)
            rate        : Yıllık nominal faiz oranı (0.30 = %30). 
                          Eğer None ise repo/DB’den otomatik bulunur.
            term        : Vade (yıl ya da ay cinsinden, term_unit ile belirlenir)
            compounding : annual|semiannual|quarterly|monthly|weekly|daily|continuous
            product     : Repo/DB için ürün anahtarı (örn: "savings" veya "loan")
            repo/db_path: Faiz oranını DB’den almak için kaynak
            schedule    : loan için amortizasyon tablosu (önizleme) oluşturulsun mu
            schedule_limit: tablodaki max satır sayısı

        Dönüş:
            Başarı: {"summary": {...}, "ui_component": {...}, "rate_meta": {...}, ["schedule": [...]]}
            Hata  : {"error": "..."}
        """
        
        try:
            mode = (type or "").strip().lower()
            if mode not in {"deposit","loan"}:
                return self._err("type must be 'deposit' or 'loan'")
            if principal is None or principal <= 0:
                return self._err("principal must be > 0")
            if term is None or term <= 0:
                return self._err("term must be > 0")

            comp = _normalize_compounding(compounding)
            m = _periods_per_year(comp)
            years = term / 12.0 if term_unit == "months" else float(term)

            # Oran çözümleme (repo→db→manuel sırası yukarıdaki helper’da)
            product_fallback = "savings" if mode == "deposit" else "loan"
            # Türkçe product isimlerini İngilizce karşılıklarına çevir
            product_mapping = {
                "savings": "mevduat",
                "loan": "ihtiyaç kredisi",
                "credit_card": "kredi kartı"
            }
            
            # Product mapping uygula
            mapped_product = product_mapping.get(product or product_fallback, product or product_fallback)
            
            try:
                resolved_rate, rate_meta = self.repo._resolve_rate_via_repo_or_db(
                    provided_rate=rate,
                    product=mapped_product, product_fallback=mapped_product,
                    currency=currency, as_of=as_of,
                )
            except Exception as e:
                # Hata detayını görmek için
                error_msg = f"Rate resolution failed for product={mapped_product}, mode={mode}, error={str(e)}"
                return self._err(error_msg)
            
            if resolved_rate < 0:
                return self._err("rate cannot be negative")

            r = self._round2 if rounding in (None, 2) else (lambda x: round(float(x), int(rounding)))

            if mode == "deposit":
                if comp == "continuous":
                    FV = principal * math.e ** (resolved_rate * years)
                else:
                    assert m is not None
                    FV = principal * (1 + resolved_rate / m) ** (m * years)
                total_interest = FV - principal
                return {
                    "summary": {
                        "mode": "deposit",
                        "principal": r(principal),
                        "annual_rate": resolved_rate,
                        "term_years": years,
                        "compounding": comp,
                        "future_value": r(FV),
                        "total_interest": r(total_interest),
                        "currency": currency or "",
                    },
                    "ui_component": {
                        "type": "interest_quote_card",
                        "quote_type": "deposit",
                        "principal": r(principal),
                        "annual_rate": resolved_rate,
                        "term_years": years,
                        "compounding": comp,
                        "future_value": r(FV),
                        "total_interest": r(total_interest),
                        "currency": currency or "",
                    },
                    "rate_meta": rate_meta,
                }

            # loan
            if comp == "continuous":
                comp, m = "monthly", 12
            assert m is not None
            n = int(round(m * years))
            if n <= 0:
                return self._err("loan term results in zero periods; increase term")
            i = resolved_rate / m
            installment = principal / n if resolved_rate == 0 else principal * i / (1 - (1 + i) ** (-n))
            total_payment = installment * n if resolved_rate != 0 else principal
            total_interest = total_payment - principal

            payload = {
                "summary": {
                    "mode": "loan",
                    "principal": r(principal),
                    "annual_rate": resolved_rate,
                    "periodic_rate": round(i, 10),
                    "periods": n,
                    "term_years": years,
                    "compounding": comp,
                    "installment": r(installment),
                    "total_payment": r(total_payment),
                    "total_interest": r(total_interest),
                    "currency": currency or "",
                },
                "ui_component": {
                    "type": "interest_quote_card",
                    "quote_type": "loan",
                    "principal": r(principal),
                    "annual_rate": resolved_rate,
                    "periodic_rate": round(i, 10),
                    "periods": n,
                    "installment": r(installment),
                    "total_payment": r(total_payment),
                    "total_interest": r(total_interest),
                    "currency": currency or "",
                },
                "rate_meta": rate_meta,
            }

            if schedule:
                rows = []
                remaining = float(principal)
                for k in range(1, n + 1):
                    interest = remaining * i
                    principal_part = installment - interest if resolved_rate != 0 else installment
                    if k == n:
                        principal_part = remaining
                        pay_k = principal_part + interest
                    else:
                        pay_k = installment
                    remaining = max(0.0, remaining - principal_part)
                    if len(rows) < int(schedule_limit):
                        rows.append({
                            "period": k,
                            "payment": r(pay_k),
                            "interest": r(interest),
                            "principal": r(principal_part),
                            "remaining": r(remaining),
                        })
                payload["schedule"] = rows

            return payload

        except Exception as e:
            return self._err(f"interest_compute_error: {e}")


  