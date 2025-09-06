# # --- Payment (transfer) yardımcıları ---
# import sqlite3
# import datetime
# import os

# class SQLitePaymentRepository:
#     """
#     Kendi hesapları arasında transfer (havale) işlemleri için basit repo.
#     'payments' tablosu bu modül tarafından yaratılır (yoksa).
#     """
#     BASE_DIR = os.path.dirname(__file__)
#     DB_PATH = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))

#     def __init__(self, db_path: str = DB_PATH):
#       self.db_path = db_path

#     def _ensure_schema(self, con):
#         cur = con.cursor()
#         cur.execute("""
#         CREATE TABLE IF NOT EXISTS payments (
#           payment_id TEXT PRIMARY KEY,
#           client_ref TEXT UNIQUE,
#           from_account INTEGER NOT NULL,
#           to_account INTEGER NOT NULL,
#           amount REAL NOT NULL,
#           currency TEXT NOT NULL,
#           fee REAL NOT NULL DEFAULT 0,
#           note TEXT,
#           status TEXT NOT NULL,              -- draft|pending|posted|failed|canceled
#           created_at TEXT NOT NULL,
#           posted_at TEXT,
#           balance_after REAL
#         )
#         """)
#         # txns tablon varsa buraya ayrıca satır düşeceğiz (opsiyonel)

#     def _now(self) -> str:
#         return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

#     def get_account_currency(self, account_id: int) -> str | None:
#         acc = self.get_account(account_id)
#         return acc.get("currency") if acc else None

#     def get_customer_id_by_account(self, account_id: int) -> int | None:
#         acc = self.get_account(account_id)
#         return acc.get("customer_id") if acc else None

#     def get_daily_out_total(self, customer_id: int, date_yyyy_mm_dd: str) -> float:
#         """
#         Bugün için bu müşterinin 'posted' durumundaki toplam çıkış tutarı (TRY varsayımı).
#         """
#         con = sqlite3.connect(self.db_path)
#         try:
#             cur = con.cursor()
#             cur.execute("""
#               SELECT COALESCE(SUM(amount), 0)
#               FROM payments
#               WHERE status='posted'
#                 AND from_account IN (SELECT account_id FROM accounts WHERE customer_id=?)
#                 AND substr(created_at,1,10)=?
#             """, (customer_id, date_yyyy_mm_dd))
#             row = cur.fetchone()
#             return float(row[0] or 0.0)
#         finally:
#             con.close()

#     def find_by_client_ref(self, client_ref: str):
#         con = sqlite3.connect(self.db_path)
#         con.row_factory = sqlite3.Row
#         try:
#             self._ensure_schema(con)
#             cur = con.cursor()
#             cur.execute("SELECT * FROM payments WHERE client_ref=?", (client_ref,))
#             r = cur.fetchone()
#             return dict(r) if r else None
#         finally:
#             con.close()

#     def insert_payment_posted(self, client_ref: str, from_account: int, to_account: int,
#                               amount: float, currency: str, fee: float, note: str,
#                               balance_after: float) -> dict:
#         """
#         Tek bir transaction içinde:
#           - from_account bakiyesini düş
#           - to_account bakiyesini artır
#           - payments tablosuna 'posted' kayıt ekle
#           - (opsiyonel) txns tablosuna 2 satır yaz
#         """
#         now = self._now()
#         payment_id = f"TX{now.replace('-','').replace(':','').replace('T','').replace('Z','')}"
#         con = sqlite3.connect(self.db_path)
#         try:
#             con.isolation_level = None  # explicit tx
#             cur = con.cursor()
#             cur.execute("BEGIN")
#             # bakiyeleri değiştir
#             cur.execute("SELECT balance FROM accounts WHERE account_id=?", (from_account,))
#             from_bal = cur.fetchone()
#             if not from_bal:
#                 raise ValueError("from_account_not_found")
#             from_bal = float(from_bal[0])
#             if from_bal < amount + fee:
#                 raise ValueError("insufficient_funds")

#             cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_id=?", (amount + fee, from_account))
#             cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_id=?", (amount, to_account))

#             # güncel bakiye
#             cur.execute("SELECT balance FROM accounts WHERE account_id=?", (from_account,))
#             bal_after = float(cur.fetchone()[0])

