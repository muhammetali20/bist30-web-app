# BIST30 Alım-Satım Bot Web Uygulaması - Güncellenmiş Sürüm

Bu web uygulaması, BIST30 endeksindeki hisseleri takip eden, teknik analiz yapan ve alım-satım sinyalleri üreten bir botun web arayüzüdür.

## Yeni Özellikler

- **Günlük Raporlama**: Her gün öğlen 13:00'te ve borsa kapanmadan önce BIST30 hisselerinden alım veya satım tavsiyeleri
- **Performans Takibi**: "Alsaydık veya satsaydık şu kadar kârdaydık" şeklinde kâr/zarar analizi
- **Haftalık Performans Raporu**: BIST30'un haftalık olarak yüzde kaç kâr ettirdiğini gösteren detaylı rapor
- **Ertesi Gün Tahmini**: Gelecek işlem günü için alım veya satım tavsiyeleri

## Özellikler

- BIST30 hisselerinin takibi
- Teknik analiz (MA, RSI, MACD, Bollinger Bantları)
- Kâr odaklı alım-satım stratejisi
- Haftalık analiz ve sinyal üretimi
- Kullanıcı dostu web arayüzü
- Detaylı grafik ve tablolar

## Kurulum Gereksinimleri

### 1. Python 3.8+

Python 3.8 veya daha yeni bir sürüm gereklidir. Python'u [python.org](https://www.python.org/downloads/) adresinden indirebilirsiniz.

### 2. TA-Lib Kütüphanesi (Önemli!)

TA-Lib, teknik analiz için kullanılan C kütüphanesidir ve Python wrapper'ı kullanmadan önce sisteminize kurulması gerekir. İşletim sisteminize göre kurulum adımları:

#### Windows:
1. [TA-Lib Windows binary](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) adresinden işletim sisteminize uygun .whl dosyasını indirin
2. İndirdiğiniz .whl dosyasını pip ile kurun:
   ```
   pip install path\to\downloaded\TA_Lib-0.4.0-cp38-cp38-win_amd64.whl
   ```

#### macOS:
Homebrew ile kurulum:
```
brew install ta-lib
```

#### Linux (Ubuntu/Debian):
```
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

### 3. Python Bağımlılıkları

Gerekli Python paketlerini kurmak için:

```
pip install -r requirements.txt
```

## Uygulama Kurulumu

1. Bu zip dosyasını bilgisayarınızda bir klasöre çıkarın
2. Yukarıdaki gereksinimleri sağladığınızdan emin olun
3. Komut satırında uygulamanın ana dizinine gidin:
   ```
   cd path/to/bist30_app_updated
   ```
4. Gerekli Python paketlerini kurun:
   ```
   pip install -r requirements.txt
   ```

## Uygulamayı Çalıştırma

1. Komut satırında uygulamanın ana dizininde olduğunuzdan emin olun
2. Aşağıdaki komutu çalıştırın:
   ```
   python src/main.py
   ```
3. Uygulama başladığında, web tarayıcınızda şu adresi açın:
   ```
   http://localhost:5000
   ```

## Yeni Özelliklerin Kullanımı

### Günlük Raporlar
- "Raporlar" sekmesinden "Günlük Öğlen Raporu" veya "Günlük Kapanış Raporu" butonlarına tıklayarak günlük raporları oluşturabilirsiniz
- Raporlar, o gün için alım/satım sinyallerini ve "alsaydık/satsaydık" performans simülasyonunu gösterir

### Haftalık Performans Raporu
- "Raporlar" sekmesinden "Haftalık Rapor" butonuna tıklayarak haftalık performans raporunu oluşturabilirsiniz
- Rapor, BIST30 endeksinin haftalık performansını ve botun tavsiyelerinin performansını karşılaştırır

### Ertesi Gün Tahmini
- "Raporlar" sekmesinden "Ertesi Gün Tahmini" butonuna tıklayarak gelecek işlem günü için tahminleri görebilirsiniz
- Tahminler, teknik göstergelere dayalı olarak alım, satım veya bekle tavsiyeleri içerir

## Telegram Entegrasyonu (İsteğe Bağlı)

Telegram bildirimleri almak istiyorsanız:

1. Telegram'da [@BotFather](https://t.me/botfather) ile yeni bir bot oluşturun
2. Bot token'ını alın
3. `src/bot/config.py` dosyasında TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID değerlerini güncelleyin

## Sorun Giderme

### TA-Lib Kurulum Sorunları

TA-Lib kurulumunda sorun yaşıyorsanız:

- Windows için: Visual C++ Build Tools kurulu olduğundan emin olun
- Linux için: build-essential ve python-dev paketlerinin kurulu olduğundan emin olun:
  ```
  sudo apt-get install build-essential python-dev
  ```
- macOS için: XCode Command Line Tools kurulu olduğundan emin olun:
  ```
  xcode-select --install
  ```

### Diğer Sorunlar

- Bağımlılık hatası alırsanız, eksik paketi pip ile kurun:
  ```
  pip install paket_adı
  ```
- Port çakışması yaşarsanız, `src/main.py` dosyasında port numarasını değiştirin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için LICENSE dosyasına bakın.
