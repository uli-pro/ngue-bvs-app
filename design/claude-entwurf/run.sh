#!/bin/bash

# NGÜ Flask App Starter Script

echo "🚀 NGÜ Bibelvers-Sponsoring Flask App Starter"
echo "============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    echo "✅ Virtuelle Umgebung erstellt"
    echo ""
fi

# Activate virtual environment
echo "🔧 Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Install/Update dependencies
echo "📚 Installiere Dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installiert"
echo ""

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start Flask app
echo "🌐 Starte Flask-Anwendung..."
echo "============================================="
echo "📍 Die Anwendung läuft unter: http://localhost:5000"
echo "📍 Zum Beenden: Ctrl+C drücken"
echo "============================================="
echo ""

python app.py