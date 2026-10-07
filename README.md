# Proliz OBS Otomasyon & Kontenjan Takip Botu

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A.svg?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg?logo=windows&logoColor=white)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Üniversitelerin **Proliz Öğrenci Bilgi Sistemi (OBS)** altyapısında ders kayıt dönemlerindeki yoğunluk, kontenjan kilitlenmesi ve zamanlama stresini ortadan kaldırmak için geliştirilmiş yüksek performanslı masaüstü otomasyonu ve kontenjan avcısı (sniper) aracı.

---

## 🌟 Öne Çıkan Yetenekler

- 🖥️ **Modern Masaüstü Arayüzü**: Koyu tema destekli, gerçek zamanlı durum göstergeleri, interaktif ders seçim listesi ve seans log terminali.
- ⏱️ **Milisaniyelik Geri Sayım & Otomatik Tetikleme**: Ders kayıt saati açıldığı an (ör. 08:30:00.000) insan reflekslerinin ötesinde milisaniyelik hassasiyetle oturum açar ve dersleri seçer.
- 🎯 **Kontenjan Takipçisi & Anlık Sniper**: Dolu olan seçmeli dersleri arka planda periyodik olarak kontrol eder; kontenjan açıldığı mikrosaniyede kontenjanı yakalar ve kaydı tamamlar.
- 🤖 **Tam Entegre Telegram Botu**:
  - Kontenjan durumu değiştiğinde veya ders kaydı tamamlandığında anında cep telefonunuza bildirim gönderir.
  - İki yönlü komut desteği ile dışarıdayken Telegram üzerinden botu uzaktan sorgulama ve tetikleme imkanı sunar.
- 🧩 **Akıllı Captcha Çözücü**: Proliz sisteminin sunduğu matematiksel doğrulama sorularını DOM üzerinden mikro-saniyeler içinde çözer.
- 🔒 **Sıfır İz / Gizlilik Odaklı Mimari**: Kimlik bilgileri ve şifreler yalnızca kendi yerel makinenizde tutulur, hiçbir sunucuya iletilmez.

---

## 🏗️ Sistem Mimarisi

```text
                                  +-----------------------+
                                  |   Masaüstü GUI (Tk)   |
                                  +-----------+-----------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
       +-----------v-----------+                             +-----------v-----------+
       |   Proliz Web Engine   |                             |    Telegram Servisi   |
       |  (Selenium WebDriver) |                             |     (Bot API / Web)   |
       +-----------+-----------+                             +-----------+-----------+
                   |                                                     |
       +-----------v-----------+                             +-----------v-----------+
       | OBS Giriş & Kayıt     |                             | Mobil Bildirimler &   |
       | Kontenjan Takipçisi   |                             | Uzaktan Komut Dinleme |
       +-----------------------+                             +-----------------------+
```

---

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
- Python 3.10 veya üzeri
- Google Chrome tarayıcısı
- Bağımlılıkları yükleyin:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Başlatma
* **Windows (Tek Tıkla):** `baslat.bat` dosyasına çift tıklayın (gerekli sanal ortamı ve eksik paketleri otomatik algılar).
* **Terminal Üzerinden:**
  ```bash
  python main.py
  ```

---

## 📱 Telegram Botu Kurulum & Yapılandırma Rehberi

Botun durumunu telefonunuzdan canlı izlemek ve uzaktan yönetmek için ücretsiz bir Telegram botu bağlayabilirsiniz. Kurulum yalnızca 2 dakika sürer:

### Adım 1: Bot Oluşturma (@BotFather)
1. Telegram uygulamasını açın ve arama çubuğuna `@BotFather` yazın (mavi onay rozetli resmi hesap).
2. BotFather'a `/start` komutunu gönderin, ardından `/newbot` yazın.
3. Botunuz için görünen bir isim girin (Örn: `Ders Kayıt Takipçim`).
4. Botunuz için sonu `_bot` ile biten benzersiz bir kullanıcı adı belirleyin (Örn: `benim_ders_kayit_botum`).
5. BotFather size aşağıdaki gibi bir **API Token** verecektir:
   ```text
   1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567
   ```
   Bu tokenı kopyalayın.

### Adım 2: Chat ID (Kullanıcı Kimliği) Öğrenme
1. Az önce oluşturduğunuz botun linkine tıklayın ve bota `/start` mesajı atın (böylece bot size mesaj atma izni kazanır).
2. Telegram arama kısmına `@userinfobot` veya `@RawDataBot` yazıp başlatın.
3. Bot size kendi kullanıcı profilinizi gösteren bir yanıt dönecektir. Buradaki `Id:` satırındaki sayıyı kopyalayın (Örn: `123456789`).

### Adım 3: Bilgileri Uygulamaya Girme
İki yöntemden birini seçebilirsiniz:
- **Yöntem A (Grafik Arayüz):** Uygulamayı açın, **Telegram Ayarları** sekmesine gidin. Token ve Chat ID kutularına bilgilerinizi yapıştırıp **"Test Mesajı Gönder"** butonuna basın. Telefonunuza test bildirimi gelirse bağlantı başarılıdır!
- **Yöntem B (Dosya ile):** `config.example.json` dosyasını kopyalayıp adını `config.json` yapın ve değerleri girin:
  ```json
  {
      "telegram_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
      "telegram_chat_id": "YOUR_CHAT_ID_HERE",
      "telegram_enabled": true,
      "telegram_listener_enabled": true
  }
  ```

### 📲 Uzaktan Telegram Komutları
Uygulama arka planda çalışırken cep telefonunuzdan botunuza aşağıdaki mesajları atarak kontrol sağlayabilirsiniz:
- `/durum` : Botun aktiflik durumunu, kalan süreyi ve izlenen dersleri listeler.
- `/kaydet` : Planlanan süreyi beklemeden anlık ders kaydı döngüsünü tetikler.
- `/durdur` : Otomasyonu ve izlemeyi uzaktan güvenli şekilde durdurur.

---

## 📁 Proje Dosya Yapısı

```text
proliz-obs-bot/
├── bot.py                  # Çekirdek otomasyon döngüsü
├── proliz_engine.py        # Proliz OBS DOM etkileşim ve oturum motoru
├── quota_watcher.py        # Arka plan kontenjan sorgulayıcı ve sniper servisi
├── telegram_service.py     # İki yönlü Telegram bildirim ve komut dinleyicisi
├── logger_service.py       # Renkli arayüz ve dosya loglayıcı
├── curriculum_data.py      # Bölüm ders kataloğu ve müfredat modelleri
├── gui.py                  # Koyu tema destekli masaüstü kontrol paneli
├── main.py                 # Uygulama giriş noktası
├── baslat.bat              # Windows tek tıkla başlatıcı
├── requirements.txt        # Gerekli Python kütüphaneleri
├── config.example.json     # Yapılandırma şablonu
└── README.md
```

---

## 🔒 Güvenlik & Sorumluluk Reddi

- Bu yazılım açık kaynaklı ve eğitim amaçlı geliştirilmiştir.
- Kimlik numarası, e-Devlet şifresi ve API anahtarları asla üçüncü parti sunuculara veya harici servislere gönderilmez; yalnızca yerel Chrome tarayıcı oturumunda kullanılır.
- Kullanıcı giriş bilgilerinizin güvenliğini sağlamak için `config.json` dosyanızı kimseyle paylaşmayınız.

---

## 👤 Geliştirici
- **İbrahim Halil Doğan** ([@eyyoibo](https://github.com/eyyoibo))
