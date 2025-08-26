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
#Balance tool’u
TOOL_SPEC_GET_BALANCE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_balance",  # MCP tool name
        "description": "Verilen account_id için güncel bakiyeyi döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "integer",
                    "description": "Hesap kimliği (örn: 1)",
                },
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
}

#account tool’u
TOOL_SPEC_GET_ACCOUNTS: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_accounts",
        "description": "customer_id ile müşterinin hesap(lar)ını döndürür. Tek hesap ise özet nesne, çok hesap ise liste döner.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Müşteri kimliği (örn: 7)",
                },
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
}

#card tool’u
TOOL_SPEC_GET_CARD_INFO: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_card_info",
        "description": "card_id ile kart özetini (limit, borç, kesim/son ödeme günü) döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "card_id": {
                    "type": "integer",
                    "description": "Kart kimliği (örn: 101)",
                },
            },
            "required": ["card_id"],
            "additionalProperties": False,
        },
    },
}

#Son işlemler tool’u
TOOL_SPEC_LIST_RECENT_TXNS: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_recent_transactions",
        "description": "Bir müşterinin tüm hesaplarındaki son n işlemi döndürür (varsayılan n=5).",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Müşteri kimliği",
                },
                "n": {
                    "type": "integer",
                    "description": "Döndürülecek işlem adedi (varsayılan 5)",
                    "minimum": 1,
                },
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
}

# Döviz oranları tool’u
TOOL_SPEC_GET_EXCHANGE_RATES: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_exchange_rates",
        "description": "fx_rates tablosundan güncel döviz kurlarını döndürür.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}

# faiz oranları tool’u
TOOL_SPEC_GET_INTEREST_RATES: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_interest_rates",
        "description": "interest_rates tablosundan güncel faiz oranlarını döndürür.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}

# Tüm ücretler listesi tool’u
TOOL_SPEC_LIST_FEES = {
    "type": "function",
    "function": {
        "name": "list_fees",
        "description": "fees tablosundaki tüm ücretleri (opsiyonel limit ile) döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            "additionalProperties": False,
        },
    },
}

# kart listesi tool’u
TOOL_SPEC_LIST_CARDS = {
    "type": "function",
    "function": {
        "name": "list_cards",
        "description": "Müşterinin kartlarını listeler.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "Müşteri kimliği"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
}

# default kart tool’u
TOOL_SPEC_PRIMARY_CARD_SUMMARY = {
    "type": "function",
    "function": {
        "name": "get_primary_card_summary",
        "description": "Tek kart ise borç/özet, çok kart ise liste döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "Müşteri kimliği"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
}

# Ücret bilgisi tool’u
TOOL_SPEC_GET_FEE: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_fee",
        "description": (
            "Tek bir hizmet kodunun ücretini döndürür. "
            "service_code örnekleri: eft, havale, fast, swift, atm_withdrawal, foreign_exchange, "
            "account_opening, account_maintenance, account_statement, card_replacement, credit_check, overdraft."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_code": {
                    "type": "string",
                    "description": "Hizmet kodu (küçük harf, boşluksuz; örn: 'eft', 'havale', 'fast').",
                },
            },
            "required": ["service_code"],
            "additionalProperties": False,
        },
    },
}


# ATM / Şube arama tool’u
TOOL_SPEC_BRANCH_ATM_SEARCH: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "branch_atm_search",
        "description": "Belirtilen şehir (ve opsiyonel ilçe) için ATM veya şube bilgilerini döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Şehir adı (örn: İstanbul)",
                },
                "district": {
                    "type": "string",
                    "description": "İlçe adı (örn: Kadıköy)",
                },
                "type": {
                    "type": "string",
                    "enum": ["atm", "branch"],
                    "description": "Aranacak nesne türü: 'atm' veya 'branch'. Varsayılan: atm",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maksimum döndürülecek sonuç sayısı. Varsayılan: 3",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5
                },
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}



def get_tool_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """LLM adapter'a verilecek tool listesi (OpenAI-compatible)."""
    # HF/OpenAI-compatible expects tools=[{type:'function', function:{...}}]
    return {
        "tools": [
            TOOL_SPEC_GET_BALANCE,
            TOOL_SPEC_GET_ACCOUNTS,
            TOOL_SPEC_GET_CARD_INFO,
            TOOL_SPEC_LIST_RECENT_TXNS,
            TOOL_SPEC_GET_EXCHANGE_RATES,
            TOOL_SPEC_GET_INTEREST_RATES,
            TOOL_SPEC_GET_FEE,
            TOOL_SPEC_BRANCH_ATM_SEARCH,
            TOOL_SPEC_LIST_FEES,
            TOOL_SPEC_LIST_CARDS,
            TOOL_SPEC_PRIMARY_CARD_SUMMARY,
        ]
    }
