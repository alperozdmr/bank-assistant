# server.py
###############
import os
import sys

from .data.sqlite_repo import SQLiteRepository
from fastmcp import FastMCP
from .tools.general_tools import GeneralTools 

###############

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.config_local import DB_PATH  ## bu import yukarıdaki kodun altında olmak zorunda yoksa çalışmaz
from common.mcp_decorators import log_tool


# === Initialize MCP server ===
mcp = FastMCP("Fortuna Banking Services")

# === Initialize tool classes ===
repo = SQLiteRepository(db_path=DB_PATH)
general_tools = GeneralTools(repo)
print(f"[MCP] Using DB: {repo.db_path}")


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
def list_fees(limit: int = 50) -> dict:
    """
    Retrieves a list of service fees and commission rates.

    This tool queries the `fees` table and returns normalized fee records,
    including fee codes, descriptions, and amounts. It is read-only and
    intended for display and selection in chat/agent flows.

    Parameters:
        limit (int): Maximum number of fee records to return. Defaults to 50,
        capped at 200.

    Returns:
        A dictionary containing:
        - fee_code (str): Unique identifier for the fee
        - description (str): Human-readable description of the fee
        - amount (float): Monetary value of the fee
        - currency (str): Currency code (TRY | USD | EUR)
        - category (str): Fee category (transfer | card | account | other)
        If no fees are found or the input is invalid, returns:
        - error (str) with an explanatory message
    """
    if not isinstance(limit, int) or limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200
    return general_tools.list_fees(limit=limit)


@mcp.tool()
@log_tool
def list_cards(customer_id: int) -> dict:
    """
    Retrieves all cards belonging to a specific customer.

    This tool queries the `cards` table and returns normalized card records,
    including limits, balances, and card types. It is read-only and intended
    for overview and display in chat/agent flows.

    Parameters:
        customer_id (int): Unique customer identifier in the banking system.

    Returns:
        A dictionary containing one or more card records with:
        - card_id (int): Unique identifier for the card
        - card_number (str, masked): Masked card number (e.g., "****1234")
        - card_type (credit | debit | prepaid)
        - limit (float): Card limit (if applicable)
        - balance (float): Current balance/usage
        - status (active | frozen | closed)
        - expiry_date (ISO-8601 string: "YYYY-MM-DD")
        If the customer has no cards or the input is invalid, returns:
        - error (str) with an explanatory message
    """
    return general_tools.list_cards(customer_id=customer_id)


@mcp.tool()
@log_tool
def get_primary_card_summary(customer_id: int) -> dict:
    """
    Retrieves a summary of the customer's primary card.

    This tool queries the `cards` table and selects the primary card record,
    returning essential attributes for quick display. It is read-only and
    intended for summary views in chat/agent flows.

    Parameters:
        customer_id (int): Unique customer identifier in the banking system.

    Returns:
        A dictionary containing the primary card summary with:
        - card_id (int): Unique identifier for the card
        - card_number (str, masked): Masked card number (e.g., "****5678")
        - card_type (credit | debit | prepaid)
        - limit (float): Card limit (if applicable)
        - balance (float): Current balance/usage
        - due_date (ISO-8601 string: "YYYY-MM-DD") for credit cards
        - status (active | frozen | closed)
        If no primary card exists or the input is invalid, returns:
        - error (str) with an explanatory message
    """
    return general_tools.get_primary_card_summary(customer_id=customer_id)


@mcp.tool()
@log_tool
def get_fee(service_code: str) -> dict:
    """
    Retrieves the details of a specific service fee.

    This tool queries the `fees` table and returns a single fee record,
    including amount, currency, and description. It is read-only and
    intended for validation or explanation in chat/agent flows.

    Parameters:
        service_code (str): Unique service/fee identifier.

    Returns:
        A dictionary containing:
        - fee_code (str): Unique identifier for the fee
        - description (str): Human-readable description of the fee
        - amount (float): Monetary value of the fee
        - currency (str): Currency code (TRY | USD | EUR)
        - category (str): Fee category (transfer | card | account | other)
        If the fee is not found or the input is invalid, returns:
        - error (str) with an explanatory message
    """
    return general_tools.get_fee(service_code=service_code)


if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8082)
