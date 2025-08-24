from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, Optional, Tuple

# .env varsa otomatik okur
try:
    from dotenv import load_dotenv  # type:ignore

    load_dotenv()
except Exception:
    pass

import urllib.error
import urllib.request

TIMEOUT_SECONDS: float = 3.0
RETRY_BACKOFF_SECONDS: float = 0.2
GET_ACCOUNT_DETAIL_PATH: str = "/api/fortuna/GetAccountDetail"


class HttpError(Exception):
    def __init__(self, status: int, body: Any):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


class InterApiClient:
    def __init__(self) -> None:
        self.base_url = (os.getenv("INTER_API_BASE_URL") or "").strip().rstrip("/")
        self.app_key = (os.getenv("INTER_API_APP_KEY") or "").strip()
        self.channel = (
            os.getenv("INTER_API_CHANNEL") or "STARTECH"
        ).strip() or "STARTECH"
        self.session_lang = (
            os.getenv("INTER_API_SESSION_LANGUAGE") or "TR"
        ).strip() or "TR"
        if not self.base_url or not self.app_key:
            raise RuntimeError("INTER_API_BASE_URL ve INTER_API_APP_KEY zorunlu.")

    def _http_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _http_post(
        self, url: str, payload: Dict[str, Any], timeout: float = TIMEOUT_SECONDS
    ) -> Tuple[int, Dict[str, Any]]:
        if os.getenv("INTER_DEBUG") == "1":
            print("URL :", url)
            print("PAYL:", json.dumps(payload, ensure_ascii=False))
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers=self._http_headers(), method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if getattr(e, "fp", None) else ""
            raise HttpError(e.code, body)
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {e.reason}")
        try:
            return status, json.loads(body) if body else {}
        except json.JSONDecodeError:
            raise Exception(f"Non-JSON response: {body}")

    def _retry_once(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            if e.status == 429 or 500 <= e.status <= 599:
                time.sleep(RETRY_BACKOFF_SECONDS)
                return func(*args, **kwargs)
            raise

    def get_account_detail(
        self,
        *,
        account_suffix: Optional[int] = None,
        branch_code: Optional[int] = None,
        customer_no: Optional[int] = None,
        iban: Optional[str] = None,
    ) -> Dict[str, Any]:
        """IBAN varsa IBANI, yoksa üçlüyü kullanır. INTER_API_MOCK=1 modunda ise sahte yanıt döner.""" ""
        # MOCK MODE TANIMI
        if os.getenv("INTER_API_MOCK") == "1":
            return {
                "ServiceResponseMessage": {
                    "Data": {
                        "AccountInfo": {
                            "IBANNo": iban or "",
                            "AccountSuffix": account_suffix,
                            "BranchCode": branch_code,
                            "CustomerNo": customer_no,
                            "CurrencyCode": "TRY",
                            "AvailableCreditDepositBalance": 12345.67,
                        }
                    }
                }
            }

        # GERÇEK ÇAĞRI
        if iban:
            payload = self._build_payload_iban(iban)
        else:
            if account_suffix is None or branch_code is None or customer_no is None:
                raise ValueError(
                    "Üçlü mod için account_suffix, branch_code, customer_no girilmesi zorunlu. Alternatif: iban girin."
                )
            payload = self._build_payload_account(
                account_suffix, branch_code, customer_no
            )

        url = f"{self.base_url}{GET_ACCOUNT_DETAIL_PATH}"
        status, data = self._retry_once(self._http_post, url, payload, TIMEOUT_SECONDS)
        if status >= 400:
            raise HttpError(status, data)
        return data

    def _header_block(self) -> Dict[str, Any]:
        return {
            "AppKey": self.app_key,
            "Channel": self.channel,
            "ChannelSessionId": str(uuid.uuid4()),
            "ChannelRequestId": str(uuid.uuid4()),
            "SessionLanguage": self.session_lang,
        }

    def _build_payload_account(
        self, account_suffix: int, branch_code: int, customer_no: int
    ) -> Dict[str, Any]:
        return {
            "Header": self._header_block(),
            "Parameters": [
                {
                    "IBANNo": "",
                    "AccountInfo": {
                        "AccountSuffix": int(account_suffix),
                        "BranchCode": int(branch_code),
                        "CustomerNo": int(customer_no),
                    },
                }
            ],
        }

    def _build_payload_iban(self, iban: str) -> Dict[str, Any]:
        return {
            "Header": self._header_block(),
            "Parameters": [{"IBANNo": iban}],
        }


# OUTPUT YARDIMCI FONKSIYONLARI
def _format_try(n: float) -> str:
    s = f"{n:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pick_display_balance(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Cevaptan AvailableCreditDepositBalance alanını seçer (iki farklı köke toleranslı)."""
    data = raw.get("Data") or raw.get("ServiceResponseMessage", {}).get("Data")
    if not data:
        return {"amount": None, "currency": None, "account": {}}
    acc = data.get("AccountInfo") or {}
    return {
        "amount": acc.get("AvailableCreditDepositBalance"),
        "currency": acc.get("CurrencyCode") or "TRY",
        "account": {
            "AccountSuffix": acc.get("AccountSuffix"),
            "BranchCode": acc.get("BranchCode"),
            "CustomerNo": acc.get("CustomerNo"),
            "IBANNo": acc.get("IBANNo"),
        },
    }


def compose_balance_reply(raw: Dict[str, Any]) -> str:
    sel = pick_display_balance(raw)
    acc = sel.get("account", {})
    label = (
        acc.get("IBANNo")
        or f"{acc.get('BranchCode')}-{acc.get('AccountSuffix')}"
        or "Hesap"
    )
    amount = sel.get("amount")
    cur = sel.get("currency") or "TRY"
    if isinstance(amount, (int, float)):
        return f"{label} için güncel bakiye: {_format_try(float(amount))} {cur}."
    return "Bakiye bilgisi çıkarılamadı."


if __name__ == "__main__":
    # CLI
    import argparse

    parser = argparse.ArgumentParser(
        description="GetAccountDetail - Minimal Account Balance Tool"
    )
    parser.add_argument("--iban", type=str, help="IBANNo")
    parser.add_argument("--suffix", type=int, help="AccountSuffix")
    parser.add_argument("--branch", type=int, help="BranchCode")
    parser.add_argument("--customer", type=int, help="CustomerNo")
    args = parser.parse_args()

    client = InterApiClient()
    raw = client.get_account_detail(
        account_suffix=args.suffix,
        branch_code=args.branch,
        customer_no=args.customer,
        iban=args.iban,
    )
    print(json.dumps(raw, ensure_ascii=False, indent=2))
    print(compose_balance_reply(raw))
