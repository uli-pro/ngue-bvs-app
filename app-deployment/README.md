# 🚀 NGÜ Bibelvers-Sponsoring App - Docker Deployment

## 📋 Übersicht

Dieses Deployment-Package enthält eine vollständige Docker-basierte Infrastruktur für die NGÜ Bibelvers-Sponsoring App mit den folgenden Features:

- **🐳 Multi-Container-Architektur**: Flask App, PostgreSQL mit pgvector, Redis, Traefik, Nginx
- **🔒 Automatisches HTTPS**: Let's Encrypt SSL mit DNS Challenge über Cloudflare
- **📊 Datenbank-Initialisierung**: Automatischer Import von ~11.000 Bibelversen mit AI-Embeddings
- **🛡️ Sicherheit**: Rate Limiting, CSRF-Schutz, Security Headers, Container-Isolation
- **💾 Backup & Restore**: Automatische Backups mit Rollback-Funktionalität
- **🎯 Health Monitoring**: Umfassende Health Checks und Logging
- **⚡ Performance**: Nginx für statische Dateien, Redis für Sessions, optimierte Caching

## 📁 Verzeichnisstruktur

```
app-deployment/
├── 📜 README.md                     # Diese Anleitung
├── 🐳 docker-compose.yml            # Multi-Service Docker Stack
├── 📦 Dockerfile                    # Multi-Stage Flask App Container
├── ⚙️  .env.example                 # Umgebungsvariablen Template
├── 🔧 deploy.sh                     # Automatisiertes Deployment Script
├── 💾 backup-and-restore.sh         # Backup/Restore Utilities
├── 🗄️  setup_db.py                  # Automatische Datenbank-Initialisierung
├── 🧠 vectorize.py                # AI-Embedding-Generierung
├── traefik/                        # Reverse Proxy Konfiguration
│   ├── traefik.yml                # Hauptkonfiguration
│   └── dynamic.yml                # Dynamische Routing-Regeln
├── nginx/                          # Statische Dateien Server
│   └── nginx.conf                 # Nginx Konfiguration
└── secrets/                        # Sichere Konfigurationsdateien
```

## 🔧 Systemanforderungen

### Server-Hardware
- **Minimum**: 2 CPU Cores, 4GB RAM, 20GB Speicher
- **Empfohlen**: 4 CPU Cores, 8GB RAM, 50GB SSD
- **Netzwerk**: Statische IP-Adresse, Ports 8090 (HTTP) und 8091 (HTTPS) freigeschaltet

### Software-Voraussetzungen
- **Betriebssystem**: Ubuntu Server 20.04 LTS oder neuer
- **Docker**: Version 20.10 oder neuer
- **Docker Compose**: Version 2.0 oder neuer

### Externe Dienste
- **Domain**: Registrierte Domain mit DNS-Kontrolle
- **Cloudflare**: Kostenloser Account für DNS-Management und SSL
- **Stripe**: Account für Payment-Processing (Test- oder Live-Modus)
- **OpenAI**: API-Schlüssel für Semantic Search (optional)

## 🚀 Schritt-für-Schritt Installation

### Schritt 1: Server-Vorbereitung

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Benutzer zu Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu anmelden (wichtig!)
newgrp docker

# Docker Compose installieren (falls nicht automatisch installiert)
sudo apt install docker-compose-plugin -y

# Installation testen
docker --version
docker compose version
```

### Schritt 2: App-Code auf Server übertragen

```bash
# Auf deinem Mac: App-Code kopieren
cd /pfad/zur/ngue-app
scp -r app-deployment/ uli@192.168.178.201:/home/uli/docker/ngue-app/
scp -r templates/ static/ app.py models.py requirements.txt uli@192.168.178.201:/home/uli/docker/ngue-app/
scp -r data/ uli@192.168.178.201:/home/uli/docker/ngue-app/

# Auf dem Server: Verzeichnisstruktur prüfen
ssh uli@192.168.178.201
cd /home/uli/docker/ngue-app
ls -la
```

### Schritt 3: Umgebungskonfiguration

```bash
# .env Datei aus Template erstellen
cp .env.example .env

# Konfiguration bearbeiten
nano .env
```

**Kritische Konfigurationswerte:**

```bash
# Domain und SSL
DOMAIN_NAME=ngue.familieprobst.org
ACME_EMAIL=uli@familieprobst.org
CLOUDFLARE_DNS_API_TOKEN=your_cloudflare_token_here

# Sicherheit (Neue Passwörter generieren!)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
POSTGRES_PASSWORD=your_secure_db_password_2025
REDIS_PASSWORD=$(openssl rand -base64 32)

# Stripe (Test- oder Live-Keys)
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# OpenAI (optional für Embedding-Regeneration)
OPENAI_API_KEY=sk-your_openai_key
```

### Schritt 4: Cloudflare DNS API Token erstellen

1. **Cloudflare Dashboard öffnen**: https://dash.cloudflare.com/profile/api-tokens
2. **"Custom Token" erstellen** mit folgenden Berechtigungen:
   - **Zone:Read** - für alle Zonen
   - **DNS:Edit** - für deine Domain (`familieprobst.org`)
3. **Token in .env einfügen**

### Schritt 5: Deployment durchführen

```bash
# Deployment-Script ausführbar machen
chmod +x deploy.sh backup-and-restore.sh

