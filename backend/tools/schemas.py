# from __future__ import annotations

# from typing import Any, Dict, List

# TOOL_SPEC_ACCOUNT_BALANCE: Dict[str, Any] = {
#     "name": "AccountBalanceTool_get_balance",
#     "description": "Belirtilen hesap (account_suffix+branch_code+customer_no) veya IBAN ile güncel bakiyeyi döndürür.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "account_suffix": {
#                 "type": "integer",
#                 "description": "Hesap ek numarası (ör. 351)",
#             },
#             "branch_code": {"type": "integer", "description": "Şube kodu (ör. 9142)"},
#             "customer_no": {
#                 "type": "integer",
#                 "description": "Müşteri numarası (ör. 17953063)",
#             },
#             "iban": {
#                 "type": "string",
#                 "description": "TR ile başlayan IBAN (25 karakter, TR + 24)",
#                 "pattern": "^TR[0-9A-Z]{24}$",
#             },
#         },
#         "oneOf": [
#             {"required": ["iban"]},
#             {"required": ["account_suffix", "branch_code", "customer_no"]},
#         ],
#         "additionalProperties": False,
#     },
# }


# def get_tool_catalog() -> Dict[str, List[Dict[str, Any]]]:
#     """LLM adapter'a verilecek tool listesi."""
#     return {"tools": [TOOL_SPEC_ACCOUNT_BALANCE]}
# schemas.py
from __future__ import annotations

from typing import Any, Dict, List

# Single tool that accepts one of three identifier patterns:
#  - account_id (MCP path)
#  - iban
#  - branch+account_suffix+customer_no (triplet, InterAPI path)
TOOL_SPEC_ACCOUNT_BALANCE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "AccountBalanceTool_get_balance",
        "description": "Belirtilen hesap (account_id veya IBAN veya account_suffix+branch_code+customer_no) için güncel bakiyeyi döndür.",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "integer",
                    "description": "MCP üzerinden erişilen tekil hesap kimliği. Örn: 1",
                },
                "iban": {
                    "type": "string",
                    "description": "TR ile başlayan 26 haneli IBAN. Örn: TR120006123451234800123456",
                },
                "account_suffix": {
                    "type": "integer",
                    "description": "Hesap ek numarası (ör. 351)",
                },
                "branch_code": {
                    "type": "integer",
                    "description": "Şube kodu (ör. 9142)",
                },
                "customer_no": {
                    "type": "integer",
                    "description": "Müşteri numarası (ör. 12345678)",
                },
            },
            "oneOf": [
                {"required": ["account_id"]},
                {"required": ["iban"]},
                {"required": ["account_suffix", "branch_code", "customer_no"]},
            ],
            "additionalProperties": False,
        },
    },
}


def get_tool_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """LLM adapter'a verilecek tool listesi (OpenAI-compatible)."""
    # HF/OpenAI-compatible expects tools=[{type:'function', function:{...}}]
    return {"tools": [TOOL_SPEC_ACCOUNT_BALANCE]}