#             # payments kaydı
#             cur.execute("""
#               INSERT INTO payments(payment_id, client_ref, from_account, to_account, amount, currency, fee, note, status, created_at, posted_at, balance_after)
#               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'posted', ?, ?, ?)
#             """, (payment_id, client_ref, from_account, to_account, amount, currency, fee, note, now, now, bal_after))

#             # opsiyonel: txns tablosuna düş (varsa)
#             try:
#                 cur.execute("""
#                   INSERT INTO txns(account_id, ts, amount, currency, direction, desc, counterparty)
#                   VALUES (?, ?, ?, ?, 'out', ?, ?)
#                 """, (from_account, now, amount + fee, currency, f"Transfer to #{to_account} | {note or ''}", str(to_account)))
#                 cur.execute("""
#                   INSERT INTO txns(account_id, ts, amount, currency, direction, desc, counterparty)
#                   VALUES (?, ?, ?, ?, 'in', ?, ?)
#                 """, (to_account, now, amount, currency, f"Transfer from #{from_account} | {note or ''}", str(from_account)))
#             except Exception:
#                 # txns yoksa dert etmeyelim
#                 pass

#             cur.execute("COMMIT")
#             return {
#                 "payment_id": payment_id,
#                 "client_ref": client_ref,
#                 "from_account": from_account,
#                 "to_account": to_account,
#                 "amount": amount,
#                 "currency": currency,
#                 "fee": fee,
#                 "note": note,
#                 "status": "posted",
#                 "created_at": now,
#                 "posted_at": now,
#                 "balance_after": bal_after
#             }
#         except Exception:
#             try: cur.execute("ROLLBACK")
#             except Exception: pass
#             raise
#         finally:
#             con.close()

# --- Payment (transfer) yardımcıları ---
import sqlite3
import datetime
import os
from .sqlite_repo import SQLiteRepository

