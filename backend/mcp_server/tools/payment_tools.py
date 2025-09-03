# tools/payment_service.py
from __future__ import annotations
import os, math, datetime
from typing import Dict, Any


DAILY_LIMIT = float(os.getenv("PAYMENT_DAILY_LIMIT", "50000"))
PER_TXN_LIMIT = float(os.getenv("PAYMENT_PER_TXN_LIMIT", "20000"))
DEFAULT_CCY = os.getenv("DEFAULT_CURRENCY", "TRY")

def today_str() -> str:
    return datetime.date.today().isoformat()

def _is_active(v): return str(v).strip().lower() in ("active","aktif")
def _is_external(v): return str(v).strip().lower() in ("external","harici")

class PaymentService:
    def __init__(self, repo):
      self.repo = repo


    def _ensure(self):
        # payments tablosu var mı kontrol
        with self.repo._conn() if hasattr(self.repo, "_conn") else None:
            pass  # repo _conn yoksa da sorun değil; _ensure_schema operatif olarak insert aşamasında çağrılır

    # def precheck(self, from_account: int, to_account: int, amount: float,
    #              currency: str | None, note: str | None) -> Dict[str, Any]:
    #     if amount is None or amount <= 0:
    #         return {"ok": False, "error": "invalid_amount"}
    #     if amount > PER_TXN_LIMIT:
    #         return {"ok": False, "error": "per_txn_limit_exceeded", "limit": PER_TXN_LIMIT, "attempt": amount}

    #     acc_from = self.repo.get_account(from_account)
    #     acc_to = self.repo.get_account(to_account)
    #     if not acc_from:
    #         return {"ok": False, "error": "from_account_not_found"}
    #     if not acc_to:
    #         return {"ok": False, "error": "to_account_not_found"}

    #     if acc_from["status"] != "Aktif":
    #         return {"ok": False, "error": "from_account_inactive"}
    #     if acc_to["status"] not in ("Aktif", "external"):
    #         return {"ok": False, "error": "to_account_inactive"}

    #     ccy_from = acc_from["currency"]
    #     ccy_to = acc_to["currency"]
    #     ccy = currency or ccy_from
    #     if ccy != ccy_from or ccy_from != ccy_to:
    #         # PoC: cross-currency kapalı
    #         return {"ok": False, "error": "currency_mismatch", "from": ccy_from, "to": ccy_to}

    #     fee = 0.0  # PoC'ta ücret yok
    #     if float(acc_from["balance"]) < amount + fee:
    #         return {"ok": False, "error": "insufficient_funds", "required": round(amount + fee, 2), "available": float(acc_from["balance"])}

    #     # günlük limit kontrol
    #     used_today = self.repo.get_daily_out_total(acc_from["customer_id"], today_str())
    #     if used_today + amount > DAILY_LIMIT:
    #         return {"ok": False, "error": "daily_limit_exceeded", "limit": DAILY_LIMIT, "used": used_today, "attempt": amount}

    #     return {
    #         "ok": True,
    #         "from_account": from_account,
    #         "to_account": to_account,
    #         "amount": round(amount, 2),
    #         "currency": ccy,
    #         "fee": fee,
    #         "note": note or "",
    #         "limits": {"per_txn": PER_TXN_LIMIT, "daily": DAILY_LIMIT, "used_today": used_today}
    #     }
    def precheck(self, from_account: int, to_account: int, amount: float,
                  currency: str | None, note: str | None) -> Dict[str, Any]:
        if amount is None or amount <= 0:
            return {"ok": False, "error": "invalid_amount", "message": "Tutar geçersiz."}
        if amount > PER_TXN_LIMIT:
            return {"ok": False, "error": "per_txn_limit_exceeded",
                    "limit": PER_TXN_LIMIT, "attempt": amount,
                    "message": "Tek işlem limiti aşıldı."}

        acc_from = self.repo.get_account(from_account)
        acc_to = self.repo.get_account(to_account)
        if not acc_from:
            return {"ok": False, "error": "from_account_not_found", "message": "Kaynak hesap bulunamadı."}
        if not acc_to:
            return {"ok": False, "error": "to_account_not_found", "message": "Hedef hesap bulunamadı."}

        if not _is_active(acc_from["status"]):
            return {"ok": False, "error": "from_account_inactive", "message": "Kaynak hesap aktif değil."}
        if not (_is_active(acc_to["status"]) or _is_external(acc_to["status"])):
            return {"ok": False, "error": "to_account_inactive", "message": "Hedef hesap aktif değil."}

        ccy_from, ccy_to = acc_from["currency"], acc_to["currency"]
        ccy = currency or ccy_from
        if ccy != ccy_from or ccy_from != ccy_to:
            return {"ok": False, "error": "currency_mismatch",
                    "from": ccy_from, "to": ccy_to,
                    "message": "Hesap para birimleri uyumsuz."}

        fee = 0.0
        if float(acc_from["balance"]) < amount + fee:
            return {"ok": False, "error": "insufficient_funds",
                    "required": round(amount + fee, 2),
                    "available": float(acc_from["balance"]),
                    "message": "Bakiye yetersiz."}

        used_today = self.repo.get_daily_out_total(acc_from["customer_id"], today_str())
        if used_today + amount > DAILY_LIMIT:
            return {"ok": False, "error": "daily_limit_exceeded",
                    "limit": DAILY_LIMIT, "used": used_today, "attempt": amount,
                    "message": "Günlük transfer limiti aşıldı."}

        return {"ok": True, "from_account": from_account, "to_account": to_account,
                "amount": round(amount,2), "currency": ccy, "fee": fee, "note": note or "",
                "limits": {"per_txn": PER_TXN_LIMIT, "daily": DAILY_LIMIT, "used_today": used_today}}
    
    def create(self, client_ref: str, from_account: int, to_account: int, amount: float,
               currency: str | None, note: str | None) -> Dict[str, Any]:
        # idempotency
        if client_ref:
            prev = self.repo.find_by_client_ref(client_ref)
            if prev:
                return {
                    "ok": True,
                    "idempotent": True,
                    "txn": prev,
                    "receipt": {
                        "pdf": {"filename": f"receipt_{prev['payment_id']}.pdf"},
                        "hash": prev["payment_id"]
                    }
                }

        pre = self.precheck(from_account, to_account, amount, currency, note)
        if not pre.get("ok"):
            return pre

        try:
            txn = self.repo.insert_payment_posted(
                client_ref=client_ref or "",
                from_account=from_account,
                to_account=to_account,
                amount=float(pre["amount"]),
                currency=pre["currency"],
                fee=float(pre["fee"]),
                note=pre.get("note") or "",
                balance_after=0.0  # repo dolduruyor
            )
            return {
                "ok": True,
                "txn": txn,
                "receipt": {
                    "pdf": {"filename": f"receipt_{txn['payment_id']}.pdf"},
                    "hash": txn["payment_id"]
                }
            }
        except ValueError as ve:
            return {"ok": False, "error": str(ve)}
        except Exception as e:
            return {"ok": False, "error": "create_failed", "detail": type(e).__name__}
