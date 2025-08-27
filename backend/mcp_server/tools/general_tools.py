from __future__ import annotations
from typing import Any, Dict, List, Optional
import math
import hashlib
import logging as log
import json

class GeneralTools:
    """
    Hesap bakiyesi ve temel hesap detaylarını döndürür.
    Repo: get_account(account_id: int) -> Optional[dict]
    """

    def __init__(self, repo):
        self.repo = repo

    def get_balance(self, account_id: int, customer_id: int) -> Dict[str, Any]:
        """
        Repository üzerinden `accounts` tablosunu okuyarak hesap bakiyesini ve
        temel hesap alanlarını döndürür; UI/agent katmanının doğrudan tüketmesi
        için normalize edilmiştir.

        Args:
            account_id (int): Bankacılık sistemindeki benzersiz sayısal hesap kimliği.
            customer_id (int): Hesap sahibinin müşteri kimliği.

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
            - ui_component (dict): Frontend için BalanceCard component data

        Use cases:
            - Kullanıcının sorduğu hesaba ait bakiyeyi sohbet içinde anında göstermek
            - İşlem başlatmadan önce bakiyeyi doğrulayıp uygun yönlendirme yapmak
            - Hesap kapalı/dondurulmuş ise neden işlem yapılamadığını açıklamak
            - Çok hesaplı müşteride seçili hesabın özetini (type/currency/balance) vermek
            - Overdraft veya düşük bakiye durumunda uyarı mesajı üretmek
            - Döviz bozdurma/kur bilgisi isteyen akışlarda kaynak bakiye verisini sağlamak
        """

        if account_id is None or customer_id is None:
            return {"error": "parametre eksik: account_id veya customer_id verin"}

        if account_id is not None:
            try:
                acc_id = int(account_id)
                cust_id = int(customer_id)
            except (TypeError, ValueError):
                return {"error": "account_id veya customer_id geçersiz (int olmalı)"}

            acc = self.repo.get_account(acc_id)
            if not acc:
                return {"error": f"Hesap bulunamadı: {acc_id}"}
            
            if acc["customer_id"] != cust_id:
                return {"error": "Hesap bilgisi bulunamadı."} # Müşteri kendine ait olmayan hesap sorduğunda

            # Format balance for display
            balance_formatted = f"{float(acc['balance']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # İstediğin alanları doğrudan döndür (UI/agent rahat işler)
            result = {
                "account_id": acc["account_id"],
                "customer_id": acc["customer_id"],
                "account_type": acc["account_type"],
                "balance": acc["balance"],
                "currency": acc["currency"],
                "status": acc["status"],
                "created_at": acc["created_at"],
                # Frontend BalanceCard component için structured data
                "ui_component": {
                    "type": "balance_card",
                    "card_type": "single_account",
                    "account_id": acc["account_id"],
                    "account_type": acc["account_type"],
                    "balance": balance_formatted,
                    "currency": acc["currency"],
                    "status": acc["status"]
                }
            }
            return result

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
            # Format balance for display
            balance_formatted = f"{float(acc['balance']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            return {
                "account_id": acc["account_id"],
                "customer_id": acc["customer_id"],
                "account_type": acc["account_type"],
                "balance": acc["balance"],
                "currency": acc["currency"],
                "status": acc["status"],
                "created_at": acc["created_at"],
                # Frontend BalanceCard component için structured data
                "ui_component": {
                    "type": "balance_card",
                    "card_type": "single_account",
                    "account_id": acc["account_id"],
                    "account_type": acc["account_type"],
                    "balance": balance_formatted,
                    "currency": acc["currency"],
                    "status": acc["status"]
                }
            }

        # birden fazla hesap
        def norm(a: Dict[str, Any]) -> Dict[str, Any]:
            balance_formatted = f"{float(a['balance']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return {
                "account_id": a["account_id"],
                "account_type": a["account_type"],
                "balance": a["balance"],
                "balance_formatted": balance_formatted,
                "currency": a["currency"],
                "status": a["status"],
                "created_at": a["created_at"],
            }

        normalized_accounts = [norm(a) for a in rows]
        
        return {
            "customer_id": cid, 
            "accounts": normalized_accounts,
            # Frontend BalanceCard component için structured data
            "ui_component": {
                "type": "balance_card",
                "card_type": "multiple_accounts",
                "total_count": len(normalized_accounts),
                "accounts": [
                    {
                        "account_id": acc["account_id"],
                        "account_type": acc["account_type"],
                        "balance": acc["balance_formatted"],
                        "currency": acc["currency"],
                        "status": acc["status"]
                    }
                    for acc in normalized_accounts
                ]
            }
        }

    def list_customer_cards(self, customer_id: int) -> Dict[str, Any]:
        """
        Müşteri kimliğine göre `cards` tablosunu sorgulayarak müşterinin sahip olduğu
        tüm kartları döndürür. Girdi doğrulaması yapar ve sonuç nesnesini UI/agent
        katmanının doğrudan tüketebilmesi için normalize eder. Kayıt bulunamazsa ya da
        geçersiz girdi varsa hata bilgisini döndürür.

        Args:
            customer_id (int): Bankacılık sistemindeki müşterinin sayısal kimliği.

        Returns:
            Dict containing (duruma göre):
            - Hata durumu:
                - error (str): "customer_id geçersiz (int olmalı)" veya
                               "Müşteri bulunamadı veya kart yok: <id>"
            - Kartlar bulunduysa (liste yapısı):
                - customer_id (int): Müşteri kimliği
                - cards (List[Dict]): Her bir öğe için:
                    - card_id (int)
                    - credit_limit (float)
                    - current_debt (float)
                    - statement_day (int)
                    - due_day (int)

        Use cases:
            - Müşterinin tüm kartlarını listeleyip kullanıcıya seçim yaptırmak
            - Kartları UI’da filtrelemek veya uyarı vermek
            - Sonraki adımda kart bilgisi/doğrulama gerektiren tool’lara girdi sağlamak
        """
        try:
            cid = int(customer_id)
        except (TypeError, ValueError):
            return {"error": "customer_id geçersiz (int olmalı)"}

        rows = self.repo.get_all_cards_for_customer(cid)
        if not rows:
            return {"error": f"Müşteri bulunamadı veya kart yok: {cid}"}

        def norm_card(c: Dict[str, Any]) -> Dict[str, Any]:
            limit_formatted = f"{float(c['credit_limit']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            borc_formatted = f"{float(c['current_debt']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            available_formatted = f"{float(c['credit_limit'] - c['current_debt']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            return {
                "card_id": c["card_id"],
                "credit_limit": c["credit_limit"],
                "current_debt": c["current_debt"],
                "statement_day": c["statement_day"],
                "due_day": c["due_day"],
                "limit_formatted": limit_formatted,
                "borc_formatted": borc_formatted,
                "available_formatted": available_formatted,
            }

        normalized_cards = [norm_card(c) for c in rows]

        return {
            "customer_id": cid,
            "cards": normalized_cards,
            "ui_component": {
                "type": "card_info_card",
                "card_type": "multiple_cards",
                "total_count": len(normalized_cards),
                "cards": [
                    {
                        "card_id": card["card_id"],
                        "limit": card["credit_limit"],
                        "borc": card["current_debt"],
                        "kesim_tarihi": card["statement_day"],
                        "son_odeme_tarihi": card["due_day"],
                    }
                    for card in normalized_cards
                ]
            }
        }

    def get_card_info(self, card_id: int, customer_id: int) -> Dict[str, Any]:
        """
        Kredi kartı detaylarını (limit, borç, ödeme günleri) döndürür ve müşteri kimliği ile doğrular.

        Args:
            card_id (int): Bankacılık sistemindeki benzersiz sayısal kart kimliği.
            customer_id (int): Kart sahibinin müşteri kimliği.

        Returns:
            Dict containing card details or an error message.
        """
        if card_id is None or customer_id is None:
            return {"error": "parametre eksik: card_id ve customer_id verin"}

        try:
            c_id = int(card_id)
            cust_id = int(customer_id)
        except (TypeError, ValueError):
            return {"error": "card_id veya customer_id geçersiz (int olmalı)"}

        card_data = self.repo.get_card_details(c_id, cust_id)

        if not card_data:
            return {"error": f"Kart bulunamadı veya bu müşteriye ait değil: {c_id}"}

        # Format currency values for display
        limit_formatted = f"{float(card_data['credit_limit']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        borc_formatted = f"{float(card_data['current_debt']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        available_formatted = f"{float(card_data['credit_limit'] - card_data['current_debt']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return {
            "card_id": card_data["card_id"],
            "limit": card_data["credit_limit"],
            "borc": card_data["current_debt"],
            "kesim_tarihi": card_data["statement_day"],
            "son_odeme_tarihi": card_data["due_day"],
            # Frontend CardInfoCard component için structured data
            "ui_component": {
                "type": "card_info_card",
                "card_id": card_data["card_id"],
                "limit": card_data["credit_limit"],
                "borc": card_data["current_debt"],
                "kesim_tarihi": card_data["statement_day"],
                "son_odeme_tarihi": card_data["due_day"]
            }
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
    
    """
    Döviz kurları ve faiz oranlarını döndürür.
    Repo: exchange_rates, interest_rates tablolarını sorgular.
    """

    def get_exchange_rates(self) -> Dict[str, Any]:
        """
        Repo içindeki hazır SQL/okuma fonksiyonunu kullanarak döviz kurlarını döndürür.
        Beklenen repo metodu: get_fx_rates() veya get_exchange_rates()
        Dönüş: {"rates": [ {...}, ... ]} veya {"rates": []} / {"error": "..."}
        """
        try:
            if hasattr(self.repo, "get_fx_rates") and callable(getattr(self.repo, "get_fx_rates")):
                rows = self.repo.get_fx_rates()
            elif hasattr(self.repo, "get_exchange_rates") and callable(getattr(self.repo, "get_exchange_rates")):
                rows = self.repo.get_exchange_rates()
            else:
                return {"error": "Repository bu okumayı desteklemiyor (get_fx_rates() ya da get_exchange_rates() bulunamadı)."}

            rows = rows or []
            # sqlite3.Row veya dict olabilir → dict'e çevir
            try:
                rows = [dict(r) for r in rows]
            except Exception:
                pass  # zaten dict listesi ise

            result = {"rates": rows}
            
            # Frontend ExchangeRatesCard component için structured data
            if rows:
                result["ui_component"] = {
                    "type": "exchange_rates_card",
                    "rates": rows
                }

            return result
        except Exception as e:
            return {"error": f"Okuma hatası: {e}"}

    def get_interest_rates(self) -> Dict[str, Any]:
        """
        Repo içindeki hazır SQL/okuma fonksiyonunu kullanarak faiz oranlarını döndürür.
        Beklenen repo metodu: get_interest_rates()
        Dönüş: {"rates": [ {...}, ... ]} veya {"rates": []} / {"error": "..."}
        """
        try:
            if hasattr(self.repo, "get_interest_rates") and callable(getattr(self.repo, "get_interest_rates")):
                rows = self.repo.get_interest_rates()
            else:
                return {"error": "Repository bu okumayı desteklemiyor (get_interest_rates() bulunamadı)."}

            rows = rows or []
            try:
                rows = [dict(r) for r in rows]
            except Exception:
                pass

            result = {"rates": rows}
            
            # Frontend InterestRatesCard component için structured data
            if rows:
                result["ui_component"] = {
                    "type": "interest_rates_card",
                    "rates": rows
                }

            return result
        except Exception as e:
            return {"error": f"Okuma hatası: {e}"}
        
    def get_fee(self, service_code: str) -> Dict[str, Any]:
        """
        Ücret tablosundan tek bir hizmet kodunun (service_code) JSON ücretlerini döndürür.
        Örn: "eft", "havale", "fast", "kredi_karti_yillik"
        """
        if not service_code or not isinstance(service_code, str):
            return {"error": "service_code gerekli"}
        row = self.repo.get_fee(service_code.strip())
        if not row:
            try:
                codes = [r["service_code"] for r in self.repo.list_fees()]
            except Exception:
                codes = []
            return {"error": f"Ücret bulunamadı: {service_code}", "available_codes": codes}

        pricing = row.get("pricing_json")
        try:
            pricing = json.loads(pricing) if isinstance(pricing, str) else pricing
        except Exception:
            pricing = {"raw": row.get("pricing_json")}

        result = {
            "service_code": row["service_code"],
            "description": row["description"],
            "pricing": pricing,          # JSON tablo olduğu gibi döner 
            "updated_at": row["updated_at"],
        }
        
        # Frontend FeesCard component için structured data
        result["ui_component"] = {
            "type": "fees_card",
            "service_code": row["service_code"],
            "description": row["description"],
            "pricing": pricing,
            "updated_at": row["updated_at"]
        }
        
        return result
    
    def search(self, city: str, district: Optional[str] = None,
               type: Optional[str] = None, limit: int = 3) -> Dict[str, Any]:
        
        """ 
        Belirtilen şehir (ve opsiyonel ilçe) için ATM veya şube bilgilerini döndürür.
        Repository üzerinden `branch_atm` tablosunu okuyarak belirli bir şehir/ilçe
        için şube ve ATM bilgilerini döndürür; UI veya MCP agent katmanının 
        doğrudan tüketmesi için normalize edilmiştir.

        Args:

            city (str): Şehir adı (örn: İstanbul)
            district (str, optional): İlçe adı (örn: Kadıköy)
            type (str, optional): 'atm' veya 'branch' (şube). Belirtilmezse tüm türler.
            limit (int, optional): Maksimum döndürülecek sonuç sayısı. Varsayılan 3.
            Dönen sonuçlar minimum 1, maksimum 5 ile sınırlandırılır.

            
        Returns:

            Dict containing:
            -  id(int): Kayıt kimliği
            -  name (str): Şube/ATM adı
            -  type (str): "atm" | "branch"
            -  address (str): Açık adres
            -  city (str): Şehir adı
            -  district (str|null): İlçe adı
            -  latitude (float|null): Enlem
            -  longitude (float|null): Boylam

        Use cases:
            - Kullanıcının belirttiği şehirdeki ATM/şube listesini anında göstermek
            - Şube/ATM arama ve yakınlardaki seçenekleri sunmak
            - Tür (ATM/şube) ve konuma göre filtreleme yapmak 
            - Repo'dan çekilen satır sayısı, mesafe veya diğer filtrelemeler için
              docstring limitinden daha fazla olabilir.           
"""
      
        city = city.strip() if city is not None else None
        district =district.strip() if district is not None else None
        if not city:
            return {"ok": False, "error": "Lütfen şehir belirtin.", "data": {"query": {"city": city, "district": district}}}

        # Biraz fazla satır al, sonra mesafeye göre kırp
        rows = self.repo.find_branch_atm(city=city, district=district, limit=max(limit, 5)*2, kind=type)

        if not rows:
            return {"ok": False, "error": "Bu bölgede sonuç bulunamadı.", "data": {"query": {"city": city, "district": district}}}

        items: List[Dict[str, Any]] = []
        for r in rows:
          
            items.append({
                "id": r["id"],
                "name": r["name"],
                "type": r["type"],           # "atm" | "branch"
                "address": r["address"],
                "city": r["city"],
                "district": r["district"],
                "latitude": r["lat"],
                "longitude": r["lon"]
             
            })

        items = items[: max(1, min(limit, 5))]

        result = {
            "ok": True,
            "data": {
                "query": {"city": city, "district": district, "type": (type or None)},
                "items": items,
                "count": len(items),
            }
        }
        
        # Frontend ATMCard component için structured data
        if items:
            result["data"]["ui_component"] = {
                "type": "atm_card",
                "query": {"city": city, "district": district, "type": (type or None)},
                "items": items,
                "count": len(items)
            }
        
        return result
    
    def transactions_list(
        self,
        account_id: int,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        TransactionsTool.list(account_id, from, to, limit) eşleniği.
        - account_id (int) zorunlu
        - from_date/to_date: "YYYY-MM-DD" veya "YYYY-MM-DD HH:MM:SS"
        - limit: pozitif int (default 50)
        İşlemleri döndürür + aynı veriyi txn_snapshots tablosuna yazar.
        """
        # account_id doğrulama
        try:
            acc_id = int(account_id)
        except (TypeError, ValueError):
            return {"error": "account_id geçersiz (int olmalı)"}

        # limit doğrulama
        if not isinstance(limit, int) or limit <= 0:
            limit = 50
        if limit > 500:
            limit = 500  # güvenlik tavanı

        # Tarih formatı için hafif validasyon (çok katı değil)
        def _ok_date(s: Optional[str]) -> Optional[str]:
            if not s:
                return None
            s = s.strip()
            if len(s) < 10:
                return None
            return s

        f = _ok_date(from_date)
        t = _ok_date(to_date)

        # Kayıtları çek
        try:
            rows = self.repo.list_transactions(acc_id, f, t, limit)
        except Exception as e:
            return {"error": f"okuma hatası: {e}"}

        # Snapshotı yaz
        try:
            snap = self.repo.save_transaction_snapshot(acc_id, f, t, limit, rows)
        except Exception as e:
            # Okuma başarılı olsa da yazma hatasında bilgiyi yine döndürelim
            snap = {"error": f"snapshot yazılamadı: {e}", "saved": 0}

        return {
            "account_id": acc_id,
            "range": {"from": f, "to": t},
            "limit": limit,
            "count": len(rows),
            "snapshot": snap,
            "transactions": rows,
        }
