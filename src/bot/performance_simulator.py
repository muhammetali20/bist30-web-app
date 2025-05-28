"""
BIST30 Alım-Satım Bot - Performans Simülasyonu Modülü
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
logger = logging.getLogger('PerformanceSimulator')

class PerformanceSimulator:
    """Alım-satım sinyallerinin performansını simüle eden sınıf"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        PerformanceSimulator sınıfını başlat
        
        Args:
            db_path: Veritabanı dosya yolu
        """
        self.db_path = db_path
        logger.info("PerformanceSimulator başlatıldı")
    
    def _get_connection(self):
        """SQLite veritabanı bağlantısı oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            return None
    
    def get_daily_performance(self, date=None):
        """
        Belirli bir gün için performans simülasyonu yap
        
        Args:
            date: Simülasyon tarihi (None ise bugün)
            
        Returns:
            dict: Performans simülasyonu sonuçları
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Simülasyon için gerekli verileri çek
        conn = self._get_connection()
        if conn is None:
            return {
                'success': False,
                'message': 'Veritabanı bağlantısı kurulamadı'
            }
        
        try:
            # O gün için üretilen sinyalleri al
            signals_query = f"""
            SELECT * FROM signals 
            WHERE date(signal_date) = date('{date}')
            """
            
            signals_df = pd.read_sql_query(signals_query, conn)
            
            if signals_df.empty:
                logger.warning(f"{date} tarihi için sinyal bulunamadı")
                return {
                    'success': True,
                    'message': f"{date} tarihi için sinyal bulunamadı",
                    'buy_signals': [],
                    'sell_signals': [],
                    'performance': {
                        'total_profit_loss': 0,
                        'total_profit_loss_percentage': 0,
                        'successful_trades': 0,
                        'total_trades': 0,
                        'success_rate': 0
                    }
                }
            
            # Sinyalleri alım ve satım olarak ayır
            buy_signals = signals_df[signals_df['buy_signal'] == 1].to_dict('records')
            sell_signals = signals_df[signals_df['sell_signal'] == 1].to_dict('records')
            
            # Her sinyal için performans hesapla
            performance_results = []
            
            # Alım sinyalleri için performans hesapla
            for signal in buy_signals:
                symbol = signal['symbol']
                signal_date = signal['signal_date']
                
                # Sinyal sonrası fiyat verilerini al
                price_query = f"""
                SELECT * FROM stock_prices 
                WHERE symbol = '{symbol}' 
                AND date(date) >= date('{signal_date}')
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
                
                # 3. Maksimum bekleme süresi
                max_holding_days = min(MAX_HOLDING_WEEKS * 5, len(price_df) - 1)
                if max_holding_days > 0:
                    sell_date = price_df.iloc[max_holding_days]['date']
                    sell_price = price_df.iloc[max_holding_days]['close']
                    profit_loss = sell_price - buy_price
                    profit_loss_percentage = (profit_loss / buy_price) * 100
                    
                    scenarios.append({
                        'scenario': 'max_holding',
                        'buy_date': signal_date,
                        'buy_price': buy_price,
                        'sell_date': sell_date,
                        'sell_price': sell_price,
                        'profit_loss': profit_loss,
                        'profit_loss_percentage': profit_loss_percentage,
                        'holding_days': max_holding_days
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
                'date': date,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'performance': performance_summary,
                'trade_details': performance_results
            }
            
        except Exception as e:
            logger.error(f"Performans simülasyonu hatası: {e}")
            return {
                'success': False,
                'message': f"Performans simülasyonu hatası: {str(e)}"
            }
        finally:
            conn.close()
    
    def get_daily_report(self, date=None, time_of_day="close"):
        """
        Günlük rapor oluştur (öğlen veya kapanış)
        
        Args:
            date: Rapor tarihi (None ise bugün)
            time_of_day: "noon" (öğlen) veya "close" (kapanış)
            
        Returns:
            dict: Günlük rapor
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Performans simülasyonu yap
        performance = self.get_daily_performance(date)
        
        # Rapor oluştur
        report = {
            'success': performance['success'],
            'date': date,
            'time_of_day': time_of_day,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'buy_signals': performance.get('buy_signals', []),
            'sell_signals': performance.get('sell_signals', []),
            'performance': performance.get('performance', {}),
            'trade_details': performance.get('trade_details', [])
        }
        
        return report
    
    def get_next_day_prediction(self, date=None):
        """
        Ertesi gün için tahmin ve tavsiye oluştur
        
        Args:
            date: Baz alınacak tarih (None ise bugün)
            
        Returns:
            dict: Ertesi gün için tahmin ve tavsiyeler
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Bir sonraki iş gününü hesapla (basit yaklaşım)
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        next_day = date_obj + timedelta(days=1)
        
        # Hafta sonu ise sonraki pazartesiye atla
        if next_day.weekday() >= 5:  # 5: Cumartesi, 6: Pazar
            days_to_add = 7 - next_day.weekday()
            next_day = next_day + timedelta(days=days_to_add)
        
        next_day_str = next_day.strftime('%Y-%m-%d')
        
        # Veritabanı bağlantısı
        conn = self._get_connection()
        if conn is None:
            return {
                'success': False,
                'message': 'Veritabanı bağlantısı kurulamadı'
            }
        
        try:
            # BIST30 hisseleri için teknik göstergeleri hesapla
            predictions = []
            
            for symbol in BIST30_SYMBOLS:
                # Son 30 günlük veriyi al
                query = f"""
                SELECT * FROM stock_prices 
                WHERE symbol = '{symbol}' 
                ORDER BY date DESC
                LIMIT 30
                """
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty or len(df) < 20:
                    logger.warning(f"{symbol} için yeterli veri bulunamadı")
                    continue
                
                # Veriyi tarih sırasına göre sırala
                df = df.sort_values('date')
                
                # Teknik göstergeleri hesapla
                if len(df) >= 5:
                    df['ma_short'] = df['close'].rolling(window=MA_SHORT).mean()
                
                if len(df) >= 20:
                    df['ma_long'] = df['close'].rolling(window=MA_LONG).mean()
                    df['std'] = df['close'].rolling(window=BOLLINGER_PERIOD).std()
                    df['upper_band'] = df['ma_long'] + (df['std'] * BOLLINGER_STD)
                    df['lower_band'] = df['ma_long'] - (df['std'] * BOLLINGER_STD)
                
                if len(df) >= 14:
                    # RSI hesapla (basit yaklaşım)
                    delta = df['close'].diff()
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)
                    avg_gain = gain.rolling(window=RSI_PERIOD).mean()
                    avg_loss = loss.rolling(window=RSI_PERIOD).mean()
                    rs = avg_gain / avg_loss
                    df['rsi'] = 100 - (100 / (1 + rs))
                
                # Son satırı al
                last_row = df.iloc[-1]
                
                # Tahmin ve tavsiye oluştur
                prediction = {
                    'symbol': symbol,
                    'current_price': last_row['close'],
                    'last_date': last_row['date'],
                    'prediction': {}
                }
                
                # Trend analizi
                if 'ma_short' in df.columns and 'ma_long' in df.columns:
                    last_ma_short = last_row['ma_short']
                    last_ma_long = last_row['ma_long']
                    
                    if last_ma_short > last_ma_long:
                        trend = "yükseliş"
                    elif last_ma_short < last_ma_long:
                        trend = "düşüş"
                    else:
                        trend = "yatay"
                    
                    prediction['prediction']['trend'] = trend
                
                # RSI analizi
                if 'rsi' in df.columns:
                    last_rsi = last_row['rsi']
                    
                    if last_rsi < RSI_OVERSOLD:
                        rsi_signal = "aşırı satım"
                    elif last_rsi > RSI_OVERBOUGHT:
                        rsi_signal = "aşırı alım"
                    else:
                        rsi_signal = "nötr"
                    
                    prediction['prediction']['rsi'] = {
                        'value': last_rsi,
                        'signal': rsi_signal
                    }
                
                # Bollinger Bantları analizi
                if 'upper_band' in df.columns and 'lower_band' in df.columns:
                    last_upper = last_row['upper_band']
                    last_lower = last_row['lower_band']
                    last_price = last_row['close']
                    
                    if last_price > last_upper:
                        bb_signal = "aşırı alım"
                    elif last_price < last_lower:
                        bb_signal = "aşırı satım"
                    else:
                        bb_signal = "nötr"
                    
                    prediction['prediction']['bollinger'] = {
                        'upper': last_upper,
                        'lower': last_lower,
                        'signal': bb_signal
                    }
                
                # Tavsiye oluştur
                buy_signals = 0
                sell_signals = 0
                
                # Trend sinyali
                if prediction['prediction'].get('trend') == "yükseliş":
                    buy_signals += 1
                elif prediction['prediction'].get('trend') == "düşüş":
                    sell_signals += 1
                
                # RSI sinyali
                if 'rsi' in prediction['prediction']:
                    if prediction['prediction']['rsi']['signal'] == "aşırı satım":
                        buy_signals += 1
                    elif prediction['prediction']['rsi']['signal'] == "aşırı alım":
                        sell_signals += 1
                
                # Bollinger sinyali
                if 'bollinger' in prediction['prediction']:
                    if prediction['prediction']['bollinger']['signal'] == "aşırı satım":
                        buy_signals += 1
                    elif prediction['prediction']['bollinger']['signal'] == "aşırı alım":
                        sell_signals += 1
                
                # Nihai tavsiye
                if buy_signals > sell_signals:
                    recommendation = "AL"
                    reason = f"Teknik göstergeler alım sinyali veriyor: {buy_signals} alım, {sell_signals} satım sinyali"
                elif sell_signals > buy_signals:
                    recommendation = "SAT"
                    reason = f"Teknik göstergeler satım sinyali veriyor: {sell_signals} satım, {buy_signals} alım sinyali"
                else:
                    recommendation = "BEKLE"
                    reason = "Teknik göstergeler karışık sinyaller veriyor"
                
                prediction['recommendation'] = {
                    'action': recommendation,
                    'reason': reason,
                    'confidence': max(buy_signals, sell_signals) / 3 * 100  # 3 gösterge var
                }
                
                # Hedef fiyat
                if recommendation == "AL":
                    target_price = last_row['close'] * (1 + TARGET_PROFIT_PERCENTAGE/100)
                    stop_loss = last_row['close'] * (1 - STOP_LOSS_PERCENTAGE/100)
                    
                    prediction['recommendation']['target_price'] = target_price
                    prediction['recommendation']['stop_loss'] = stop_loss
                
                predictions.append(prediction)
            
            # Tahminleri tavsiyeye göre sırala
            buy_recommendations = [p for p in predictions if p['recommendation']['action'] == "AL"]
            sell_recommendations = [p for p in predictions if p['recommendation']['action'] == "SAT"]
            hold_recommendations = [p for p in predictions if p['recommendation']['action'] == "BEKLE"]
            
            # Güven skoruna göre sırala
            buy_recommendations = sorted(buy_recommendations, key=lambda x: x['recommendation']['confidence'], reverse=True)
            sell_recommendations = sorted(sell_recommendations, key=lambda x: x['recommendation']['confidence'], reverse=True)
            
            return {
                'success': True,
                'current_date': date,
                'next_trading_day': next_day_str,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'buy_recommendations': buy_recommendations,
                'sell_recommendations': sell_recommendations,
                'hold_recommendations': hold_recommendations,
                'all_predictions': predictions
            }
            
        except Exception as e:
            logger.error(f"Ertesi gün tahmini hatası: {e}")
            return {
                'success': False,
                'message': f"Ertesi gün tahmini hatası: {str(e)}"
            }
        finally:
            conn.close()

