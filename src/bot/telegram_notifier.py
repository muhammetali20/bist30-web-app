"""
BIST30 Alım-Satım Bot - Telegram Bildirim Modülü
"""

import os
import logging
import sys
import json
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Konfigürasyon dosyasını import et
from src.bot.config import *

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TelegramNotifier')

class TelegramNotifier:
    """Telegram üzerinden bildirim gönderen sınıf"""
    
    def __init__(self, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID):
        """
        TelegramNotifier sınıfını başlat
        
        Args:
            token: Telegram Bot API token
            chat_id: Mesaj gönderilecek chat ID
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        logger.info("TelegramNotifier başlatıldı")
    
    async def send_message(self, message):
        """
        Telegram üzerinden mesaj gönder
        
        Args:
            message: Gönderilecek mesaj
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            logger.info("Telegram mesajı gönderildi")
            return True
        except TelegramError as e:
            logger.error(f"Telegram mesaj gönderme hatası: {e}")
            return False
    
    def send_message_sync(self, message):
        """
        Telegram üzerinden mesaj gönder (senkron)
        
        Args:
            message: Gönderilecek mesaj
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.send_message(message))
            return result
        finally:
            loop.close()
    
    def format_buy_signal(self, signal):
        """
        Alım sinyali için mesaj formatla
        
        Args:
            signal: Sinyal bilgileri (dict)
            
        Returns:
            str: Formatlanmış mesaj
        """
        return f"""
🟢 <b>ALIM SİNYALİ</b> 🟢

<b>Hisse:</b> {signal['symbol']}
<b>Fiyat:</b> {signal['current_price']:.2f} TL
<b>Tarih:</b> {signal['last_date'].strftime('%d.%m.%Y') if isinstance(signal['last_date'], datetime) else signal['last_date']}

<b>Sinyal Nedeni:</b>
{signal['buy_reason']}

<b>Hedef Kâr:</b> %{TARGET_PROFIT_PERCENTAGE:.1f} (≈ {signal['current_price'] * (1 + TARGET_PROFIT_PERCENTAGE/100):.2f} TL)
<b>Stop-Loss:</b> %{STOP_LOSS_PERCENTAGE:.1f} (≈ {signal['current_price'] * (1 - STOP_LOSS_PERCENTAGE/100):.2f} TL)

#BIST30 #{signal['symbol']}
"""
    
    def format_sell_signal(self, signal):
        """
        Satım sinyali için mesaj formatla
        
        Args:
            signal: Sinyal bilgileri (dict)
            
        Returns:
            str: Formatlanmış mesaj
        """
        return f"""
🔴 <b>SATIM SİNYALİ</b> 🔴

<b>Hisse:</b> {signal['symbol']}
<b>Fiyat:</b> {signal['current_price']:.2f} TL
<b>Tarih:</b> {signal['last_date'].strftime('%d.%m.%Y') if isinstance(signal['last_date'], datetime) else signal['last_date']}

<b>Sinyal Nedeni:</b>
{signal['sell_reason']}

#BIST30 #{signal['symbol']}
"""
    
    def format_weekly_report(self, signals):
        """
        Haftalık rapor için mesaj formatla
        
        Args:
            signals: Tüm sinyaller (dict)
            
        Returns:
            str: Formatlanmış mesaj
        """
        buy_signals = signals.get('buy_signals', [])
        sell_signals = signals.get('sell_signals', [])
        
        message = f"""
📊 <b>BIST30 HAFTALIK RAPOR</b> 📊
<b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y')}

"""
        
        if buy_signals:
            message += "<b>🟢 ALIM SİNYALLERİ</b>\n"
            for signal in buy_signals:
                message += f"• {signal['symbol']} - {signal['current_price']:.2f} TL\n"
            message += "\n"
        else:
            message += "<b>🟢 ALIM SİNYALİ YOK</b>\n\n"
        
        if sell_signals:
            message += "<b>🔴 SATIM SİNYALLERİ</b>\n"
            for signal in sell_signals:
                message += f"• {signal['symbol']} - {signal['current_price']:.2f} TL\n"
            message += "\n"
        else:
            message += "<b>🔴 SATIM SİNYALİ YOK</b>\n\n"
        
        message += """
