from typing import Any, Dict, Optional, List


class AccountBalanceTool:
    """
    Hesap bakiyesi ve temel hesap detaylarını döndürür.
    Repo: get_account(account_id: int) -> Optional[dict]
    """

    def __init__(self, repo):
        self.repo = repo

    def get_balance(self, account_id: Optional[int] = None, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Repository üzerinden `accounts` tablosunu okuyarak hesap bakiyesini ve
        temel hesap alanlarını döndürür; UI/agent katmanının doğrudan tüketmesi
        için normalize edilmiştir.

        Args:
            account_id (int): Bankacılık sistemindeki benzersiz sayısal hesap kimliği.

        Returns:
            Dict containing:
            - account_id (int): Hesap kimliği
            - customer_id (int): Hesap sahibinin müşteri kimliği
            - account_type (str): checking | savings | credit
            - balance (float): Güncel bakiye (negatif olabilir)
            - currency (str): TRY | USD | EUR
            - status (str): active | frozen | closed
            - created_at (str): "YYYY-MM-DD HH:MM:SS"
            - error (str, optional): Geçersiz giriş ya da kayıt bulunamazsa

        Use cases:
            - Kullanıcının sorduğu hesaba ait bakiyeyi sohbet içinde anında göstermek
            - İşlem başlatmadan önce bakiyeyi doğrulayıp uygun yönlendirme yapmak
            - Hesap kapalı/dondurulmuş ise neden işlem yapılamadığını açıklamak
            - Çok hesaplı müşteride seçili hesabın özetini (type/currency/balance) vermek
            - Overdraft veya düşük bakiye durumunda uyarı mesajı üretmek
            - Döviz bozdurma/kur bilgisi isteyen akışlarda kaynak bakiye verisini sağlamak
        """

        if account_id is None and customer_id is None:
            return {"error": "parametre eksik: account_id veya customer_id verin"}
        
        if account_id is not None:
            try:
                acc_id = int(account_id)
            except (TypeError, ValueError):
                return {"error": "account_id geçersiz (int olmalı)"}

            acc = self.repo.get_account(acc_id)
            if not acc:
                return {"error": f"Hesap bulunamadı: {acc_id}"}

            # İstediğin alanları doğrudan döndür (UI/agent rahat işler)
            return {
                "account_id": acc["account_id"],
                "customer_id": acc["customer_id"],
                "account_type": acc["account_type"],
                "balance": acc["balance"],
                "currency": acc["currency"],
                "status": acc["status"],
                "created_at": acc["created_at"],
            }
    
        try:
            cid = int(customer_id)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return {"error": "customer_id geçersiz (int olmalı)"}

        rows = self.repo.get_accounts_by_customer(cid)
        if not rows:
            return {"error": f"Müşteri bulunamadı veya hesap yok: {cid}"}
        if len(rows) == 1:
            acc = rows[0]
            return {
                "account_id": acc["account_id"],
                "customer_id": acc["customer_id"],
                "account_type": acc["account_type"],
                "balance": acc["balance"],
                "currency": acc["currency"],
                "status": acc["status"],
                "created_at": acc["created_at"],
            }
        # birden fazla hesap
        def norm(a: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "account_id": a["account_id"],
                "account_type": a["account_type"],
                "balance": a["balance"],
                "currency": a["currency"],
                "status": a["status"],
                "created_at": a["created_at"],
            }
        return {"customer_id": cid, "accounts": [norm(a) for a in rows]}
