<div align="center">

<img src="frontend/public/logo.jpg" alt="InterChat Logo" width="200" height="200">

# InterChat - Akıllı Bankacılık Asistanı

*Modern web teknolojileri kullanılarak geliştirilmiş, yapay zeka destekli bankacılık asistanı*

</div>

InterChat, kullanıcıların bankacılık işlemlerini kolayca gerçekleştirmelerini sağlayan yapay zeka destekli bir bankacılık asistanı uygulamasıdır.

## ✨ Özellikler

### 🔐 Güvenli Kimlik Doğrulama
- Müşteri numarası ve şifre ile giriş
- JWT token tabanlı oturum yönetimi
- Güvenli API endpoint'leri

### 💰 Hesap Yönetimi
- **Bakiye Sorgulama**: Tüm hesapların bakiyelerini görüntüleme
- **Hesap Türleri**: Vadeli mevduat, vadesiz mevduat, maaş hesabı, yatırım hesabı
- **Kart Bilgileri**: Kredi kartı limitleri, borç durumu, ekstre tarihleri

### 💸 Para Transferi
- **Hesap İçi Transfer**: Kendi hesaplarınız arasında para transferi
- **Hesap Türü ile Transfer**: Hesap numarası belirtmeden transfer
- **Güvenlik Kontrolleri**: Yeterli bakiye, günlük limit kontrolleri
- **Onay Sistemi**: Transfer öncesi önizleme ve onay

### 📊 İşlem Geçmişi
- **Detaylı İşlem Listesi**: Tarih aralığına göre filtreleme
- **Hesap Bazlı Sorgulama**: Belirli hesabın işlem geçmişi
- **İşlem Türleri**: Gelen/giden transferler, ödemeler

### 💱 Döviz ve Faiz İşlemleri
- **Canlı Döviz Kurları**: TCMB'den güncel kurlar
- **Döviz Çevirici**: Anlık kur hesaplamaları
- **Faiz Hesaplama**: Mevduat ve kredi faiz hesaplamaları
- **Kredi Amortisman**: Kredi ödeme planları

### 📈 Yatırım Araçları
- **Portföy Simülasyonu**: Monte Carlo simülasyonu ile yatırım projeksiyonları
- **ROI Hesaplama**: Yatırım getirisi hesaplamaları
- **Portföy Türleri**: Düşük risk, dengeli, büyüme portföyleri

### 🏢 Şube ve ATM
- **Konum Bazlı Arama**: Şehir ve ilçeye göre şube/ATM bulma
- **Yakınlık Sıralaması**: En yakın şube ve ATM'leri listeleme
- **Detaylı Bilgiler**: Adres, çalışma saatleri, koordinatlar

### 💳 Kart İşlemleri
- **Kart Limit Artışı**: Kredi kartı limit artış talepleri
- **Kart Bilgileri**: Mevcut limit, borç, ekstre tarihleri
- **Kart Listesi**: Tüm kartların özet bilgileri

## 🛠️ Teknoloji Stack'i

### Backend
- **FastAPI**: Modern, hızlı Python web framework
- **SQLite**: Hafif, dosya tabanlı veritabanı
- **LangChain**: Yapay zeka ve dil modeli entegrasyonu
- **LangGraph**: ReAct pattern ile akıllı agent
- **MCP (Model Context Protocol)**: Tool entegrasyonu
- **Uvicorn**: ASGI web sunucusu
- **Pydantic**: Veri doğrulama ve serileştirme

### Frontend
- **React 19**: Modern JavaScript kütüphanesi
- **Vite**: Hızlı build tool ve dev server
- **Chart.js**: Grafik ve görselleştirme
- **HTML2Canvas & jsPDF**: Rapor oluşturma
- **CSS3**: Modern styling ve responsive tasarım

### AI/ML
- **OpenAI API**: GPT model entegrasyonu
- **LangChain Tools**: Bankacılık işlemleri için özel araçlar
- **MCP Server**: Tool çağrıları için protokol

## 📁 Proje Yapısı

```
bank-assistant-master23agustos/
├── backend/                 # Backend uygulaması
│   ├── app/                # FastAPI uygulaması
│   │   ├── main.py         # Ana uygulama dosyası
│   │   └── auth.py         # Kimlik doğrulama
│   ├── agent/              # AI Agent
│   │   └── AdvancedAgent.py # LangGraph ReAct Agent
│   ├── chat/               # Chat geçmişi yönetimi
│   │   ├── __init__.py
│   │   └── chat_history.py # Chat mesajları ve oturum yönetimi
│   ├── mcp_server/         # MCP Server
│   │   ├── server.py       # MCP server ana dosyası
│   │   ├── tools/          # Bankacılık araçları
│   │   │   ├── general_tools.py      # Genel bankacılık araçları
│   │   │   ├── calculation_tools.py  # Hesaplama araçları
│   │   │   ├── payment_tools.py      # Ödeme araçları
│   │   │   └── roi_simulator_tool.py # Yatırım simülasyonu
│   │   └── data/           # Veritabanı repository'leri
│   │       ├── sqlite_repo.py        # SQLite repository
│   │       └── sql_payment_repo.py   # Ödeme repository
│   ├── requirements.txt    # Python bağımlılıkları
│   ├── config_local.py     # Konfigürasyon dosyası
│   ├── security.py         # Güvenlik modülleri
│   ├── tcmb_service.py     # TCMB döviz kuru servisi
│   ├── chat.db            # Chat veritabanı
│   └── dummy_bank.db      # Bankacılık veritabanı
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React bileşenleri
│   │   │   ├── BalanceCard.jsx           # Bakiye kartı
│   │   │   ├── TransactionsCard.jsx      # İşlem geçmişi
│   │   │   ├── PaymentTransferModal.jsx  # Para transferi
│   │   │   ├── ExchangeRatesCard.jsx     # Döviz kurları
│   │   │   ├── ROISimulationCard.jsx     # Yatırım simülasyonu
│   │   │   ├── UserProfileCard.jsx       # Kullanıcı profili
│   │   │   └── ... (diğer UI bileşenleri)
│   │   ├── App.jsx         # Ana uygulama
│   │   ├── Login.jsx       # Giriş sayfası
│   │   ├── App.css         # Ana stil dosyası
│   │   └── index.css       # Global stiller
│   ├── public/
│   │   └── logo.jpg        # Logo dosyası
│   ├── package.json        # Node.js bağımlılıkları
│   ├── vite.config.js      # Vite konfigürasyonu
│   └── eslint.config.js    # ESLint konfigürasyonu
├── common/                 # Ortak Python modülleri
│   ├── __init__.py
│   ├── http_middleware.py  # HTTP middleware
│   ├── logging_setup.py    # Logging konfigürasyonu
│   ├── mcp_decorators.py   # MCP dekoratörleri
│   └── pii.py             # PII maskeleme
├── run_all.py             # Tüm servisleri başlatma scripti
└── package-lock.json      # NPM lock dosyası
```