class SQLitePaymentRepository(SQLiteRepository):
    """
    Kendi hesapları arasında transfer (havale) işlemleri için repo.
    payments tablosu yoksa otomatik oluşturur.
    """
    BASE_DIR = os.path.dirname(__file__)
    DEFAULT_DB = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))

    def __init__(self, db_path: str = None):
        super().__init__(db_path )  # SQLiteAccountRepository db_path kurar
        self.db_path = db_path 

    def _ensure_schema(self, con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
          payment_id TEXT PRIMARY KEY,
          customer_id INTEGER NOT NULL,
          from_account INTEGER NOT NULL,
          to_account INTEGER NOT NULL,
          amount REAL NOT NULL,
          currency TEXT NOT NULL,
          fee REAL NOT NULL DEFAULT 0,
          note TEXT,
          status TEXT NOT NULL,              -- draft|pending|posted|failed|canceled
          created_at TEXT NOT NULL,
          posted_at TEXT,
          from_balance_after REAL,
          to_balance_after REAL
        )
        """)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        self._ensure_schema(con)  # <-- her bağlantıda şema garantisi
        return con

    def _now(self) -> str:
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def get_account_currency(self, account_id: int) -> str | None:
        acc = self.get_account(account_id)  # mirastan gelir
        return acc.get("currency") if acc else None

    def get_customer_id_by_account(self, account_id: int) -> int | None:
        acc = self.get_account(account_id)
        return acc.get("customer_id") if acc else None

    def get_daily_out_total(self, customer_id: int, date_yyyy_mm_dd: str) -> float:
        """
        Bugün için bu müşterinin 'posted' durumundaki toplam çıkış tutarı.
        """
        con = self._connect()
        try:
            cur = con.cursor()
            cur.execute("""
              SELECT COALESCE(SUM(amount), 0)
              FROM payments
              WHERE status='posted'
                AND from_account IN (SELECT account_id FROM accounts WHERE customer_id=?)
                AND substr(created_at,1,10)=?
            """, (customer_id, date_yyyy_mm_dd))
            row = cur.fetchone()
            return float(row[0] or 0.0)
        finally:
            con.close()

    def find_by_customer_id(self, customer_id: int):
        con = self._connect()
        try:
            cur = con.cursor()
            cur.execute("SELECT * FROM payments WHERE customer_id=?", (customer_id,))
            r = cur.fetchone()
            return dict(r) if r else None
        finally:
            con.close()

    def insert_payment_posted(self, customer_id: int, from_account: int, to_account: int,
                              amount: float, currency: str, fee: float, note: str) -> dict:
        """
        Tek transaction içinde: bakiyeleri güncelle + payments'a 'posted' kayıt ekle
        + varsa txns tablosuna 2 satır.
        """
        now = self._now()
        payment_id = f"TX{now.replace('-','').replace(':','').replace('T','').replace('Z','')}"
        con = self._connect()
        try:
            con.isolation_level = None  # explicit tx
            cur = con.cursor()
            cur.execute("BEGIN")

            # bakiyeler
            cur.execute("SELECT balance FROM accounts WHERE account_id=?", (from_account,))
            r = cur.fetchone()
            if not r:
                raise ValueError("from_account_not_found")
            from_bal = float(r[0])
            if from_bal < amount + fee:
                raise ValueError("insufficient_funds")

            cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_id=?", (amount + fee, from_account))
            cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_id=?", (amount, to_account))

            # güncel bakiyeler
            cur.execute("SELECT balance FROM accounts WHERE account_id=?", (from_account,))
            from_bal_after = float(cur.fetchone()[0])
            cur.execute("SELECT balance FROM accounts WHERE account_id=?", (to_account,))
            to_bal_after = float(cur.fetchone()[0])

            # payments kaydı
            cur.execute("""
              INSERT INTO payments(payment_id, customer_id, from_account, to_account, amount, currency, fee, note, status, created_at, posted_at, from_balance_after, to_balance_after)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'posted', ?, ?, ?, ?)
            """, (payment_id, customer_id, from_account, to_account, amount, currency, fee, note, now, now, from_bal_after, to_bal_after))

            # opsiyonel txns
            try:
                cur.execute("""
                  INSERT INTO txns(account_id, ts, amount, currency, direction, desc, counterparty)
                  VALUES (?, ?, ?, ?, 'out', ?, ?)
                """, (from_account, now, amount + fee, currency, f"Transfer to #{to_account} | {note or ''}", str(to_account)))
                cur.execute("""
                  INSERT INTO txns(account_id, ts, amount, currency, direction, desc, counterparty)
                  VALUES (?, ?, ?, ?, 'in', ?, ?)
                """, (to_account, now, amount, currency, f"Transfer from #{from_account} | {note or ''}", str(from_account)))
            except Exception:
                pass

            cur.execute("COMMIT")
            return {
                "payment_id": payment_id,
                "customer_id": customer_id,
                "from_account": from_account,
                "to_account": to_account,
                "amount": amount,
                "currency": currency,
                "fee": fee,
                "note": note,
                "status": "posted",
                "created_at": now,
                "posted_at": now,
                "from_balance_after": from_bal_after,
                "to_balance_after": to_bal_after
            }
        except Exception:
            try: cur.execute("ROLLBACK")
            except Exception: pass
            raise
        finally:
            con.close()

    def ensure_card_limit_request_schema(self, con: sqlite3.Connection):
        """
        'card_limit_requests' tablosunu garanti eder.
        Eğer yoksa oluşturur.
        """
        cur = con.cursor()
        # YENİ: kart limit artış talepleri
        cur.execute("""
        CREATE TABLE IF NOT EXISTS card_limit_requests (
          request_id      INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at      TEXT NOT NULL,
          card_id         INTEGER NOT NULL,
          customer_id     INTEGER NOT NULL,
          requested_limit REAL NOT NULL,
          reason          TEXT,
          status          TEXT NOT NULL   -- received|approved|rejected
        )
        """)

    def save_card_limit_increase_request(
        self,
        card_id: int,
        customer_id: int,
        requested_limit: float,
        reason: str | None,
        status: str = "received",
    ) -> dict:
        con = self._connect()
        try:
            now = self._now()
            cur = con.cursor()
            cur.execute("""
              INSERT INTO card_limit_requests
              (created_at, card_id, customer_id, requested_limit, reason, status)
              VALUES (?, ?, ?, ?, ?, ?)
            """, (now, int(card_id), int(customer_id), float(requested_limit), reason, status))
            con.commit()
            rid = cur.lastrowid
            return {
                "request_id": int(rid),
                "created_at": now,
                "status": status,
                "reason": reason,
            }
        finally:
            con.close()
