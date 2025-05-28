# 🚀 BIST30 Trading Bot

BIST30 endeksindeki hisseleri takip eden, teknik analiz yapan ve Telegram bildirimleri gönderen akıllı trading bot.

## 🎯 Özellikler

- 📈 **BIST30 hisselerini takip**
- 🤖 **Teknik analiz** (MA, RSI, MACD, Bollinger Bands)
- 📱 **Telegram bildirimleri**
- 🎯 **Akıllı sinyal üretimi** (%5 hedef kâr, %3 stop-loss)
- 📊 **Haftalık raporlar**
- 🌐 **Modern web arayüzü**

## 🛠️ Teknolojiler

- **Backend:** Python Flask
- **Veritabanı:** SQLite
- **Veri Kaynağı:** Yahoo Finance API
- **Bildirimler:** Telegram Bot API
- **Frontend:** HTML/CSS/JavaScript

## 🚀 Deployment

### Render.com ile Deploy (Ücretsiz)

1. Bu repository'yi fork edin
2. [Render.com](https://render.com) hesabı oluşturun
3. Web Service oluşturun ve GitHub'dan bu repo'yu seçin
4. Build ayarları:
   ```
   Build Command: pip install -r requirements-cloud.txt
   Start Command: python src/main.py
   ```

5. **Environment Variables** ekleyin:
   ```
   DEBUG=false
   SECRET_KEY=your-secret-key-here
   TELEGRAM_TOKEN=your-telegram-bot-token
   TELEGRAM_CHAT_ID=your-telegram-chat-id
   ```

6. **Disk Mount** ekleyin:
   ```
   Mount Path: /app/data
   Size: 1 GB
   ```

## 🔧 Telegram Bot Kurulumu

1. [@BotFather](https://t.me/botfather) ile bot oluşturun
2. Token'ı alın
3. Bot ile konuşun
4. Chat ID'nizi `https://api.telegram.org/bot<TOKEN>/getUpdates` ile bulun

## 📁 Proje Yapısı

```
src/
├── bot/                 # Bot mantığı
│   ├── config.py       # Konfigürasyon
│   ├── data_fetcher.py # Veri çekme
│   ├── technical_analyzer.py # Teknik analiz
│   ├── signal_generator.py   # Sinyal üretme
│   └── telegram_notifier.py  # Telegram bildirimleri
├── routes/             # Web routes
├── static/             # Frontend dosyaları
└── main.py            # Ana uygulama

```

## 🔒 Güvenlik

- Token'lar ve API anahtarları asla kodda bulunmamalı
- Sadece environment variables kullanın
- `.env` dosyalarını `.gitignore`'a ekleyin

## 📚 Detaylı Dokümantasyon

- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Genel deployment rehberi
- [`TELEGRAM_SETUP.md`](TELEGRAM_SETUP.md) - Telegram kurulum rehberi
- [`FINAL_DEPLOY_INSTRUCTIONS.md`](FINAL_DEPLOY_INSTRUCTIONS.md) - Hızlı deploy rehberi

## 📄 Lisans

MIT License

---

⚠️ **DİKKAT:** Bu bot yatırım tavsiyesi vermez. Sadece teknik analiz yapar. Yatırım kararlarınızı kendi sorumluluğunuzda alın.