## 🚀 Kurulum ve Çalıştırma

### Ön Gereksinimler

- **Python 3.12+**
- **Node.js 18+**
- **npm**

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/your-username/bank-assistant.git
cd bank-assistant
```

### 2. Backend Kurulumu

```bash
# Python sanal ortamı oluşturun
python -m venv backend/.venv

# Sanal ortamı aktifleştirin
# Windows:
backend\.venv\Scripts\activate
# Linux/Mac:
source backend/.venv/bin/activate

# Bağımlılıkları yükleyin
cd backend
pip install -r requirements.txt

# Veritabanını başlatın (gerekirse)
python -c "from mcp_server.data.sqlite_repo import SQLiteRepository; SQLiteRepository('dummy_bank.db').init_db()"
```

### 3. Frontend Kurulumu

```bash
cd frontend
npm install
```

### 4. Konfigürasyon

Backend'de `config_local.py` dosyasını düzenleyin:

```python
# config_local.py
# LLM (OpenAI-compatible / Ollama / HF Router) ayarları
LLM_API_BASE = "https://router.huggingface.co/v1"  # veya kendi API'niz
LLM_CHAT_PATH = "/chat/completions"
LLM_MODEL = "Qwen/Qwen3-30B-A3B:fireworks-ai"  # veya gpt-4, gpt-3.5-turbo
LLM_API_KEY = "your-huggingface-api-key-here"  # Hugging Face API anahtarınız
```

**Not**: `LLM_API_KEY` alanını Hugging Face'den aldığınız API anahtarı ile doldurun.

### 5. Uygulamayı Başlatın

#### Otomatik Başlatma (Önerilen)

```bash
# Ana dizinde
python run_all.py
```

Bu script aşağıdaki servisleri otomatik başlatır:
- MCP Server (port 8081)
- FastAPI Backend (port 8000)
- React Frontend (port 5173)

#### Manuel Başlatma

Terminal 1 - MCP Server:
```bash
cd backend
python -m mcp_server.server
```

Terminal 2 - FastAPI Backend:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 3 - React Frontend:
```bash
cd frontend
npm run dev
```

### 6. Uygulamaya Erişim

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Dokümantasyonu**: http://localhost:8000/docs

## 🔧 Geliştirme

### Backend Geliştirme

```bash
cd backend
# Sanal ortamı aktifleştirin
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate     # Windows

# Uygulamayı geliştirme modunda çalıştırın
uvicorn app.main:app --reload
```

### Frontend Geliştirme

```bash
cd frontend
npm run dev
```

### Veritabanı Yönetimi

```bash
cd backend
python -c "
from mcp_server.data.sqlite_repo import SQLiteRepository
repo = SQLiteRepository('dummy_bank.db')
# Veritabanı işlemleri
"
```

## 📚 API Dokümantasyonu

### Ana Endpoint'ler

- `POST /auth/login` - Kullanıcı girişi
- `POST /chat` - Chat mesajı gönderme
- `GET /accounts` - Kullanıcı hesapları
- `GET /health` - Sistem durumu

### MCP Tools

Backend'de 20+ bankacılık aracı mevcuttur:

- `get_balance` - Hesap bakiyesi sorgulama
- `get_accounts` - Hesap listesi
- `transactions_list` - İşlem geçmişi
- `payment_request` - Para transferi
- `get_exchange_rates` - Döviz kurları
- `loan_amortization_schedule` - Kredi hesaplama
- `run_roi_simulation` - Yatırım simülasyonu
- `branch_atm_search` - Şube/ATM arama

## 🔒 Güvenlik

- **JWT Token**: Güvenli oturum yönetimi
- **PII Masking**: Kişisel bilgilerin maskeleme
- **Input Validation**: Tüm girdilerin doğrulanması
- **SQL Injection Koruması**: Parametreli sorgular
- **CORS**: Cross-origin isteklerin kontrolü
- **Rate Limiting**: API istek limitleri

## 📊 Logging ve Monitoring

- **Structured Logging**: JSON formatında loglar
- **Correlation ID**: İstek takibi
- **Performance Metrics**: Yanıt süreleri
- **Error Tracking**: Hata logları ve stack trace'ler

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Ticari kullanım için INTERTECH şirketi ile iletişime geçiniz.

## 👥 Geliştirici Ekibi

**INTERTECH** şirketi - 2025 InternTech Staj Programı **Takım 2**

---

**InterChat** - Dijital bankacılık deneyimi için yapay zeka destekli asistanınız 🚀
