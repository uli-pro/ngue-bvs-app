# WeasyPrint Debugging Guide

## 🚨 Problem-Zusammenfassung

Wir haben zwei verschiedene WeasyPrint-Probleme identifiziert, die beide gelöst werden müssen:

1. **System-Dependencies Problem** - gobject-2.0 Library wird nicht gefunden
2. **API Inkompatibilität Problem** - `PDF.__init__()` Parameter-Mismatch

## 📊 Aktuelle Situation

### Problem 1: Library Loading Error
```
OSError: cannot load library 'gobject-2.0-0': dlopen(gobject-2.0-0, 0x0002): tried: 'gobject-2.0-0' (no such file)
```

### Problem 2: API Parameter Error  
```
TypeError: PDF.__init__() takes 1 positional argument but 3 were given
```

## 🔍 Detailierte Problemanalyse

### Problem 1: gobject-2.0 Library Issue

#### Was passiert:

- WeasyPrint versucht `gobject-2.0-0` als shared library zu laden
- macOS/Homebrew installiert es als `libgobject-2.0.dylib`
- WeasyPrint's FFI-Layer findet die Library nicht unter dem erwarteten Namen

#### Bereits durchgeführte Schritte:
```bash
✅ brew install cairo pango gdk-pixbuf libffi gobject-introspection
✅ export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
✅ export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
✅ pkg-config --libs gobject-2.0  # Funktioniert: zeigt korrekte Pfade
```

#### Warum es trotzdem nicht funktioniert:
WeasyPrint's `text/ffi.py` sucht explizit nach `gobject-2.0-0`, aber Homebrew installiert:
- `/opt/homebrew/lib/libgobject-2.0.dylib` 
- `/opt/homebrew/lib/libgobject-2.0.0.dylib`

### Problem 2: PDF API Inkompatibilität

#### Was passiert:
```python
# WeasyPrint ruft auf:
pdf = pydyf.PDF((version or '1.7'), identifier)

# Aber pydyf.PDF erwartet:
PDF.__init__(self)  # Nur self parameter
```

#### Mögliche Ursachen:
1. **Version Mismatch**: WeasyPrint 60.2 inkompatibel mit aktueller pydyf Version
2. **Dependency Conflict**: Andere Library überschreibt pydyf

## 🛠️ Debugging-Strategie

### Phase 1: Versions-Analyse

#### Schritt 1: Aktuelle Versionen prüfen
```bash
pip show weasyprint
pip show pydyf
pip show cairocffi
pip show cffi
```

#### Schritt 2: Dependency Tree analysieren
```bash
pip freeze | grep -E "(weasyprint|pydyf|cairocffi|cffi)"
```

### Phase 2: Library Loading Debug

#### Schritt 1: Verfügbare gobject Libraries finden
```bash
find /opt/homebrew/lib -name "*gobject*" -type f
otool -L /opt/homebrew/lib/libgobject-2.0.dylib
```

#### Schritt 2: CFFI Debug aktivieren
```python
import os
os.environ['CFFI_VERBOSE'] = '1'
import weasyprint
```

#### Schritt 3: Manual Library Loading Test
```python
from cffi import FFI
ffi = FFI()
# Test verschiedene Library Namen
names = [
    'gobject-2.0-0',
    'gobject-2.0',
    'libgobject-2.0',
    '/opt/homebrew/lib/libgobject-2.0.dylib'
]
for name in names:
    try:
        lib = ffi.dlopen(name)
        print(f"✅ Erfolgreich geladen: {name}")
    except Exception as e:
        print(f"❌ Fehlgeschlagen: {name} - {e}")
```

### Phase 3: Version Compatibility Fix

#### Option A: WeasyPrint Version Downgrade
```bash
# Test mit älterer WeasyPrint Version
pip uninstall weasyprint pydyf
pip install weasyprint==58.1  # Letzte stabile Version
```

#### Option B: pydyf Version Fix
```bash
# Test mit spezifischer pydyf Version
pip install pydyf==0.8.0  # Kompatible Version
```

#### Option C: Clean Install
```bash
# Komplett clean install
pip uninstall weasyprint pydyf cairocffi cffi
pip install weasyprint==60.2 --no-cache-dir
```

## 🔧 Konkrete Lösungsschritte

### Lösung 1: Library Symlink erstellen

#### Problem: WeasyPrint sucht `gobject-2.0-0`, findet aber `libgobject-2.0.0.dylib`

```bash
# Erstelle Symlink für gobject
cd /opt/homebrew/lib
sudo ln -sf libgobject-2.0.0.dylib libgobject-2.0-0.dylib

# Test ob es funktioniert
python3 -c "
import os
os.environ['PKG_CONFIG_PATH'] = '/opt/homebrew/lib/pkgconfig'
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'
from cffi import FFI
ffi = FFI()
lib = ffi.dlopen('gobject-2.0-0')
print('✅ gobject-2.0 erfolgreich geladen')
"
```

### Lösung 2: Environment Variables erweitern

