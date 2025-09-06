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

def _map_account_type_to_db(account_type: str) -> str:
    """
    Kullanıcı dostu account type'ları veritabanı değerlerine çevirir.
    Veritabanında Türkçe değerler: vadeli mevduat, vadesiz mevduat, maaş, yatırım
    """
    mapping = {
        "vadeli": "vadeli mevduat",
        "vadeli mevduat": "vadeli mevduat",
        "vadesiz mevduat": "vadesiz mevduat", 
        "vadesiz": "vadesiz mevduat",
        "maaş": "maaş",
        "maaş hesabı": "maaş",
        "yatırım": "yatırım",
        "yatırım hesabı": "yatırım"
    }
    return mapping.get(account_type.lower().strip(), account_type)

class PaymentService:
    def __init__(self, repo):
      self.repo = repo


    def _ensure(self):
        # payments tablosu var mı kontrol
        with self.repo._conn() if hasattr(self.repo, "_conn") else None:
            pass  # repo _conn yoksa da sorun değil; _ensure_schema operatif olarak insert aşamasında çağrılır

    def find_account_by_type(self, customer_id: int, account_type: str) -> Dict[str, Any]:
        """
        Müşterinin belirtilen account type'ına sahip hesabını bulur.
        """
        try:
            # Account type'ı veritabanı formatına çevir
            db_account_type = _map_account_type_to_db(account_type)
            
            # Müşterinin tüm hesaplarını al
            accounts = self.repo.get_accounts_by_customer(customer_id)
            if not accounts:
                return {"ok": False, "error": "no_accounts_found", "message": "Hesap bulunamadı."}
            
            # Account type'a göre filtrele
            matching_accounts = []
            for acc in accounts:
                if acc.get("account_type", "").lower() == db_account_type.lower():
                    matching_accounts.append(acc)
            
            if not matching_accounts:
                return {"ok": False, "error": "account_type_not_found", 
                       "message": f"{account_type} tipinde hesap bulunamadı."}
            
            if len(matching_accounts) > 1:
                return {"ok": False, "error": "multiple_accounts_found",
                       "message": f"Birden fazla {account_type} hesabınız var. Lütfen hesap numarası belirtin."}
            
            return {"ok": True, "account": matching_accounts[0]}
            
        except Exception as e:
            return {"ok": False, "error": "find_account_error", "message": f"Hesap bulunurken hata: {str(e)}"}

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
                  currency: str | None, note: str | None, customer_id: int = None) -> Dict[str, Any]:
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

        # Gönderici hesabın kullanıcıya ait olup olmadığını kontrol et
        if customer_id is not None and acc_from.get("customer_id") != customer_id:
            return {"ok": False, "error": "from_account_not_owned", "message": "Bu hesap size ait değil."}

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
    
    def create(self, customer_id: int, from_account: int, to_account: int, amount: float,
               currency: str | None, note: str | None) -> Dict[str, Any]:
        # Her transfer için yeni işlem yapılır (idempotency kaldırıldı)
        pre = self.precheck(from_account, to_account, amount, currency, note, customer_id)
        if not pre.get("ok"):
            return pre

        try:
            txn = self.repo.insert_payment_posted(
                customer_id=customer_id,
                from_account=from_account,
                to_account=to_account,
                amount=float(pre["amount"]),
                currency=pre["currency"],
                fee=float(pre["fee"]),
                note=pre.get("note") or ""
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
        

    def card_limit_increase_request(
        self,
        card_id: int,
        customer_id: int,
        new_limit: float,
        reason: str | None = None,
    ) -> Dict[str, Any]:
        """
        Kart limit artış talebi:
          - Kartın müşteriye ait olduğunu doğrular.
          - Basit politika kontrolleri uygular.
          - Talebi DB'ye 'received' statüsüyle kaydeder.
        """
        # 1) Tip/pozitiflik
        try:
            cid = int(card_id)
            cust = int(customer_id)
            nl = float(new_limit)
        except Exception:
            return {"error": "card_id/customer_id/new_limit geçersiz."}
        if nl <= 0:
            return {"error": "new_limit pozitif olmalı."}

        # 2) Kart doğrulama (SQLiteRepository'den gelir)
        card = self.repo.get_card_details(card_id=cid, customer_id=cust)  # inherits
        if not card:
            return {"error": "Kart bulunamadı ya da bu müşteriye ait değil."}

        current_limit = float(card.get("credit_limit") or 0.0)
        current_debt  = float(card.get("current_debt") or 0.0)

        # 3) Politika: mevcut limitten büyük, borcun altında olamaz, üst sınır = 2x
        if nl <= current_limit:
            return {"error": "Yeni limit mevcut limitten büyük olmalı."}
        if nl < current_debt:
            return {"error": "Yeni limit mevcut borcun altında olamaz."}
        max_limit = current_limit * 2.0
        if nl > max_limit:
            return {"error": f"Talep edilen limit üst sınırı aşıyor (<= {max_limit:,.2f})."}

        # 4) DB'ye kaydet
        saved = self.repo.save_card_limit_increase_request(
            card_id=cid,
            customer_id=cust,
            requested_limit=nl,
            reason=(reason or "").strip() or None,
            status="received",
        )

        # 5) Dönüş
        return {
            "ok": True,
            "request_id": saved.get("request_id"),
            "status": saved.get("status"),
            "card": {
                "card_id": cid,
                "current_limit": current_limit,
                "current_debt": current_debt,
                "statement_day": card.get("statement_day"),
                "due_day": card.get("due_day"),
            },
            "requested_limit": nl,
            "reason": saved.get("reason"),
            "created_at": saved.get("created_at"),
            "ui_component": {
                "type": "card_limit_increase_request",
                "title": "Kart Limit Artış Talebi Alındı",
                "card_id": cid,
                "current_limit": current_limit,
                "requested_limit": nl,
                "status": saved.get("status"),
                "created_at": saved.get("created_at"),
            },
        }
