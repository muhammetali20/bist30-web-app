"""
BIST30 Alım-Satım Bot - Teknik Analiz Modülü
"""

import os
import logging
import pandas as pd
import numpy as np
# import talib  # Removed - using manual calculations instead
from datetime import datetime
import sqlite3
import sys

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
logger = logging.getLogger('TechnicalAnalyzer')

class TechnicalAnalyzer:
    """BIST30 hisseleri için teknik analiz yapan sınıf"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        TechnicalAnalyzer sınıfını başlat
        
        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        logger.info("TechnicalAnalyzer başlatıldı")
    
    def get_stock_data(self, symbol, limit=52):
        """
        Belirtilen hisse için veritabanından veri çek
        
        Args:
            symbol: Hisse sembolü
            limit: Kaç haftalık veri çekileceği (varsayılan: 52 hafta)
            
        Returns:
            pandas.DataFrame: Veritabanından çekilen veri
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = f'''
            SELECT * FROM stock_data
            WHERE symbol = ?
            ORDER BY date DESC
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
            logger.error(f"{symbol} için veri getirme hatası: {e}")
            return pd.DataFrame()
    
    def calculate_moving_averages(self, data, short_period=MA_SHORT, long_period=MA_LONG):
        """
        Hareketli ortalamaları hesapla
        
        Args:
            data: Hisse verisi (pandas.DataFrame)
            short_period: Kısa vadeli hareketli ortalama periyodu
            long_period: Uzun vadeli hareketli ortalama periyodu
            
        Returns:
            pandas.DataFrame: Hareketli ortalamalar eklenmiş veri
        """
        if data.empty:
            return data
        
        try:
            # Kısa vadeli hareketli ortalama
            data['ma_short'] = data['close'].rolling(window=short_period).mean()
            
            # Uzun vadeli hareketli ortalama
            data['ma_long'] = data['close'].rolling(window=long_period).mean()
            
            return data
        except Exception as e:
            logger.error(f"Hareketli ortalama hesaplama hatası: {e}")
            return data
    
    def calculate_rsi(self, data, period=RSI_PERIOD):
        """
        Göreceli Güç Endeksi (RSI) hesapla
        
        Args:
            data: Hisse verisi (pandas.DataFrame)
            period: RSI periyodu
            
        Returns:
            pandas.DataFrame: RSI eklenmiş veri
        """
        if data.empty:
            return data
        
        try:
            # Fiyat değişimlerini hesapla
            delta = data['close'].diff()
            
            # Pozitif ve negatif değişimleri ayır
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # İlk değerleri hesapla
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # RSI hesapla
            rs = avg_gain / avg_loss
            data['rsi'] = 100 - (100 / (1 + rs))
            
            return data
        except Exception as e:
            logger.error(f"RSI hesaplama hatası: {e}")
            return data
    
    def calculate_macd(self, data, fast_period=MACD_FAST, slow_period=MACD_SLOW, signal_period=MACD_SIGNAL):
        """
        MACD (Moving Average Convergence Divergence) hesapla
        
        Args:
            data: Hisse verisi (pandas.DataFrame)
            fast_period: Hızlı EMA periyodu
            slow_period: Yavaş EMA periyodu
            signal_period: Sinyal EMA periyodu
            
        Returns:
            pandas.DataFrame: MACD eklenmiş veri
        """
        if data.empty:
            return data
        
        try:
            # Hızlı ve yavaş EMA hesapla
            ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
            ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
            
            # MACD hattı
            data['macd'] = ema_fast - ema_slow
            
            # Sinyal hattı
            data['macd_signal'] = data['macd'].ewm(span=signal_period, adjust=False).mean()
            
            return data
        except Exception as e:
            logger.error(f"MACD hesaplama hatası: {e}")
            return data
    
    def calculate_bollinger_bands(self, data, period=BOLLINGER_PERIOD, std_dev=BOLLINGER_STD):
        """
        Bollinger Bantlarını hesapla
        
        Args:
            data: Hisse verisi (pandas.DataFrame)
            period: Bollinger periyodu
            std_dev: Standart sapma çarpanı
            
        Returns:
            pandas.DataFrame: Bollinger Bantları eklenmiş veri
        """
        if data.empty:
            return data
        
        try:
            # Orta bant (SMA)
            data['bollinger_middle'] = data['close'].rolling(window=period).mean()
            
            # Standart sapma
            rolling_std = data['close'].rolling(window=period).std()
            
            # Üst ve alt bantlar
            data['bollinger_upper'] = data['bollinger_middle'] + (rolling_std * std_dev)
            data['bollinger_lower'] = data['bollinger_middle'] - (rolling_std * std_dev)
            
            return data
        except Exception as e:
            logger.error(f"Bollinger Bantları hesaplama hatası: {e}")
            return data
    
    def calculate_all_indicators(self, symbol):
        """
        Belirtilen hisse için tüm teknik göstergeleri hesapla
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            pandas.DataFrame: Tüm göstergeler eklenmiş veri
        """
        try:
            # Veriyi çek
            data = self.get_stock_data(symbol)
            
            if data.empty:
                logger.warning(f"{symbol} için veri bulunamadı")
                return None
            
            # Tüm göstergeleri hesapla
            data = self.calculate_moving_averages(data)
            data = self.calculate_rsi(data)
            data = self.calculate_macd(data)
            data = self.calculate_bollinger_bands(data)
            
            logger.info(f"{symbol} için tüm teknik göstergeler hesaplandı")
            return data
        except Exception as e:
            logger.error(f"{symbol} için gösterge hesaplama hatası: {e}")
            return None
    
    def save_indicators_to_db(self, symbol, data):
        """
        Hesaplanan göstergeleri veritabanına kaydet
        
        Args:
            symbol: Hisse sembolü
            data: Göstergeler eklenmiş veri (pandas.DataFrame)
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if data is None or data.empty:
            logger.warning(f"{symbol} için kaydedilecek gösterge yok")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Göstergeleri kaydet
            for _, row in data.iterrows():
                # NaN değerleri kontrol et
                if (pd.isna(row.get('ma_short', np.nan)) or 
                    pd.isna(row.get('ma_long', np.nan)) or 
                    pd.isna(row.get('rsi', np.nan))):
                    continue
                
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], datetime) else row['date']
                
                conn.execute('''
                INSERT OR REPLACE INTO technical_indicators 
                (symbol, date, ma_short, ma_long, rsi, macd, macd_signal, 
                bollinger_upper, bollinger_middle, bollinger_lower)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    date_str,
                    float(row.get('ma_short', 0)),
                    float(row.get('ma_long', 0)),
                    float(row.get('rsi', 0)),
                    float(row.get('macd', 0)),
                    float(row.get('macd_signal', 0)),
                    float(row.get('bollinger_upper', 0)),
                    float(row.get('bollinger_middle', 0)),
                    float(row.get('bollinger_lower', 0))
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"{symbol} için göstergeler veritabanına kaydedildi")
            return True
        
        except Exception as e:
            logger.error(f"{symbol} için gösterge kaydetme hatası: {e}")
            return False
    
    def analyze_all_stocks(self):
        """
        Tüm BIST30 hisseleri için teknik analiz yap ve veritabanına kaydet
        
        Returns:
            dict: Her sembol için başarı durumu
        """
        results = {}
        
        for symbol in BIST30_SYMBOLS:
            try:
                data = self.calculate_all_indicators(symbol)
                success = self.save_indicators_to_db(symbol, data)
                results[symbol] = success
            except Exception as e:
                logger.error(f"{symbol} için analiz hatası: {e}")
                results[symbol] = False
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Toplam {len(results)} hisseden {success_count} tanesi başarıyla analiz edildi")
        
        return results

# Test fonksiyonu
def test_technical_analyzer():
    """TechnicalAnalyzer sınıfını test et"""
    analyzer = TechnicalAnalyzer()
    
    # Test sembolleri
    test_symbols = ["GARAN", "THYAO", "AKBNK"]
    
    for symbol in test_symbols:
        print(f"\n{symbol} için teknik analiz testi:")
        data = analyzer.calculate_all_indicators(symbol)
        
        if data is not None and not data.empty:
            print(f"Göstergeler başarıyla hesaplandı: {len(data)} satır")
            print("\nSon 2 satır:")
            print(data.tail(2)[['date', 'close', 'ma_short', 'ma_long', 'rsi', 'macd', 'macd_signal']])
            
            success = analyzer.save_indicators_to_db(symbol, data)
            print(f"Veritabanına kayıt: {'Başarılı' if success else 'Başarısız'}")
        else:
            print(f"Göstergeler hesaplanamadı")

if __name__ == "__main__":
    test_technical_analyzer()
