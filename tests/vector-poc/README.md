# Vector Search Proof of Concept

Dieser Ordner enthält Tests zur Validierung unseres Vektorsuche-Konzepts.

## Ziel

Bevor wir mit der Hauptentwicklung beginnen, wollen wir sicherstellen, dass:
1. Die semantische Suche mit deutschen Bibeltexten funktioniert
2. Die HFA 2015 bessere Ergebnisse liefert als Schlachter 1951
3. Die Performance bei ~11.000 Versen akzeptabel ist
4. Cosine Similarity sinnvolle Ähnlichkeiten findet

## Struktur

- `test_embeddings.py` - Haupttest-Script
- `sample_verses.json` - Kleine Auswahl von Testversen
- `requirements.txt` - Benötigte Python-Pakete
- `results/` - Testergebnisse und Benchmarks

## Quick Start

```bash
# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# PostgreSQL mit Docker starten
docker run -d --name pgvector-test -e POSTGRES_PASSWORD=testpass -p 5432:5432 ankane/pgvector

# Tests ausführen
python test_embeddings.py
```

## Was getestet wird

1. **Embedding-Qualität**: Wie gut erfassen die Vektoren semantische Bedeutung?
2. **Übersetzungsvergleich**: HFA vs. Schlachter für Vektorisierung
3. **Suchszenarien**:
   - Stichwortsuche ("Hoffnung", "Liebe", "Stärke")
   - Ähnliche Verse finden
   - Thematische Gruppierung
4. **Performance**: Zeit für Vektorisierung und Suche

## Erwartete Ergebnisse

Nach dem Test sollten wir wissen:
- Welches Embedding-Modell am besten funktioniert
- Ob unser Dual-Translation-Ansatz sinnvoll ist
- Realistische Performance-Zahlen
- Ob weitere Optimierungen nötig sind
