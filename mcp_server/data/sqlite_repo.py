# data/sqlite_repo.py
import sqlite3
from typing import Any, Dict, Optional


class SQLiteAccountRepository:
    """
    accounts tablosundan tek kaydı (account_id ile) okur.
    """

    def __init__(self, db_path: str = "bank.db"):
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
