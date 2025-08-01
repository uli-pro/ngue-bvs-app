#!/bin/bash

# Setup-Script für PostgreSQL mit pgvector

echo "NGÜ Vector POC - PostgreSQL Setup"
echo "=================================="

# Prüfe ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker ist nicht gestartet. Bitte Docker starten und erneut versuchen."
    exit 1
fi

# Stoppe und entferne alten Container falls vorhanden
echo "Entferne alten Container (falls vorhanden)..."
docker stop pgvector-test 2>/dev/null
docker rm pgvector-test 2>/dev/null

# Starte PostgreSQL mit pgvector
echo "Starte PostgreSQL mit pgvector..."
docker run -d \
    --name pgvector-test \
    -e POSTGRES_PASSWORD=testpass \
    -e POSTGRES_DB=vector_test \
    -p 5432:5432 \
    ankane/pgvector

# Warte kurz
echo "Warte 5 Sekunden auf Datenbankstart..."
sleep 5

# Teste Verbindung
echo "Teste Datenbankverbindung..."
docker exec pgvector-test psql -U postgres -d vector_test -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL mit pgvector läuft!"
    echo ""
    echo "Verbindungsdaten:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: vector_test"
    echo "  User: postgres"
    echo "  Password: testpass"
    echo ""
    echo "Nächster Schritt: python test_embeddings.py"
else
    echo "❌ Verbindung fehlgeschlagen. Prüfe Docker-Logs:"
    echo "docker logs pgvector-test"
fi
