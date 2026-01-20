# 🏥 KRATS - Klinik Yönetim Sistemi

Modern, güvenli ve tam özellikli klinik yönetim yazılımı.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-0.25+-green.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

## 🌟 Özellikler

### ✅ Temel Modüller
- 👥 **Hasta Yönetimi** - Kayıt, arama, arşivleme
- 📅 **Randevu Sistemi** - Google Calendar entegrasyonu
- 💰 **Finans** - Gelir/gider takibi, raporlama
- 📦 **Stok** - Malzeme ve ilaç takibi
- 💬 **Mesajlaşma** - Klinik içi iletişim
- 📊 **CRM & Analiz** - Hasta kaynakları, grafikler

### 🚀 Gelişmiş Özellikler
- 🤖 **AI Asistan** - GPT-4, Claude, Gemini desteği
- 📰 **Tıbbi Bülten** - RSS feed ile güncel haberler
- 🏥 **E-Nabız Entegrasyonu** - Otomatik veri gönderimi
- 📺 **TV Bekleme Ekranı** - Hasta sırası gösterimi
- 📄 **PDF Reçete** - Otomatik reçete oluşturma
- 🔔 **Bildirimler** - SMS, Email, WhatsApp

### 🔒 Güvenlik
- 🔐 **Lisans Sistemi** - Donanım kilidi
- 🔑 **Şifreleme** - AES-256 veri koruması
- 📝 **Audit Logs** - Tüm işlem kaydı (Gizli özellik)
- 💾 **Yedekleme** - Otomatik yedekleme (Gizli özellik)

## 📦 Kurulum

### 1. Gereksinimler
```bash
Python 3.10 veya üstü
pip (Python paket yöneticisi)
```

### 2. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Ayarla
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

### 4. Veritabanını Başlat
```bash
python -c "from database.db_manager import DatabaseManager; DatabaseManager()"
```

### 5. Uygulamayı Çalıştır
```bash
python main.py
```

## 🔑 İlk Giriş

**Varsayılan Admin Hesabı:**
- Kullanıcı Adı: `admin`
- Şifre: `admin`

⚠️ **Güvenlik:** İlk girişten sonra şifreyi mutlaka değiştirin!

## 🎯 Kullanım

### TV Bekleme Ekranı
```bash
python tv_launcher.py
```

### Modül Yönetimi
Ayarlar > Modüller bölümünden:
- E-Nabız
- SMS
- Mesajlaşma
- AI Asistan

### API Anahtarları
**AI Asistan için gerekli:**
- Google AI (Gemini): https://ai.google.dev/
- OpenAI (GPT-4): https://platform.openai.com/
- Anthropic (Claude): https://console.anthropic.com/

Ayarlar > AI Sağlayıcı Ayarları'ndan ekleyin.

## 📁 Proje Yapısı
```
krats/
├── main.py                 # Ana giriş noktası
├── tv_launcher.py          # TV ekranı launcher
├── config.py               # Yapılandırma
├── requirements.txt        # Bağımlılıklar
├── .env.example            # Çevre değişkenleri şablonu
├── database/
│   ├── db_manager.py       # Veritabanı yöneticisi
│   └── models.py           # Veri modelleri
├── services/
│   ├── license_service.py  # Lisans kontrolü
│   ├── encryption_manager.py # Veri şifreleme
│   ├── notification_service.py # Bildirimler
│   ├── pdf_service.py      # PDF oluşturma
│   ├── enabiz_service.py   # E-Nabız entegrasyonu
│   ├── google_calendar_service.py # Google Calendar
│   └── backup_service.py   # Yedekleme
├── ui/
│   ├── app_layout.py       # Ana layout
│   └── pages/
│       ├── login.py
│       ├── doctor_home.py
│       ├── patient_list.py
│       ├── appointments.py
│       ├── settings.py
│       ├── backup.py       # 🔒 Gizli özellik
│       ├── audit_logs.py   # 🔒 Gizli özellik
│       └── ...
├── utils/
│   └── logger.py           # Loglama
└── assets/
    └── (logo, resimler)
```

## 🔧 Yapılandırma

### `.env` Dosyası
```env
# Uygulama
APP_NAME=KRATS
APP_VERSION=3.0.0
DEBUG=False

# Veritabanı
DATABASE_PATH=krats.db

# Güvenlik
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-fernet-key-here

# E-Nabız
USS_USERNAME=your-uss-username
USS_PASSWORD=your-uss-password
KURUM_KODU=0000

# Email (Bildirimlersahibi için)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🐛 Hata Ayıklama

### Log Dosyası
```bash
tail -f krats.log
```

### Veritabanı Sıfırlama
```bash
python reset_factory.py
```
⚠️ **Dikkat:** Tüm verileri siler!

### Lisans Sıfırlama
```bash
rm license.key
python main.py
```

## 📊 Performans

- ⚡ Ortalama yanıt süresi: <100ms
- 💾 Veritabanı boyutu: ~50MB (10,000 hasta)
- 🚀 Eş zamanlı kullanıcı: 50+

## 🔐 Güvenlik Notları

1. **Şifreleme:** Tüm hassas veriler (TC, telefon) AES-256 ile şifrelenir
2. **Şifreler:** SHA-256 hash ile saklanır
3. **Session:** Fernet ile imzalanır
4. **Audit:** Tüm işlemler loglanır
5. **Backup:** Günlük otomatik yedekleme

## 🆘 Destek

### Sorun Bildirimi
GitHub Issues: [github.com/yourrepo/krats/issues](https://github.com)

### İletişim
- Email: support@krats.com
- Telefon: +90 XXX XXX XX XX

## 📝 Lisans

Bu yazılım ticari lisans altındadır. Kullanım için geçerli lisans anahtarı gereklidir.

Lisans satın almak için: sales@krats.com

## 🎓 Eğitim Videoları

1. **Temel Kullanım** - [YouTube Link]
2. **Randevu Yönetimi** - [YouTube Link]
3. **AI Asistan Kullanımı** - [YouTube Link]
4. **E-Nabız Entegrasyonu** - [YouTube Link]

## 🔄 Güncellemeler

### v3.0.0 (2024-01-20)
- ✨ AI asistan eklendi (GPT-4, Claude, Gemini)
- ✨ Tıbbi bülten sistemi
- ✨ Gelişmiş güvenlik (şifreleme)
- ✨ Audit log sistemi
- 🐛 100+ bug düzeltmesi

### v2.5.0 (2023-12-15)
- ✨ E-Nabız entegrasyonu
- ✨ Google Calendar senkronizasyonu
- 🐛 Performans iyileştirmeleri

## 🙏 Teşekkürler

- [Flet](https://flet.dev/) - UI Framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Cryptography](https://cryptography.io/) - Şifreleme
- [ReportLab](https://www.reportlab.com/) - PDF

---

**© 2024 KRATS. Tüm hakları saklıdır.**