# data/sqlite_repo.py
import os
import sqlite3
from typing import Any, Dict, List, Optional


class SQLiteAccountRepository:
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
