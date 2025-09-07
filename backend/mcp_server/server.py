# server.py
###############
import os
import sys
from typing import Any, Dict, Optional
from .data.sql_payment_repo import SQLitePaymentRepository
from .data.sqlite_repo import SQLiteRepository
from fastmcp import FastMCP
from .tools.general_tools import GeneralTools
from .tools.calculation_tools import CalculationTools
from .tools.roi_simulator_tool import ROISimulatorTool
from .tools.payment_tools import PaymentService

###############

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.config_local import DB_PATH ## bu import yukarıdaki kodun altında olmak zorunda yoksa çalışmaz
from common.mcp_decorators import log_tool

# === Initialize MCP server ===
mcp = FastMCP("Fortuna Banking Services")
# === Initialize tool classes ===
repo = SQLiteRepository(db_path=DB_PATH)
general_tools = GeneralTools(repo)
calc_tools = CalculationTools(repo)
roi_simulator_tool = ROISimulatorTool(repo)

repo_payment = SQLitePaymentRepository(db_path=DB_PATH)
pay = PaymentService(repo_payment)



# ============ GENERAL TOOL ==============#
@mcp.tool()
@log_tool
def get_balance(account_id: int, customer_id: int) -> dict:
    """
    Retrieves current balance information for a specific account, ensuring it belongs to the specified customer.

    This tool reads from the `accounts` table and returns normalized account data
    including monetary balance with currency and core account attributes. It is
    read-only and intended for validation and display in chat/agent flows.

    Parameters:
        account_id (int): Unique account identifier in the banking system.
        customer_id (int): The unique identifier for the customer.

    Returns:
        Account record containing:
        - account_id (int) and customer_id (int)
        - account_type (checking | savings | credit)
        - balance (float) and currency (TRY | USD | EUR)
        - status (active | frozen | closed)
        - created_at (ISO-8601 string: "YYYY-MM-DD HH:MM:SS")
        If the account is not found, the input is invalid, or the account does not belong to the customer, returns:
        - error (str) with an explanatory message
    """
    return general_tools.get_balance(account_id, customer_id)


@mcp.tool()
@log_tool
def get_accounts(customer_id: int) -> dict:
    """
    Fetch customer's account(s) from `accounts`. Read-only; output is
    normalized for chat/agent flows.

    Parameters:
        customer_id (int): Customer ID.

    Returns:
        - {"error": str} if input is invalid or no records exist.
        - Single account → object with: account_id, customer_id, account_type
          (checking/savings/credit), balance, currency (TRY/USD/EUR),
          status (active/frozen/closed), created_at ("YYYY-MM-DD HH:MM:SS").
        - Multiple accounts → {"customer_id": int, "accounts": [
          {account_id, account_type, balance, currency, status, created_at}
          ]}.
    """
    return general_tools.get_accounts(customer_id)


@mcp.tool()
@log_tool
def get_balance_by_account_type(customer_id: int, account_type: str) -> dict:
    """
    Retrieves balance information for a specific account type (e.g., "maaş hesabımın bakiyesi").

    This tool allows users to query their account balance by account type instead of account ID.
    It's particularly useful when users ask questions like "maaş hesabımın bakiyesi ne?" or
    "vadeli mevduat hesabımın bakiyesi".

    Parameters:
        customer_id (int): The unique identifier for the customer.
        account_type (str): Account type to search for. Supported types:
            - "vadeli mevduat" (term deposit)
            - "vadesiz mevduat" (demand deposit)
            - "maaş" (salary account)
            - "yatırım" (investment account)

    Returns:
        Account record containing:
        - account_id (int) and customer_id (int)
        - account_number (str) and account_type (str)
        - balance (float) and balance_formatted (str)
        - currency (str) and status (str)
        - created_at (ISO-8601 string)
        - ui_component (dict): Frontend BalanceCard component data
        If the account type is not found or invalid, returns:
        - error (str) with an explanatory message

    Examples:
        - "maaş hesabımın bakiyesi" → account_type="maaş"
        - "vadeli mevduat hesabımın bakiyesi" → account_type="vadeli mevduat"
        - "yatırım hesabımın bakiyesi" → account_type="yatırım"
    """
    return general_tools.get_balance_by_account_type(customer_id, account_type)


