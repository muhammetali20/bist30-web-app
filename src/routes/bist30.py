from flask import Blueprint, jsonify, request, current_app
import os
import sys
import json
from datetime import datetime

# Bot modüllerini import et
from src.bot.data_fetcher import DataFetcher
from src.bot.technical_analyzer import TechnicalAnalyzer
from src.bot.signal_generator import SignalGenerator
from src.bot.performance_simulator import PerformanceSimulator
from src.bot.weekly_report_generator import WeeklyReportGenerator
from src.bot.telegram_notifier import TelegramNotifier
from src.bot.config import validate_telegram_config

# Blueprint oluştur
bist30_bp = Blueprint('bist30', __name__)

# Veri tabanı yolunu ayarla
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot/data/bist_bot.db')

# Modül örneklerini oluştur
data_fetcher = DataFetcher(db_path=DATABASE_PATH)
technical_analyzer = TechnicalAnalyzer(db_path=DATABASE_PATH)
signal_generator = SignalGenerator(db_path=DATABASE_PATH)
performance_simulator = PerformanceSimulator(db_path=DATABASE_PATH)
weekly_report_generator = WeeklyReportGenerator(db_path=DATABASE_PATH)

@bist30_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """BIST30 sembollerini döndür"""
    from src.bot.config import BIST30_SYMBOLS
    return jsonify({
        'symbols': BIST30_SYMBOLS,
        'count': len(BIST30_SYMBOLS)
    })

@bist30_bp.route('/fetch-data', methods=['POST'])
def fetch_data():
    """Tüm BIST30 hisseleri için veri çek"""
    try:
        results = data_fetcher.fetch_all_stocks()
        success_count = sum(1 for success in results.values() if success)
        
        return jsonify({
            'success': True,
            'message': f"Toplam {len(results)} hisseden {success_count} tanesi başarıyla işlendi",
            'results': {symbol: str(success) for symbol, success in results.items()}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Veri çekme hatası: {str(e)}"
        }), 500

@bist30_bp.route('/analyze', methods=['POST'])
def analyze_stocks():
    """Tüm BIST30 hisseleri için teknik analiz yap"""
    try:
        results = technical_analyzer.analyze_all_stocks()
        success_count = sum(1 for success in results.values() if success)
        
        return jsonify({
            'success': True,
            'message': f"Toplam {len(results)} hisseden {success_count} tanesi başarıyla analiz edildi",
            'results': {symbol: str(success) for symbol, success in results.items()}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Analiz hatası: {str(e)}"
        }), 500

@bist30_bp.route('/generate-signals', methods=['POST'])
def generate_signals():
    """Tüm BIST30 hisseleri için sinyal üret"""
    try:
        signals = signal_generator.generate_all_signals()
        buy_signals = signals.get('buy_signals', [])
        sell_signals = signals.get('sell_signals', [])
        
        # Datetime nesnelerini string'e dönüştür (JSON serileştirme için)
        for signal_list in [buy_signals, sell_signals]:
            for signal in signal_list:
                if 'last_date' in signal and isinstance(signal['last_date'], datetime):
                    signal['last_date'] = signal['last_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'message': f"Toplam {len(buy_signals)} alım ve {len(sell_signals)} satım sinyali üretildi",
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Sinyal üretme hatası: {str(e)}"
        }), 500