#### Problem: DYLD_LIBRARY_PATH reicht nicht aus

```bash
# Erweiterte Environment Setup
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib:/usr/lib"
export LD_LIBRARY_PATH="/opt/homebrew/lib:$LD_LIBRARY_PATH"

# Für permanente Lösung in ~/.zshrc oder ~/.bash_profile
echo 'export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"' >> ~/.zshrc
echo 'export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"' >> ~/.zshrc
echo 'export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib:/usr/lib"' >> ~/.zshrc
```

### Lösung 3: WeasyPrint Version Compatibility Fix

#### Problem: pydyf API Inkompatibilität

```bash
# Teste kompatible Versionen
pip uninstall weasyprint pydyf -y
pip install weasyprint==59.0 pydyf==0.8.0

# Oder neueste kompatible Version
pip install weasyprint==61.0  # Aktuellste Version mit Fix
```

## 🧪 Test-Sequence

### Test 1: Library Loading
```python
#!/usr/bin/env python3
import os

# Environment setup
os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib:/usr/local/lib:/usr/lib"

try:
    from weasyprint.text.ffi import ffi, gobject
    print("✅ gobject successfully loaded")
except Exception as e:
    print(f"❌ gobject loading failed: {e}")
```

### Test 2: PDF API
```python
#!/usr/bin/env python3
import os
os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib:/usr/local/lib:/usr/lib"

try:
    import weasyprint
    import pydyf
    
    # Test PDF creation
    pdf = pydyf.PDF()
    print(f"✅ pydyf.PDF() works - Version: {pydyf.__version__}")
    
    # Test WeasyPrint HTML to PDF
    html = weasyprint.HTML(string="<html><body><h1>Test</h1></body></html>")
    pdf_bytes = html.write_pdf()
    print(f"✅ WeasyPrint PDF generation works - {len(pdf_bytes)} bytes")
    
except Exception as e:
    print(f"❌ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
```

### Test 3: Full Certificate Generation
```python
#!/usr/bin/env python3
import os
os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib:/usr/local/lib:/usr/lib"

try:
    import weasyprint
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page { size: A4; margin: 20mm; }
            body { font-family: Arial, sans-serif; }
            .title { color: #2c5f8f; text-align: center; font-size: 24pt; }
        </style>
    </head>
    <body>
        <h1 class="title">NGÜ Test-Zertifikat</h1>
        <p>Dies ist ein Test der WeasyPrint PDF-Generierung.</p>
    </body>
    </html>
    """
    
    html = weasyprint.HTML(string=html_content)
    pdf_path = "docs/weasyprint_test_final.pdf"
    html.write_pdf(pdf_path)
    
    print(f"✅ Test-PDF erfolgreich erstellt: {pdf_path}")
    
except Exception as e:
    print(f"❌ Certificate generation failed: {e}")
    import traceback
    traceback.print_exc()
```

## 📋 Debugging Checklist

### Vor dem Fix:
- [ ] Aktuelle WeasyPrint Version dokumentieren
- [ ] Aktuelle pydyf Version dokumentieren  
- [ ] Verfügbare gobject Libraries auflisten
- [ ] Environment Variables prüfen

### Fix-Versuche (in Reihenfolge):
1. [ ] **Symlink-Lösung**: gobject Library-Namen korrigieren
2. [ ] **Environment-Lösung**: Erweiterte DYLD Pfade setzen
3. [ ] **Version-Lösung**: Kompatible WeasyPrint/pydyf Versionen installieren

### Nach dem Fix:
- [ ] Library Loading Test erfolgreich
- [ ] PDF API Test erfolgreich  
- [ ] Full Certificate Generation Test erfolgreich
- [ ] Alle 4 Zertifikat-PDFs erstellt

## 🎯 Erwartetes Endergebnis

Nach erfolgreicher Problemlösung sollten folgende PDFs in `/docs` erstellt werden:

```
docs/
├── ngue_personal_certificate_example.pdf     # Persönliches Zertifikat
├── ngue_group_certificate_example.pdf        # Gruppenzertifikat
├── ngue_gift_certificate_example.pdf         # Geschenkzertifikat  
└── ngue_tax_receipt_example.pdf             # Spendenbescheinigung
```

Jede PDF sollte:
- ✅ A4-Format haben
- ✅ Korrekte Schriftarten verwenden
- ✅ NGÜ-Design und Layout zeigen
- ✅ Beispieldaten enthalten
- ✅ Mit PDF-Viewer korrekt anzeigbar sein

## 🚀 Nächste Schritte

1. **Debug Tests ausführen** - Test-Scripts von oben durchlaufen
2. **Fix implementieren** - Je nach Test-Ergebnissen passende Lösung wählen
3. **PDFs generieren** - generate_pdfs_direct.py mit Fix ausführen
4. **Qualität prüfen** - PDFs öffnen und Design validieren

Dieses systematische Vorgehen sollte das WeasyPrint-Problem definitiv lösen!