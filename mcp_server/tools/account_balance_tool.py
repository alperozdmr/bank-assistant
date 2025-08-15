from typing import Any, Dict, Optional


class AccountBalanceTool:
    """
    Hesap bakiyesi ve temel hesap detaylarını döndürür.
    Repo: get_account(account_id: int) -> Optional[dict]
    """

    def __init__(self, repo):
        self.repo = repo

    def get_balance(self, account_id: int) -> Dict[str, Any]:
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
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            return {"error": "account_id geçersiz (int olmalı)"}

        acc: Optional[Dict[str, Any]] = self.repo.get_account(account_id)
        if not acc:
            return {"error": f"Hesap bulunamadı: {account_id}"}

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
