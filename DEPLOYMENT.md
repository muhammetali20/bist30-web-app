# BIST30 Bot - Ücretsiz Bulut Deployment Rehberi

Bu rehber, BIST30 botunuzu ücretsiz bulut platformlarında 7/24 çalışır hale getirmenizi sağlar.

## 🚀 1. Render.com (Önerilen - En Kolay)

### Adımlar:
1. [Render.com](https://render.com) hesabı oluşturun
2. GitHub'a projenizi upload edin
3. Render'da "New Web Service" oluşturun
4. GitHub repository'nizi bağlayın
5. Aşağıdaki ayarları yapın:
   - **Build Command:** `pip install -r requirements-cloud.txt`
   - **Start Command:** `python src/main.py`
   - **Python Version:** 3.11.9

### Avantajları:
- ✅ 750 saat/ay ücretsiz (7/24 çalışır)
- ✅ Otomatik SSL
- ✅ Kolay setup
- ✅ PostgreSQL desteği

---

## 🚂 2. Railway.app

### Adımlar:
1. [Railway.app](https://railway.app) hesabı oluşturun
2. "Deploy from GitHub repo" seçin
3. Repository'nizi seçin
4. Otomatik deployment başlar

### Avantajları:
- ✅ $5 ücretsiz kredi/ay
- ✅ Çok hızlı deployment
- ✅ Database desteği

---

## ✈️ 3. Fly.io

### Adımlar:
1. [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) kurun
2. Hesap oluşturun: `flyctl auth signup`
3. Proje dizininde: `flyctl launch`
4. Deploy edin: `flyctl deploy`

### Avantajları:
- ✅ 3 ücretsiz app
- ✅ Güçlü performans
- ✅ Global deployment

---

## 🌍 4. Cyclic.sh

### Adımlar:
1. [Cyclic.sh](https://cyclic.sh) hesabı oluşturun
2. GitHub ile bağlayın
3. Repository'yi seçin
4. Otomatik deploy

### Avantajları:
- ✅ Unlimited apps
- ✅ Kolay kullanım

---

## 📦 5. Replit (Geliştirme için ideal)

### Adımlar:
1. [Replit.com](https://replit.com) hesabı oluşturun
2. "Import from GitHub" seçin
3. Repository URL'ini girin
4. "Run" butonuna basın

### Avantajları:
- ✅ Online IDE
- ✅ Anında çalışır
- ❌ Sleep modu var (activity olmayınca durur)

---

## 🔧 Production İçin Önemli Ayarlar

### Environment Variables:
```bash
DEBUG=false
SECRET_KEY=your-secret-key-here
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 1. GitHub Repository Hazırlama:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/bist30-bot.git
git push -u origin main
```

### 2. Gerekli Dosyalar:
- ✅ `Procfile` (oluşturuldu)
- ✅ `runtime.txt` (oluşturuldu) 
- ✅ `requirements-cloud.txt` (oluşturuldu)
- ✅ `render.yaml` (oluşturuldu)

### 3. Database Persistence:
- Render.com: Disk mount kullanın
- Railway: Volume attach edin
- Fly.io: Volume oluşturun

---

## 🤖 Otomatik Çalışması İçin Cron Job

Botun düzenli olarak analiz yapması için:

### Option 1: GitHub Actions (Ücretsiz)
`.github/workflows/scheduler.yml` dosyası oluşturun:

```yaml
name: BIST30 Scheduler
on:
  schedule:
    - cron: '0 10 * * 1-5'  # Hafta içi her gün 10:00'da

jobs:
  run-analysis:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Analysis
        run: |
          curl -X POST ${{ secrets.APP_URL }}/api/bist30/run-weekly-analysis
```

### Option 2: Uptimerobot (Ücretsiz)
1. [UptimeRobot](https://uptimerobot.com) hesabı oluşturun
2. Monitor ekleyin: `https://your-app.render.com/api/bist30/run-weekly-analysis`
3. HTTP(s) - POST request seçin
4. 5 dakikada bir kontrol edin

---

## 🔍 Sorun Giderme

### Yaygın Problemler:

1. **TA-Lib Hatası:**
   - `requirements-cloud.txt` kullanın (talib-binary içerir)

2. **Port Hatası:**
   - Environment variable PORT kullanılıyor

3. **Static Files:**
   - WhiteNoise middleware eklendi

4. **Database:**
   - SQLite production'da çalışır
   - Backup için disk mount kullanın

---

## 📈 Monitoring ve Logs

### 1. Render.com'da:
- Dashboard'da logs görülebilir
- Metrics mevcut

### 2. Telegram Bildirimleri:
- Bot token ekleyin
- Chat ID ayarlayın
- Otomatik raporlar alın

---

## 💰 Maliyet Karşılaştırması

| Platform | Ücretsiz Limit | Ücretli Plan |
|----------|----------------|--------------|
| Render   | 750 saat/ay    | $7/ay        |
| Railway  | $5 kredi/ay    | Pay-per-use  |
| Fly.io   | 3 app          | $1.94/ay     |
| Cyclic   | Unlimited      | $5/ay        |

## 🎯 Sonuç

**En iyi seçenek:** Render.com ile başlayın. Kolay kurulum, güvenilir ve 7/24 çalışır.

Deploy ettikten sonra:
1. URL'nizi kaydedin
2. Telegram bildirimleri aktif edin  
3. UptimeRobot ile monitoring kurun
4. GitHub Actions ile otomatik güncellemeler yapın 