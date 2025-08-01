# Anleitung für erweiterten Test (Morgen)

## Was wurde vorbereitet:

1. **prepare_extended_test.py** - Extrahiert 100 echte AT-Verse aus deinen Schlachter HTML-Dateien
2. **test_extended.py** - Führt umfassende Tests mit diesen Versen durch
3. Nur Schlachter wird getestet (keine HFA mehr nötig!)

## Schritte für morgen:

### 1. Vorbereitung (5 Minuten)
```bash
cd tests/vector-poc

# Falls noch nicht geschehen
pip install beautifulsoup4

# PostgreSQL starten (falls nicht läuft)
./setup_postgres.sh
```

### 2. Testdaten generieren (5 Minuten)
```bash
python prepare_extended_test.py
```

Dies wird:
- 100 Verse aus verschiedenen AT-Büchern extrahieren
- Automatisch Test-Queries basierend auf gefundenen Themen erstellen
- Alles in `extended_test_data.json` speichern

### 3. Test ausführen (10-15 Minuten)
```bash
python test_extended.py
```

Der Test wird:
- Embeddings für alle 100 Verse generieren
- Verschiedene Suchmetriken evaluieren:
  - Precision@1, @3, @5, @10
  - Mean Reciprocal Rank
  - Durchschnittliche Suchzeiten
- Performance nach Buchtyp analysieren
- Detaillierten Bericht erstellen

## Was du erwarten kannst:

### Performance-Zahlen:
- Embedding-Zeit pro Vers
- Hochrechnung für 11.000 Verse
- Durchschnittliche Suchzeit

### Qualitätsmetriken:
- Ob die 72,7% sich bestätigen
- Welche Buchtypen besser/schlechter funktionieren
- Welche Arten von Queries Probleme machen

### Praktische Erkenntnisse:
- Ist die Performance für Production akzeptabel?
- Brauchen wir Optimierungen?
- Funktioniert es mit echten AT-Texten genauso gut?

## Troubleshooting:

**HTML-Parsing fehlschlägt:**
- Schau dir eine HTML-Datei an und passe die Parser-Logik in `prepare_extended_test.py` an
- Die Funktion `extract_verses_from_html()` hat bereits mehrere Fallback-Optionen

**Zu wenige Verse gefunden:**
- Erhöhe die Anzahl der Kapitel pro Buch (Zeile 108: `book_files[:5]`)
- Füge mehr Bücher zu TEST_BOOKS hinzu

**Performance-Probleme:**
- Reduziere die Batch-Size beim Embedding (Zeile 99 in test_extended.py)
- Teste mit weniger Versen (ändere `num_verses=100` in prepare_extended_test.py)

## Zeitaufwand: ~30 Minuten

Der Test läuft weitgehend automatisch. Du musst nur die Scripts starten und kannst nebenbei Kaffee trinken ☕

Viel Erfolg morgen!