@mcp.tool()
@log_tool
def transactions_list_by_type(
    customer_id: int,
    account_type: str,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
) -> dict:
    """
    Hesap tipine göre TEK adımda işlem geçmişini döndürür.

    Parametreler:
      - customer_id (int): Müşteri kimliği
      - account_type (str): "vadeli mevduat" | "vadesiz mevduat" | "maaş" | "yatırım"
      - from_date/to_date (str|None): ISO benzeri tarih aralığı
      - limit (int): döndürülecek işlem sayısı (1..500)
    """
    # 1) Hesabı bulun
    found = pay.find_account_by_type(customer_id, account_type)
    if not isinstance(found, dict) or not found.get("ok"):
        return {"ok": False, **(found or {"error": "find_account_failed"})}

    acc = found.get("account") or {}
    acc_id = acc.get("account_id")
    if not acc_id:
        return {"ok": False, "error": "account_not_found"}

    # 2) transactions_list mantığı (müşteri doğrulaması + tarih/limit temizliği)
    try:
        acc_id = int(acc_id)
        req_cust_id = int(customer_id)
    except Exception:
        return {"ok": False, "error": "invalid_parameters"}

    acc_row = repo.get_account(acc_id)
    if not acc_row:
        return {"ok": False, "error": f"Hesap bulunamadı: {acc_id}"}
    owner_cust_id = int(acc_row.get("customer_id"))
    if owner_cust_id != req_cust_id:
        return {"ok": False, "error": "forbidden", "status_code": 403}

    try:
        lim = int(limit)
    except Exception:
        lim = 50
    if lim <= 0:
        lim = 50
    if lim > 500:
        lim = 500

    f = from_date.strip() if isinstance(from_date, str) and from_date.strip() else None
    t = to_date.strip() if isinstance(to_date, str) and to_date.strip() else None
    if f is None and t is None:
        f, t = "1970-01-01 00:00:00", "9999-12-31 23:59:59"
    elif f is None:
        f = "1970-01-01 00:00:00"
    elif t is None:
        t = "9999-12-31 23:59:59"

    try:
        from datetime import datetime
        def _parse_dt(s: str):
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None
        df = _parse_dt(f) if isinstance(f, str) else None
        dt = _parse_dt(t) if isinstance(t, str) else None
        if df and dt and df > dt:
            f, t = t, f
    except Exception:
        pass

    try:
        rows = repo.list_transactions(
            account_id=acc_id,
            customer_id=req_cust_id,
            from_date=f,
            to_date=t,
            limit=lim,
        )
    except Exception as e:
        return {"ok": False, "error": f"okuma hatası: {e}"}

    try:
        snap = repo.save_transaction_snapshot(
            account_id=acc_id,
            from_date=f,
            to_date=t,
            limit=lim,
            transactions=rows,
        )
    except Exception as e:
        snap = {"error": f"snapshot yazılamadı: {e}", "saved": 0}

    def _fmt_amount(val):
        try:
            v = float(val)
        except Exception:
            return str(val)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    items = []
    for r in rows:
        amt = r.get("amount")
        items.append({
            "id": r.get("txn_id") or r.get("id"),
            "datetime": r.get("txn_date") or r.get("date"),
            "amount": amt,
            "amount_formatted": _fmt_amount(amt) if amt is not None else None,
            "currency": r.get("currency") or "TRY",
            "type": r.get("txn_type") or r.get("type"),
            "description": r.get("description"),
            "balance_after": r.get("balance_after"),
            "account_id": r.get("account_id") or acc_id,
        })

    return {
        "ok": True,
        "account_id": acc_id,
        "range": {"from": f, "to": t},
        "limit": lim,
        "count": len(rows),
        "snapshot": snap,
        "transactions": rows,
        "ui_component": {
            "type": "transactions_list",
            "account_id": acc_id,
            "items": items,
        },
    }


@mcp.tool()
@log_tool
def get_card_info(card_id: int, customer_id: int) -> dict:
    """
    Fetches a financial summary for a credit card, including its limit, current debt, statement date, and due date,
    ensuring the card belongs to the specified customer.

    When to use:
    - This tool is ideal for answering specific questions about a credit card's financial state.
    - Use for queries like: "What is my credit card debt?", "What is my available credit limit?",
      "When is my statement date?", or "What is the payment due date for my card?".

    Args:
        card_id (int): The unique numerical identifier for the credit card.
        customer_id (int): The unique identifier for the customer.

    Returns:
        A dictionary containing the financial summary of the card.
        If the card is not found, the input is invalid, or the card does not belong to the customer, it returns a dictionary with an 'error' key.
    """
    return general_tools.get_card_info(card_id=card_id, customer_id=customer_id)


