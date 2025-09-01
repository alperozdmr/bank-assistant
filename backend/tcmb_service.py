import requests
import xml.etree.ElementTree as ET
from datetime import datetime, time
from typing import Dict, List, Optional
import logging
import sqlite3

logger = logging.getLogger(__name__)

class TCMBService:
    """TCMB'den döviz kurlarını çeken servis"""
    
    TCMB_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"
    
    # TCMB'den gelen para birimi kodlarını sistem kodlarına eşleştirme
    CURRENCY_MAPPING = {
        'USD': 'USD/TRY',
        'EUR': 'EUR/TRY', 
        'GBP': 'GBP/TRY',
        'JPY': 'JPY/TRY',
        'CHF': 'CHF/TRY',
        'CAD': 'CAD/TRY',
        'AUD': 'AUD/TRY',
        'CNY': 'CNY/TRY',
        'RUB': 'RUB/TRY',
        'SAR': 'SAR/TRY',
        'AED': 'AED/TRY',
        'KWD': 'KWD/TRY',
        'NOK': 'NOK/TRY',
        'SEK': 'SEK/TRY',
        'DKK': 'DKK/TRY',
        'BGN': 'BGN/TRY',
        'RON': 'RON/TRY',
        'PKR': 'PKR/TRY',
        'QAR': 'QAR/TRY',
        'KRW': 'KRW/TRY',
        'AZN': 'AZN/TRY'
    }
    
    # TCMB'den 100 birim olarak gelen para birimleri (100'e bölünmesi gerekenler)
    HUNDRED_UNIT_CURRENCIES = {'JPY'}
    
    def __init__(self, db_path: str = None):
        self.last_update = None
        self.cached_rates = []
        self.db_path = db_path
    
    def fetch_exchange_rates(self) -> List[Dict[str, any]]:
        """
        TCMB'den güncel döviz kurlarını çeker
        
        Returns:
            List[Dict]: Döviz kurları listesi
        """
        try:
            logger.info("TCMB'den döviz kurları çekiliyor...")
            
            response = requests.get(self.TCMB_URL, timeout=10)
            response.raise_for_status()
            
            # XML'i parse et
            root = ET.fromstring(response.content)
            
            rates = []
            current_time = datetime.now()
            
            # TCMB'den tarih bilgisini al (root element'in attributes'ından)
            tarih_attr = root.get('Tarih')
            if tarih_attr:
                try:
                    # TCMB tarih formatı: "29.08.2025" -> "2025-08-29"
                    day, month, year = tarih_attr.split('.')
                    tcmb_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    # TCMB saati 15:30'da açıklanıyor
                    tcmb_datetime = f"{tcmb_date} 15:30:00"
                    logger.info(f"TCMB tarih bilgisi alındı: {tarih_attr} -> {tcmb_datetime}")
                except Exception as e:
                    logger.warning(f"TCMB tarih parse hatası: {e}")
                    tcmb_datetime = current_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                logger.warning("TCMB tarih attribute'u bulunamadı")
                tcmb_datetime = current_time.strftime('%Y-%m-%d %H:%M:%S')
            

            
            # TCMB XML yapısı: <Tarih_Date><Currency>...</Currency></Tarih_Date>
            for currency in root.findall('.//Currency'):
                currency_code = currency.get('Kod')
                
                if currency_code in self.CURRENCY_MAPPING:
                    try:
                        # TCMB'den gelen değerleri al
                        forex_buying = currency.find('ForexBuying')
                        forex_selling = currency.find('ForexSelling')
                        
                        if forex_buying is not None and forex_selling is not None:
                            buy_rate = float(forex_buying.text.replace(',', '.'))
                            sell_rate = float(forex_selling.text.replace(',', '.'))
                            
                            # 100 birim olarak gelen para birimleri için 100'e böl
                            if currency_code in self.HUNDRED_UNIT_CURRENCIES:
                                buy_rate = buy_rate / 100
                                sell_rate = sell_rate / 100
                            
                            rate_data = {
                                'code': self.CURRENCY_MAPPING[currency_code],
                                'buy': buy_rate,
                                'sell': sell_rate,
                                'updated_at': tcmb_datetime,
                                'source': 'TCMB'
                            }
                            
                            rates.append(rate_data)
                            logger.debug(f"Kur eklendi: {rate_data['code']} - Alış: {buy_rate}, Satış: {sell_rate}")
                    
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Kur verisi parse edilemedi {currency_code}: {e}")
                        continue
            
            self.cached_rates = rates
            self.last_update = current_time
            
            # Veritabanına kaydet
            if self.db_path:
                self.save_rates_to_db(rates)
            
            logger.info(f"TCMB'den {len(rates)} adet kur başarıyla çekildi ve veritabanına kaydedildi")
            return rates
            
        except requests.RequestException as e:
            logger.error(f"TCMB'den veri çekme hatası: {e}")
            return self.cached_rates if self.cached_rates else []
        
        except ET.ParseError as e:
            logger.error(f"XML parse hatası: {e}")
            return self.cached_rates if self.cached_rates else []
        
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            return self.cached_rates if self.cached_rates else []
    
    def should_update_today(self) -> bool:
        """
        Bugün 15:31'de güncelleme yapılıp yapılmadığını kontrol eder
        
        Returns:
            bool: Güncelleme gerekiyorsa True
        """
        if not self.last_update:
            return True
        
        now = datetime.now()
        today_15_31 = now.replace(hour=15, minute=31, second=0, microsecond=0)
        
        # Eğer şu an 15:31'den sonra ve son güncelleme bugün 15:31'den önceyse güncelle
        if now >= today_15_31 and self.last_update < today_15_31:
            return True
        
        # Eğer şu an 15:31'den önceyse ve son güncelleme dünden önceyse güncelle
        if now < today_15_31 and self.last_update.date() < now.date():
            return True
        
        return False
    
    def get_exchange_rates(self) -> List[Dict[str, any]]:
        """
        Döviz kurlarını döndürür, gerekirse TCMB'den günceller
        Veritabanından okur, güncelleme gerekiyorsa TCMB'den çeker
        
        Returns:
            List[Dict]: Güncel döviz kurları
        """
        if self.should_update_today():
            return self.fetch_exchange_rates()
        else:
            # Veritabanından oku
            rates = self.load_rates_from_db()
            if rates:
                logger.info("TCMB'den güncelleme gerekmiyor, veritabanından döndürülüyor")
                return rates
            else:
                # Veritabanında veri yoksa TCMB'den çek
                logger.info("Veritabanında veri bulunamadı, TCMB'den çekiliyor")
                return self.fetch_exchange_rates()
    
    def save_rates_to_db(self, rates: List[Dict[str, any]]) -> bool:
        """
        Döviz kurlarını fx_rates tablosuna kaydeder
        
        Args:
            rates: Döviz kurları listesi
            
        Returns:
            bool: Başarılı ise True
        """
        if not self.db_path:
            logger.warning("Veritabanı yolu belirtilmemiş, kayıt yapılamıyor")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Mevcut kayıtları temizle
            cursor.execute("DELETE FROM fx_rates")
            
            # Yeni kayıtları ekle
            for rate in rates:
                cursor.execute(
                    "INSERT INTO fx_rates (code, buy, sell, updated_at) VALUES (?, ?, ?, ?)",
                    (rate['code'], rate['buy'], rate['sell'], rate['updated_at'])
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"{len(rates)} adet kur veritabanına kaydedildi")
            return True
            
        except Exception as e:
            logger.error(f"Veritabanına kayıt hatası: {e}")
            return False
    
    def load_rates_from_db(self) -> List[Dict[str, any]]:
        """
        fx_rates tablosundan döviz kurlarını okur
        
        Returns:
            List[Dict]: Döviz kurları listesi
        """
        if not self.db_path:
            logger.warning("Veritabanı yolu belirtilmemiş, okuma yapılamıyor")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT code, buy, sell, updated_at FROM fx_rates ORDER BY code")
            rows = cursor.fetchall()
            
            conn.close()
            
            rates = []
            for row in rows:
                rates.append({
                    'code': row['code'],
                    'buy': row['buy'],
                    'sell': row['sell'],
                    'updated_at': row['updated_at'],
                    'source': 'TCMB (DB)'
                })
            
            logger.info(f"Veritabanından {len(rates)} adet kur okundu")
            return rates
            
        except Exception as e:
            logger.error(f"Veritabanından okuma hatası: {e}")
            return []
    
    def should_update_today(self) -> bool:
        """
        Bugün 15:31'de güncelleme yapılıp yapılmadığını kontrol eder
        Veritabanındaki son güncelleme tarihini kontrol eder
        
        Returns:
            bool: Güncelleme gerekiyorsa True
        """
        if not self.db_path:
            # Veritabanı yoksa her zaman güncelle
            return True
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # En son güncelleme tarihini al
            cursor.execute("SELECT MAX(updated_at) as last_update FROM fx_rates")
            result = cursor.fetchone()
            
            conn.close()
            
            if not result or not result[0]:
                # Veritabanında kayıt yoksa güncelle
                return True
            
            # Son güncelleme tarihini parse et
            last_update_str = result[0]
            try:
                last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Tarih formatı uygun değilse güncelle
                return True
            
            now = datetime.now()
            today_15_30 = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            # Eğer şu an 15:30'dan sonra ve son güncelleme bugün 15:30'dan önceyse güncelle
            if now >= today_15_30 and last_update < today_15_30:
                return True
            
            # Eğer şu an 15:30'dan önceyse ve son güncelleme dünden önceyse güncelle
            if now < today_15_30 and last_update.date() < now.date():
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Güncelleme kontrolü hatası: {e}")
            return True

# Global TCMB servis instance'ı - veritabanı yolu ile başlatılacak
tcmb_service = None
