"""
BIST30 Alım-Satım Bot - Veri Çekme Modülü
"""

import os
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import sys

# Konfigürasyon dosyasını import et
from src.bot.config import *

# Loglama ayarları
# LOG_FILE_PATH config.py'den None olarak gelecek, bu yüzden FileHandler kullanmayacağız.
log_handlers = [logging.StreamHandler()] # Sadece konsola (stdout/stderr)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger('DataFetcher')

class DataFetcher:
    """Yahoo Finance API kullanarak BIST30 hisselerinin verilerini çeken sınıf"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        DataFetcher sınıfını başlat
        
        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        self._ensure_db_exists()
        logger.info("DataFetcher başlatıldı")
    
    def _ensure_db_exists(self):
        """Veritabanı ve gerekli tabloları oluştur"""
        try:
            # Veritabanı dizininin varlığını kontrol et
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Veritabanına bağlan ve tabloları oluştur
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hisse verileri tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
            ''')
            
            # Teknik göstergeler tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS technical_indicators (
                symbol TEXT,
                date TEXT,
                ma_short REAL,
                ma_long REAL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                bollinger_upper REAL,
                bollinger_middle REAL,
                bollinger_lower REAL,
                PRIMARY KEY (symbol, date)
            )
            ''')
            
            # Sinyaller tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                date TEXT,
                signal_type TEXT,
                price REAL,
                reason TEXT,
                created_at TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Veritabanı ve tablolar oluşturuldu")
        except Exception as e:
            logger.error(f"Veritabanı oluşturma hatası: {e}")
            raise
    
    def format_symbol(self, symbol):
        """
        BIST sembollerini Yahoo Finance formatına dönüştür
        
        Args:
            symbol: Hisse sembolü (örn. GARAN)
            
        Returns:
            str: Yahoo Finance formatında sembol (örn. GARAN.IS)
        """
        return f"{symbol}.{YAHOO_FINANCE_REGION}"
    
    def fetch_stock_data(self, symbol, interval=DATA_FETCH_INTERVAL, period=DATA_FETCH_PERIOD):
        """
        Belirtilen hisse için veri çek
        
        Args:
            symbol: Hisse sembolü
            interval: Veri aralığı (1d, 1wk, 1mo vb.)
            period: Veri periyodu (1mo, 3mo, 1y vb.)
            
        Returns:
            pandas.DataFrame: Çekilen veri
        """
        try:
            formatted_symbol = self.format_symbol(symbol)
            logger.info(f"{symbol} için veri çekiliyor (format: {formatted_symbol})")
            
            # Yahoo Finance API ile veri çek
            data = yf.download(
                formatted_symbol,
                interval=interval,
                period=period,
                progress=False,
                auto_adjust=True,
                prepost=False,
                threads=True
            )
            
            if data.empty:
                logger.warning(f"{symbol} için veri bulunamadı")
                return None
            
            # Veriyi düzenle
            data = data.reset_index()
            
            # MultiIndex columns'u düzelt (yeni Yahoo Finance API)
            if isinstance(data.columns, pd.MultiIndex):
                # İkinci seviye sütun adlarını al (ticker kısmını kaldır)
                data.columns = [col[0] if col[0] != 'Date' else 'Date' for col in data.columns]
            
            # Sütun adlarını düzenle
            data.columns = [col if col != 'Date' else 'date' for col in data.columns]
            data.columns = [col.lower() for col in data.columns]
            
            # Adj Close sütununu kaldır (gerekirse)
            if 'adj close' in data.columns:
                data = data.drop('adj close', axis=1)
            
            logger.info(f"{symbol} için {len(data)} satır veri çekildi")
            return data
        
        except Exception as e:
            logger.error(f"{symbol} için veri çekme hatası: {e}")
            return None
    
    def save_to_db(self, symbol, data):
        """
        Çekilen veriyi veritabanına kaydet
        
        Args:
            symbol: Hisse sembolü
            data: pandas.DataFrame formatında veri
            
        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if data is None or data.empty:
            logger.warning(f"{symbol} için kaydedilecek veri yok")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Veriyi kaydet
            for _, row in data.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], datetime) else row['date']
                
                conn.execute('''
                INSERT OR REPLACE INTO stock_data 
                (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    date_str,
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['volume'])
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"{symbol} için {len(data)} satır veri veritabanına kaydedildi")
            return True
        
        except Exception as e:
            logger.error(f"{symbol} için veri kaydetme hatası: {e}")
            return False
    
    def fetch_all_stocks(self):
        """
        Tüm BIST30 hisseleri için veri çek ve veritabanına kaydet
        
        Returns:
            dict: Her sembol için başarı durumu
        """
        results = {}
        
        for symbol in BIST30_SYMBOLS:
            try:
                data = self.fetch_stock_data(symbol)
                success = self.save_to_db(symbol, data)
                results[symbol] = success
            except Exception as e:
                logger.error(f"{symbol} için işlem hatası: {e}")
                results[symbol] = False
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Toplam {len(results)} hisseden {success_count} tanesi başarıyla işlendi")
        
        return results
    
    def get_latest_data(self, symbol, limit=10):
        """
        Belirtilen hisse için en son verileri getir
        
        Args:
            symbol: Hisse sembolü
            limit: Kaç satır veri getirileceği
            
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
            
            return data
        except Exception as e:
            logger.error(f"{symbol} için veri getirme hatası: {e}")
            return pd.DataFrame()

# Test fonksiyonu
def test_data_fetcher():
    """DataFetcher sınıfını test et"""
    fetcher = DataFetcher()
    
    # Test sembolleri
    test_symbols = ["GARAN", "THYAO", "AKBNK"]
    
    for symbol in test_symbols:
        print(f"\n{symbol} için test:")
        data = fetcher.fetch_stock_data(symbol, period="1mo")
        
        if data is not None and not data.empty:
            print(f"Veri başarıyla çekildi: {len(data)} satır")
            print(data.head(2))
            
            success = fetcher.save_to_db(symbol, data)
            print(f"Veritabanına kayıt: {'Başarılı' if success else 'Başarısız'}")
            
            latest = fetcher.get_latest_data(symbol, 2)
            print(f"Veritabanından en son veriler:")
            print(latest)
        else:
            print(f"Veri çekilemedi")

if __name__ == "__main__":
    test_data_fetcher()
