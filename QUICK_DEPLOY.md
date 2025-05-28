# 🚀 HIZLI DEPLOY REHBERİ - BIST30 Bot

## 📋 Bilgileriniz Hazır:
- ✅ **Token:** `8046475269:AAHlONWcOHMZkn_mMsowXzqP6UqyJ4NMw1o`
- ✅ **Bot Username:** `@bist_30_bot`
- ⏳ **Chat ID:** Sonra ekleyeceğiz

## 🌐 1. Render.com'da Deploy

### Adım 1: Render'a Git
1. [render.com](https://render.com) açın
2. **"Sign Up"** ile GitHub hesabınızla giriş yapın

### Adım 2: Web Service Oluştur
1. **"New +"** butonuna tıklayın
2. **"Web Service"** seçin
3. **"Build and deploy from a Git repository"** seçin
4. **GitHub'ı bağlayın** ve repository'nizi seçin

### Adım 3: Ayarları Yapın
```
Name: bist30-bot
Runtime: Python 3
Build Command: pip install -r requirements-cloud.txt
Start Command: python src/main.py
Plan: Free
```

### Adım 4: Environment Variables
**Environment** sekmesinde şunları ekleyin:

```
DEBUG=false
SECRET_KEY=bist30-production-secret-key-2024
TELEGRAM_TOKEN=8046475269:AAHlONWcOHMZkn_mMsowXzqP6UqyJ4NMw1o
TELEGRAM_CHAT_ID=temp_will_update_later
```

### Adım 5: Disk Ekleyin
**Disks** sekmesinde:
```
Mount Path: /app/data
Size: 1 GB
```

### Adım 6: Deploy Et
**"Create Web Service"** butonuna basın!

## ⏱️ 2. Deploy Beklerken Chat ID Bulalım

Deploy süreci devam ederken (5-10 dakika):

1. **Bot ile konuşun:** [t.me/bist_30_bot](https://t.me/bist_30_bot)
2. **"/start" yazın**
3. **Bu URL'ye gidin:** https://api.telegram.org/bot8046475269:AAHlONWcOHMZkn_mMsowXzqP6UqyJ4NMw1o/getUpdates
4. **Chat ID'yi kopyalayın**

## 🔧 3. Chat ID'yi Güncelle

Deploy bittikten sonra:
1. **Render Dashboard** → **Environment** 
2. **TELEGRAM_CHAT_ID** değerini bulduğunuz Chat ID ile değiştirin
3. **"Save Changes"** basın

## ✅ 4. Test Et

Deploy bitince:
1. **Web arayüzüne git:** `https://your-app.onrender.com`
2. **Ayarlar** → **"Telegram Test Et"**
3. **Dashboard** → **"Haftalık Analiz"**

## 🎯 Sonuç

- 🌍 **7/24 çalışacak**
- 📱 **Telegram bildirimleri gelecek** 
- 📊 **Otomatik BIST30 analizi**
- 💰 **Tamamen ücretsiz**

**Şimdi deploy edelim, Chat ID'yi sonra hallederiz! 🚀** 