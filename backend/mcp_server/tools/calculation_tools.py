# backend/app/tools/calculation_tools.py
from __future__ import annotations
import base64
import csv
import io
import math
from typing import Dict, Any, List, Optional


class CalculationTools:
    """
    S4–S6: Hesaplama araçları (DB erişimi yok; saf hesap).
    Dönüş şekli general_tools.py ile uyumludur:
      - Başarı: normalize edilmiş sözlük (ör. {"summary": {...}, "schedule": [...]})
      - Hata:   {"error": "mesaj"}
    """

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
        rate: float,
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
            if rate is None or rate < 0:
                return self._err("annual rate must be >= 0")
            if term is None or int(term) < 1:
                return self._err("term (months) must be >= 1")
            term = int(term)

            m = (method or "annuity").lower()
            if m != "annuity":
                return self._err("only 'annuity' method is supported")

            i = rate / 12.0
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
                    "annual_rate": rate,
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
                        "annual_rate": rate,
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

  