# Erstes Deployment starten
./deploy.sh init
```

Das Initialisierungs-Script führt automatisch folgende Schritte aus:
1. ✅ Docker-Images pullen und bauen
2. ✅ PostgreSQL mit pgvector-Extension starten
3. ✅ **setup_db.py**: Datenbank-Schema erstellen und ~11.000 Verse importieren
4. ✅ **vectorize.py**: AI-Embeddings für Semantic Search generieren (5-10 Min)
5. ✅ SSL-Zertifikate über Let's Encrypt anfordern
6. ✅ Alle Services starten und Health Checks durchführen

### Schritt 6: Deployment verifizieren

```bash
# Status prüfen
./deploy.sh status

# Logs anzeigen
./deploy.sh logs

# Health Check
./deploy.sh health

# Direkt testen
curl -I https://ngue.familieprobst.org/health
```

## 🔄 Täglicher Betrieb

### App-Updates deployen

Die meisten Updates erfordern **keine** komplette Datenbank-Reinitialisierung oder Vektorisierung!

#### ✅ Standard Code-Updates (app.py, templates, static files):

```bash
# 1. Neue Dateien auf Server übertragen
cd /path/to/local/ngue-app
scp app.py benutzer@homeserver:~/docker/ngue-app/
scp -r templates/ benutzer@homeserver:~/docker/ngue-app/
scp -r static/ benutzer@homeserver:~/docker/ngue-app/

# 2. Auf dem Server: App aktualisieren (mit automatischem Backup)
cd ~/docker/ngue-app/app-deployment
./deploy.sh deploy

# 3. Oder einfacher Container-Neustart:
docker compose down
docker compose up -d
```

#### ⚠️ Updates mit Datenbankänderungen (models.py):

```bash
# 1. Backup erstellen (Sicherheit!)
./backup-and-restore.sh backup

# 2. Code übertragen und deployen
./deploy.sh deploy

# 3. Bei DB-Strukturänderungen: Setup manuell ausführen
docker compose run --rm ngue-app python /app/app-deployment/setup_db.py
```

#### 🚨 Vollständige Reinitialisierung (nur bei Major Changes):

```bash
# Nur wenn wirklich nötig (löscht alle Daten!)
docker compose down -v
./deploy.sh init  # Komplett neu: DB-Setup + Vektorisierung
```

### Verschiedene Update-Typen:

| Update-Typ | Aktion | Dauer | Downtime |
|------------|--------|-------|----------|
| **Code-Fixes** (app.py, templates) | `docker compose restart` | 30s | Minimal |
| **Features ohne DB-Änderung** | `./deploy.sh deploy` | 2 Min | ~30s |
| **Neue DB-Felder** | `./deploy.sh deploy` + DB-Setup | 5 Min | 1-2 Min |
| **Major DB-Changes** | `./deploy.sh init` | 10-15 Min | 10 Min |

### Backup und Restore

```bash
# Manuelles Backup erstellen
./backup-and-restore.sh backup --compress

# Verfügbare Backups auflisten
./backup-and-restore.sh list

# Aus Backup wiederherstellen
./backup-and-restore.sh restore backups/ngue_backup_20240824_143000.sql.gz

# Alte Backups aufräumen (7 neueste behalten)
./backup-and-restore.sh cleanup --keep 7
```

### Service-Management

```bash
# Services neustarten
./deploy.sh restart

# Einzelnen Service neustarten
./deploy.sh restart postgres
./deploy.sh restart ngue-app

# Logs eines Services anzeigen
./deploy.sh logs ngue-app
./deploy.sh logs traefik

# Services stoppen
./deploy.sh stop

# Ressourcen aufräumen
./deploy.sh cleanup
```

### Monitoring und Debugging

```bash
# System-Status
docker compose ps
docker compose logs -f --tail=100

# Datenbank-Verbindung testen
docker compose exec postgres psql -U ngue_user -d ngue_db -c "SELECT COUNT(*) FROM verses;"

# App-Container shell
docker compose exec ngue-app /bin/bash

# Performance monitoring
docker stats

# Traefik Dashboard
# https://traefik.ngue.familieprobst.org (mit Basic Auth)
```

## 🛡️ Sicherheit und Wartung

### Sicherheits-Checkliste

- ✅ **Starke Passwörter**: Alle Passwörter in .env sind einzigartig und sicher
- ✅ **SSL/HTTPS**: Let's Encrypt Zertifikate automatisch erneuert
- ✅ **Firewall**: Nur Ports 8090, 8091 von außen erreichbar
- ✅ **Container-Isolation**: Services laufen in isolierten Containern
- ✅ **Rate Limiting**: Schutz vor DDoS und Brute Force Attacks
- ✅ **Security Headers**: HSTS, CSP, XSS-Protection aktiv
- ✅ **Input Validation**: CSRF-Schutz und Form-Validierung

### Regelmäßige Wartung

```bash
# Wöchentlich: Automatisches Backup
./backup-and-restore.sh auto-backup

