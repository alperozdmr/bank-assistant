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

    def get_card_details(self, card_id: int, customer_id: int) -> Optional[Dict]:
        """Verilen card_id'ye ait kart detaylarını veritabanından çeker ve müşteri kimliği ile doğrular."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row  # dict benzeri erişim için
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT
                    c.card_id,
                    c.credit_limit,
                    c.current_debt,
                    c.statement_day,
                    c.due_day
                FROM cards c
                JOIN accounts a ON c.account_id = a.account_id
                WHERE c.card_id = ? AND a.customer_id = ?;
                """,
                (card_id, customer_id),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    def get_all_cards_for_customer(self, customer_id: int) -> List[Dict]:
        """Belirli bir müşteriye ait tüm kartların detaylarını veritabanından çeker."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT
                    c.card_id,
                    c.credit_limit,
                    c.current_debt,
                    c.statement_day,
                    c.due_day
                FROM cards c
                JOIN accounts a ON c.account_id = a.account_id
                WHERE a.customer_id = ?;
                """,
                (customer_id,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
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

    def get_fx_rates(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT code, buy, sell, updated_at FROM fx_rates ORDER BY code"
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_interest_rates(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT product, rate_apy, updated_at FROM interest_rates ORDER BY product"
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_fee(self, service_code: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                """
                SELECT service_code, description, pricing_json, updated_at
                FROM fees
                WHERE service_code = ? COLLATE NOCASE
                """,
                (service_code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_fees(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                """
                SELECT service_code, description, pricing_json, updated_at
                FROM fees
                ORDER BY service_code
                """
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def find_branch_atm(
        self,
        city: str,
        district: Optional[str] = None,
        limit: int = 5,
        kind: Optional[str] = None,   # 'ATM' veya 'BRANCH' (opsiyonel)
    ) -> List[Dict[str, Any]]:
        """
        branch_atm tablosundan satırları döner.
        Kolonlar: id, kind('ATM'|'BRANCH'), name, city, district, address, latitude, longitude
        **Not:** Türkçe harf problemi nedeniyle filtreyi Python tarafında casefold ile yapıyoruz.
        """
        city_q = (city or "").strip()
        dist_q = (district or "").strip() or None

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            # NOT: Burada lower(...) KULLANMIYORUZ.
            cur.execute(
                """
                SELECT id, kind, name, city, district, address, latitude, longitude
                FROM branch_atm
                """
            )
            rows = cur.fetchall()

            def cf(s: Optional[str]) -> str:
                return (s or "").casefold()

            # Python tarafında Unicode-aware eşleştirme
            out: List[Dict[str, Any]] = []
            for r in rows:
                city_db = str(r["city"])
                dist_db = str(r["district"]) if r["district"] is not None else None

                if cf(city_db) != cf(city_q):
                    continue
                if dist_q is not None and cf(dist_db) != cf(dist_q):
                    continue

                # tür filtresi (opsiyonel)
                kind_db = str(r["kind"]).upper() if r["kind"] is not None else ""
                if kind:
                    k = kind.strip().casefold()
                    want = "ATM" if k == "atm" else ("BRANCH" if k in ("branch", "şube", "sube") else None)
                    if want and kind_db != want:
                        continue

                out.append({
                    "id": int(r["id"]),
                    "type": "atm" if kind_db == "ATM" else "branch",
                    "name": str(r["name"]),
                    "city": city_db,
                    "district": dist_db,
                    "address": str(r["address"]),
                    "lat": float(r["latitude"]) if r["latitude"] is not None else None,
                    "lon": float(r["longitude"]) if r["longitude"] is not None else None,
                })

            # sıralama & limit
            out.sort(key=lambda x: (x.get("district") or "", x["name"]))
            return out[: max(0, min(limit, 50))]  # üst sınır güvenliği
        finally:
            con.close()

    def list_transactions(
        self,
        account_id: int,
        customer_id: int, # customer_id eklendi
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Belirli hesabın işlem kayıtlarını tarih filtresiyle getirir ve müşteri kimliği ile doğrular.
        Tarih alanı: txns.txn_date (TEXT/DATETIME). 'YYYY-MM-DD' veya
        'YYYY-MM-DD HH:MM:SS' formatları desteklenir.
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()

            where = ["t.account_id = ?", "a.customer_id = ?"]
            params: list[Any] = [account_id, customer_id]

            if from_date:
                where.append("t.txn_date >= ?")
                params.append(from_date)
            if to_date:
                where.append("t.txn_date <= ?")
                params.append(to_date)

            where_sql = " AND ".join(where)
            sql = f"""
                SELECT
                    t.txn_id, t.account_id, t.amount, t.txn_type,
                    t.txn_date, t.description
                FROM txns t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE {where_sql}
                ORDER BY t.txn_date DESC
                LIMIT ?
            """
            params.append(limit if isinstance(limit, int) and limit > 0 else 50)
            rows = cur.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def save_transaction_snapshot(
        self,
        account_id: int,
        from_date: str | None,
        to_date: str | None,
        limit: int,
        transactions: list[dict],
    ) -> dict:
        """
        Listelediğimiz işlemleri 'txn_snapshots' tablosuna snapshot olarak kaydeder.
        Her işlem satırını, istek metadatasıyla birlikte saklarız.
        """
        con = sqlite3.connect(self.db_path)
        try:
            con.execute("""
                CREATE TABLE IF NOT EXISTS txn_snapshots (
                  snapshot_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                  snapshot_at   TEXT NOT NULL,
                  account_id    INTEGER NOT NULL,
                  range_from    TEXT,
                  range_to      TEXT,
                  request_limit INTEGER,
                  txn_id        INTEGER NOT NULL,
                  txn_date      TEXT NOT NULL,
                  amount        REAL NOT NULL,
                  txn_type      TEXT,
                  description   TEXT,
                  FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                  FOREIGN KEY (txn_id)     REFERENCES txns(txn_id)       ON DELETE CASCADE
                )
            """)
            con.commit()

            from datetime import datetime
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            cur = con.cursor()
            for tx in transactions:
                cur.execute(
                    """
                    INSERT INTO txn_snapshots (
                      snapshot_at, account_id, range_from, range_to, request_limit,
                      txn_id, txn_date, amount, txn_type, description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now,
                        account_id,
                        from_date,
                        to_date,
                        int(limit) if isinstance(limit, int) else None,
                        tx["txn_id"],
                        tx["txn_date"],
                        tx["amount"],
                        tx.get("txn_type"),
                        tx.get("description"),
                    ),
                )
            con.commit()
            return {"snapshot_at": now, "saved": len(transactions)}
        finally:
            con.close()