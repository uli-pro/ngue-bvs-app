#!/usr/bin/env python3
"""
Positivitäts-Scoring für Bibelverse mit PostgreSQL
Dieses Skript bewertet Bibelverse nach ihrer emotionalen Valenz
und speichert die Ergebnisse in einer PostgreSQL-Datenbank.
"""

import json
import re
import os
import psycopg2
from psycopg2 import sql
from typing import Dict, List, Tuple
from datetime import datetime
import sys

# Konfiguration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': 'verse_positivity_scoring'
}

class DatabaseManager:
    """Verwaltet die PostgreSQL-Datenbankverbindung und -operationen."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Stellt eine Verbindung zur Datenbank her."""
        try:
            # Zuerst zur postgres DB verbinden um neue DB zu erstellen
            temp_config = DB_CONFIG.copy()
            temp_config['database'] = 'postgres'
            temp_conn = psycopg2.connect(**temp_config)
            temp_conn.autocommit = True
            temp_cursor = temp_conn.cursor()
            
            # Prüfe ob Datenbank existiert, wenn nicht, erstelle sie
            temp_cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DB_CONFIG['database'],)
            )
            if not temp_cursor.fetchone():
                temp_cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(DB_CONFIG['database'])
                    )
                )
                print(f"Datenbank '{DB_CONFIG['database']}' erstellt.")
            
            temp_cursor.close()
            temp_conn.close()
            
            # Jetzt zur eigentlichen Datenbank verbinden
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"Verbunden mit Datenbank '{DB_CONFIG['database']}'.")
            
        except Exception as e:
            print(f"Fehler beim Datenbankverbindung: {e}")
            sys.exit(1)
    
    def create_tables(self):
        """Erstellt die notwendigen Tabellen."""
        try:
            # Tabelle für die Scoring-Ergebnisse
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS verse_scores (
                    id SERIAL PRIMARY KEY,
                    verse_id VARCHAR(50) UNIQUE NOT NULL,
                    reference VARCHAR(100) NOT NULL,
                    book VARCHAR(50) NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    positivity_score DECIMAL(5,2) NOT NULL,
                    raw_score DECIMAL(5,2) NOT NULL,
                    keyword_score DECIMAL(5,2) NOT NULL,
                    structure_score DECIMAL(5,2) NOT NULL,
                    theme_bonus DECIMAL(5,2) NOT NULL,
                    positive_keywords JSONB,
                    negative_keywords JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index für schnellere Sortierung
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_positivity_score 
                ON verse_scores(positivity_score DESC)
            """)
            
            self.conn.commit()
            print("Tabellen erfolgreich erstellt.")
            
        except Exception as e:
            print(f"Fehler beim Erstellen der Tabellen: {e}")
            self.conn.rollback()
            sys.exit(1)
    
    def insert_scores(self, scored_verses: List[Dict]):
        """Fügt die bewerteten Verse in die Datenbank ein."""
        try:
            for verse in scored_verses:
                self.cursor.execute("""
                    INSERT INTO verse_scores 
                    (verse_id, reference, book, chapter, verse, text,
                     positivity_score, raw_score, keyword_score, 
                     structure_score, theme_bonus, positive_keywords, negative_keywords)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (verse_id) 
                    DO UPDATE SET
                        positivity_score = EXCLUDED.positivity_score,
                        raw_score = EXCLUDED.raw_score,
                        keyword_score = EXCLUDED.keyword_score,
                        structure_score = EXCLUDED.structure_score,
                        theme_bonus = EXCLUDED.theme_bonus,
                        positive_keywords = EXCLUDED.positive_keywords,
                        negative_keywords = EXCLUDED.negative_keywords,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    verse['verse_id'],
                    verse['reference'],
                    verse['book'],
                    verse['chapter'],
                    verse['verse'],
                    verse['text'],
                    verse['positivity_score'],
                    verse['raw_score'],
                    verse['keyword_score'],
                    verse['structure_score'],
                    verse['theme_bonus'],
                    json.dumps(verse['found_keywords']['positive']),
                    json.dumps(verse['found_keywords']['negative'])
                ))
            
            self.conn.commit()
            print(f"{len(scored_verses)} Verse in die Datenbank eingefügt.")
            
        except Exception as e:
            print(f"Fehler beim Einfügen der Daten: {e}")
            self.conn.rollback()
    
    def close(self):
        """Schließt die Datenbankverbindung."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


class BibelversPositivityScorer:
    """Hauptklasse für das Positivitäts-Scoring von Bibelversen."""
    
    def __init__(self):
        # Positive Schlüsselwörter mit Gewichtungen
        self.positive_keywords = {
            # Göttliche Eigenschaften
            'liebe': 3.0, 'lieben': 3.0, 'liebt': 3.0, 'geliebt': 3.0,
            'gnade': 3.0, 'gnädig': 3.0, 'barmherzig': 3.0, 'barmherzigkeit': 3.0,
            'güte': 3.0, 'gütig': 3.0, 'freundlich': 2.5, 'freundlichkeit': 2.5,
            
            # Positive Emotionen
            'freude': 3.0, 'freuen': 3.0, 'fröhlich': 2.5, 'glück': 2.5, 'glücklich': 2.5,
            'frieden': 3.0, 'friedlich': 2.5, 'ruhe': 2.0, 'ruhig': 2.0,
            'hoffnung': 3.0, 'hoffen': 2.5, 'zuversicht': 2.5, 'zuversichtlich': 2.5,
            
            # Spirituelle Konzepte
            'segen': 3.0, 'segnen': 3.0, 'gesegnet': 3.0, 'segnung': 3.0,
            'heil': 3.0, 'heilung': 3.0, 'heilen': 3.0, 'geheilt': 3.0,
            'erlösung': 3.0, 'erlösen': 3.0, 'erlöst': 3.0, 'erretten': 3.0, 'gerettet': 3.0,
            'ewigkeit': 2.5, 'ewig': 2.5, 'leben': 2.5, 'lebens': 2.5, 'lebendig': 2.5,
            
            # Positive Handlungen
            'helfen': 2.5, 'hilfe': 2.5, 'hilft': 2.5, 'geholfen': 2.5,
            'schutz': 2.5, 'schützen': 2.5, 'beschützen': 2.5, 'bewahren': 2.5,
            'trost': 2.5, 'trösten': 2.5, 'getröstet': 2.5, 'ermutigen': 2.5,
            'vertrauen': 2.5, 'glauben': 2.5, 'glaube': 2.5, 'treue': 2.5, 'treu': 2.5,
            
            # Positive Eigenschaften
            'stark': 2.0, 'stärke': 2.0, 'kraft': 2.0, 'kräftig': 2.0, 'mächtig': 2.0,
            'weisheit': 2.0, 'weise': 2.0, 'verstand': 2.0, 'erkenntnis': 2.0,
            'gerecht': 2.0, 'gerechtigkeit': 2.0, 'rechtschaffen': 2.0,
            'gut': 2.0, 'gutes': 2.0, 'guten': 2.0, 'beste': 2.0,
            
            # Licht und Führung
            'licht': 2.5, 'leuchten': 2.0, 'hell': 2.0, 'strahlen': 2.0,
            'führen': 2.0, 'führung': 2.0, 'leiten': 2.0, 'weg': 1.5,
            
            # Gemeinschaft
            'gemeinschaft': 2.0, 'zusammen': 1.5, 'einheit': 2.0, 'gemeinsam': 1.5,
            
            # Dankbarkeit
            'danken': 2.5, 'dank': 2.5, 'dankbar': 2.5, 'loben': 2.5, 'preisen': 2.5,
            
            # Vergebung
            'vergeben': 3.0, 'vergebung': 3.0, 'verzeihen': 2.5, 'verzeihung': 2.5,
            
            # Wachstum
            'wachsen': 1.5, 'gedeihen': 2.0, 'blühen': 2.0, 'frucht': 1.5,
            
            # Himmlisches
            'himmel': 2.0, 'himmlisch': 2.0, 'paradies': 2.5, 'herrlichkeit': 2.5
        }
        
        # Negative Schlüsselwörter mit Gewichtungen
        self.negative_keywords = {
            # Tod und Zerstörung
            'tod': -3.0, 'tot': -3.0, 'sterben': -3.0, 'gestorben': -3.0, 'töten': -3.0,
            'vernichten': -3.0, 'vernichtung': -3.0, 'zerstören': -3.0, 'zerstörung': -3.0,
            
            # Negative Emotionen
            'zorn': -3.0, 'zornig': -3.0, 'wut': -3.0, 'wütend': -3.0, 'hass': -3.0, 'hassen': -3.0,
            'angst': -2.5, 'fürchten': -2.5, 'furcht': -2.5, 'erschrecken': -2.5,
            'trauer': -2.5, 'traurig': -2.5, 'weinen': -2.0, 'tränen': -2.0, 'klagen': -2.0,
            'schmerz': -2.5, 'leiden': -2.5, 'qual': -2.5, 'pein': -2.5,
            
            # Sünde und Schuld
            'sünde': -2.5, 'sündigen': -2.5, 'sünder': -2.5, 'schuld': -2.5, 'schuldig': -2.5,
            'böse': -2.5, 'übel': -2.5, 'schlecht': -2.0, 'gottlos': -2.5,
            
            # Strafe und Gericht
            'strafe': -2.5, 'strafen': -2.5, 'gericht': -2.5, 'richten': -2.0,
            'verdammen': -3.0, 'verdammnis': -3.0, 'fluch': -3.0, 'verfluchen': -3.0,
            
            # Konflikt
            'krieg': -2.5, 'kampf': -2.0, 'streit': -2.0, 'feind': -2.0, 'feinde': -2.0,
            'schlagen': -2.0, 'schwert': -2.0, 'waffe': -2.0,
            
            # Negation und Mangel (nicht und kein entfernt - zu allgemein)
            'niemals': -1.0, 'nie': -1.0, 'nimmer': -1.0, 'nirgends': -1.0,
            'mangel': -2.0, 'fehlen': -1.5, 'verloren': -2.0, 'verlieren': -2.0,
            
            # Dunkelheit
            'finsternis': -2.5, 'dunkel': -2.0, 'dunkelheit': -2.0, 'schatten': -1.5,
            
            # Negative Zustände
            'krank': -2.0, 'krankheit': -2.0, 'schwach': -1.5, 'schwäche': -1.5,
            'arm': -1.5, 'armut': -2.0, 'elend': -2.5, 'not': -2.0,
            
            # Täuschung
            'lüge': -2.5, 'lügen': -2.5, 'betrug': -2.5, 'betrügen': -2.5,
            'falsch': -2.0, 'täuschen': -2.0, 'täuschung': -2.0
        }
        
        # Kontextmodifikatoren - Phrasen die die Bedeutung umkehren
        self.context_modifiers = {
            # Negation von Negativem wird positiv
            'nicht .{0,20}fürchten': 3.0,
            'fürchte.{0,10}nicht': 3.0,
            'keine?.{0,20}furcht': 2.5,
            'keine?.{0,20}angst': 2.5,
            'nicht.{0,20}verlassen': 2.5,
            'nicht.{0,20}schämen': 2.0,
            'kein.{0,20}tod': 3.0,
            'kein.{0,20}mangel': 2.5,
            'nicht.{0,20}zuschanden': 2.0,
            
            # Überwindung des Negativen
            'vom.{0,20}erlösen': 3.0,
            'aus.{0,20}erretten': 3.0,
            'überwind.{0,20}böse': 2.5,
            'sieg über': 2.5,
            'befreit von': 2.5,
            
            # Transformation
            'aus.{0,20}finsternis.{0,20}licht': 3.0,
            'vom.{0,20}tod.{0,20}leben': 3.0,
            'trauer.{0,20}freude': 3.0,
        }
    
    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict[str, int]]:
        """Berechnet den Keyword-basierten Score."""
        text_lower = text.lower()
        
        positive_score = 0.0
        negative_score = 0.0
        found_keywords = {'positive': {}, 'negative': {}}
        
        # Positive Keywords zählen
        for keyword, weight in self.positive_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
            if count > 0:
                positive_score += weight * count
                found_keywords['positive'][keyword] = count
                
        # Negative Keywords zählen
        for keyword, weight in self.negative_keywords.items():
            count = len(re.findall(r'\b' + keyword + r'\b', text_lower))
            if count > 0:
                negative_score += weight * count
                found_keywords['negative'][keyword] = count
        
        # Kontextmodifikatoren anwenden
        for pattern, modifier in self.context_modifiers.items():
            if re.search(pattern, text_lower):
                positive_score += modifier
                
        total_score = positive_score + negative_score
        
        return total_score, found_keywords
    
    def analyze_structure(self, text: str) -> float:
        """Analysiert die Struktur des Verses."""
        structure_score = 0.0
        
        # Ausrufezeichen deuten oft auf Ermutigung hin
        exclamation_count = text.count('!')
        structure_score += exclamation_count * 0.5
        
        # Rhetorische Fragen können negativ sein
        if '?' in text and any(word in text.lower() for word in ['warum', 'weshalb', 'wieso']):
            structure_score -= 1.0
            
        # Direkte Anrede ist oft ermutigend
        if any(phrase in text.lower() for phrase in ['du bist', 'ihr seid', 'wir sind']):
            structure_score += 0.5
            
        return structure_score
    
    def calculate_theme_bonus(self, text: str) -> float:
        """Gibt Bonus-Punkte für bestimmte positive Themen."""
        theme_score = 0.0
        text_lower = text.lower()
        
        # Verheißungen und Zusagen Gottes
        if any(phrase in text_lower for phrase in ['ich will', 'ich werde', 'er wird', 'gott wird']):
            if any(word in text_lower for word in ['segnen', 'helfen', 'erretten', 'bewahren', 'geben', 'schenken']):
                theme_score += 3.0
        
        # Zusicherungen und Versprechen
        if any(phrase in text_lower for phrase in ['der herr ist', 'gott ist', 'er ist']):
            if any(word in text_lower for word in ['treu', 'gnädig', 'barmherzig', 'gut', 'gerecht']):
                theme_score += 2.5
                
        # Lobpreis und Anbetung
        if any(phrase in text_lower for phrase in ['lobet den herrn', 'preiset', 'danket', 'halleluja', 'ehre sei']):
            theme_score += 3.0
            
        # Direkte Ermutigung
        if any(phrase in text_lower for phrase in ['sei stark', 'sei mutig', 'fürchte dich nicht', 'sei getrost']):
            theme_score += 3.0
            
        # Seligpreisungen
        if text_lower.startswith('selig') or 'selig sind' in text_lower or 'glücklich sind' in text_lower:
            theme_score += 2.5
            
        # Ewige Perspektive
        if 'ewiges leben' in text_lower or 'ewige freude' in text_lower or 'ewiger friede' in text_lower:
            theme_score += 2.0
            
        return theme_score
    
    def calculate_positivity_score(self, verse: Dict) -> Dict:
        """Berechnet den Gesamt-Positivitätsscore für einen Vers."""
        text = verse['text']
        
        # Scores berechnen
        keyword_score, found_keywords = self.calculate_keyword_score(text)
        structure_score = self.analyze_structure(text)
        theme_bonus = self.calculate_theme_bonus(text)
        
        # Gesamtscore
        total_score = keyword_score + structure_score + theme_bonus
        
        # Normalisierung auf 0-100 Skala
        normalized_score = max(0, min(100, (total_score + 20) * 2.5))
        
        return {
            'verse_id': verse.get('id', ''),
            'reference': verse.get('reference', ''),
            'book': verse.get('book', ''),
            'chapter': verse.get('chapter', 0),
            'verse': verse.get('verse', 0),
            'text': text,
            'positivity_score': round(normalized_score, 2),
            'raw_score': round(total_score, 2),
            'keyword_score': round(keyword_score, 2),
            'structure_score': round(structure_score, 2),
            'theme_bonus': round(theme_bonus, 2),
            'found_keywords': found_keywords
        }
    
    def score_verses(self, verses: List[Dict]) -> List[Dict]:
        """Bewertet eine Liste von Versen."""
        scored_verses = []
        
        for verse in verses:
            scored_verse = self.calculate_positivity_score(verse)
            scored_verses.append(scored_verse)
            
        # Nach Score sortieren
        scored_verses.sort(key=lambda x: x['positivity_score'], reverse=True)
        
        return scored_verses


def generate_detailed_report(scored_verses: List[Dict], output_dir: str, timestamp: str):
    """Generiert einen detaillierten Markdown-Report mit vollständigen Texten."""
    report_file = os.path.join(output_dir, f"positivity_analysis_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Bibelvers Positivitäts-Analyse Report\n\n")
        f.write(f"**Generiert am**: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}\n")
        f.write(f"**Anzahl analysierter Verse**: {len(scored_verses)}\n\n")
        
        # Zusammenfassung
        scores = [v['positivity_score'] for v in scored_verses]
        avg_score = sum(scores) / len(scores)
        
        f.write("## Zusammenfassung\n\n")
        f.write(f"- **Durchschnittlicher Positivitäts-Score**: {avg_score:.2f}/100\n")
        f.write(f"- **Höchster Score**: {max(scores):.2f}\n")
        f.write(f"- **Niedrigster Score**: {min(scores):.2f}\n")
        f.write(f"- **Verse mit Score ≥ 70**: {len([s for s in scores if s >= 70])} ")
        f.write(f"({(len([s for s in scores if s >= 70])/len(scores)*100):.1f}%)\n")
        f.write(f"- **Verse mit Score ≤ 30**: {len([s for s in scores if s <= 30])} ")
        f.write(f"({(len([s for s in scores if s <= 30])/len(scores)*100):.1f}%)\n\n")
        
        # Score-Verteilung
        f.write("## Score-Verteilung\n\n")
        f.write("| Score-Bereich | Anzahl Verse | Prozent |\n")
        f.write("|---------------|--------------|----------|\n")
        ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        for low, high in ranges:
            count = len([s for s in scores if low <= s < high])
            percentage = (count / len(scores)) * 100
            f.write(f"| {low}-{high} | {count} | {percentage:.1f}% |\n")
        
        # Top 50 Positive Verse (bei 11.000 Versen mehr zeigen)
        f.write("\n## Top 50 Positive Verse\n\n")
        f.write("Die folgenden Verse haben die höchsten Positivitäts-Scores und eignen sich ")
        f.write("besonders gut für die Spenden-App:\n\n")
        
        for i, verse in enumerate(scored_verses[:50], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"**Vollständiger Text:**\n")
            f.write(f"> {verse['text']}\n\n")
            
            f.write("**Analyse:**\n")
            if verse['found_keywords']['positive']:
                f.write(f"- **Positive Schlüsselwörter**: ")
                pos_words = [f"{k} ({v}x)" for k, v in verse['found_keywords']['positive'].items()]
                f.write(f"{', '.join(pos_words)}\n")
            
            if verse['found_keywords']['negative']:
                f.write(f"- **Negative Schlüsselwörter**: ")
                neg_words = [f"{k} ({v}x)" for k, v in verse['found_keywords']['negative'].items()]
                f.write(f"{', '.join(neg_words)}\n")
            
            f.write(f"- **Score-Komponenten**: ")
            f.write(f"Keywords: {verse['keyword_score']:.1f}, ")
            f.write(f"Struktur: {verse['structure_score']:.1f}, ")
            f.write(f"Thema: {verse['theme_bonus']:.1f}\n")
            f.write("\n---\n\n")
        
        # Mittlere Verse (Beispiele)
        f.write("## Verse mit mittlerem Score (40-60)\n\n")
        f.write("Beispiele für Verse mit neutralem bis leicht positivem Score:\n\n")
        
        middle_verses = [v for v in scored_verses if 40 <= v['positivity_score'] <= 60][:10]
        for i, verse in enumerate(middle_verses, 1):
            f.write(f"### {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"> {verse['text']}\n\n")
        
        # Bottom 20 (niedrigste Scores)
        f.write("## Bottom 20 - Verse mit niedrigem Score\n\n")
        f.write("Diese Verse sind für die Spenden-App weniger geeignet, ")
        f.write("da sie überwiegend negative Themen behandeln:\n\n")
        
        for i, verse in enumerate(scored_verses[-20:], 1):
            f.write(f"### {i}. {verse['reference']} (Score: {verse['positivity_score']})\n\n")
            f.write(f"**Vollständiger Text:**\n")
            f.write(f"> {verse['text']}\n\n")
            
            f.write("**Analyse:**\n")
            if verse['found_keywords']['negative']:
                f.write(f"- **Negative Schlüsselwörter**: ")
                neg_words = [f"{k} ({v}x)" for k, v in verse['found_keywords']['negative'].items()]
                f.write(f"{', '.join(neg_words)}\n")
            
            if verse['found_keywords']['positive']:
                f.write(f"- **Positive Schlüsselwörter**: ")
                pos_words = [f"{k} ({v}x)" for k, v in verse['found_keywords']['positive'].items()]
                f.write(f"{', '.join(pos_words)}\n")
            
            f.write("\n---\n\n")
        
        # Top 1000 für die App
        top_1000 = scored_verses[:1000]
        f.write("## Top 1000 Verse für die App\n\n")
        f.write(f"Die Top 1000 Verse haben Scores zwischen {top_1000[-1]['positivity_score']:.1f} ")
        f.write(f"und {top_1000[0]['positivity_score']:.1f}.\n\n")
        
        # Bücher-Statistik für Top 1000
        book_counts = {}
        for verse in top_1000:
            book = verse['book']
            book_counts[book] = book_counts.get(book, 0) + 1
        
        f.write("### Verteilung nach Büchern (Top 1000):\n\n")
        for book, count in sorted(book_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"- {book}: {count} Verse\n")
        
        # Empfehlungen
        f.write("\n## Empfehlungen für die App\n\n")
        f.write(f"1. **Schwellenwert**: Die Top 1000 haben alle einen Score ≥ {top_1000[-1]['positivity_score']:.1f}\n")
        f.write("2. **Diversität**: Die Verse kommen aus verschiedenen Büchern (siehe Verteilung oben)\n")
        f.write("3. **Zufallsauswahl**: Bei jedem Besuch 3 zufällige Verse aus den Top 1000 zeigen\n")
        f.write("4. **Manuelle Prüfung**: Stichproben der Top-Kandidaten sollten geprüft werden\n")
        
    print(f"✓ Detaillierter Report gespeichert: {report_file}")
    return report_file


def main():
    """Hauptfunktion."""
    print("=== Bibelvers Positivitäts-Scoring ===\n")
    
    # Pfade
    base_path = "/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app"
    input_file = os.path.join(base_path, "tests/vector-poc/final_verses_data.json")
    output_dir = os.path.join(base_path, "tests/positivity-scoring/results")
    
    # Datenbank-Manager initialisieren
    print("1. Initialisiere Datenbank...")
    db = DatabaseManager()
    db.connect()
    db.create_tables()
    
    # Scorer initialisieren
    scorer = BibelversPositivityScorer()
    
    # Verse laden
    print("\n2. Lade Verse...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            verses_data = json.load(f)
        verses = verses_data['verses']
        print(f"   ✓ {len(verses)} Verse geladen")
    except Exception as e:
        print(f"   ✗ Fehler beim Laden der Verse: {e}")
        sys.exit(1)
    
    # Scoring durchführen
    print("\n3. Berechne Positivitäts-Scores...")
    scored_verses = scorer.score_verses(verses)
    print(f"   ✓ Scoring abgeschlossen")
    
    # In Datenbank speichern
    print("\n4. Speichere in Datenbank...")
    db.insert_scores(scored_verses)
    
    # Reports generieren
    print("\n5. Generiere Reports...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON-Export
    json_file = os.path.join(output_dir, f"scored_verses_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': len(scored_verses),
                'timestamp': timestamp,
                'average_score': sum(v['positivity_score'] for v in scored_verses) / len(scored_verses)
            },
            'scored_verses': scored_verses
        }, f, ensure_ascii=False, indent=2)
    print(f"   ✓ JSON-Export: {json_file}")
    
    # Detaillierter Markdown-Report
    report_file = generate_detailed_report(scored_verses, output_dir, timestamp)
    
    # Top 1000 für die App exportieren
    top_1000_file = os.path.join(output_dir, f"top_1000_verses_{timestamp}.json")
    top_1000_verses = scored_verses[:1000]
    
    with open(top_1000_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_verses': 1000,
                'timestamp': timestamp,
                'score_range': {
                    'min': top_1000_verses[-1]['positivity_score'],
                    'max': top_1000_verses[0]['positivity_score']
                },
                'description': 'Top 1000 positive Bibelverse für die NGÜ Spenden-App'
            },
            'verses': top_1000_verses
        }, f, ensure_ascii=False, indent=2)
    print(f"   ✓ Top 1000 Verse exportiert: {top_1000_file}")
    
    # Zusammenfassung ausgeben
    print("\n=== ZUSAMMENFASSUNG ===")
    print(f"\nTop 5 positive Verse:")
    for i, verse in enumerate(scored_verses[:5], 1):
        print(f"\n{i}. {verse['reference']} (Score: {verse['positivity_score']})")
        print(f"   \"{verse['text'][:80]}...\"")
    
    print(f"\n\nAlle Ergebnisse wurden gespeichert in:")
    print(f"- Datenbank: {DB_CONFIG['database']}")
    print(f"- Reports: {output_dir}")
    
    # Datenbank schließen
    db.close()
    print("\n✓ Fertig!")


if __name__ == "__main__":
    main()
