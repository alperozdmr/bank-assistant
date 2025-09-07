from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
import sqlite3
import math
import hashlib
import logging as log
import json
import sys
import os
from geopy.geocoders import Nominatim

# TCMB servisini import etmek için path ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from tcmb_service import TCMBService

class GeneralTools:
    """
    Hesap bakiyesi ve temel hesap detaylarını döndürür.
    Repo: get_account(account_id: int) -> Optional[dict]
    """

    def __init__(self, repo):
        self.repo = repo
    
    @staticmethod
    def mask_card_number(card_number: str) -> str:
        """
        Kart numarasını güvenli bir şekilde maskeler.
        İlk 4 ve son 4 rakamı gösterir, kalanları yıldız ile değiştirir.
        
        Args:
            card_number (str): Kart numarası (örn: "7575457589041837")
            
        Returns:
            str: Maskelenmiş kart numarası (örn: "7575********1837")
        """
        if not card_number or len(card_number) < 8:
            return "****"
        
        # İlk 4 ve son 4 rakamı al
        first_four = card_number[:4]
        last_four = card_number[-4:]
        
        # Ortadaki rakamları yıldız ile değiştir
        middle_length = len(card_number) - 8
        masked_middle = "*" * middle_length
        
        return f"{first_four}{masked_middle}{last_four}"
    
    def get_balance_by_account_type(self, customer_id: int, account_type: str) -> Dict[str, Any]:
        """
        Hesap türüne göre bakiye sorgulama. Örnek: "maaş hesabımın bakiyesi"
        
        Args:
            customer_id (int): Müşteri ID'si
            account_type (str): Hesap türü (vadeli mevduat, vadesiz mevduat, maaş, yatırım)
            
        Returns:
            Dict containing account details or error message
        """
        if customer_id is None or account_type is None:
            return {"error": "parametre eksik: customer_id ve account_type verin"}
        
        try:
            cust_id = int(customer_id)
        except (TypeError, ValueError):
            return {"error": "customer_id geçersiz (int olmalı)"}
        
        # Hesap türü eşleştirmesi - case insensitive mapping
        account_type_mapping = {
            "Vadeli Mevduat": ["vadeli mevduat", "vadeli"],
            "Vadesiz Mevduat": ["vadesiz mevduat", "vadesiz"],
            "Maaş": ["maaş", "maas"],
            "Yatırım": ["yatırım", "yatirim"]
        }
        
        # Gelen hesap türünü normalize et
        input_type = account_type.lower().strip()
        normalized_type = None
        
        # Mapping'de ara - case insensitive
        for db_type, aliases in account_type_mapping.items():
            if input_type in [alias.lower() for alias in aliases]:
                normalized_type = db_type
                break
        
        if not normalized_type:
            return {"error": f"Geçersiz hesap türü: {account_type}. Desteklenen türler: vadeli mevduat, vadesiz mevduat, maaş, yatırım"}
        
        # Hesap türüne göre hesapları getir
        accounts = self.repo.get_accounts_by_customer(cust_id, normalized_type)
        
        if not accounts:
            # Debug: Tüm hesapları kontrol et
            all_accounts = self.repo.get_accounts_by_customer(cust_id)
            available_types = [acc["account_type"] for acc in all_accounts] if all_accounts else []
            return {
                "error": f"{normalized_type} hesabınız bulunamadı. Mevcut hesap türleri: {', '.join(available_types)}"
            }
        
        # İlk hesabı döndür (genellikle bir türde tek hesap olur)
        account = accounts[0]
        
        # Format currency for display
        balance_formatted = f"{float(account['balance']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return {
            "account_id": account["account_id"],
            "customer_id": account["customer_id"],
            "account_number": account["account_number"],
            "account_type": account["account_type"],
            "balance": account["balance"],
            "balance_formatted": balance_formatted,
            "currency": account["currency"],
            "status": account["status"],
            "created_at": account["created_at"],
            "ui_component": {
                "type": "balance_card",
                "card_type": "single_account",
                "account_id": account["account_id"],
                "account_number": account["account_number"],
                "account_type": account["account_type"],
                "balance": account["balance"],
                "balance_formatted": balance_formatted,
                "currency": account["currency"],
                "status": account["status"]
            }
        }
    
    def __init__(self, repo):
        self.repo = repo
        # TCMB servisini veritabanı yolu ile başlat
        if hasattr(repo, 'db_path'):
            self.tcmb_service = TCMBService(db_path=repo.db_path)
        else:
            self.tcmb_service = TCMBService()

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
                "account_number": acc.get("account_number"),
                # Frontend BalanceCard component için structured data
                "ui_component": {
                    "type": "balance_card",
                    "card_type": "single_account",
                    "account_id": acc["account_id"],
                    "account_type": acc["account_type"],
                    "balance": balance_formatted,
                    "currency": acc["currency"],
                    "status": acc["status"],
                    "account_number": acc.get("account_number")
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
                "account_number": acc.get("account_number"),
                # Frontend BalanceCard component için structured data
                "ui_component": {
                    "type": "balance_card",
                    "card_type": "single_account",
                    "account_id": acc["account_id"],
                    "account_type": acc["account_type"],
                    "balance": balance_formatted,
                    "currency": acc["currency"],
                    "status": acc["status"],
                    "account_number": acc.get("account_number")
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
                "account_number": a.get("account_number"),
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
                        "status": acc["status"],
                        "account_number": acc.get("account_number")
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
            
            # Mask card number for security
            masked_card_number = self.mask_card_number(c.get('card_number', ''))

            return {
                "card_id": c["card_id"],
                "card_number": masked_card_number,
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
                        "card_number": card["card_number"],
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

        # Mask card number for security
        masked_card_number = self.mask_card_number(card_data.get('card_number', ''))

        return {
            "card_id": card_data["card_id"],
            "card_number": masked_card_number,
            "limit": card_data["credit_limit"],
            "borc": card_data["current_debt"],
            "kesim_tarihi": card_data["statement_day"],
            "son_odeme_tarihi": card_data["due_day"],
            # Frontend CardInfoCard component için structured data
            "ui_component": {
                "type": "card_info_card",
                "card_id": card_data["card_id"],
                "card_number": masked_card_number,
                "limit": card_data["credit_limit"],
                "borc": card_data["current_debt"],
                "kesim_tarihi": card_data["statement_day"],
                "son_odeme_tarihi": card_data["due_day"]
            }
        }
   
    """
    Döviz kurları ve faiz oranlarını döndürür.
    Repo: exchange_rates, interest_rates tablolarını sorgular.
    """

    def get_exchange_rates(self) -> Dict[str, Any]:
        """
        TCMB'den canlı döviz kurlarını çeker ve döndürür.
        Günlük 15:31'de otomatik güncelleme yapar.
        Dönüş: {"rates": [ {...}, ... ]} veya {"rates": []} / {"error": "..."}
        """
        try:
            # TCMB servisinden güncel kurları al
            rates = self.tcmb_service.get_exchange_rates()
            
            if not rates:
                return {"error": "TCMB'den döviz kuru verisi alınamadı."}

            result = {"rates": rates}
            
            # Frontend ExchangeRatesCard component için structured data
            if rates:
                result["ui_component"] = {
                    "type": "exchange_rates_card",
                    "rates": rates
                }

            return result
        except Exception as e:
            return {"error": f"TCMB veri çekme hatası: {e}"}

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
        
    def get_all_fees(self) -> Dict[str, Any]:
        """
        fees tablosundaki TÜM ücret kayıtlarını (19 satır) eksiksiz döndürür.
        Dönüş formatı, frontend’in doğrudan kullanabileceği şekilde normalize edilir.

        Returns:
            {
              "ok": True,
              "count": <int>,
              "items": [
                 {
                   "service_code": str,
                   "description": str,
                   "pricing": dict|str,   # pricing_json parse edilebiliyorsa dict
                   "updated_at": str
                 },
                 ...
              ],
              "ui_component": {
                "type": "fees_table",
                "items": [...]
              }
            }
        """
        try:
            rows = self.repo.list_fees()  # Repo 19 satırı döndürür
        except Exception as e:
            return {"ok": False, "error": f"Okuma hatası: {e}"}

        if not rows:
            return {"ok": True, "count": 0, "items": []}

        items: List[Dict[str, Any]] = []
        for r in rows:
            raw = r.get("pricing_json")
            # pricing_json'u mümkünse JSON'a çevir
            try:
                pricing = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                pricing = raw  # bozuksa string olarak bırak

            items.append({
                "service_code": r.get("service_code"),
                "description": r.get("description"),
                "pricing": pricing,
                "updated_at": r.get("updated_at"),
            })

        return {
            "ok": True,
            "count": len(items),
            "items": items,
            "ui_component": {
                "type": "fees_table",
                "items": items,
                "hide_service_code": True,            # tablo görünümünde kodu gizle
                "display_field": "description"        # FE liste sütununda description’ı öne çıkarabilir
            }
        }

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
            "title_tr": "Hizmet Ücreti",
            "display_name": row["description"],       # FE bunu başlık/isim olarak kullansın
            "description": row["description"],
            "pricing": pricing,
            "updated_at": row["updated_at"],
            "service_code": row["service_code"],      
            "hide_service_code": True                 
        }
        
        return result
    
    def search(self, city: str, district: Optional[str] = None,
               type: Optional[str] = None, limit: int = 3, nearby: bool = False) -> Dict[str, Any]:
        
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

        # Türkçe yer-yön ekleri ("-da/-de/-ta/-te" ve apostrof varyasyonları) temizleme
        # Örn: "Van'da", "vanda", "İzmirde" -> "Van", "van", "İzmir"
        def _strip_tr_locative(token: Optional[str]) -> Optional[str]:
            if not token:
                return token
            t = token.strip()
            # Sondaki "'da/'de/'ta/'te" veya direkt bitişik "da/de/ta/te" eklerini kaldır
            t = re.sub(r"(?:'|')?\s*(?:d[ea]|t[ea])$", "", t, flags=re.IGNORECASE)
            return t.strip()
        
        # Türkçe karakterleri normalize etme fonksiyonu
        def _normalize_tr(s: Optional[str]) -> str:
            """Türkçe karakterleri normalize eder"""
            if not s:
                return ""
            # Türkçe karakterleri normalize et
            s = s.replace("İ", "i").replace("I", "i")
            s = s.replace("Ğ", "g").replace("Ğ", "g")
            s = s.replace("Ü", "u").replace("Ü", "u")
            s = s.replace("Ş", "s").replace("Ş", "s")
            s = s.replace("Ö", "o").replace("Ö", "o")
            s = s.replace("Ç", "c").replace("Ç", "c")
            return s.lower().strip()

        city = _strip_tr_locative(city)
        district = _strip_tr_locative(district)
        if not city:
            return {"ok": False, "error": "Lütfen şehir belirtin.", "data": {"query": {"city": city, "district": district}}}

        # Biraz fazla satır al, sonra mesafeye göre kırp
        # type parametresini doğru formata çevir
        kind_param = None
        if type:
            t = type.strip().lower()
            # Türkçe karakterleri normalize et
            t = t.replace("ş", "s").replace("ü", "u")
            if t == "atm":
                kind_param = "ATM"
            elif t in ("branch", "sube", "şube"):
                kind_param = "BRANCH"
        
        rows = self.repo.find_branch_atm(city=city, district=district, limit=max(limit, 5)*2, kind=kind_param)

        if not rows:
            # Eksakt eşleşme yoksa: önce kullanıcıya yakın sonuç isteğini soran mesaj dön
            if not nearby:
                suggestion = {
                    "ok": False,
                    "error": "Belirttiğiniz bölgede sonuç bulunamadı. Dilerseniz 'en yakın ATM/şube' şeklinde sorabilirsiniz.",
                    "data": {
                        "query": {"city": city, "district": district, "type": (type or None)},
                        "hint": {"nearby_param": True}
                    }
                }
                return suggestion

            # Kullanıcı yakın isterse geocode ederek en yakın kayıtları dön (inline)
            try:
                loc_query = f"{city} {district}".strip() if district else city
                geocoder = Nominatim(user_agent="bank_assistant_geocoder")
                g = geocoder.geocode(loc_query, language="tr")
                if not g or not g.latitude or not g.longitude:
                    raise ValueError("konum bulunamadı")
                lat0, lon0 = float(g.latitude), float(g.longitude)

                if not hasattr(self.repo, "list_branch_atm_all"):
                    raise ValueError("repo list_branch_atm_all yok")
                all_rows = self.repo.list_branch_atm_all() or []

                want_kind = None
                if type:
                    k = type.strip().lower()
                    # Türkçe karakterleri normalize et
                    k = k.replace("ş", "s").replace("ü", "u")
                    if k == "atm":
                        want_kind = "atm"
                    elif k in ("branch", "sube", "şube"):
                        want_kind = "branch"

                def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
                    R = 6371.0
                    from math import radians, sin, cos, asin, sqrt
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) ** 2
                    c = 2 * asin(sqrt(a))
                    return R * c

                scored: List[Dict[str, Any]] = []
                for r in all_rows:
                    if want_kind and r.get("type") != want_kind:
                        continue
                    la, lo = r.get("lat"), r.get("lon")
                    if la is None or lo is None:
                        continue
                    dist = haversine_km(lat0, lon0, float(la), float(lo))
                    rr = dict(r)
                    rr["distance_km"] = round(dist, 3)
                    scored.append(rr)

                if not scored:
                    return {"ok": False, "error": "Yakında kayıt bulunamadı.", "data": {"query": {"city": city, "district": district}}}

                scored.sort(key=lambda x: x["distance_km"])
                items = [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "type": s["type"],
                        "address": s["address"],
                        "city": s["city"],
                        "district": s.get("district"),
                        "latitude": s.get("lat"),
                        "longitude": s.get("lon"),
                        "distance_km": s["distance_km"],
                    }
                    for s in scored[: max(1, min(limit, 5))]
                ]

                result = {
                    "ok": True,
                    "data": {
                        "query": {"city": city, "district": district, "type": (type or None)},
                        "items": items,
                        "count": len(items),
                    }
                }
                result["data"]["ui_component"] = {
                    "type": "atm_card",
                    "query": {"city": city, "district": district, "type": (type or None)},
                    "items": items,
                    "count": len(items)
                }
                return result
            except Exception:
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

        # UI component için öğeleri normalize et
        def _fmt_amount(x: Any) -> str:
            try:
                val = float(x)
            except Exception:
                return str(x)
            # Türkçe biçimlendirme: binlik ayraç nokta, ondalık virgül
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        items = []
        for r in rows:
            amt = r.get("amount")
            items.append({
                "id": r.get("txn_id") or r.get("id"),
                "datetime": r.get("txn_date") or r.get("date"),
                "amount": amt,
                "amount_formatted": _fmt_amount(amt) if amt is not None else None,
                "currency": r.get("currency") or "TRY",
                "type": r.get("txn_type") or r.get("type"),
                "description": r.get("description"),
                "balance_after": r.get("balance_after"),
                "account_id": r.get("account_id") or acc_id,
            })

        base = {
            "account_id": acc_id,
            "range": {"from": f, "to": t},
            "limit": limit,
            "count": len(rows),
            "snapshot": snap,
            "transactions": rows,
        }

        # Frontend'in beklediği UI şeması
        ui_component = {
            "type": "transactions_list",
            "account_id": acc_id,
            "items": items,
        }

        base["ui_component"] = ui_component
        base["ok"] = True
        return base
    
    def list_available_portfolios(self, portfolio_type: Optional[str] = None) -> dict:
        """
        Fetches investment portfolios. Can be filtered by type.
        Maps user-friendly names like 'korumalı' to database values like 'Düşük'.
        """
        # Kullanıcıdan gelebilecek farklı isimleri veritabanındaki standart değere eşleştiriyoruz.
        risk_level_map = {
            "düşük": "Düşük",
            "korumalı": "Düşük",
            "orta": "Orta",
            "dengeli": "Orta",
            "yüksek": "Yüksek",
            "büyüme": "Yüksek",
        }

        db_risk_level = None
        if portfolio_type:
            # Gelen parametreyi küçük harfe çevirip haritada arıyoruz
            db_risk_level = risk_level_map.get(portfolio_type.lower())

        # Yeni ve esnek repo metodumuzu çağırıyoruz
        portfolios_data = self.repo.get_portfolios(risk_level=db_risk_level)

        if not portfolios_data:
            if db_risk_level:
                return {"message": f"'{db_risk_level}' risk seviyesinde portföy bulunamadı."}
            return {"error": "Sistemde kayıtlı portföy bulunamadı."}
        
        # Frontend'in beklediği UI şeması
        ui_component = {
            "type": "portfolios_card",
            "portfolios": portfolios_data
        }
        
        base = {
            "available_portfolios": portfolios_data,
            "ui_component": ui_component,
            "ok": True
        }
        
        return base
