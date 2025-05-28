"""
BIST30 Alım-Satım Bot Konfigürasyon Dosyası
"""

import os

# Telegram Bot Ayarları
# Environment variables'dan oku, yoksa default değerler kullan
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'YOUR_TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

# Yahoo Finance API Ayarları
YAHOO_FINANCE_REGION = "IS"  # Türkiye borsası için

# Veri Çekme Ayarları
DATA_FETCH_INTERVAL = "1wk"  # Haftalık veri
DATA_FETCH_PERIOD = "1y"    # Son 1 yıllık veri

# Strateji Parametreleri
TARGET_PROFIT_PERCENTAGE = 5.0  # Hedef kâr yüzdesi
STOP_LOSS_PERCENTAGE = 3.0      # Stop-loss yüzdesi
MAX_HOLDING_WEEKS = 4           # Maksimum bekleme süresi (hafta)
PARTIAL_PROFIT_THRESHOLD = 0.8   # Kısmi kâr alma eşiği (hedefin %80'i)
PARTIAL_PROFIT_PERCENTAGE = 0.5  # Kısmi kâr alma yüzdesi (pozisyonun %50'si)

# Teknik Gösterge Parametreleri
MA_SHORT = 5   # Kısa vadeli hareketli ortalama periyodu
MA_LONG = 20   # Uzun vadeli hareketli ortalama periyodu
RSI_PERIOD = 14  # RSI periyodu
RSI_OVERSOLD = 30  # RSI aşırı satım seviyesi
RSI_OVERBOUGHT = 70  # RSI aşırı alım seviyesi
MACD_FAST = 12  # MACD hızlı periyot
MACD_SLOW = 26  # MACD yavaş periyot
MACD_SIGNAL = 9  # MACD sinyal periyodu
BOLLINGER_PERIOD = 20  # Bollinger bantları periyodu
BOLLINGER_STD = 2  # Bollinger bantları standart sapma çarpanı

# Veritabanı Ayarları
DATABASE_PATH = "/app/data/bist_bot.db"

# BIST30 Hisseleri
BIST30_SYMBOLS = [
    "AEFES", "AKBNK", "ASELS", "BIMAS", "CIMSA", 
    "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN", 
    "HEKTS", "ISCTR", "KCHOL", "KOZAL", "KRDMD", 
    "MGROS", "PETKM", "SAHOL", "SASA", "SISE", 
    "TAVHL", "TCELL", "THYAO", "TOASO", "TTKOM", 
    "TUPRS", "ULKER", "YKBNK", "PGSUS", "ASTOR"
]

# Dosya Yolları
LOG_FILE_PATH = "/app/data/logs/bist_bot.log"
REPORT_TEMPLATE_PATH = "templates/report_template.html"

# Production/Development ayarları
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

def validate_telegram_config():
    """Telegram konfigürasyonunu doğrula"""
    if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_TOKEN':
        print("⚠️  UYARI: Telegram token ayarlanmamış!")
        print("📋 Telegram bot kurulumu için TELEGRAM_SETUP.md dosyasına bakın")
        return False
    
    if TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID':
        print("⚠️  UYARI: Telegram chat ID ayarlanmamış!")
        print("📋 Telegram bot kurulumu için TELEGRAM_SETUP.md dosyasına bakın")
        return False
    
    print("✅ Telegram konfigürasyonu OK")
    return True

# Startup'ta konfigürasyonu kontrol et
if __name__ == "__main__":
    validate_telegram_config()
