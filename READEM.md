# Bank Assistant

# Pre-commit Kurulumu ve Kullanımı

Bu doküman, projede kod kalitesini artırmak ve kod standartlarını korumak amacıyla kullanılan **pre-commit** hook'unun nasıl kurulacağını ve kullanılacağını açıklar.

## 1. Pre-commit Nedir?
Pre-commit, **git commit** komutu çalıştırılmadan **önce** otomatik olarak belirlenen kontrolleri çalıştıran bir araçtır.
Bunun amacı, kodun **format, lint ve test kurallarına** uymasını sağlamak ve hatalı kodun commitlenmesini engellemektir.

## 2. Kurulum Adımları

### 2.1 Pre-commit Kütüphanesini Kur
Proje ortamında pre-commit'i yüklemek için:

```bash
pip install pre-commit==3.7.1 black==24.8.0 ruff==0.5.7 isort==5.13.2
pre-commit install

### Pre-commit Kütüphanesini çalıştırmak için
pre-commit run --all-files

###MINIMAL AGENT VE ACCOUNT_BALANCE TOOLUNUN KULLANIMI###
.env dosyaları mevcut ise mevcut olanı çekip kullanıyoruz. Değilse kodu çalıştırmadan eklemek gerekiyor.
1) terminali kullanarak projenin klasöründe backende girin
    cd <repo-dizini>/backend
2) MAC için
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    # mock için zorunlu değil ama isterseniz:
    pip install python-dotenv
2) WIN için
    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install python-dotenv
3) MOCK MODE, MAC için
    export INTER_API_MOCK=1
3) MOCK MODE, WIN için
    $env:INTER_API_MOCK = "1"
4) KODU DOĞRUDAN ÇALIŞTIRMA
    python -m tools.account_balance --iban TR220013400001795306300001
    # veya üçlü:
    python -m tools.account_balance --suffix 351 --branch 9142 --customer 17953063
4) MINIMAL AGENT (interaktif)
    python -m agent.agent
    IBAN TR220013400001795306300001 bakiyem?
## GERÇEK APILERLE KULLANIMA GEÇME (vdi gerekli)
1) MAC: unset INTER_API_MOCK
   WIN: Remove-Item Env:INTER_API_MOCK
2) ENV KURULUMU
    export INTER_API_BASE_URL="https://devfortunav3.intertech.com.tr/Intertech.Fortuna.WebApi.Services"
    export INTER_API_APP_KEY="(app key)"
    export INTER_API_CHANNEL="STARTECH"
    export INTER_API_SESSION_LANGUAGE="TR"
3) GERÇEK TEST
    python -m tools.account_balance --iban TR220013400001795306300001




### FastAPI
çalışması için önce UI çalıştığı portu mainy.py içinde xxxx yazan yere yazıp sonra
uvicorn main:app --reload
bu commendi çalıştırın ama /app klasörünün içinde çalıştırmanız lazım

## Agent MCP server entegrasyonu tamamlandı test için:
önce server'ı çalıştırın
sonra backend klasöründe .env'leri aktive edin:
source .venv/bin/activate
daha sonra aşağıdaki komut ile agent'ı test edebilirsiniz:
##########
export USE_MCP=1
export MCP_SSE_URL="http://127.0.0.1:8081/sse"
export MCP_BALANCE_TOOL="get_balance"
python -m agent.agent
##########