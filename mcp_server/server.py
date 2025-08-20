# server.py

###############
import os
import sys

from data.sqlite_repo import SQLiteRepository
from fastmcp import FastMCP
from tools.general_tools import GeneralTools

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
###############
from backend.config_local import DB_PATH

# === Initialize MCP server ===
mcp = FastMCP("Fortuna Banking Services")

# BASE_DIR = os.path.dirname(__file__)
# DB_PATH = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))

# === Initialize tool classes ===
repo = SQLiteRepository(db_path=DB_PATH)
account_tools = GeneralTools(repo)


@mcp.tool()
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
    return account_tools.get_balance(account_id)


@mcp.tool()
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
    return account_tools.get_accounts(customer_id)


if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8081)