# Test fonksiyonu
def test_performance_simulator():
    """PerformanceSimulator sınıfını test et"""
    print("Performance Simulator Test")
    
    simulator = PerformanceSimulator()
    
    # Test tarihi
    test_date = datetime.now().strftime('%Y-%m-%d')
    
    # Günlük performans testi
    print("\nGünlük Performans Testi:")
    performance = simulator.get_daily_performance(test_date)
    print(f"Başarı: {performance['success']}")
    if performance['success']:
        print(f"Alım Sinyalleri: {len(performance.get('buy_signals', []))}")
        print(f"Satım Sinyalleri: {len(performance.get('sell_signals', []))}")
        
        if 'performance' in performance:
            perf = performance['performance']
            print(f"Toplam Kâr/Zarar: {perf.get('total_profit_loss', 0):.2f} TL")
            print(f"Ortalama Kâr/Zarar: %{perf.get('avg_profit_loss_percentage', 0):.2f}")
            print(f"Başarılı İşlemler: {perf.get('successful_trades', 0)}/{perf.get('total_trades', 0)}")
            print(f"Başarı Oranı: %{perf.get('success_rate', 0):.2f}")
    
    # Günlük rapor testi
    print("\nGünlük Rapor Testi:")
    report = simulator.get_daily_report(test_date, "close")
    print(f"Başarı: {report['success']}")
    print(f"Tarih: {report['date']}")
    print(f"Zaman: {report['time_of_day']}")
    
    # Ertesi gün tahmini testi
    print("\nErtesi Gün Tahmini Testi:")
    prediction = simulator.get_next_day_prediction(test_date)
    print(f"Başarı: {prediction['success']}")
    if prediction['success']:
        print(f"Mevcut Tarih: {prediction['current_date']}")
        print(f"Sonraki İşlem Günü: {prediction['next_trading_day']}")
        print(f"Alım Tavsiyeleri: {len(prediction.get('buy_recommendations', []))}")
        print(f"Satım Tavsiyeleri: {len(prediction.get('sell_recommendations', []))}")
        print(f"Bekle Tavsiyeleri: {len(prediction.get('hold_recommendations', []))}")

if __name__ == "__main__":
    test_performance_simulator()
