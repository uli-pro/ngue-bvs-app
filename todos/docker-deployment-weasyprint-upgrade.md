# Docker Deployment - WeasyPrint 62.3 Upgrade

## 🎯 Ziel
WeasyPrint wurde lokal von 60.2 auf 62.3 aktualisiert, um die pydyf 0.11.0 Kompatibilitätsprobleme zu lösen. Diese Änderungen müssen für das Docker-Deployment übernommen werden.

## 📊 Ausgangssituation
- **Lokal**: WeasyPrint 62.3 mit pydyf 0.11.0 funktioniert ✅
- **Docker**: Noch WeasyPrint 60.2 konfiguriert ❌
- **Problem**: Ohne Anpassungen wird PDF-Generierung im Docker-Container fehlschlagen

## ✅ Erforderliche Änderungen

### 1. app-deployment/requirements.txt
```diff
- WeasyPrint==60.2
+ WeasyPrint==62.3
```
**Datei**: `/app-deployment/requirements.txt`  
**Zeile**: 27  
**Grund**: Synchronisation mit Haupt-requirements.txt für pydyf-Kompatibilität

### 2. app-deployment/Dockerfile
```diff
RUN apt-get update && apt-get install -y \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    libffi8 \
    libjpeg62-turbo \
    libpng16-16 \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
+   libgobject-2.0-0 \
    libgtk-3-0 \
    curl \
    ca-certificates \
```
**Datei**: `/app-deployment/Dockerfile`  
**Zeile**: Nach Zeile 57 (nach `libgdk-pixbuf-2.0-0`)  
**Stage**: Production Runtime (Stage 2)  
**Grund**: WeasyPrint 62.3 benötigt libgobject-2.0-0 zur Laufzeit

### 3. pdf_service.py
```python
# Am Anfang der Datei, VOR Zeile 10 (vor "import weasyprint"):
import os
import platform

# Setup environment for WeasyPrint on macOS
if platform.system() == "Darwin":
    os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
    os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib"

import weasyprint  # Zeile 10 - bestehendes Import
```
**Datei**: `/pdf_service.py`  
**Position**: Vor Zeile 10 (vor dem WeasyPrint-Import)  
**Grund**: Environment-Variablen müssen gesetzt werden BEVOR WeasyPrint importiert wird

### 4. generate_pdfs_direct.py
```python
def setup_weasyprint_env():
    """Setup environment for WeasyPrint"""
    import platform
    
    # Nur auf macOS setzen wir diese Variablen
    if platform.system() == "Darwin":  # macOS
        os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
        os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
        os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib"
    # Auf Linux (Docker) sind die Libraries bereits im System-Pfad
```
**Datei**: `/generate_pdfs_direct.py`  
**Zeilen**: 13-17 (Funktion setup_weasyprint_env)  
**Grund**: Cross-Platform-Kompatibilität (macOS lokal, Linux im Docker)

## 🔍 Kritische Punkte

### Import-Kette beachten
```
app.py → pdf_service.py → weasyprint
```
**Wichtig**: Da app.py beim Start pdf_service.py importiert, muss die Environment-Setup-Logik in pdf_service.py stehen!

### Platform-Detection
- **macOS (lokal)**: Benötigt Homebrew-Pfade (`/opt/homebrew/lib`)
- **Linux (Docker)**: Libraries sind im System-Pfad, keine speziellen Environment-Variablen nötig
- **DYLD_* Variablen**: Nur für macOS relevant, nicht für Linux

### Library-Namen
- **macOS**: `libgobject-2.0.dylib`
- **Linux**: `libgobject-2.0-0` (mit .so Extension)

## 📋 Deployment-Checkliste

### Lokale Änderungen
- [x] pdf_service.py: Platform-Detection hinzugefügt ✅
- [x] generate_pdfs_direct.py: Platform-Detection hinzugefügt ✅
- [x] app-deployment/requirements.txt: WeasyPrint auf 62.3 ✅
- [x] app-deployment/Dockerfile: libgobject-2.0-0 hinzugefügt ✅
- [ ] Änderungen committen

### Server-Deployment
- [ ] Git pull auf Server
- [ ] Docker Images neu bauen: `docker-compose build --no-cache ngue-app`
- [ ] Container neu starten: `docker-compose down && docker-compose up -d`
- [ ] Logs prüfen: `docker-compose logs -f ngue-app`
- [ ] PDF-Generierung testen

## 🧪 Test-Kommandos

### Lokaler Test (macOS)
```bash
python3 generate_pdfs_direct.py
```

### Docker-Test (nach Deployment)
```bash
docker-compose exec ngue-app python generate_pdfs_direct.py
```

### WeasyPrint-Import-Test
```bash
docker-compose exec ngue-app python -c "import weasyprint; print(f'WeasyPrint {weasyprint.__version__} loaded successfully')"
```

## 🚨 Fallback bei Problemen

Falls die PDF-Generierung nach dem Update nicht funktioniert:

### Option 1: Zurück zur alten Version
```bash
# In requirements.txt und app-deployment/requirements.txt:
WeasyPrint==60.2
pydyf==0.10.0
```

### Option 2: Debug im Container
```bash
# Shell im Container öffnen
docker-compose exec ngue-app bash

# Libraries prüfen
ldconfig -p | grep gobject
python -c "import weasyprint"
```

## 📝 Notizen

- **Erstellt am**: 28.08.2025
- **Aktualisiert am**: 28.08.2025
- **WeasyPrint Upgrade**: 60.2 → 62.3 ✅
- **pydyf Version**: 0.11.0 (kompatibel mit WeasyPrint 62.3) ✅
- **Platform-Detection**: Implementiert in pdf_service.py und generate_pdfs_direct.py ✅
- **Docker-Dateien**: Alle aktualisiert ✅
- **Getestet auf**: macOS lokal ✅, Docker-Deployment bereit für Test ⏳

## 🔗 Verwandte Dokumente
- `/todos/weasyprint-debugging-guide.md` - Ursprüngliche Problemanalyse
- `/requirements.txt` - Haupt-Dependencies (bereits aktualisiert)
- `/app-deployment/` - Deployment-Konfiguration