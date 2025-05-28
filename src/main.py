import os
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from whitenoise import WhiteNoise

# Bot modüllerini import et
from src.routes.bist30 import bist30_bp
from src.bot.config import validate_telegram_config

def create_app():
    """Flask uygulamasını oluştur ve konfigüre et"""
    app = Flask(__name__, static_folder='static', template_folder='static')
    
    # Static dosyalar için WhiteNoise middleware
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')
    
    # Blueprint'leri kaydet
    app.register_blueprint(bist30_bp, url_prefix='/api/bist30')
    
    @app.route('/')
    def index():
        """Ana sayfa"""
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Sağlık kontrolü endpoint'i"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'BIST30 Web App'
        })
    
    # Telegram konfigürasyonunu kontrol et
    validate_telegram_config()
    
    return app

def initial_data_setup():
    """Uygulama başlatılırken veri kontrolü ve ilk veri çekme"""
    try:
        from src.bot.data_fetcher import DataFetcher
        import sqlite3
        import os
        
        # Veritabanı dosyasının varlığını kontrol et
        df = DataFetcher()
        
        # Veritabanında veri var mı kontrol et
        conn = sqlite3.connect(df.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        data_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Veritabanında {data_count} satır veri bulundu")
        
        # Eğer veri yoksa veya çok azsa, veri çek
        if data_count < 100:  # 30 hisse * 3-4 veri = minimum 90-120 satır beklenir
            print("🔄 Veritabanı boş veya eksik veri var, veri çekme başlatılıyor...")
            results = df.fetch_all_stocks()
            success_count = sum(1 for success in results.values() if success)
            print(f"✅ İlk veri çekme tamamlandı: {success_count}/{len(results)} hisse başarılı")
        else:
            print("✅ Veritabanında yeterli veri mevcut")
            
    except Exception as e:
        print(f"❌ İlk veri kurulumu sırasında hata: {e}")

# Flask uygulamasını oluştur
app = create_app()

if __name__ == '__main__':
    # İlk veri kurulumunu background thread'de yap
    setup_thread = threading.Thread(target=initial_data_setup)
    setup_thread.daemon = True
    setup_thread.start()
    
    # Geliştirme sunucusunu başlat
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 