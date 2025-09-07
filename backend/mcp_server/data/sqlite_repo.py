# data/sqlite_repo.py
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional,Tuple
import pandas as pd


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
                  account_number,
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
                "account_number": row["account_number"],
                "account_type": str(row["account_type"]),
                "balance": float(row["balance"]),
                "currency": str(row["currency"]),
                "created_at": str(row["created_at"]),  # ISO-8601 string
                "status": str(row["status"]),
            }
        finally:
            con.close()

    def get_accounts_by_customer(self, customer_id: int, account_type: str = None) -> List[Dict[str, Any]]:
        """
        Müşteriye ait hesapları getirir. İsteğe bağlı olarak hesap türüne göre filtreleme yapabilir.
        
        Args:
            customer_id (int): Müşteri ID'si
            account_type (str, optional): Hesap türü filtresi (vadeli mevduat, vadesiz mevduat, maaş, yatırım)
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            
            if account_type:
                cur.execute(
                    """
                    SELECT account_id, customer_id, account_number, account_type, balance, currency, created_at, status
                    FROM accounts
                    WHERE customer_id = ? AND account_type = ?
                    ORDER BY account_id
                    """,
                    (customer_id, account_type),
                )
            else:
                cur.execute(
                    """
                    SELECT account_id, customer_id, account_number, account_type, balance, currency, created_at, status
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
                        "account_number": r["account_number"],
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
                    c.card_number,
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
                    c.card_number,
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

            def normalize_tr(s: Optional[str]) -> str:
                """Türkçe karakterleri normalize eder"""
                if not s:
                    return ""
                # Türkçe karakterleri normalize et
                s = s.replace("İ", "i").replace("I", "i")
                s = s.replace("Ğ", "g").replace("Ğ", "g")
                s = s.replace("Ü", "u").replace("Ü", "u")
                s = s.replace("Ş", "s").replace("Ş", "s")
                s = s.replace("Ö", "o").replace("Ö", "o")
                s = s.replace("Ç", "c").replace("Ç", "c")
                return s.lower().strip()

            # Python tarafında Unicode-aware eşleştirme
            out: List[Dict[str, Any]] = []
            for r in rows:
                city_db = str(r["city"])
                dist_db = str(r["district"]) if r["district"] is not None else None

                # Normalize edilmiş karşılaştırma
                if normalize_tr(city_db) != normalize_tr(city_q):
                    continue
                if dist_q is not None and normalize_tr(dist_db) != normalize_tr(dist_q):
                    continue

                # tür filtresi (opsiyonel)
                kind_db = str(r["kind"]).upper() if r["kind"] is not None else ""
                if kind:
                    k = kind.strip().lower()
                    # Türkçe karakterleri normalize et
                    k = k.replace("ş", "s").replace("ü", "u")
                    want = None
                    if k == "atm":
                        want = "ATM"
                    elif k in ("branch", "sube", "şube"):
                        want = "BRANCH"
                    
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

    def list_branch_atm_all(self) -> List[Dict[str, Any]]:
        """
        Tüm şube/ATM kayıtlarını döndürür (şehir/ilçe filtresi olmadan).
        Dönüş: {id, type, name, city, district, address, lat, lon}
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            cur = con.cursor()
            cur.execute(
                """
                SELECT id, kind, name, city, district, address, latitude, longitude
                FROM branch_atm
                """
            )
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                kind_db = str(r["kind"]).upper() if r["kind"] is not None else ""
                out.append({
                    "id": int(r["id"]),
                    "type": "atm" if kind_db == "ATM" else "branch",
                    "name": str(r["name"]),
                    "city": str(r["city"]),
                    "district": str(r["district"]) if r["district"] is not None else None,
                    "address": str(r["address"]),
                    "lat": float(r["latitude"]) if r["latitude"] is not None else None,
                    "lon": float(r["longitude"]) if r["longitude"] is not None else None,
                })
            return out
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

    
    def get_interest_rate(self, product: str) -> float:
        """
        interest_rates tablosundan tek ürün için en güncel oranı döner.
        Şema uyarlaması:
          - Oran kolonu annual_rate varsa onu, yoksa rate_apy'yi kullanır.
          - Tarih kolonu effective_date varsa onu, yoksa updated_at'ı kullanır.
        """
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            # kolon keşfi
            cols = {r[1] for r in con.execute("PRAGMA table_info('interest_rates')")}
            rate_col = "annual_rate" if "annual_rate" in cols else "rate_apy"
            date_col = "effective_date" if "effective_date" in cols else "updated_at"

            sql = f"""
                SELECT {rate_col} AS rate_value
                FROM interest_rates
                WHERE product = ? COLLATE NOCASE
                ORDER BY
                  COALESCE(datetime({date_col}), datetime('1970-01-01')) DESC,
                  rowid DESC
                LIMIT 1
            """
            row = con.execute(sql, (product,)).fetchone()
            if not row or row["rate_value"] is None:
             raise ValueError(f"Interest rate not found for product={product}")
            
            rate_value = float(row["rate_value"])
            
            # rate_apy sütunundan geliyorsa 100'e böl (zaten yüzde olarak geliyor)
            if rate_col == "rate_apy":
                rate_value = rate_value / 100.0
                
            return rate_value
        finally:
            con.close()

    def _resolve_rate_via_repo_or_db(
    self,
    provided_rate: Optional[float],
    product: Optional[str],
    product_fallback: str,   # "savings" (deposit) | "loan" (loan)
    currency: str = "TRY",
    as_of: Optional[str] = None,
    ) -> Tuple[float, dict]:
        """
        1) provided_rate verilmişse onu kullanır.
        2) repo.get_interest_rate(product) varsa onu kullanır.
        3) Yoksa sqlite DB'de interest_rates benzeri tablodan çeker.
        - Tablo adı: interest_rates | rates | deposit_rates | loan_rates ... (esnek)
        - Oran sütunu: annual_rate | rate_apy | rate | apr (esnek)
        - Ürün sütunu: product | product_type (esnek)
        - Para birimi: currency | ccy (esnek)
        - Tarih: effective_date | valid_from | updated_at | date (en güncel satır)
        """
        # 1) Manuel
        if provided_rate is not None:
            return float(provided_rate), {"source": "manual"}

        # 2) Repo
        prod = product or product_fallback
        #if repo is not None and hasattr(repo, "get_interest_rate"):
        if prod is not None:
            r = float(self.get_interest_rate(prod))
            return r, {"source": "db:get_interest_rate", "product": prod}

        # 3) SQLite fallback
        if not self.db_path:
            raise ValueError("rate not provided; repo yok; db_path verilmedi")

        as_of_date = None
        if as_of:
            try:
                as_of_date = datetime.fromisoformat(as_of).date()
            except Exception:
                raise ValueError("as_of must be ISO date YYYY-MM-DD")

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            # Aday tablolar
            tbls = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND (lower(name) LIKE '%interest%' OR lower(name) LIKE '%rate%')"
            ).fetchall()]
            if not tbls:
                raise ValueError("No interest/rate tables found in DB")

            preferred = ["interest_rates", "rates", "deposit_rates", "loan_rates", "bank_interest_rates", "interest"]
            tbls_sorted = sorted(tbls, key=lambda t: (preferred.index(t) if t in preferred else 999, t))

            best_row, best_tbl, meta = None, None, {}
            best_score = -1

            for tbl in tbls_sorted:
                cols = {r[1] for r in con.execute(f"PRAGMA table_info('{tbl}')").fetchall()}
                def pick(cands):
                    for c in cands:
                        if c in cols: return c
                    return None

                rate_col     = pick(["annual_rate","rate_apy","rate","apr"])
                product_col  = pick(["product","product_type","category"])
                currency_col = pick(["currency","ccy","iso_currency"])
                eff_col      = pick(["effective_date","valid_from","updated_at","date"])

                if not rate_col:
                    continue

                where, params, score = [], [], 0
                if product_col:
                    where.append(f"LOWER({product_col}) = LOWER(?)")
                    params.append(prod)
                    score += 1
                if currency_col:
                    where.append(f"UPPER({currency_col}) = UPPER(?)")
                    params.append(currency)
                    score += 1
                if as_of_date and eff_col:
                    where.append(f"date({eff_col}) <= date(?)")
                    params.append(as_of_date.isoformat())

                sql = f"SELECT * FROM '{tbl}'"
                if where: sql += " WHERE " + " AND ".join(where)
                if eff_col:
                    sql += f" ORDER BY date({eff_col}) DESC, rowid DESC LIMIT 1"
                else:
                    sql += " ORDER BY rowid DESC LIMIT 1"

                row = con.execute(sql, params).fetchone()
                if row is not None and score > best_score:
                    best_score, best_row, best_tbl = score, row, tbl
                    meta = {
                        "source": "db",
                        "table": tbl,
                        "matched_columns": {
                            "rate": rate_col, "product": product_col,
                            "currency": currency_col, "effective": eff_col
                        }
                    }

            if not best_row:
                raise ValueError(f"Could not resolve rate for product={prod}, currency={currency}")

            return float(best_row[meta["matched_columns"]["rate"]]), meta
        finally:
            con.close()
    
    def _get_connection(self):
        """
        Yeni bir veritabanı bağlantısı oluşturur ve döndürür.

        Bu, sınıf içinde kullanılmak üzere özel bir yardımcı metottur.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def get_asset_performance_data(self) -> pd.DataFrame:
        """
        Retrieves the asset performance data from the 'asset_performance' table.
        """
        query = "SELECT * FROM asset_performance;"
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df

    def get_portfolio_mixes_data(self) -> pd.DataFrame:
        """
        'asset_performance' tablosundan varlık performans verilerini çeker.
        """
        query = "SELECT * FROM portfolio_mixes;"
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            return df

    def get_portfolios(self, risk_level: Optional[str] = None) -> list[dict]:
        """
        Retrieves portfolio definitions from the 'portfolio_mixes' table.
        If a risk_level is provided, it filters the results.
        Otherwise, it returns all portfolios.

        Args:
            risk_level (Optional[str]): The risk level to filter by (e.g., 'Düşük', 'Orta', 'Yüksek').

        Returns:
            A list of dictionaries, where each dictionary represents a portfolio.
        """
        base_query = "SELECT portfoy_adi, risk_seviyesi, varlik_dagilimi FROM portfolio_mixes"
        params = []

        if risk_level:
            base_query += " WHERE risk_seviyesi = ?;"
            params.append(risk_level)
        else:
            base_query += ";"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            results = cursor.execute(base_query, params).fetchall()
            return [dict(row) for row in results]