@bist30_bp.route('/run-weekly-analysis', methods=['POST'])
def run_weekly_analysis():
    """Haftalık analiz akışını çalıştır"""
    try:
        # 1. Veri çekme
        fetch_results = data_fetcher.fetch_all_stocks()
        fetch_success_count = sum(1 for success in fetch_results.values() if success)
        
        # 2. Teknik analiz
        analysis_results = technical_analyzer.analyze_all_stocks()
        analysis_success_count = sum(1 for success in analysis_results.values() if success)
        
        # 3. Sinyal üretimi
        signals = signal_generator.generate_all_signals()
        buy_signals = signals.get('buy_signals', [])
        sell_signals = signals.get('sell_signals', [])
        
        # Datetime nesnelerini string'e dönüştür (JSON serileştirme için)
        for signal_list in [buy_signals, sell_signals]:
            for signal in signal_list:
                if 'last_date' in signal and isinstance(signal['last_date'], datetime):
                    signal['last_date'] = signal['last_date'].strftime('%Y-%m-%d')
        
        # Rapor oluştur
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fetch_results': {
                'total': len(fetch_results),
                'success': fetch_success_count
            },
            'analysis_results': {
                'total': len(analysis_results),
                'success': analysis_success_count
            },
            'signals': {
                'buy_count': len(buy_signals),
                'sell_count': len(sell_signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals
            }
        }
        
        # Telegram bildirimi gönder (eğer konfigüre edilmişse)
        try:
            if validate_telegram_config():
                telegram_notifier = TelegramNotifier()
                
                # Sinyalleri Telegram'a gönder
                if buy_signals or sell_signals:
                    telegram_signals = {
                        'buy_signals': buy_signals,
                        'sell_signals': sell_signals
                    }
                    telegram_notifier.send_signals(telegram_signals)
                
                # Haftalık özet mesajı
                summary_message = f"""
📊 <b>BIST30 Haftalık Analiz Tamamlandı</b>

📅 <b>Tarih:</b> {report['timestamp']}

📈 <b>Veri İşleme:</b>
• Toplam hisse: {report['fetch_results']['total']}
• Başarılı: {report['fetch_results']['success']}

🔍 <b>Teknik Analiz:</b>
• Analiz edilen: {report['analysis_results']['total']}
• Başarılı: {report['analysis_results']['success']}

🎯 <b>Sinyaller:</b>
• 🟢 Alım: {report['signals']['buy_count']}
• 🔴 Satım: {report['signals']['sell_count']}

#BIST30 #HaftalıkAnaliz
"""
                telegram_notifier.send_message_sync(summary_message)
                
        except Exception as telegram_error:
            print(f"Telegram bildirimi gönderilemedi: {telegram_error}")
        
        return jsonify({
            'success': True,
            'message': "Haftalık analiz başarıyla tamamlandı",
            'report': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Haftalık analiz hatası: {str(e)}"
        }), 500

@bist30_bp.route('/stock-data/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """Belirli bir hisse için veri getir"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        data = data_fetcher.get_latest_data(symbol, limit)
        
        # DataFrame'i JSON'a dönüştür
        if not data.empty:
            data_dict = data.to_dict(orient='records')
            return jsonify({
                'success': True,
                'symbol': symbol,
                'data': data_dict
            })
        else:
            return jsonify({
                'success': False,
                'message': f"{symbol} için veri bulunamadı"
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Veri getirme hatası: {str(e)}"
        }), 500

@bist30_bp.route('/technical-data/<symbol>', methods=['GET'])
def get_technical_data(symbol):
    """Belirli bir hisse için teknik göstergeleri getir"""
    try:
        data = technical_analyzer.calculate_all_indicators(symbol)
        
        # DataFrame'i JSON'a dönüştür
        if data is not None and not data.empty:
            # Datetime nesnelerini string'e dönüştür
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')
            data_dict = data.to_dict(orient='records')
            return jsonify({
                'success': True,
                'symbol': symbol,
                'data': data_dict
            })
        else:
            return jsonify({
                'success': False,
                'message': f"{symbol} için teknik gösterge bulunamadı"
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Teknik gösterge getirme hatası: {str(e)}"
        }), 500

@bist30_bp.route('/signals/<symbol>', methods=['GET'])
def get_signals(symbol):
    """Belirli bir hisse için sinyal üret"""
    try:
        signal = signal_generator.generate_signals(symbol)
        
        # Datetime nesnelerini string'e dönüştür
        if 'last_date' in signal and isinstance(signal['last_date'], datetime):
            signal['last_date'] = signal['last_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'signal': signal
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Sinyal üretme hatası: {str(e)}"
        }), 500