@mcp.tool()
@log_tool
def list_customer_cards(customer_id: int) -> dict:
    """
    Müşteri kimliğine göre tüm kredi kartlarını listeler.

    Ne zaman kullanılır:
    - "Kart bilgilerimi göster", "Tüm kartlarım", "Kredi kartlarımı listele" gibi genel kart sorguları için kullanılır.
    - Kullanıcı belirli bir kart kimliği belirtmediğinde, ancak kart bilgisi talep ettiğinde bu araç çağrılır.

    Argümanlar:
        customer_id (int): Müşterinin benzersiz sayısal kimliği. Bu bilgi oturumdan alınır, kullanıcıdan istenmez.

    Dönüş:
        Kartların listesini veya bir hata mesajını içeren bir sözlük döndürür.
    """
    return general_tools.list_customer_cards(customer_id=customer_id)


@mcp.tool()
@log_tool
def get_exchange_rates() -> dict:
    """Fetch live FX rates from TCMB (Turkish Central Bank). Updates daily at 15:30 TR time.

    Data source:
        - TCMB XML API: https://www.tcmb.gov.tr/kurlar/today.xml
        - Updates automatically at 15:30 TR time daily (TCMB announcement time)
        - Data is stored in fx_rates table and served from database between updates
        - JPY rates are divided by 100 (TCMB provides rates for 100 JPY)
        - Uses TCMB's official date from XML for updated_at timestamp

    Parameters:
        (none)

    Returns:
        - Success:
            {
              "rates": [
                {
                  "code": "USD/TRY",
                  "buy": 40.9441,
                  "sell": 41.0178,
                  "updated_at": "2025-01-20 15:31:00",
                  "source": "TCMB"
                },
                ...
              ]
            }
            * The list may be empty if TCMB data is unavailable.
        - Error:
            { "error": "<explanatory message>" }

    Use cases:
        - Display current FX quotes in UI.
        - Validate supported currency pair before conversion flows.
        - Show the last refresh timestamp for transparency and troubleshooting.
        - Real-time exchange rate information from official source."""
    return general_tools.get_exchange_rates()


@mcp.tool()
@log_tool
def get_interest_rates() -> dict:
    """Fetch interest rates from `interest_rates`. Read-only; output is normalized for chat/agent flows.

    Data source:
        - Table: interest_rates
        - Columns:
            - product (TEXT): Product key (e.g., "savings", "loan")
            - rate_apy (REAL): Annual Percentage Yield as a decimal (e.g., 0.175 = 17.5%)
            - updated_at (TEXT): "YYYY-MM-DD HH:MM:SS" (or ISO-like timestamp)

    Parameters:
        (none)

    Returns:
        - Success:
            {
              "rates": [
                {
                  "product": "savings",
                  "rate_apy": 0.175,
                  "updated_at": "2025-08-20 12:00:00"
                },
                ...
              ]
            }
            * The list may be empty if the table has no rows.
        - Error:
            { "error": "<explanatory message>" }

    Use cases:
        - Present current deposit/loan rates to users.
        - Quote product pricing in onboarding or simulation flows.
        - Surface last update time for auditability and support."""
    return general_tools.get_interest_rates()

@mcp.tool()
@log_tool
def get_fee(service_code: str) -> dict:
    """
    Tek bir hizmet kodu için ücret bilgisini döndürür.
    Örn kullanım: get_fee("eft"), get_fee("havale")
    """
    return general_tools.get_fee(service_code=service_code)

@mcp.tool()
@log_tool
def get_all_fees() -> dict:
    """
    Tüm ücretleri (fees) eksiksiz döndürür.
    """
    return general_tools.get_all_fees()

