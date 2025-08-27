# server.py
###############
import os
import sys
from typing import Any, Dict
from .data.sqlite_repo import SQLiteRepository
from fastmcp import FastMCP
from .tools.general_tools import GeneralTools 
from .tools.calculation_tools import CalculationTools

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
calc_tools = CalculationTools()


@mcp.tool()
@log_tool
def get_balance(account_id: int) -> dict:
    """
    Retrieves current balance information for a specific account.

    This tool reads from the `accounts` table and returns normalized account data
    including monetary balance with currency and core account attributes. It is
    read-only and intended for validation and display in chat/agent flows.

    Parameters:
        account_id (int): Unique account identifier in the banking system.

    Returns:
        Account record containing:
        - account_id (int) and customer_id (int)
        - account_type (checking | savings | credit)
        - balance (float) and currency (TRY | USD | EUR)
        - status (active | frozen | closed)
        - created_at (ISO-8601 string: "YYYY-MM-DD HH:MM:SS")
        If the account is not found or the input is invalid, returns:
        - error (str) with an explanatory message
    """
    return general_tools.get_balance(account_id)


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
def get_card_info(card_id: int) -> dict:
    """
    Fetches a financial summary for a credit card, including its limit, current debt, statement date, and due date.

    When to use:
    - This tool is ideal for answering specific questions about a credit card's financial state.
    - Use for queries like: "What is my credit card debt?", "What is my available credit limit?",
      "When is my statement date?", or "What is the payment due date for my card?".

    Args:
        card_id (int): The unique numerical identifier for the credit card.

    Returns:
        A dictionary containing the financial summary of the card.
        If the card is not found, it returns a dictionary with an 'error' key.
    """
    return general_tools.get_card_info(card_id=card_id)


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

    Veri kaynağı:
        - transactions tablosundan okuma yapar.
        - İşlem anlık görüntülerini txn_snapshots tablosuna yazar.

    Parametreler:
        account_id (int): Zorunlu. Benzersiz hesap kimliği.
        from_date (str, optional): Alt tarih sınırı ("YYYY-AA-GG" veya "YYYY-AA-GG SS:DD:SS").
        to_date (str, optional): Üst tarih sınırı ("YYYY-AA-GG" veya "YYYY-AA-GG SS:DD:SS").
        limit (int, optional): Maksimum kayıt sayısı (varsayılan 50, en fazla 500).

    Dönen değer:
        dict türünde:
        - account_id (int)
        - range {from, to}
        - limit (int)
        - count (int)
        - snapshot (object: snapshot bilgisi veya hata)
        - transactions (işlem kayıtları listesi) VEYA {"error": str} (hata durumunda)
    """

    return general_tools.transactions_list(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )

if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8081)
