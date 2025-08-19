# server.py
import os
from typing import Optional
from data.sqlite_repo import SQLiteAccountRepository
from fastmcp import FastMCP
from tools.account_balance_tool import AccountBalanceTool

# === Initialize MCP server ===
mcp = FastMCP("Fortuna Banking Services")

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))

# === Initialize tool classes ===
repo = SQLiteAccountRepository(db_path=DB_PATH)
account_tools = AccountBalanceTool(repo)


# === TIER 1: FOUNDATION TOOLS ===
@mcp.tool()
def get_balance(account_id: Optional[int] = None, customer_id: Optional[int] = None) -> dict:
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
    return account_tools.get_balance(account_id=account_id, customer_id=customer_id)



if __name__ == "__main__":
    # Varsayılan port ile başlat (kütüphanen ne destekliyorsa)
    # mcp.run() veya mcp.run(port=8001)
    mcp.run("sse", host="127.0.0.1", port=8081)