@mcp.tool()
@log_tool
def branch_atm_search(city: str, district: str | None = None, type: str | None = None, limit: int = 3, nearby: bool | None = None) -> dict:
    """
    Finds nearby bank branches/ATMs for a given location.

    Reads from the `branch_atm` table and returns a normalized, demo-friendly list.
    Matching is Unicode-aware (casefold) for Turkish (İ/ı). 

    Parameters:
        city (str): Required city name.
        district (Optional[str]): District/neighborhood filter.
        type (Optional[str]): 'atm' or 'branch' (also accepts 'şube'/'sube').
        limit (int): Max results (default 3, capped at 5).

    Returns:
        dict:
        - ok (bool): Success flag.
        - error (str, optional): Short error when ok=False.
        - data (object, when ok=True):
            - query: {city, district|null, type|null}
            - items: [{id, name, type, address, city, district|null,
                        latitude|null, longitude|null, distance_km, hours|null}]
            - count (int): Number of returned items.

    Errors:
        - Missing city → "Lütfen şehir belirtin."
        - No records for given area → short not-found message.
    """
    # güvenlik: limit tavanı
    if not isinstance(limit, int) or limit <= 0:
        limit = 3
    if limit > 5:
        limit = 5
    # türkçe 'şube' desteği
    if type and type.strip().casefold() in ("şube", "sube"):
        type = "branch"
    return general_tools.search(city=city, district=district, type=type, limit=limit, nearby=bool(nearby) if nearby is not None else False)


## Removed: branch_atm_near tool (fallback is handled within search)

@mcp.tool()
@log_tool
def transactions_list(
    account_id: int,
    customer_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50
) -> dict:
    """
    Belirli bir hesap için, isteğe bağlı tarih aralığında işlemleri listeler.
    Tarih verilmezse tüm zamanlar sorgulanır. Erişim için hesap sahibinin customer_id’si
    accounts tablosundan alınır ve repo.list_transactions doğru parametre sırası ile çağrılır.
    Ayrıca snapshot kaydı yapılır.
    """
    # account_id
    try:
        acc_id = int(account_id)
    except Exception:
        return {"error": "account_id geçersiz (int olmalı)"}

    # hesabı ve customer_id’yi al
    acc = repo.get_account(acc_id)
    if not acc:
        return {"error": f"Hesap bulunamadı: {acc_id}"}
    cust_id = int(acc["customer_id"])  # hesap sahibinin customer_id’si
    try:
        req_cust_id = int(customer_id)
    except Exception:
        return {"error": "customer_id geçersiz (int olmalı)"}

    # Güvenlik: İstek yapan müşteri, hesabın sahibi mi?
    if req_cust_id != cust_id:
        return {"error": "forbidden: account does not belong to this customer", "status_code": 403}

    # limit güvenliği
    try:
        lim = int(limit)
    except Exception:
        lim = 50
    if lim <= 0:
        lim = 50
    if lim > 500:
        lim = 500

    # boş tarihleri uç tarihlere çevir ki repo BETWEEN filtresi kaçırmasın
    f = from_date.strip() if isinstance(from_date, str) and from_date.strip() else None
    t = to_date.strip() if isinstance(to_date, str) and to_date.strip() else None
    if f is None and t is None:
        f, t = "1970-01-01 00:00:00", "9999-12-31 23:59:59"
    elif f is None:
        f = "1970-01-01 00:00:00"
    elif t is None:
        t = "9999-12-31 23:59:59"

    # Eğer iki tarih de verildiyse ve sıraları ters ise otomatik düzelt
    try:
        from datetime import datetime
        def _parse_dt(s: str):
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None
        df = _parse_dt(f) if isinstance(f, str) else None
        dt = _parse_dt(t) if isinstance(t, str) else None
        if df and dt and df > dt:
            f, t = t, f
    except Exception:
        pass

    # işlemleri çek  DOĞRU parametre sırası çok önemli
    try:
        rows = repo.list_transactions(
            account_id=acc_id,
            customer_id=req_cust_id,
            from_date=f,
            to_date=t,
            limit=lim,
        )
    except Exception as e:
        return {"error": f"okuma hatası: {e}"}

    # snapshot kaydı
    try:
        snap = repo.save_transaction_snapshot(
            account_id=acc_id,
            from_date=f,  # kullanıcıdan gelen ham değerleri yazalım
            to_date=t,
            limit=lim,
            transactions=rows,
        )
    except Exception as e:
        snap = {"error": f"snapshot yazılamadı: {e}", "saved": 0}

    # UI component için normalize edilmiş öğeler
    def _fmt_amount(val):
        try:
            v = float(val)
        except Exception:
            return str(val)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    items = []
    for r in rows:
        amt = r.get("amount")
        items.append({
            "id": r.get("txn_id") or r.get("id"),
            "datetime": r.get("txn_date") or r.get("date"),
            "amount": amt,
            "amount_formatted": _fmt_amount(amt) if amt is not None else None,
            "currency": r.get("currency") or "TRY",
            "type": r.get("txn_type") or r.get("type"),
            "description": r.get("description"),
            "balance_after": r.get("balance_after"),
            "account_id": r.get("account_id") or acc_id,
        })

    return {
        "ok": True,
        "account_id": acc_id,
        "range": {"from": f, "to": t},
        "limit": lim,
        "count": len(rows),
        "snapshot": snap,
        "transactions": rows,
        "ui_component": {
            "type": "transactions_list",
            "account_id": acc_id,
            "items": items,
        },
    }