<i>Detaylı bilgiler için her sinyal ayrıca gönderilecektir.</i>

#BIST30 #HaftalıkRapor
"""
        return message
    
    def send_signals(self, signals):
        """
        Tüm sinyalleri Telegram üzerinden gönder
        
        Args:
            signals: Tüm sinyaller (dict)
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        try:
            buy_signals = signals.get('buy_signals', [])
            sell_signals = signals.get('sell_signals', [])
            
            # Haftalık rapor gönder
            weekly_report = self.format_weekly_report(signals)
            self.send_message_sync(weekly_report)
            
            # Alım sinyallerini gönder
            for signal in buy_signals:
                message = self.format_buy_signal(signal)
                self.send_message_sync(message)
            
            # Satım sinyallerini gönder
            for signal in sell_signals:
                message = self.format_sell_signal(signal)
                self.send_message_sync(message)
            
            logger.info(f"Toplam {len(buy_signals)} alım ve {len(sell_signals)} satım sinyali gönderildi")
            return True
        
        except Exception as e:
            logger.error(f"Sinyal gönderme hatası: {e}")
            return False

# Test fonksiyonu
def test_telegram_notifier():
    """TelegramNotifier sınıfını test et"""
    # Not: Gerçek bir test için geçerli token ve chat_id gereklidir
    # Bu test fonksiyonu sadece kod yapısını göstermek içindir
    
    print("Telegram Notifier Test")
    print("Not: Gerçek bir test için config.py dosyasında geçerli TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID tanımlanmalıdır.")
    
    # Test verileri
    test_signals = {
        'buy_signals': [
            {
                'symbol': 'GARAN',
                'buy_signal': True,
                'sell_signal': False,
                'buy_reason': 'Fiyat 5 haftalık MA üzerinde ve yükseliş trendinde, RSI 30-50 aralığında ve yükseliş eğiliminde',
                'sell_reason': 'Yeterli sinyal yok',
                'current_price': 110.50,
                'last_date': datetime.now()
            }
        ],
        'sell_signals': [
            {
                'symbol': 'THYAO',
                'buy_signal': False,
                'sell_signal': True,
                'buy_reason': 'Yeterli sinyal yok',
                'sell_reason': 'Hedef kâr yüzdesine ulaşıldı: %5.2',
                'current_price': 275.30,
                'last_date': datetime.now()
            }
        ]
    }
    
    # Mesaj formatlamayı test et (token olmadan da çalışır)
    notifier = TelegramNotifier()
    
    print("\nAlım Sinyali Formatı:")
    buy_message = notifier.format_buy_signal(test_signals['buy_signals'][0])
    print(buy_message)
    
    print("\nSatım Sinyali Formatı:")
    sell_message = notifier.format_sell_signal(test_signals['sell_signals'][0])
    print(sell_message)
    
    print("\nHaftalık Rapor Formatı:")
    weekly_report = notifier.format_weekly_report(test_signals)
    print(weekly_report)
    
    # Gerçek gönderim testi (geçerli token ve chat_id gerektirir)
    if TELEGRAM_TOKEN != "YOUR_TELEGRAM_TOKEN" and TELEGRAM_CHAT_ID != "YOUR_CHAT_ID":
        print("\nGerçek mesaj gönderimi test ediliyor...")
        notifier.send_message_sync("🤖 BIST30 Bot Test Mesajı")
        print("Test mesajı gönderildi. Lütfen Telegram'ı kontrol edin.")
    else:
        print("\nGerçek mesaj gönderimi için geçerli token ve chat_id gereklidir.")

if __name__ == "__main__":
    test_telegram_notifier()