# YENİ API UÇLARI

@bist30_bp.route('/daily-report', methods=['POST'])
def get_daily_report():
    """Günlük rapor oluştur (öğlen veya kapanış)"""
    try:
        # İstek parametrelerini al
        data = request.get_json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        time_of_day = data.get('time_of_day', 'close')  # 'noon' veya 'close'
        
        # Günlük rapor oluştur
        report = performance_simulator.get_daily_report(date, time_of_day)
        
        return jsonify({
            'success': True,
            'message': f"{date} tarihi için {time_of_day} raporu oluşturuldu",
            'report': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Günlük rapor oluşturma hatası: {str(e)}"
        }), 500

@bist30_bp.route('/performance-simulation', methods=['POST'])
def run_performance_simulation():
    """Performans simülasyonu yap"""
    try:
        # İstek parametrelerini al
        data = request.get_json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Performans simülasyonu yap
        performance = performance_simulator.get_daily_performance(date)
        
        return jsonify({
            'success': True,
            'message': f"{date} tarihi için performans simülasyonu tamamlandı",
            'performance': performance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Performans simülasyonu hatası: {str(e)}"
        }), 500

@bist30_bp.route('/next-day-prediction', methods=['POST'])
def get_next_day_prediction():
    """Ertesi gün için tahmin ve tavsiye oluştur"""
    try:
        # İstek parametrelerini al
        data = request.get_json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Ertesi gün tahmini yap
        prediction = performance_simulator.get_next_day_prediction(date)
        
        return jsonify({
            'success': True,
            'message': f"{date} tarihine göre ertesi gün tahmini oluşturuldu",
            'prediction': prediction
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Ertesi gün tahmini hatası: {str(e)}"
        }), 500

@bist30_bp.route('/weekly-report', methods=['POST'])
def get_weekly_report():
    """Haftalık rapor oluştur"""
    try:
        # İstek parametrelerini al
        data = request.get_json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Haftalık rapor oluştur
        report = weekly_report_generator.get_weekly_report(date)
        
        return jsonify({
            'success': True,
            'message': f"{date} tarihini içeren hafta için rapor oluşturuldu",
            'report': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Haftalık rapor oluşturma hatası: {str(e)}"
        }), 500

@bist30_bp.route('/bist30-weekly-performance', methods=['POST'])
def get_bist30_weekly_performance():
    """BIST30 endeksinin haftalık performansını hesapla"""
    try:
        # İstek parametrelerini al
        data = request.get_json()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # BIST30 haftalık performansını hesapla
        performance = weekly_report_generator.get_weekly_bist30_performance(date)
        
        return jsonify({
            'success': True,
            'message': f"{date} tarihini içeren hafta için BIST30 performansı hesaplandı",
            'performance': performance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"BIST30 haftalık performans hesaplama hatası: {str(e)}"
        }), 500

@bist30_bp.route('/test-telegram', methods=['POST'])
def test_telegram():
    """Telegram bot bağlantısını test et"""
    try:
        if not validate_telegram_config():
            return jsonify({
                'success': False,
                'message': "Telegram konfigürasyonu eksik! TELEGRAM_SETUP.md dosyasına bakın."
            }), 400
        
        telegram_notifier = TelegramNotifier()
        test_message = """
🤖 <b>BIST30 Bot Test Mesajı</b>

✅ Telegram entegrasyonu başarıyla çalışıyor!

📅 Test tarihi: """ + datetime.now().strftime('%d.%m.%Y %H:%M:%S') + """

#BIST30 #Test
"""
        
        success = telegram_notifier.send_message_sync(test_message)
        
        if success:
            return jsonify({
                'success': True,
                'message': "Telegram test mesajı başarıyla gönderildi!"
            })
        else:
            return jsonify({
                'success': False,
                'message': "Telegram mesajı gönderilemedi. Token ve Chat ID'yi kontrol edin."
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Telegram test hatası: {str(e)}"
        }), 500