# ============ CALCULATION TOOL ==============#
@mcp.tool()
@log_tool
def loan_amortization_schedule(
   principal: float,
    term: int,
    rate: float | None = None,
    method: str = "annuity",
    currency: str | None = None,
    export: str = "none",
) -> Dict[str, Any]:
    """
        S5: Kredi ödeme planı (amortisman tablosu) ve özet değerler.

        Amaç:
            Aylık anüite yöntemiyle (method="annuity") her ay için:
            taksit, faiz, anapara ve kalan borç kalemlerini hesaplar. İsteğe bağlı
            olarak CSV çıktısını base64 olarak döndürür.

        Parametreler:
            principal (float): Anapara ( > 0 )
            currency (str, ops.): Para birimi (örn. "TRY")
            rate (float, ops): Yıllık nominal faiz ( >= 0, örn. 0.35 )
            term (int): Vade (ay, >= 1)
            method (str, ops.): Şimdilik sadece "annuity" desteklenir.
            export (str, ops.): "csv" → `csv_base64` alanı döner; "none" → dönmez.

        Dönüş (başarı):
            {
            "summary": {
                "principal": 200000.0,
                "annual_rate": 0.40,
                "term_months": 24,
                "installment": 12258.91,
                "total_interest": 146113.78,
                "total_payment": 346113.78,
                "method": "annuity_monthly"
            },
            "schedule": [
                {"month":1,"installment":12258.91,"interest":6666.67,"principal":5592.24,"remaining":194407.76},
                ...
            ],
            "ui_component": {...},
            "csv_base64": "..."   # export="csv" ise yer alır
            }

        Hata (ör.):
            {"error": "principal must be > 0"}
            {"error": "only 'annuity' method is supported"}

        Notlar:
            - Son ayda yuvarlama farkı kapatılır (kalan=0’a çekilir).
            - Hesaplama deterministiktir; DB erişimi yoktur.
            - CSV UTF-8, başlıklar: month,installment,interest,principal,remaining
        """
    return calc_tools.loan_amortization_schedule(
        principal=principal,
        rate=rate,
        term=term,
        method=method,
        currency=currency,
        export=export,
    )