# Monatlich: System-Updates
sudo apt update && sudo apt upgrade -y
docker compose pull
./deploy.sh deploy

# Vierteljährlich: Backup-Retention prüfen
./backup-and-restore.sh cleanup --keep 30

# Bei Bedarf: Logs rotieren
docker system prune -f
```

## 📊 Überwachung und Metriken

### Health Check Endpunkte

- **App Health**: `https://ngue.familieprobst.org/health`
- **Database**: Automatisch über Container Health Checks
- **SSL-Zertifikat**: Automatische Erneuerung alle 90 Tage

### Log-Dateien

```bash
# App-Logs
docker compose logs ngue-app

# Datenbank-Logs  
docker compose logs postgres

# Traefik-Logs (Access & Error)
docker compose logs traefik

# Nginx-Logs
docker compose logs nginx

# System-weite Logs
journalctl -u docker
```

### Performance-Metriken

```bash
# Container-Ressourcen
docker stats --no-stream

# Datenbank-Performance
docker compose exec postgres psql -U ngue_user -d ngue_db -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;
"

# Festplatten-Nutzung
df -h
du -sh backups/
```

## 🆘 Troubleshooting

### Häufige Probleme und Lösungen

#### Problem: Services starten nicht

```bash
# Diagnose
./deploy.sh status
docker compose ps
docker compose logs

# Lösung
./deploy.sh restart
# oder
docker compose down && docker compose up -d
```

#### Problem: SSL-Zertifikat kann nicht erstellt werden

```bash
# Cloudflare API Token prüfen
echo $CLOUDFLARE_DNS_API_TOKEN

# DNS-Einträge prüfen
dig ngue.familieprobst.org

# Traefik-Logs prüfen
docker compose logs traefik | grep -i "acme\|certificate"

# Lösung: Traefik neu starten
docker compose restart traefik
```

#### Problem: Datenbank-Verbindung fehlgeschlagen

```bash
# PostgreSQL-Status prüfen
docker compose exec postgres pg_isready -U ngue_user -d ngue_db

# Verbindungsparameter testen
docker compose exec ngue-app python -c "
from sqlalchemy import create_engine
engine = create_engine('$SQLALCHEMY_DATABASE_URI')
print('DB Connection OK')
"

# Lösung: PostgreSQL neu starten
docker compose restart postgres
```

#### Problem: Verse-Import oder Vektorisierung fehlgeschlagen

```bash
# Import-Status prüfen
docker compose logs ngue-app

# Manueller DB-Setup
docker compose run --rm ngue-app python /app/app-deployment/setup_db.py

# Manuelle Vektorisierung
docker compose run --rm ngue-app python /app/app-deployment/vectorize.py

# Verses-Datei prüfen
ls -la app-deployment/verses.json
```

### Emergency-Rollback

```bash
# Schneller Rollback zum letzten Backup
./deploy.sh rollback

# Oder manueller Restore
./backup-and-restore.sh list
./backup-and-restore.sh restore backups/[backup-file]
```

## 🔗 Nützliche Links und Ressourcen

### Offizielle Dokumentation
- **Docker Compose**: https://docs.docker.com/compose/
- **Traefik**: https://doc.traefik.io/traefik/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **pgvector**: https://github.com/pgvector/pgvector
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Cloudflare API**: https://developers.cloudflare.com/api/

### Monitoring und Tools
- **Traefik Dashboard**: `https://traefik.ngue.familieprobst.org`
- **SSL Test**: https://www.ssllabs.com/ssltest/
- **DNS Check**: https://dnschecker.org/
- **Stripe Dashboard**: https://dashboard.stripe.com/

### Support und Community
- **Docker Community**: https://forums.docker.com/
- **Traefik Community**: https://community.traefik.io/
- **PostgreSQL Community**: https://www.postgresql.org/community/

## 📞 Support

Bei Problemen oder Fragen zum Deployment:

1. **Logs prüfen**: `./deploy.sh logs` und `./deploy.sh health`
2. **Dokumentation durchsuchen**: Dieses README und offizielle Docs
3. **Community fragen**: Docker/Traefik/PostgreSQL Communities
4. **Backup erstellen**: Vor experimentellen Änderungen

---

## 📝 Changelog

### Version 1.0.0 (August 2024)
- ✨ Initiales Release
- 🐳 Multi-Container Docker Setup
- 🔒 Let's Encrypt SSL Integration
- 📊 Automatische Datenbank-Initialisierung
- 💾 Backup/Restore System
- 🛡️ Umfassende Sicherheitsfeatures

---

**🎉 Viel Erfolg mit deinem NGÜ Bibelvers-Sponsoring App Deployment!**