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
