# server.py
###############
import os
import sys
from typing import Any, Dict
from .data.sqlite_repo import SQLiteRepository
from fastmcp import FastMCP
from .tools.general_tools import GeneralTools 
from .tools.calculation_tools import CalculationTools
from .tools.roi_simulator_tool import RoiSimulatorTool  

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
roi_simulator_tool = RoiSimulatorTool(repo)




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
def list_recent_transactions(customer_id: int, n: int = 5) -> dict:
    """
    Lists the last 'n' transactions (money in/out) across all accounts for a given customer, sorted by date.

    When to use:
    - Use this to fulfill general requests for account activity, such as "What are my recent transactions?",
      "Show my account statement", or "List my recent expenses".
    - Use it when the user specifies a number of transactions, like "show me my last 3 transactions".
    - Useful for quickly reviewing recent activity to check for suspicious transactions.

    Args:
        customer_id (int): The unique identifier for the customer.
        n (int, optional): The number of transactions to retrieve. Defaults to 5.

    Returns:
        A dictionary containing a list of transaction objects. Returns an empty list if there are no transactions.
    """
    return general_tools.list_recent_transactions(customer_id=customer_id, n=n)

@mcp.tool()
@log_tool
def get_exchange_rates() -> dict:
    """Fetch FX rates from `fx_rates`. Read-only; output is normalized for chat/agent flows.

    Data source:
        - Table: fx_rates
        - Columns:
            - code (TEXT): Currency pair code (e.g., "USD/TRY", "EUR/TRY")
            - buy (REAL): Bank buy price for the pair
            - sell (REAL): Bank sell price for the pair
            - updated_at (TEXT): "YYYY-MM-DD HH:MM:SS" (or ISO-like timestamp)

    Parameters:
        (none)

    Returns:
        - Success:
            {
              "rates": [
                {
                  "code": "USD/TRY",
                  "buy": 32.10,
                  "sell": 32.40,
                  "updated_at": "2025-08-20 12:00:00"
                },
                ...
              ]
            }
            * The list may be empty if the table has no rows.
        - Error:
            { "error": "<explanatory message>" }

    Use cases:
        - Display current FX quotes in UI.
        - Validate supported currency pair before conversion flows.
        - Show the last refresh timestamp for transparency and troubleshooting."""
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
def branch_atm_search(city: str, district: str | None = None, type: str | None = None, limit: int = 3) -> dict:
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
    return general_tools.search(city=city, district=district, type=type, limit=limit)


@mcp.tool()
@log_tool
def loan_amortization_schedule(
    principal: float,
    rate: float,
    term: int,
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
        rate (float): Yıllık nominal faiz ( >= 0, örn. 0.35 )
        term (int): Vade (ay, >= 1)
        method (str, ops.): Şimdilik sadece "annuity" desteklenir.
        currency (str | None, ops.): Görsel amaçlı para birimi etiketi (örn. "TRY")
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
            "currency": "TRY",
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
def transactions_list(
    account_id: int,
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
    cust_id = int(acc["customer_id"])

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

    # işlemleri çek  DOĞRU parametre sırası çok önemli
    try:
        rows = repo.list_transactions(
            account_id=acc_id,
            customer_id=cust_id,
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

    return {
        "account_id": acc_id,
        "range": {"from": f, "to": t},
        "limit": lim,
        "count": len(rows),
        "snapshot": snap,
        "transactions": rows,
    }

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
def list_portfolios() -> dict:
    """
    Lists all available investment portfolios with their names, risk levels, and asset allocations.

    When to use:
    - This tool is perfect for answering user questions about what investment options are available.
    - Use for queries like: "What are my portfolio options?", "Show me the available investment strategies",
      "Which portfolios can I choose from?", or "List all portfolios".
    - This should be used before running a simulation if the user doesn't know which portfolio to choose.

    Args:
        None

    Returns:
        A dictionary containing a list of all available portfolios.
        Each portfolio in the list is a dictionary with 'portfoy_adi', 'risk_seviyesi',
        and 'varlik_dagilimi' keys.
    """
    
    return general_tools.list_available_portfolios()


if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8081)
