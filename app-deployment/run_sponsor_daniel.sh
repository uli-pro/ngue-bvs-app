#!/bin/bash
# Einfacher Ausführungsscript für Daniel-Verse Sponsoring
# Läuft das Python-Skript im NGU Flask-Container

echo "=== NGÜ Daniel-Verse Sponsoring ==="
echo "Führe Skript im Flask-Container aus..."
echo

# Prüfe ob Container läuft
if ! docker ps --format "table {{.Names}}" | grep -q "ngue-flask-app"; then
    echo "❌ Fehler: NGU Flask-Container 'ngue-flask-app' läuft nicht!"
    echo
    echo "Container starten mit:"
    echo "  cd /docker/ngue-app/app-deployment"
    echo "  docker compose up -d ngue-app"
    echo
    exit 1
fi

echo "✅ Container 'ngue-flask-app' gefunden"
echo "Führe Daniel-Sponsoring-Skript aus..."
echo

# Führe Skript im Container aus
docker exec -it ngue-flask-app python /app/app-deployment/sponsor_daniel_container.py

echo
echo "Skript abgeschlossen."