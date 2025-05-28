"""
BIST30 Alım-Satım Bot - Sinyal Üreteci Modülü
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import sys

# Konfigürasyon dosyasını import et
from src.bot.config import *

# Loglama ayarları
log_handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger('SignalGenerator')

class SignalGenerator:
    """BIST30 hisseleri için alım-satım sinyalleri üreten sınıf"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        SignalGenerator sınıfını başlat
        
        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        logger.info("SignalGenerator başlatıldı")
    
    def get_latest_data_with_indicators(self, symbol, limit=10):
        """
        Belirtilen hisse için en son verileri ve göstergeleri getir
        
        Args:
            symbol: Hisse sembolü
            limit: Kaç satır veri getirileceği
            
        Returns:
            pandas.DataFrame: Veritabanından çekilen veri ve göstergeler
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = f'''
            SELECT s.*, t.ma_short, t.ma_long, t.rsi, t.macd, t.macd_signal,
                   t.bollinger_upper, t.bollinger_middle, t.bollinger_lower
            FROM stock_data s
            LEFT JOIN technical_indicators t ON s.symbol = t.symbol AND s.date = t.date
            WHERE s.symbol = ?
            ORDER BY s.date DESC
            LIMIT {limit}
            '''
            
            data = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            # Tarihe göre sırala (eskiden yeniye)
            if not data.empty:
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
            
            return data
        except Exception as e:
            logger.error(f"{symbol} için veri ve gösterge getirme hatası: {e}")
            return pd.DataFrame()
    
    def check_buy_signals(self, data):
        """
        Alım sinyallerini kontrol et
        
        Args:
            data: Hisse verisi ve göstergeleri (pandas.DataFrame)
            
        Returns:
            bool: Alım sinyali varsa True, yoksa False
            str: Sinyal nedeni
        """
        if data.empty or len(data) < 2:
            return False, "Yeterli veri yok"
        
        # Son satırı al
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        signals = []
        
        # 1. Fiyat 5 haftalık hareketli ortalamanın üzerinde ve yükseliş trendinde
        if (last_row['close'] > last_row['ma_short'] and 
            last_row['close'] > prev_row['close']):
            signals.append("Fiyat 5 haftalık MA üzerinde ve yükseliş trendinde")
        
        # 2. RSI 30-50 aralığında ve yükseliş eğiliminde
        if (30 <= last_row['rsi'] <= 50 and 
            last_row['rsi'] > prev_row['rsi']):
            signals.append("RSI 30-50 aralığında ve yükseliş eğiliminde")
        
        # 3. MACD, sinyal çizgisini yukarı yönde kesmiş
        if (prev_row['macd'] < prev_row['macd_signal'] and 
            last_row['macd'] > last_row['macd_signal']):
            signals.append("MACD sinyal çizgisini yukarı yönde kesmiş")
        
        # 4. Fiyat Bollinger alt bandına yakın veya bandı aşağıdan yukarı kesmiş
        band_threshold = (last_row['bollinger_middle'] - last_row['bollinger_lower']) * 0.2
        if (last_row['close'] <= last_row['bollinger_lower'] + band_threshold or
            (prev_row['close'] < prev_row['bollinger_lower'] and 
             last_row['close'] > last_row['bollinger_lower'])):
            signals.append("Fiyat Bollinger alt bandına yakın veya bandı aşağıdan yukarı kesmiş")
        
        # 5. Son 4 haftanın en yüksek işlem hacmi görülmüş
        if len(data) >= 5 and last_row['volume'] == data['volume'].tail(5).max():
            signals.append("Son 4 haftanın en yüksek işlem hacmi görülmüş")
        
        # En az 2 sinyal varsa alım sinyali üret
        if len(signals) >= 2:
            return True, ", ".join(signals)
        
        return False, "Yeterli sinyal yok"
    
    def check_sell_signals(self, data, buy_price=None, buy_date=None):
        """
        Satım sinyallerini kontrol et
        
        Args:
            data: Hisse verisi ve göstergeleri (pandas.DataFrame)
            buy_price: Alış fiyatı (varsa)
            buy_date: Alış tarihi (varsa)
            
        Returns:
            bool: Satım sinyali varsa True, yoksa False
            str: Sinyal nedeni
        """
        if data.empty or len(data) < 2:
            return False, "Yeterli veri yok"
        
        # Son satırı al
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        # Alış fiyatı ve tarihi varsa kâr hedefi ve stop-loss kontrolü yap
        if buy_price is not None and buy_date is not None:
            # Kâr hedefi kontrolü
            profit_percentage = (last_row['close'] - buy_price) / buy_price * 100
            if profit_percentage >= TARGET_PROFIT_PERCENTAGE:
                return True, f"Hedef kâr yüzdesine ulaşıldı: %{profit_percentage:.2f}"
            
            # Stop-loss kontrolü
            if profit_percentage <= -STOP_LOSS_PERCENTAGE:
                return True, f"Stop-loss seviyesine gelindiği için satış: %{profit_percentage:.2f}"
            
            # Maksimum bekleme süresi kontrolü
            buy_date = pd.to_datetime(buy_date)
            last_date = pd.to_datetime(last_row['date'])
            weeks_passed = (last_date - buy_date).days / 7
            if weeks_passed >= MAX_HOLDING_WEEKS:
                return True, f"Maksimum bekleme süresi doldu: {weeks_passed:.1f} hafta"
        
        signals = []
        
        # 1. RSI > 70 ve düşüş eğiliminde
        if last_row['rsi'] > 70 and last_row['rsi'] < prev_row['rsi']:
            signals.append("RSI > 70 ve düşüş eğiliminde")
        
        # 2. MACD, sinyal çizgisini aşağı yönde kesmiş
        if (prev_row['macd'] > prev_row['macd_signal'] and 
            last_row['macd'] < last_row['macd_signal']):
            signals.append("MACD sinyal çizgisini aşağı yönde kesmiş")
        
        # 3. Fiyat 5 haftalık hareketli ortalamanın altına düşmüş
        if (prev_row['close'] > prev_row['ma_short'] and 
            last_row['close'] < last_row['ma_short']):
            signals.append("Fiyat 5 haftalık MA altına düşmüş")
        
        # 4. Fiyat Bollinger üst bandını yukarıdan aşağı kesmiş
        if (prev_row['close'] > prev_row['bollinger_upper'] and 
            last_row['close'] < last_row['bollinger_upper']):
            signals.append("Fiyat Bollinger üst bandını yukarıdan aşağı kesmiş")
        
        # En az 2 sinyal varsa satım sinyali üret
        if len(signals) >= 2:
            return True, ", ".join(signals)
        
        return False, "Yeterli sinyal yok"
    
    def generate_signals(self, symbol):
        """
        Belirtilen hisse için alım-satım sinyalleri üret
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            dict: Sinyal bilgileri
        """
        try:
            # Son 10 haftalık veriyi çek
            data = self.get_latest_data_with_indicators(symbol, 10)
            
            if data.empty:
                logger.warning(f"{symbol} için veri bulunamadı")
                return {
                    'symbol': symbol,
                    'buy_signal': False,
                    'sell_signal': False,
                    'buy_reason': "Veri bulunamadı",
                    'sell_reason': "Veri bulunamadı",
                    'current_price': None,
                    'last_date': None
                }
            
            # Son fiyat ve tarih
            last_row = data.iloc[-1]
            current_price = last_row['close']
            last_date = last_row['date']
            
            # Alım sinyali kontrolü
            buy_signal, buy_reason = self.check_buy_signals(data)
            
            # Satım sinyali kontrolü (şu an için alış fiyatı ve tarihi olmadan)
            sell_signal, sell_reason = self.check_sell_signals(data)
            
            # Sonuçları döndür
            return {
                'symbol': symbol,
                'buy_signal': buy_signal,
                'sell_signal': sell_signal,
                'buy_reason': buy_reason,
                'sell_reason': sell_reason,
                'current_price': current_price,
                'last_date': last_date
            }
        
        except Exception as e:
            logger.error(f"{symbol} için sinyal üretme hatası: {e}")
            return {
                'symbol': symbol,
                'buy_signal': False,
                'sell_signal': False,
                'buy_reason': f"Hata: {str(e)}",
                'sell_reason': f"Hata: {str(e)}",
                'current_price': None,
                'last_date': None
            }
    
    def save_signal_to_db(self, signal):
        """
        Üretilen sinyali veritabanına kaydet
        
        Args:
            signal: Sinyal bilgileri (dict)
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if signal['current_price'] is None or signal['last_date'] is None:
            logger.warning(f"{signal['symbol']} için kaydedilecek sinyal yok")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Alım sinyali varsa kaydet
            if signal['buy_signal']:
                conn.execute('''
                INSERT INTO signals 
                (symbol, date, signal_type, price, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    signal['symbol'],
                    signal['last_date'].strftime('%Y-%m-%d') if isinstance(signal['last_date'], datetime) else signal['last_date'],
                    'BUY',
                    float(signal['current_price']),
                    signal['buy_reason'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            # Satım sinyali varsa kaydet
            if signal['sell_signal']:
                conn.execute('''
                INSERT INTO signals 
                (symbol, date, signal_type, price, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    signal['symbol'],
                    signal['last_date'].strftime('%Y-%m-%d') if isinstance(signal['last_date'], datetime) else signal['last_date'],
                    'SELL',
                    float(signal['current_price']),
                    signal['sell_reason'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            
            if signal['buy_signal'] or signal['sell_signal']:
                logger.info(f"{signal['symbol']} için sinyal veritabanına kaydedildi")
                return True
            else:
                return False
        
        except Exception as e:
            logger.error(f"{signal['symbol']} için sinyal kaydetme hatası: {e}")
            return False
    
    def generate_all_signals(self):
        """
        Tüm BIST30 hisseleri için sinyal üret ve veritabanına kaydet
        
        Returns:
            dict: Alım ve satım sinyalleri olan hisseler
        """
        buy_signals = []
        sell_signals = []
        
        for symbol in BIST30_SYMBOLS:
            try:
                signal = self.generate_signals(symbol)
                self.save_signal_to_db(signal)
                
                if signal['buy_signal']:
                    buy_signals.append(signal)
                
                if signal['sell_signal']:
                    sell_signals.append(signal)
                
            except Exception as e:
                logger.error(f"{symbol} için sinyal işleme hatası: {e}")
        
        logger.info(f"Toplam {len(buy_signals)} alım ve {len(sell_signals)} satım sinyali üretildi")
        
        return {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        }

# Test fonksiyonu
def test_signal_generator():
    """SignalGenerator sınıfını test et"""
    generator = SignalGenerator()
    
    # Test sembolleri
    test_symbols = ["GARAN", "THYAO", "AKBNK"]
    
    for symbol in test_symbols:
        print(f"\n{symbol} için sinyal testi:")
        signal = generator.generate_signals(symbol)
        
        print(f"Güncel Fiyat: {signal['current_price']}")
        print(f"Son Tarih: {signal['last_date']}")
        print(f"Alım Sinyali: {'EVET' if signal['buy_signal'] else 'HAYIR'}")
        print(f"Alım Nedeni: {signal['buy_reason']}")
        print(f"Satım Sinyali: {'EVET' if signal['sell_signal'] else 'HAYIR'}")
        print(f"Satım Nedeni: {signal['sell_reason']}")
        
        if signal['buy_signal'] or signal['sell_signal']:
            success = generator.save_signal_to_db(signal)
            print(f"Veritabanına kayıt: {'Başarılı' if success else 'Başarısız'}")

if __name__ == "__main__":
    test_signal_generator()