@mcp.tool()
@log_tool
def interest_compute(
    type: str,
    principal: float,
    term: float,
    compounding: str,
    rate: float | None = None,
    product: str | None = None,
    term_unit: str = "years",
    currency: str = "TRY",
    schedule: bool = False,
    schedule_limit: int = 24,
    rounding: int | None = None,
) -> dict:
    """
        Belirtilen anapara, faiz oranı veya repo/DB’den alınan oran kullanılarak
        **mevduat getirisi** (deposit) veya **eşit taksitli kredi** (loan) ödemelerini hesaplar.

        type='deposit':
            - Bileşik faiz formülü uygulanır:
              FV = P * (1 + r/m)^(m * t)
              i = dönemsel faiz oranı = yıllık faiz / m
              n = toplam dönem sayısı = m * t
              Getiri = FV - P
            - "continuous" seçilirse sürekli bileşik formülü kullanılır: FV = P * e^(r*t)

        type='loan':
            - Anapara ve faiz üzerinden eşit taksit (annuity) hesaplanır:
              installment = P * [ i(1+i)^n / ((1+i)^n - 1) ], i = r/m
              Her dönemde faiz = kalan_anapara * i
              Anapara ödemesi  = installment - faiz
              Toplam ödeme     = installment * n
              Toplam faiz      = toplam ödeme - P
            - schedule=True verilirse, amortisman tablosu (her dönem için faiz, anapara, bakiye) döndürülür.
              schedule_limit ile tablodaki maksimum satır sayısı belirlenebilir.

        Parametreler:
            type (str)        : "deposit" veya "loan"
            principal (float) : Anapara tutarı (>0)
            term (float)      : Vade (term_unit'e göre yıl ya da ay cinsinden)
            compounding (str) : Faiz dönemi ("annual", "semiannual", "quarterly", "monthly", "weekly", "daily", "continuous")
            rate (float, opt) : Yıllık nominal faiz oranı (örn. 0.30 = %30). None ise repo/DB’den alınır.
            product (str)     : Faiz oranı almak için ürün kodu/anahtar.
            repo (Any, opt)   : Oranı almak için kullanılacak repository nesnesi.
            db_path (str, opt): Oranı DB’den çekmek için kullanılacak path.
            as_of (str, opt)  : Oranın geçerli olduğu tarih ("YYYY-AA-GG").
            schedule (bool)   : True ise, kredi için amortisman tablosu döner.
            schedule_limit(int): Amortisman tablosunda gösterilecek maksimum satır.

        Dönüş:
            dict
              - "summary": Genel özet (FV, toplam ödeme, toplam faiz vb.)
              - "ui_component": UI’de gösterilecek özet
              - "rate_meta": Oran bilgisinin kaynağı
              - (Opsiyonel) "schedule": Amortisman satırları listesi
              - veya {"error": "..."} hata durumunda
    """
    return calc_tools.interest_compute(
        type=type,
        principal=principal,
        term=term,
        compounding=compounding,
        rate=rate,
        product=product,
        term_unit=term_unit,
        currency=currency,
        schedule=schedule,
        schedule_limit=schedule_limit,
        rounding=rounding,
    )
    

@mcp.tool()
@log_tool
def run_roi_simulation(portfolio_name: str, monthly_investment: float, years: int) -> dict:
    """
    Runs a Monte Carlo simulation to project the future value of an investment portfolio.

    When to use:
    - This tool is ideal for answering user questions about long-term investment outcomes.
    - Use for queries like: "If I invest 5000 TL per month in a Balanced Portfolio for 10 years, what could be the result?",
      "Simulate the growth of my portfolio", or "Show me the potential outcomes for the Growth Portfolio".

    Args:
        portfolio_name (str): The name of the portfolio to simulate (e.g., "Dengeli Portföy", "Büyüme Portföyü").
        monthly_investment (float): The amount of money to be invested every month.
        years (int): The total number of years for the investment period.

    Returns:
        A dictionary summarizing the simulation results, including:
        - average_outcome: The mean final balance across all simulations.
        - good_scenario_outcome: The 75th percentile final balance.
        - bad_scenario_outcome: The 25th percentile final balance.
        If the portfolio name is not found, it returns a dictionary with an 'error' key.
    """
    return roi_simulator_tool.run(
        portfolio_name=portfolio_name,
        monthly_investment=monthly_investment,
        years=years
    )



@mcp.tool()
@log_tool
def list_portfolios(portfolio_type: Optional[str] = None) -> dict:
    """
    Lists available investment portfolios. Can be filtered by risk level/type.
    If no type is specified, it returns all portfolios.

    When to use:
    - Use when a user asks about available investment options.
    - For general queries like: "What are my portfolio options?", "List all portfolios".
    - For specific, filtered queries like: "Show me the low-risk portfolios", "List the 'growth' strategies",
      or "dengeli portföyleri göster".

    Args:
        portfolio_type (Optional[str]): The type of portfolio to filter by.
                                        Accepts values like 'düşük', 'korumalı', 'orta', 'dengeli', 'yüksek', 'büyüme'.
                                        This argument is case-insensitive.

    Returns:
        A dictionary containing a list of the requested portfolios.
    """
    return general_tools.list_available_portfolios(portfolio_type=portfolio_type)

