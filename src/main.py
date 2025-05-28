import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, send_from_directory
import logging
from datetime import datetime
import sqlite3

# Import bot config to get correct paths
from src.bot.config import DATABASE_PATH, LOG_FILE_PATH

# Import routes
from src.routes.user import user_bp
from src.routes.bist30 import bist30_bp

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bist30-bot-secret-key')

# Static files için whitenoise benzeri middleware
from whitenoise import WhiteNoise
app.wsgi_app = WhiteNoise(app.wsgi_app, root='src/static/')

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(bist30_bp, url_prefix='/api/bist30')

# Ensure database and log directories exist on persistent storage
db_dir = os.path.dirname(DATABASE_PATH)
# log_dir = os.path.dirname(LOG_FILE_PATH) # config.py hallediyor
os.makedirs(db_dir, exist_ok=True)
# os.makedirs(log_dir, exist_ok=True) # config.py hallediyor

# Initialize database
def init_db():
    db_path = DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create stock_prices table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(symbol, date)
        )
        ''')
        
        # Create technical_indicators table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            ma_short REAL,
            ma_long REAL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            upper_band REAL,
            lower_band REAL,
            UNIQUE(symbol, date)
        )
        ''')
        
        # Create signals table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            signal_date TEXT NOT NULL,
            buy_signal INTEGER DEFAULT 0,
            sell_signal INTEGER DEFAULT 0,
            buy_reason TEXT,
            sell_reason TEXT,
            current_price REAL,
            UNIQUE(symbol, signal_date)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def internal_server_error(e):
    return {"error": "Internal server error"}, 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Run app
    app.run(host=host, port=port, debug=debug)
