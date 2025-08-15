from __future__ import annotations

from typing import Any, Dict, List

TOOL_SPEC_ACCOUNT_BALANCE: Dict[str, Any] = {
    "name": "AccountBalanceTool_get_balance",
    "description": "Belirtilen hesap (account_suffix+branch_code+customer_no) veya IBAN ile güncel bakiyeyi döndürür.",
    "parameters": {
        "type": "object",
        "properties": {
            "account_suffix": {
                "type": "integer",
                "description": "Hesap ek numarası (ör. 351)",
            },
            "branch_code": {"type": "integer", "description": "Şube kodu (ör. 9142)"},
            "customer_no": {
                "type": "integer",
                "description": "Müşteri numarası (ör. 17953063)",
            },
            "iban": {
                "type": "string",
                "description": "TR ile başlayan IBAN (25 karakter, TR + 24)",
                "pattern": "^TR[0-9A-Z]{24}$",
            },
        },
        "oneOf": [
            {"required": ["iban"]},
            {"required": ["account_suffix", "branch_code", "customer_no"]},
        ],
        "additionalProperties": False,
    },
}


def get_tool_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """LLM adapter'a verilecek tool listesi."""
    return {"tools": [TOOL_SPEC_ACCOUNT_BALANCE]}
