import React, { useState } from 'react';
import './UserGuide.css';

const UserGuide = ({ isOpen, onClose }) => {
  const [activeSection, setActiveSection] = useState('giris');

  const sections = {
    giris: {
      title: 'Giriş',
      content: (
        <div>
          <h3>InterChat Bankacılık Asistanına Hoş Geldiniz!</h3>
          <p>InterChat, yapay zeka destekli bankacılık asistanınızdır. Size 7/24 hizmet vererek müşteri hizmetlerine gerek duymadan bankacılık işlemlerinizi gerçekleştirmenize olanak tanır.</p>
          
          <h4>Temel Özellikler</h4>
          <ul>
            <li>Kullanıcı girişi</li>
            <li>Açık/Koyu tema desteği</li>
            <li>Sohbet geçmişi</li>
            <li>Hızlı işlem butonları</li>
            <li>Sesli işlemler</li>
            <li>Yapay zeka destekli işlemler</li>
            <li>Hesap bakiyesi sorgulama</li>
            <li>Para transferi işlemleri</li>
            <li>ATM/Şube arama</li>
            <li>Döviz kurları</li>
            <li>Faiz oranları</li>
            <li>İşlem ücretleri</li>
            <li>İşlem geçmişi</li>
            <li>Kart bilgileri</li>
            <li>Yatırım portföyleri</li>
            <li>Faiz hesaplama</li>
            <li>Kredi ödeme planı hesaplama</li>
            <li>Yatırım simülasyonu</li>
          </ul>

          <h4>Güvenlik</h4>
          <p>InterChat, bankacılık güvenlik standartlarına uygun olarak tasarlanmıştır. Tüm işlemleriniz güvenli bir şekilde işlenir.</p>
        </div>
      )
    },
    hesap: {
      title: 'Hesap İşlemleri',
      content: (
        <div>          
          <h4>Bakiye Sorgulama</h4>
          <p>Hesap bakiyenizi öğrenmek için şu komutları kullanabilirsiniz:</p>
          <ul>
            <li><strong>"Tüm hesaplarımın bakiyesi"</strong> - Tüm hesaplarınızın bakiyesini gösterir</li>
            <li><strong>"Hesap 123 bakiyesi"</strong> - Belirtilen hesabın bakiyesini gösterir</li>
            <li><strong>"Vadeli hesabımın bakiyesi"</strong> - Hesap türüne göre bakiye sorgulama</li>
          </ul>

          <h4>Hesap Türleri</h4>
          <ul>
            <li><strong>Vadeli Mevduat:</strong> Belirli bir vade ile açılan tasarruf hesabı</li>
            <li><strong>Vadesiz Mevduat:</strong> Günlük işlemler için kullanılan hesap</li>
            <li><strong>Maaş Hesabı:</strong> Maaş ödemelerinin yapıldığı hesap</li>
            <li><strong>Yatırım Hesabı:</strong> Yatırım işlemleri için kullanılan hesap</li>
          </ul>

          <h4>Hesap Bilgileri</h4>
          <p>Her hesabınız için şu bilgileri görebilirsiniz:</p>
          <ul>
            <li>Hesap numarası</li>
            <li>IBAN</li>
            <li>Bakiye</li>
            <li>Para birimi</li>
            <li>Hesap türü</li>
            <li>Hesap durumu</li>
          </ul>
        </div>
      )
    },
    transfer: {
      title: 'Para Transferi',
      content: (
        <div>
          <p><strong>NOT:</strong> Henüz yalnızca kullanıcının kendi hesapları arasında para transfer işlemi desteklenmektedir.</p>
          <h4>Transfer Yapma</h4>
          <p>Para transferi yapmak için şu adımları izleyin:</p>
          <ol>
            <li><strong>Transfer talep edin:</strong> "1000 TL transfer etmek istiyorum"</li>
            <li><strong>Hesap seçin:</strong> Kaynak ve hedef hesabı belirtin</li>
            <li><strong>Onaylayın:</strong> Transfer detaylarını kontrol edip onaylayın</li>
          </ol>

          <h4>Transfer Komutları</h4>
          <ul>
            <li><strong>"Hesap 123'ten hesap 456'ya 1000 TL transfer et"</strong></li>
            <li><strong>"Vadeli hesabımdan maaş hesabıma 500 TL gönder"</strong></li>
          </ul>

          <h4>Transfer Limitleri</h4>
          <ul>
            <li><strong>Tek işlem limiti:</strong> 20.000 TL</li>
            <li><strong>Günlük limit:</strong> 50.000 TL</li>
            <li><strong>Para birimi kontrolü:</strong> Yalnızca aynı para birimindeki hesaplar arası transfer</li>
          </ul>

          <h4>Güvenlik Kontrolleri</h4>
          <ul>
            <li>Hesap sahipliği doğrulaması</li>
            <li>Bakiye yeterliliği kontrolü</li>
            <li>Limit kontrolü</li>
            <li>Hesap durumu kontrolü</li>
            <li>Para birimi eşleşmesi kontrolü</li>
          </ul>
        </div>
      )
    },
    sube: {
      title: 'Şube/ATM',
      content: (
        <div> 
          <h4>Şube Arama</h4>
          <p>En yakın şubeleri bulmak için:</p>
          <ul>
            <li><strong>"İstanbul şube"</strong> - Belirtilen ildeki şubeleri listeler</li>
            <li><strong>"İstanbul Kadıköy şube"</strong> - Belirtilen ilçedeki şubeleri listeler</li>
            <li><strong>"İstanbul Sarıyer'e en yakın şube"</strong> - Belirtilen lokasyonda şube yoksa en yakındaki opsiyonları gösterir</li>
          </ul>

          <h4>ATM Arama</h4>
          <p>En yakın ATM'leri bulmak için:</p>
          <ul>
            <li><strong>"İstanbul ATM"</strong> - Belirtilen ildeki ATM'leri listeler</li>
            <li><strong>"İstanbul Beşiktaş ATM"</strong> - Belirtilen ilçedeki ATM'leri listeler</li>
            <li><strong>"İstanbul Sarıyer'e en yakın ATM"</strong> - Belirtilen lokasyonda ATM yoksa en yakındaki opsiyonları gösterir</li>
          </ul>

          <h4>Konum Bilgileri</h4>
          <p>Her şube ve ATM için şu bilgileri görebilirsiniz:</p>
          <ul>
            <li>Adres</li>
            <li>Haritalarda görüntüleyebilme</li>
          </ul>
        </div>
      )
    },
    doviz: {
      title: 'Döviz İşlemleri',
      content: (
        <div>
          <h4>Döviz Kurları</h4>
          <p>Güncel döviz kurlarını öğrenmek için:</p>
          <ul>
            <li><strong>"Döviz kurları"</strong> - Tüm kurları gösterir</li>
          </ul>

          <h4>Döviz Çevirme</h4>
          <p>Döviz çevirme işlemi için:</p>
          <ul>
            <li><strong>"100 USD kaç TL?"</strong></li>
            <li><strong>"500 Euro'yu Sterlin'e çevir"</strong></li>
            <li><strong>"1000 Frank kaç manat?"</strong></li>
          </ul>

          <h4>Desteklenen Para Birimleri</h4>
          <ul>
            <li><strong>USD</strong> (Amerikan Doları)</li>
            <li><strong>EUR</strong> (Euro)</li>
            <li><strong>GBP</strong> (İngiliz Sterlini)</li>
            <li><strong>JPY</strong> (Japon Yeni)</li>
            <li><strong>CHF</strong> (İsviçre Frangı)</li>
            <li><strong>CAD</strong> (Kanada Doları)</li>
            <li><strong>AUD</strong> (Avustralya Doları)</li>
            <li><strong>CNY</strong> (Çin Yuanı)</li>
            <li><strong>RUB</strong> (Rus Rublesi)</li>
            <li><strong>SAR</strong> (Suudi Arabistan Riyali)</li>
            <li><strong>AED</strong> (BAE Dirhemi)</li>
            <li><strong>KWD</strong> (Kuveyt Dinarı)</li>
            <li><strong>NOK</strong> (Norveç Kronu)</li>
            <li><strong>SEK</strong> (İsveç Kronu)</li>
            <li><strong>DKK</strong> (Danimarka Kronu)</li>
            <li><strong>BGN</strong> (Bulgar Levası)</li>
            <li><strong>RON</strong> (Rumen Leyi)</li>
            <li><strong>PKR</strong> (Pakistan Rupisi)</li>
            <li><strong>QAR</strong> (Katar Riyali)</li>
            <li><strong>KRW</strong> (Güney Kore Wonu)</li>
            <li><strong>AZN</strong> (Azerbaycan Yeni Manatı)</li>
          </ul>

          <h4>Kur Güncellemeleri</h4>
          <p>Döviz kurları hafta içi her gün saat <strong>15:30</strong>'da TCMB'den güncel olarak alınır ve veritabanına kaydedilir.</p>
        </div>
      )
    },
    faiz_oranlari: {
      title: 'Faiz Oranları',
      content: (
        <div>
          <h4>Faiz Oranları</h4>
          <p>Güncel faiz oranlarını öğrenmek için:</p>
          <ul>
            <li><strong>"Faiz oranları"</strong> - Tüm faiz oranlarını gösterir</li>
          </ul>

          <h4>Faiz Türleri</h4>
          <ul>
            <li><strong>Mevduat Faizi</strong></li>
            <li><strong>İhtiyaç Kredisi Faizi</strong></li>            
            <li><strong>Kredi Kartı Faizi</strong></li>
          </ul>
        </div>
      )
    },
    islem_ucretleri: {
      title: 'İşlem Ücretleri',
      content: (
        <div>
          <h4>Ücret Bilgileri</h4>
          <p>İşlem ücretlerini öğrenmek için:</p>
          <ul>
            <li><strong>"İşlem ücretleri"</strong> - Tüm ücretleri gösterir</li>
          </ul>

          <h4>Ücret Türleri</h4>
          <ul>
            <li><strong>Elektronik Fon Transferi</strong></li>
            <li><strong>Havale İşlemi</strong></li>
            <li><strong>FAST Sistemi ile Transfer</strong></li>
            <li><strong>ATM Para Çekme</strong></li>
            <li><strong>Uluslararası SWIFT Transferi</strong></li>
            <li><strong>Mobil Ödeme</strong></li>
            <li><strong>Fatura Ödeme</strong></li>
            <li><strong>Hesap Açılışı</strong></li>
            <li><strong>Hesap Kapatma</strong></li>
            <li><strong>Kredi Sorgulama</strong></li>
            <li><strong>Kredi Limiti Aşımı</strong></li>
            <li><strong>Döviz Alım-Satımı</strong></li>
            <li><strong>Çek Yatırma</strong></li>
            <li><strong>Çek İade Ücreti</strong></li>
            <li><strong>ATM Bakiye Sorgulama</strong></li>
            <li><strong>ATM PIN Değişikliği</strong></li>
            <li><strong>Hesap Özeti Talebi</strong></li>
            <li><strong>Hesap Bakım Ücreti</strong></li>
            <li><strong>Kart Değişim Ücreti</strong></li>
          </ul>
        </div>
      )
    },
    islem: {
      title: 'İşlem Geçmişi',
      content: (
        <div>
          <h4>İşlem Listesi</h4>
          <p>İşlem geçmişinizi görüntülemek için:</p>
          <ul>
            <li><strong>"Hesap 123 işlemleri"</strong> - Belirtilen hesabın tüm işlemlerini gösterir</li>
            <li><strong>"Hesap 123 son 20 işlem"</strong> - Belirtilen sayıda işlemi gösterir</li>
            <li><strong>"Hesap 123 2025-09-09 ile 2025-03-03 arası işlemleri"</strong> - Belirtilen tarih aralığındaki işlemleri gösterir</li>
          </ul>

          <h4>İşlem Detayları</h4>
          <p>Her işlem için şu bilgileri görebilirsiniz:</p>
          <ul>
            <li>İşlem tarihi ve saati</li>
            <li>İşlem türü</li>
            <li>Tutar</li>
            <li>İşlem açıklaması</li>
          </ul>
        </div>
      )
    },
    kart: {
      title: 'Kredi Kartı',
      content: (
        <div>
          <h4>Kart Bilgileri</h4>
          <p>Kredi kartı bilgilerinizi öğrenmek için:</p>
          <ul>
            <li><strong>"Kartlarımı göster"</strong> - Tüm kartlarınızı listeler</li>
            <li><strong>"Kart 123 bilgileri"</strong> - Belirli kartın detaylarını gösterir</li>
          </ul>

          <h4>Kart Detayları</h4>
          <p>Her kartınız için şu bilgileri görebilirsiniz:</p>
          <ul>
            <li>Kart ID</li>
            <li>Kart numarası (maskelenmiş)</li>
            <li>Kredi limiti</li>
            <li>Güncel borç</li>
            <li>Kullanılabilir limit</li>
            <li>Kesim tarihi</li>
            <li>Son ödeme tarihi</li>
            <li>Limit kullanımı (%)</li>
          </ul>
        </div>
      )
    },
    yatirim: {
      title: 'Yatırım Portföyleri',
      content: (
        <div>
          <h4>Portföy Görüntüleme</h4>
          <p>Yatırım portföylerini görüntülemek için:</p>
          <ul>
            <li><strong>"Yatırım portföylerini göster"</strong> - Tüm yatırım portföylerini listeler</li>
            <li><strong>"Orta riskli portföyleri göster"</strong> - Belirtilen riskteki portföyleri gösterir</li>
          </ul>
        </div>
      )
    },
    faiz_hesaplama: {
      title: 'Faiz Hesaplama',
      content: (
        <div>
          <h4>Faiz Hesaplama</h4>
          <p>Faiz hesaplama için:</p>
          <ul>
            <li><strong>"100.000 TL mevduat için 12 ay vadeli, aylık bileşik faiz hesapla"</strong></li>
          </ul>

          <h4>Faiz Hesaplama Aracı</h4>
          <p>Faiz hesaplama aracında şu parametreleri girebilirsiniz:</p>
          <ul>
            <li><strong>Hesaplama Türü:</strong> Mevduat/Kredi</li>
            <li><strong>Ana Para:</strong> Yatırım miktarı</li>
            <li><strong>Vade:</strong> Yatırım süresi (ay/yıl)</li>
            <li><strong>Faiz Oranı:</strong> Yıllık faiz oranı (%)</li>
            <li><strong>Bileşik Sıklığı:</strong> Yıllık/Aylık/Haftalık/Günlük/Sürekli vb.</li>
          </ul>

          <h4>Hesaplama Sonuçları</h4>
          <ul>
            <li>Toplam faiz getirisi</li>
            <li>Vade sonu toplam tutar</li>
          </ul>
        </div>
      )
    },
    kredi_odeme: {
      title: 'Kredi Ödeme Planı',
      content: (
        <div> 
          <h4>Ödeme Planı Hesaplama</h4>
          <p>Kredi ödeme planı hesaplamak için:</p>
          <ul>
            <li><strong>"200.000 TL 24 ay kredi aylık ödemem?"</strong></li>
          </ul>

          <h4>Kredi Planı Hesaplama Aracı</h4>
          <p>Kredi ödeme planı hesaplama aracında şu parametreleri girebilirsiniz:</p>
          <ul>
            <li><strong>Kredi Tutarı:</strong> Çekilecek kredi miktarı</li>
            <li><strong>Vade:</strong> Kredi vadesi (ay)</li>
            <li><strong>Faiz Oranı:</strong> Yıllık faiz oranı (%)</li>
          </ul>

          <h4>Ödeme Planı Detayları</h4>
          <ul>
            <li>Aylık taksit tutarı</li>
            <li>Toplam ödenecek tutar</li>
            <li>Toplam faiz miktarı</li>
            <li>Amortisman tablosu indirebilme (CSV)</li>
          </ul>
        </div>
      )
    },
    yatirim_simulasyon: {
      title: 'Yatırım Simülasyonu',
      content: (
        <div>
          <h4>Simülasyon Başlatma</h4>
          <p>Yatırım simülasyonu için:</p>
          <ul>
            <li><strong>"100.000 TL için yatırım simülasyonu"</strong></li>
            <li><strong>"ROI simülasyonu"</strong> - Getiri simülasyonu</li>
          </ul>

          <h4>Simülasyon Aracı</h4>
          <p>Simülasyon aracında şu parametreleri girebilirsiniz:</p>
          <ul>
            <li><strong>Portföy:</strong> Korumalı/Dengeli/Büyüme</li>
            <li><strong>Aylık Yatırım:</strong> Aylık yatırım miktarı</li>
            <li><strong>Yatırım Vadesi:</strong> Yatırım süresi (yıl)</li>
          </ul>

          <h4>Simülasyon Sonuçları</h4>
          <ul>
            <li>Kötümser/Ortalama/İyimser senaryolar</li>
            <li>Toplam getiri miktarı</li>
            <li>Yıllık ortalama getiri oranı (%)</li>
            <li>Risk aralığı</li>
            <li>ROI (yatırım getirisi) grafiği</li>
          </ul>
        </div>
      )
    },
    sikca: {
      title: 'Sıkça Sorulan Sorular',
      content: (
        <div>
          <h4>Genel Sorular</h4>
          <div className="faq-item">
            <strong>S: InterChat nedir?</strong>
            <p>C: InterChat, yapay zeka destekli bankacılık asistanınızdır. Bankacılık işlemlerinizi kolaylaştırmak için tasarlanmıştır.</p>
          </div>

          <div className="faq-item">
            <strong>S: InterChat güvenli mi?</strong>
            <p>C: Evet, InterChat bankacılık güvenlik standartlarına uygun olarak tasarlanmıştır. Tüm işlemleriniz güvenli bir şekilde işlenir.</p>
          </div>

          <div className="faq-item">
            <strong>S: 7/24 hizmet alabilir miyim?</strong>
            <p>C: Evet, InterChat 7/24 hizmet verir. Müşteri hizmetlerine gerek duymadan istediğiniz zaman bankacılık işlemlerinizi gerçekleştirebilirsiniz.</p>
          </div>

          <h4>Hesap İşlemleri</h4>
          <div className="faq-item">
            <strong>S: Kaç hesabımı yönetebilirim?</strong>
            <p>C: Tüm hesaplarınızı InterChat üzerinden yönetebilirsiniz. Vadeli, vadesiz, maaş ve yatırım hesaplarınız dahil.</p>
          </div>

          <div className="faq-item">
            <strong>S: Bakiye sorgulama ücretli mi?</strong>
            <p>C: Hayır, bakiye sorgulama işlemi ücretsizdir.</p>
          </div>

          <h4>Para Transferi</h4>
          <div className="faq-item">
            <strong>S: Transfer limitleri nelerdir?</strong>
            <p>C: Tek işlem limiti 20.000 TL, günlük limit ise 50.000 TL'dir.</p>
          </div>

          <div className="faq-item">
            <strong>S: Transfer işlemi ne kadar sürer?</strong>
            <p>C: Kendi hesaplarınız arası transferler anında gerçekleşir.</p>
          </div>

          <h4>Teknik Sorular</h4>
          <div className="faq-item">
            <strong>S: InterChat çalışmıyor, ne yapmalıyım?</strong>
            <p>C: Sayfayı yenileyin veya tarayıcınızı yeniden başlatın. Sorun devam ederse tarafımızla iletişime geçin.</p>
          </div>

          <div className="faq-item">
            <strong>S: Hangi tarayıcıları destekliyor?</strong>
            <p>C: Chrome, Firefox, Safari ve Edge tarayıcılarını destekler.</p>
          </div>
        </div>
      )
    },
    gelistirici: {
      title: 'Hakkımızda',
      content: (
        <div>
          <div className="faq-item">
            <strong>Proje Ekibi</strong>
            <p>InternTech - Takım 2</p>
          </div>

          <div className="faq-item">
            <strong>Teknoloji</strong>
            <p>Modern web, backend teknolojileri ve yapay zeka entegrasyonu ile geliştirilmiştir.</p>
          </div>

          <div className="faq-item">
            <strong>Versiyon</strong>
            <p>InterChat v1.0 - Yapay Zeka Destekli Bankacılık Asistanı</p>
          </div>
        </div>
      )
    }
  };

  if (!isOpen) return null;

  return (
    <div className="user-guide-overlay" onClick={onClose}>
      <div className="user-guide-modal" onClick={(e) => e.stopPropagation()}>
        <div className="user-guide-header">
          <h2>Kullanıcı Kılavuzu</h2>
          <button className="user-guide-close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        
        <div className="user-guide-content">
          <div className="user-guide-sidebar">
            <nav className="guide-navigation">
              {Object.entries(sections).map(([key, section]) => (
                <button
                  key={key}
                  className={`nav-item ${activeSection === key ? 'active' : ''}`}
                  onClick={() => setActiveSection(key)}
                >
                  {section.title}
                </button>
              ))}
            </nav>
          </div>
          
          <div className="user-guide-main">
            <div className="guide-section">
              <h2>{sections[activeSection].title}</h2>
              <div className="guide-content">
                {sections[activeSection].content}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserGuide;