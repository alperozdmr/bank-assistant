from typing import Any, Dict


class GeneralTools:
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

        if account_id is None:
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

    def get_accounts(self, customer_id: int) -> Dict[str, Any]:
        """
        Müşteri kimliğine göre `accounts` tablosunu sorgulayarak müşterinin sahip olduğu
        hesap(ları) döndürür. Girdi doğrulaması yapar ve sonuç nesnesini UI/agent
        katmanının doğrudan tüketebilmesi için normalize eder. Kayıt bulunamazsa ya da
        geçersiz girdi varsa hata bilgisini döndürür.

        Args:
            customer_id (int): Bankacılık sistemindeki müşterinin sayısal kimliği.

        Returns:
            Dict containing (duruma göre):
            - Hata durumu:
                - error (str): "customer_id geçersiz (int olmalı)" veya
                               "Müşteri bulunamadı veya hesap yok: <id>"
            - Tek hesap bulunduysa (özet nesne):
                - account_id (int): Hesap kimliği
                - customer_id (int): Müşteri kimliği
                - account_type (str): checking | savings | credit
                - balance (float): Güncel bakiye
                - currency (str): TRY | USD | EUR
                - status (str): active | frozen | closed
                - created_at (str): "YYYY-MM-DD HH:MM:SS"
            - Birden fazla hesap bulunduysa (liste yapısı):
                - customer_id (int): Müşteri kimliği
                - accounts (List[Dict]): Her bir öğe için:
                    - account_id (int)
                    - account_type (str)
                    - balance (float)
                    - currency (str)
                    - status (str)
                    - created_at (str)

        Use cases:
            - Müşterinin tüm hesaplarını listeleyip kullanıcıya seçim yaptırmak
            - Çok hesaplı müşteride hızlı özet (type/currency/balance) göstermek
            - İşlem akışında uygun kaynağı (TRY, USD vb.) belirlemek
            - Kapalı/dondurulmuş hesapları UI’da filtrelemek veya uyarı vermek
            - Sonraki adımda bakiye/doğrulama gerektiren tool’lara girdi sağlamak
        """
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

    def get_card_info(self, card_id: int) -> Dict[str, Any]:
        """
        Kredi kartı detaylarını (limit, borç, ödeme günleri) döndürür.

        Args:
            card_id (int): Bankacılık sistemindeki benzersiz sayısal kart kimliği.

        Returns:
            Dict containing card details or an error message.
        """
        if card_id is None:
            return {"error": "parametre eksik: card_id verin"}

        try:
            c_id = int(card_id)
        except (TypeError, ValueError):
            return {"error": "card_id geçersiz (int olmalı)"}

        card_data = self.repo.get_card_details(c_id)

        if not card_data:
            return {"error": f"Kart bulunamadı: {c_id}"}

        return {
            "card_id": card_data["card_id"],
            "limit": card_data["credit_limit"],
            "borc": card_data["current_debt"],
            "kesim_tarihi": card_data["statement_day"],
            "son_odeme_tarihi": card_data["due_day"],
        }

    def list_recent_transactions(self, customer_id: int, n: int = 5) -> Dict[str, Any]:
        """
        Bir müşterinin tüm hesaplarındaki son 'n' adet işlemi listeler.

        Args:
            customer_id (int): Müşteri kimliği.
            n (int): Listelenecek işlem sayısı (varsayılan: 5).

        Returns:
            A dictionary containing a list of transactions or an error.
        """
        if customer_id is None:
            return {"error": "parametre eksik: customer_id verin"}

        try:
            c_id = int(customer_id)
        except (TypeError, ValueError):
            return {"error": "customer_id geçersiz (int olmalı)"}

        transactions = self.repo.get_transactions_by_customer(c_id, n)

        if not transactions:
            return {
                "customer_id": c_id,
                "transactions": [],
                "message": "Müşteriye ait son işlem bulunamadı.",
            }

        return {"customer_id": c_id, "transactions": transactions}
