"""
BIST30 Alım-Satım Bot - Haftalık Getiri Raporu Modülü
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
logger = logging.getLogger('WeeklyReportGenerator')

class WeeklyReportGenerator:
    """Haftalık getiri raporu üreten sınıf"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        WeeklyReportGenerator sınıfını başlat
        
        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        logger.info("WeeklyReportGenerator başlatıldı")
    
    def _get_connection(self):
        """SQLite veritabanı bağlantısı oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            return None
    
    def _get_week_dates(self, date=None):
        """
        Belirli bir tarihin bulunduğu haftanın başlangıç ve bitiş tarihlerini hesapla
        
        Args:
            date: Referans tarihi (None ise bugün)
            
        Returns:
            tuple: (hafta_başlangıç, hafta_bitiş) tarihleri
        """
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        
        # Haftanın başlangıcı (Pazartesi)
        start_of_week = date - timedelta(days=date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Haftanın bitişi (Pazar)
        end_of_week = start_of_week + timedelta(days=6)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return start_of_week, end_of_week
    
    def get_weekly_bist30_performance(self, date=None):
        """
        BIST30 endeksinin haftalık performansını hesapla
        
        Args:
            date: Referans tarihi (None ise bugün)
            
        Returns:
            dict: BIST30 haftalık performans verileri
        """
        start_of_week, end_of_week = self._get_week_dates(date)
        
        # Veritabanı bağlantısı
        conn = self._get_connection()
        if conn is None:
            return {
                'success': False,
                'message': 'Veritabanı bağlantısı kurulamadı'
            }
        
        try:
            # BIST30 hisselerinin haftalık performansını hesapla
            stock_performances = []
            
            for symbol in BIST30_SYMBOLS:
                # Haftanın ilk ve son işlem günü verilerini al
                query = f"""
                SELECT * FROM stock_prices 
                WHERE symbol = '{symbol}' 
                AND date >= '{start_of_week.strftime('%Y-%m-%d')}' 
                AND date <= '{end_of_week.strftime('%Y-%m-%d')}'
                ORDER BY date ASC
                """
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty or len(df) < 2:
                    logger.warning(f"{symbol} için haftalık veri bulunamadı")
                    continue
                
                # İlk ve son işlem günü fiyatları
                first_price = df.iloc[0]['close']
                last_price = df.iloc[-1]['close']
                
                # Haftalık değişim
                weekly_change = last_price - first_price
                weekly_change_percentage = (weekly_change / first_price) * 100
                
                # Haftalık en yüksek ve en düşük
                weekly_high = df['high'].max()
                weekly_low = df['low'].min()
                
                # Haftalık işlem hacmi
                weekly_volume = df['volume'].sum()
                
                stock_performances.append({
                    'symbol': symbol,
                    'first_date': df.iloc[0]['date'],
                    'last_date': df.iloc[-1]['date'],
                    'first_price': first_price,
                    'last_price': last_price,
                    'weekly_change': weekly_change,
                    'weekly_change_percentage': weekly_change_percentage,
                    'weekly_high': weekly_high,
                    'weekly_low': weekly_low,
                    'weekly_volume': weekly_volume
                })
            
            # Performansı yüzdeye göre sırala
            stock_performances = sorted(stock_performances, key=lambda x: x['weekly_change_percentage'], reverse=True)
            
            # BIST30 endeksinin ortalama performansı
            if stock_performances:
                avg_change_percentage = sum(stock['weekly_change_percentage'] for stock in stock_performances) / len(stock_performances)
                
                # En iyi ve en kötü performans gösteren hisseler
                best_performers = stock_performances[:3] if len(stock_performances) >= 3 else stock_performances
                worst_performers = stock_performances[-3:] if len(stock_performances) >= 3 else stock_performances
                worst_performers.reverse()  # En kötüden en iyiye sırala
                
                return {
                    'success': True,
                    'week_start': start_of_week.strftime('%Y-%m-%d'),
                    'week_end': end_of_week.strftime('%Y-%m-%d'),
                    'avg_change_percentage': avg_change_percentage,
                    'stock_count': len(stock_performances),
                    'positive_count': sum(1 for stock in stock_performances if stock['weekly_change'] > 0),
                    'negative_count': sum(1 for stock in stock_performances if stock['weekly_change'] < 0),
                    'neutral_count': sum(1 for stock in stock_performances if stock['weekly_change'] == 0),
                    'best_performers': best_performers,
                    'worst_performers': worst_performers,
                    'all_performances': stock_performances
                }
            else:
                return {
                    'success': True,
                    'week_start': start_of_week.strftime('%Y-%m-%d'),
                    'week_end': end_of_week.strftime('%Y-%m-%d'),
                    'message': 'Haftalık performans verisi bulunamadı',
                    'avg_change_percentage': 0,
                    'stock_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'best_performers': [],
                    'worst_performers': [],
                    'all_performances': []
                }
            
        except Exception as e:
            logger.error(f"Haftalık BIST30 performans hesaplama hatası: {e}")
            return {
                'success': False,
                'message': f"Haftalık BIST30 performans hesaplama hatası: {str(e)}"
            }
        finally:
            conn.close()
    
    def get_weekly_signals_performance(self, date=None):
        """
        Haftalık sinyal performansını hesapla
        
        Args:
            date: Referans tarihi (None ise bugün)
            
        Returns:
            dict: Haftalık sinyal performans verileri
        """
        start_of_week, end_of_week = self._get_week_dates(date)
        
        # Veritabanı bağlantısı
        conn = self._get_connection()
        if conn is None:
            return {
                'success': False,
                'message': 'Veritabanı bağlantısı kurulamadı'
            }
        
        try:
            # Haftanın sinyallerini al
            signals_query = f"""
            SELECT * FROM signals 
            WHERE date(signal_date) >= date('{start_of_week.strftime('%Y-%m-%d')}') 
            AND date(signal_date) <= date('{end_of_week.strftime('%Y-%m-%d')}')
            """
            
            signals_df = pd.read_sql_query(signals_query, conn)
            
            if signals_df.empty:
                logger.warning(f"{start_of_week.strftime('%Y-%m-%d')} - {end_of_week.strftime('%Y-%m-%d')} tarihleri arasında sinyal bulunamadı")
                return {
                    'success': True,
                    'week_start': start_of_week.strftime('%Y-%m-%d'),
                    'week_end': end_of_week.strftime('%Y-%m-%d'),
                    'message': 'Haftalık sinyal bulunamadı',
                    'buy_signals': [],
                    'sell_signals': [],
                    'performance': {
                        'total_profit_loss': 0,
                        'avg_profit_loss_percentage': 0,
                        'successful_trades': 0,
                        'total_trades': 0,
                        'success_rate': 0
                    },
                    'trade_details': []
                }
            
            # Sinyalleri alım ve satım olarak ayır
            buy_signals = signals_df[signals_df['buy_signal'] == 1].to_dict('records')
            sell_signals = signals_df[signals_df['sell_signal'] == 1].to_dict('records')
            
            # Her alım sinyali için performans hesapla
            performance_results = []
            
            for signal in buy_signals:
                symbol = signal['symbol']
                signal_date = signal['signal_date']
                
                # Sinyal sonrası fiyat verilerini al
                price_query = f"""
                SELECT * FROM stock_prices 
                WHERE symbol = '{symbol}' 
                AND date(date) >= date('{signal_date}')
                AND date(date) <= date('{end_of_week.strftime('%Y-%m-%d')}')
                ORDER BY date ASC
                """
                
                price_df = pd.read_sql_query(price_query, conn)
                
                if price_df.empty or len(price_df) < 2:
                    logger.warning(f"{symbol} için yeterli fiyat verisi bulunamadı")
                    continue
                
                # Alım fiyatı (sinyal günü kapanış)
                buy_price = price_df.iloc[0]['close']
                
                # Satış senaryoları
                scenarios = []
                
                # 1. Hedef kâra ulaşma
                target_price = buy_price * (1 + TARGET_PROFIT_PERCENTAGE/100)
                for i in range(1, len(price_df)):
                    if price_df.iloc[i]['high'] >= target_price:
                        sell_date = price_df.iloc[i]['date']
                        sell_price = target_price
                        profit_loss = sell_price - buy_price
                        profit_loss_percentage = (profit_loss / buy_price) * 100
                        
                        scenarios.append({
                            'scenario': 'target_profit',
                            'buy_date': signal_date,
                            'buy_price': buy_price,
                            'sell_date': sell_date,
                            'sell_price': sell_price,
                            'profit_loss': profit_loss,
                            'profit_loss_percentage': profit_loss_percentage,
                            'holding_days': i
                        })
                        break
                
                # 2. Stop-loss'a düşme
                stop_price = buy_price * (1 - STOP_LOSS_PERCENTAGE/100)
                for i in range(1, len(price_df)):
                    if price_df.iloc[i]['low'] <= stop_price:
                        sell_date = price_df.iloc[i]['date']
                        sell_price = stop_price
                        profit_loss = sell_price - buy_price
                        profit_loss_percentage = (profit_loss / buy_price) * 100
                        
                        scenarios.append({
                            'scenario': 'stop_loss',
                            'buy_date': signal_date,
                            'buy_price': buy_price,
                            'sell_date': sell_date,
                            'sell_price': sell_price,
                            'profit_loss': profit_loss,
                            'profit_loss_percentage': profit_loss_percentage,
                            'holding_days': i
                        })
                        break
                
                # 3. Haftanın son işlem günü
                if len(price_df) > 1:
                    sell_date = price_df.iloc[-1]['date']
                    sell_price = price_df.iloc[-1]['close']
                    profit_loss = sell_price - buy_price
                    profit_loss_percentage = (profit_loss / buy_price) * 100
                    
                    scenarios.append({
                        'scenario': 'week_end',
                        'buy_date': signal_date,
                        'buy_price': buy_price,
                        'sell_date': sell_date,
                        'sell_price': sell_price,
                        'profit_loss': profit_loss,
                        'profit_loss_percentage': profit_loss_percentage,
                        'holding_days': len(price_df) - 1
                    })
                
                # En iyi senaryoyu seç (en yüksek kâr veya en düşük zarar)
                if scenarios:
                    best_scenario = max(scenarios, key=lambda x: x['profit_loss_percentage'])
                    best_scenario['symbol'] = symbol
                    performance_results.append(best_scenario)
            
            # Performans özeti
            if performance_results:
                total_profit_loss = sum(result['profit_loss'] for result in performance_results)
                avg_profit_loss_percentage = sum(result['profit_loss_percentage'] for result in performance_results) / len(performance_results)
                successful_trades = sum(1 for result in performance_results if result['profit_loss'] > 0)
                success_rate = (successful_trades / len(performance_results)) * 100 if performance_results else 0
                
                performance_summary = {
                    'total_profit_loss': total_profit_loss,
                    'avg_profit_loss_percentage': avg_profit_loss_percentage,
                    'successful_trades': successful_trades,
                    'total_trades': len(performance_results),
                    'success_rate': success_rate
                }
            else:
                performance_summary = {
                    'total_profit_loss': 0,
                    'avg_profit_loss_percentage': 0,
                    'successful_trades': 0,
                    'total_trades': 0,
                    'success_rate': 0
                }
            
            return {
                'success': True,
                'week_start': start_of_week.strftime('%Y-%m-%d'),
                'week_end': end_of_week.strftime('%Y-%m-%d'),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'performance': performance_summary,
                'trade_details': performance_results
            }
            
        except Exception as e:
            logger.error(f"Haftalık sinyal performansı hesaplama hatası: {e}")
            return {
                'success': False,
                'message': f"Haftalık sinyal performansı hesaplama hatası: {str(e)}"
            }
        finally:
            conn.close()
    
    def get_weekly_report(self, date=None):
        """
        Haftalık rapor oluştur
        
        Args:
            date: Referans tarihi (None ise bugün)
            
        Returns:
            dict: Haftalık rapor
        """
        # BIST30 performansı
        bist30_performance = self.get_weekly_bist30_performance(date)
        
        # Sinyal performansı
        signals_performance = self.get_weekly_signals_performance(date)
        
        # Rapor oluştur
        report = {
            'success': bist30_performance['success'] and signals_performance['success'],
            'week_start': bist30_performance.get('week_start'),
            'week_end': bist30_performance.get('week_end'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bist30_performance': {
                'avg_change_percentage': bist30_performance.get('avg_change_percentage', 0),
                'stock_count': bist30_performance.get('stock_count', 0),
                'positive_count': bist30_performance.get('positive_count', 0),
                'negative_count': bist30_performance.get('negative_count', 0),
                'neutral_count': bist30_performance.get('neutral_count', 0),
                'best_performers': bist30_performance.get('best_performers', []),
                'worst_performers': bist30_performance.get('worst_performers', [])
            },
            'signals_performance': {
                'buy_signals_count': len(signals_performance.get('buy_signals', [])),
                'sell_signals_count': len(signals_performance.get('sell_signals', [])),
                'performance': signals_performance.get('performance', {}),
                'trade_details': signals_performance.get('trade_details', [])
            },
            'comparison': {
                'bot_vs_market': 0  # Botun performansı - BIST30 performansı
            }
        }
        
        # Bot performansı vs BIST30 performansı karşılaştırması
        if report['signals_performance']['performance'].get('avg_profit_loss_percentage') is not None and report['bist30_performance'].get('avg_change_percentage') is not None:
            report['comparison']['bot_vs_market'] = report['signals_performance']['performance'].get('avg_profit_loss_percentage', 0) - report['bist30_performance'].get('avg_change_percentage', 0)
        
        return report

# Test fonksiyonu
def test_weekly_report_generator():
    """WeeklyReportGenerator sınıfını test et"""
    print("Weekly Report Generator Test")
    
    generator = WeeklyReportGenerator()
    
    # Test tarihi
    test_date = datetime.now().strftime('%Y-%m-%d')
    
    # BIST30 performans testi
    print("\nBIST30 Haftalık Performans Testi:")
    bist30_performance = generator.get_weekly_bist30_performance(test_date)
    print(f"Başarı: {bist30_performance['success']}")
    if bist30_performance['success']:
        print(f"Hafta Başlangıç: {bist30_performance.get('week_start')}")
        print(f"Hafta Bitiş: {bist30_performance.get('week_end')}")
        print(f"Ortalama Değişim: %{bist30_performance.get('avg_change_percentage', 0):.2f}")
        print(f"Hisse Sayısı: {bist30_performance.get('stock_count', 0)}")
        print(f"Yükselen: {bist30_performance.get('positive_count', 0)}")
        print(f"Düşen: {bist30_performance.get('negative_count', 0)}")
        print(f"Değişmeyen: {bist30_performance.get('neutral_count', 0)}")
        
        if bist30_performance.get('best_performers'):
            print("\nEn İyi Performans Gösterenler:")
            for stock in bist30_performance['best_performers']:
                print(f"{stock['symbol']}: %{stock['weekly_change_percentage']:.2f}")
        
        if bist30_performance.get('worst_performers'):
            print("\nEn Kötü Performans Gösterenler:")
            for stock in bist30_performance['worst_performers']:
                print(f"{stock['symbol']}: %{stock['weekly_change_percentage']:.2f}")
    
    # Sinyal performans testi
    print("\nHaftalık Sinyal Performans Testi:")
    signals_performance = generator.get_weekly_signals_performance(test_date)
    print(f"Başarı: {signals_performance['success']}")
    if signals_performance['success']:
        print(f"Hafta Başlangıç: {signals_performance.get('week_start')}")
        print(f"Hafta Bitiş: {signals_performance.get('week_end')}")
        print(f"Alım Sinyalleri: {len(signals_performance.get('buy_signals', []))}")
        print(f"Satım Sinyalleri: {len(signals_performance.get('sell_signals', []))}")
        
        if 'performance' in signals_performance:
            perf = signals_performance['performance']
            print(f"Toplam Kâr/Zarar: {perf.get('total_profit_loss', 0):.2f} TL")
            print(f"Ortalama Kâr/Zarar: %{perf.get('avg_profit_loss_percentage', 0):.2f}")
            print(f"Başarılı İşlemler: {perf.get('successful_trades', 0)}/{perf.get('total_trades', 0)}")
            print(f"Başarı Oranı: %{perf.get('success_rate', 0):.2f}")
    
    # Haftalık rapor testi
    print("\nHaftalık Rapor Testi:")
    report = generator.get_weekly_report(test_date)
    print(f"Başarı: {report['success']}")
    print(f"Hafta Başlangıç: {report.get('week_start')}")
    print(f"Hafta Bitiş: {report.get('week_end')}")
    print(f"BIST30 Ortalama Değişim: %{report['bist30_performance'].get('avg_change_percentage', 0):.2f}")
    print(f"Bot Ortalama Kâr/Zarar: %{report['signals_performance']['performance'].get('avg_profit_loss_percentage', 0):.2f}")
    print(f"Bot vs BIST30: %{report['comparison'].get('bot_vs_market', 0):.2f}")

if __name__ == "__main__":
    test_weekly_report_generator()
