# data/sqlite_repo.py
import os
import sqlite3
from typing import Any, Dict, List, Optional


class SQLiteRepository:
    """
    accounts tablosundan tek kaydı (account_id ile) okur.
    """

    BASE_DIR = os.path.dirname(__file__)
    DB_PATH = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        if account_id is None:
            return None

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row  # dict benzeri erişim
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT
                  account_id,
                  customer_id,
                  account_type,
                  balance,
                  currency,
                  created_at,
                  status
                FROM accounts
                WHERE account_id = ?
                """,
                (account_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            # Türleri netleştir
            return {
                "account_id": int(row["account_id"]),
                "customer_id": int(row["customer_id"]),
                "account_type": str(row["account_type"]),
                "balance": float(row["balance"]),
                "currency": str(row["currency"]),
                "created_at": str(row["created_at"]),  # ISO-8601 string
                "status": str(row["status"]),
            }
        finally:
            con.close()

    def get_accounts_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT account_id, customer_id, account_type, balance, currency, created_at, status
                FROM accounts
                WHERE customer_id = ?
                ORDER BY account_id
                """,
                (customer_id,),
            )
            rows = cur.fetchall()

            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "account_id": int(r["account_id"]),
                        "customer_id": int(r["customer_id"]),
                        "account_type": str(r["account_type"]),
                        "balance": float(r["balance"]),
                        "currency": str(r["currency"]),
                        "created_at": str(r["created_at"]),
                        "status": str(r["status"]),
                    }
                )
            return out
        finally:
            con.close()

    def get_card_details(self, card_id: int) -> Optional[Dict]:
        """Verilen card_id'ye ait kart detaylarını veritabanından çeker."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row  # dict benzeri erişim için
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT
                    card_id,
                    credit_limit,
                    current_debt,
                    statement_day,
                    due_day
                FROM cards
                WHERE card_id = ?;
                """,
                (card_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    def get_transactions_by_customer(
        self, customer_id: int, limit: int = 5
    ) -> List[Dict]:
        """
        Bir müşteriye ait tüm hesaplardaki son işlemleri tarih sırasına göre çeker.
        'txns' tablosunda customer_id olmadığı için 'accounts' tablosuyla birleştirme (JOIN) yaparız.
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT
                    t.txn_id,
                    t.txn_date,
                    t.description,
                    t.amount,
                    t.txn_type,
                    a.account_id
                FROM txns t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = ?
                ORDER BY t.txn_date DESC
                LIMIT ?;
                """,
                (customer_id, limit),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()
