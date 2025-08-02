# Positivitäts-Scoring für Bibelverse

Dieses Modul bewertet Bibelverse nach ihrer emotionalen Valenz, um positive und ermutigende Verse für die NGÜ Bible Vers Donation App zu identifizieren.

## Dateien

- `run_positivity_scoring.py` - Hauptskript mit PostgreSQL-Integration
- `simple_scorer.py` - Einfache Version ohne Datenbank
- `requirements.txt` - Python-Abhängigkeiten
- `results/` - Ordner für generierte Reports

## Installation

1. Python-Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. PostgreSQL muss installiert und laufend sein (für `run_positivity_scoring.py`)

## Verwendung

### Option 1: Mit PostgreSQL-Datenbank

```bash
python run_positivity_scoring.py
```

Dies erstellt automatisch:
- Eine neue Datenbank `verse_positivity_scoring`
- Eine Tabelle `verse_scores` mit allen Bewertungen
- JSON- und Markdown-Reports im `results/` Ordner

### Option 2: Einfache Version (nur Reports)

```bash
python simple_scorer.py
```

Dies generiert nur einen Markdown-Report ohne Datenbank.

## Scoring-Algorithmus

Der Score basiert auf mehreren Komponenten:

1. **Keyword-Score**: Positive und negative Schlüsselwörter werden gewichtet
2. **Struktur-Score**: Ausrufezeichen, Fragen, direkte Anrede
3. **Themen-Bonus**: Verheißungen, Lobpreis, Trost

Der finale Score wird auf eine Skala von 0-100 normalisiert.

## Empfehlungen

- Verse mit Score ≥ 70 sind besonders positiv und ermutigend
- Verse mit Score ≤ 30 sollten vermieden werden
- Die Top 1000 Verse bilden eine gute Grundlage für die App

## Anpassungen

Die Keyword-Listen können in den Skripten angepasst werden:
- `positive_keywords`: Wörter mit positiver Valenz
- `negative_keywords`: Wörter mit negativer Valenz
- Gewichtungen können individuell justiert werden
