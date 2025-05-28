#!/bin/bash

# BIST30 Bot Deployment Script
echo "🚀 BIST30 Bot Deployment Script"
echo "================================"

# Git repository kontrolü
if [ ! -d ".git" ]; then
    echo "📂 Git repository başlatılıyor..."
    git init
    git add .
    git commit -m "Initial commit - BIST30 Bot"
    echo "✅ Git repository oluşturuldu"
else
    echo "📂 Git repository mevcut, güncellemeler commit ediliyor..."
    git add .
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ Değişiklikler commit edildi"
fi

echo ""
echo "🌐 Deployment Seçenekleri:"
echo "1. Render.com (Önerilen)"
echo "2. Railway.app" 
echo "3. Fly.io"
echo "4. Manuel GitHub Push"
echo ""

read -p "Seçiminizi yapın (1-4): " choice

case $choice in
    1)
        echo "🚀 Render.com için hazırlanıyor..."
        echo "📝 Adımlar:"
        echo "   1. https://render.com adresine gidin"
        echo "   2. GitHub hesabınızla giriş yapın"
        echo "   3. 'New Web Service' oluşturun"
        echo "   4. Bu repository'yi seçin"
        echo "   5. Ayarlar:"
        echo "      - Build Command: pip install -r requirements-cloud.txt"
        echo "      - Start Command: python src/main.py"
        echo "      - Python Version: 3.11.9"
        ;;
    2)
        echo "🚂 Railway.app için hazırlanıyor..."
        echo "📝 Adımlar:"
        echo "   1. https://railway.app adresine gidin"
        echo "   2. 'Deploy from GitHub repo' seçin"
        echo "   3. Bu repository'yi seçin"
        echo "   4. Otomatik deployment başlar"
        ;;
    3)
        echo "✈️ Fly.io için hazırlanıyor..."
        echo "📝 Adımlar:"
        echo "   1. Fly CLI kurun: https://fly.io/docs/hands-on/install-flyctl/"
        echo "   2. flyctl auth signup"
        echo "   3. flyctl launch"
        echo "   4. flyctl deploy"
        ;;
    4)
        echo "📤 Manuel GitHub push..."
        if [ -z "$1" ]; then
            read -p "GitHub repository URL'ini girin: " repo_url
        else
            repo_url=$1
        fi
        
        git remote add origin $repo_url 2>/dev/null || git remote set-url origin $repo_url
        git branch -M main
        git push -u origin main
        
        echo "✅ Kod GitHub'a yüklendi"
        echo "🌐 Şimdi tercih ettiğiniz bulut platformunda deploy edebilirsiniz"
        ;;
    *)
        echo "❌ Geçersiz seçim"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment hazırlığı tamamlandı!"
echo ""
echo "📋 Yapılacaklar:"
echo "   • Environment variables ayarlayın (TELEGRAM_TOKEN, SECRET_KEY)"
echo "   • Database disk mount yapın (veriler kaybolmasın)"
echo "   • UptimeRobot ile monitoring kurun"
echo "   • Telegram bildirimleri test edin"
echo ""
echo "🎉 Bot 7/24 çalışmaya hazır!" 