# ============ FX CONVERTER TOOL ==============#
@mcp.tool()
@log_tool
def fx_convert(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict:
    """
    Converts a given amount from one currency to another using rates from the database.

    This tool is ideal for answering user questions about currency conversions.
    Use for queries like: "Convert 100 dollars to TRY", "How much is 50 euros in dollars?",
    or "Show me the exchange rate for JPY to TRY".

    Args:
        amount (float): The amount of money to be converted.
        from_currency (str): The currency to convert from (e.g., "USD", "EUR").
        to_currency (str): The currency to convert to (e.g., "TRY", "USD").

    Returns:
        A dictionary summarizing the conversion results, including:
        - amount_from: The original amount.
        - currency_from: The original currency.
        - amount_to: The converted amount.
        - currency_to: The target currency.
        - rate: The exchange rate used for the conversion.
        - summary_text: A human-readable summary of the conversion.
        If the conversion is not possible, it returns a dictionary with an 'error' key.
    """
    return calc_tools.fx_convert(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
    )



# ============ PAYMENT TOOL ==============#
@mcp.tool()
@log_tool
def payment_request(
    from_account: int,
    to_account: int,
    amount: float,
    customer_id: int,
    currency: str = "TRY",
    note: str = "",
    confirm: bool = False,
):
    """
    Own-accounts transfer (preview or commit) with idempotency and safety checks.

    Phases (via `confirm`):
    - False → preview/dry-run: validate and return summary + `suggested_client_ref`
    - True  → commit: re-validate and post transfer atomically

    Params:
    from_account:int, to_account:int, amount:float,
    currency:str="TRY", note:str="", client_ref:str="", confirm:bool=False

    Returns:
    - Preview: { ok, phase:"precheck", suggested_client_ref, preview{...} }
    - Commit:  { ok, phase:"commit", txn{...}, receipt{...} }
    - Error:   { ok:false, error:<code>, ... }

    Rules: accounts exist/active, same currency, sufficient funds, per-txn & daily limits,
    idempotent by `client_ref`. Reads `accounts`; writes `payments` (and optionally `txns`).
    """
    # 1) Her zaman precheck: güvenlik ağımız
    pre = pay.precheck(from_account, to_account, amount, currency, note, customer_id)
    if not pre.get("ok"):
        return [{"type": "json", "json": {"ok": False, "phase": "precheck", **pre}}]

    # 2) Kullanıcıdan onay istenecekse (dry-run cevabı)
    if not confirm:
        preview = {
            "ok": True,
            "phase": "precheck",
            "confirm_required": True,
            "suggested_client_ref": str(customer_id),  # customer_id'yi string olarak kullan
            "preview": {
                "from_account": from_account,
                "to_account": to_account,
                "amount": pre["amount"],
                "currency": pre["currency"],
                "fee": pre["fee"],
                "note": pre.get("note", ""),
                "limits": pre.get("limits", {}),
            },
            "message": (
                f"{from_account} numaralı hesabınızdan --> {to_account} numaralı hesabınıza {amount} {currency} transfer etmek üzeresiniz. İşlem onay penceresi açılıyor..."
            ),
        }
        return [{"type": "json", "json": preview}]

    # 3) Onaylandı → create (idempotent)
    res = pay.create(customer_id, from_account, to_account, amount, currency, note)
    return [{"type": "json", "json": {"phase": "commit", **res}}]


@mcp.tool()
@log_tool
def payment_request_by_type(
    from_account_type: str,
    to_account_type: str,
    amount: float,
    customer_id: int,
    currency: str = "TRY",
    note: str = "",
    confirm: bool = False,
) -> dict:
    """
    Account type ile para transferi (preview veya commit) - hesap numarası belirtmeye gerek yok.

    Kullanıcı dostu account type'lar:
    - "vadeli mevduat" veya "vadeli"
    - "vadesiz mevduat" veya "vadesiz" 
    - "maaş" veya "maaş hesabı"
    - "yatırım" veya "yatırım hesabı"

    Örnek kullanım:
    - "1000 TL vadesizden maaş hesabıma gönder"
    - "500 USD yatırım hesabımdan vadeli mevduata transfer et"
    - "2000 TRY vadesiz mevduattan yatırım hesabıma transfer et"

    Phases (via `confirm`):
    - False → preview/dry-run: validate and return summary
    - True  → commit: re-validate and post transfer atomically

    Returns:
    - Preview: { ok, phase:"precheck", suggested_client_ref, preview{...} }
    - Commit:  { ok, phase:"commit", txn{...}, receipt{...} }
    - Error:   { ok:false, error:<code>, message:<text> }
    """
    # 1) Account type'larından hesap numaralarını bul
    from_result = pay.find_account_by_type(customer_id, from_account_type)
    if not from_result.get("ok"):
        return [{"type": "json", "json": {"ok": False, "phase": "precheck", **from_result}}]
    
    to_result = pay.find_account_by_type(customer_id, to_account_type)
    if not to_result.get("ok"):
        return [{"type": "json", "json": {"ok": False, "phase": "precheck", **to_result}}]
    
    from_account_id = from_result["account"]["account_id"]
    to_account_id = to_result["account"]["account_id"]
    
    # 2) Normal payment işlemini gerçekleştir
    # 1) Her zaman precheck: güvenlik ağımız
    pre = pay.precheck(from_account_id, to_account_id, amount, currency, note, customer_id)
    if not pre.get("ok"):
        return [{"type": "json", "json": {"ok": False, "phase": "precheck", **pre}}]

    # 2) Kullanıcıdan onay istenecekse (dry-run cevabı)
    if not confirm:
        preview = {
            "ok": True,
            "phase": "precheck",
            "confirm_required": True,
            "suggested_client_ref": str(customer_id),
            "preview": {
                "from_account": from_account_id,
                "to_account": to_account_id,
                "amount": pre["amount"],
                "currency": pre["currency"],
                "fee": pre["fee"],
                "note": pre.get("note", ""),
                "limits": pre.get("limits", {}),
            },
            "message": (
                f"{from_account_id} numaralı hesabınızdan --> {to_account_id} numaralı hesabınıza {amount} {currency} transfer etmek üzeresiniz. İşlem onay penceresi açılıyor..."
            ),
        }
        return [{"type": "json", "json": preview}]

    # 3) Onaylandı → create (idempotent)
    res = pay.create(customer_id, from_account_id, to_account_id, amount, currency, note)
    return [{"type": "json", "json": {"phase": "commit", **res}}]


@mcp.tool()
@log_tool
def card_limit_increase_request(
    card_id: int,
    customer_id: int,
    new_limit: float,
    reason: str | None = None,
) -> dict:
    """
    Kart limit artış talebi aracıdır.

    Amaç:
        Belirli bir kredi kartı için müşteri tarafından yapılan limit artış talebini
        alır, basit doğrulama/politika kontrolleri uygular ve sonucu `card_limit_requests`
        tablosuna kaydeder. İlk kayıt durumu varsayılan olarak "received" olur.

    Kullanım Senaryoları:
        - "Kart limitimi 30.000 TL'den 45.000 TL'ye çıkarmak istiyorum."
        - "Limit artış talebim kaydedildi mi?"

    Veri kaynağı:
        - Tablo: card_limit_requests
        - Kolonlar:
            request_id      INTEGER PRIMARY KEY AUTOINCREMENT
            created_at      TEXT (UTC, ISO-8601 "YYYY-MM-DD HH:MM:SS")
            card_id         INTEGER
            customer_id     INTEGER
            requested_limit REAL
            reason          TEXT (opsiyonel)
            status          TEXT ("received" | "approved" | "rejected")

    Parametreler:
        card_id (int): Kartın benzersiz kimliği.
        customer_id (int): Talepte bulunan müşterinin kimliği.
        new_limit (float): Talep edilen yeni kredi limiti (pozitif olmalı).
        reason (str|None): Opsiyonel açıklama veya talep gerekçesi.

    Dönüş:
        - Başarı (örnek):
            {
              "ok": True,
              "request_id": 101,
              "status": "received",
              "card": {
                "card_id": 5,
                "current_limit": 30000.0,
                "current_debt": 12450.0,
                "statement_day": 15,
                "due_day": 25
              },
              "requested_limit": 45000.0,
              "reason": "Gelir artışı",
              "created_at": "2025-09-04 18:00:00",
              "ui_component": {...}
            }
        - Hata:
            { "error": "Yeni limit mevcut limitten büyük olmalı." }
            { "error": "Kart bulunamadı ya da bu müşteriye ait değil." }
    """
    return pay.card_limit_increase_request(
        card_id=card_id,
        customer_id=customer_id,
        new_limit=new_limit,
        reason=reason,
    )


if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8081)
