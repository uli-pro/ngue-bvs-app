# Plan: /vers-auswaehlen dynamisch implementieren

**Status:** In Planung  
**Priorität:** Hoch  
**Datum:** 2025-08-16  
**Abhängigkeiten:** Database Models (Verse), Session Management

## Überblick

Die Route `/vers-auswaehlen` ist aktuell komplett statisch mit hardcoded Versen im Template. Wir implementieren eine intelligente, session-basierte Vers-Auswahl mit optimaler User Experience.

## Aktuelle Situation

### Route (app.py):
```python
@app.route("/vers-auswaehlen")
def vers_auswaehlen():
    """Verse selection page"""
    return render_template("vers-auswaehlen.html")
```
- Keine Datenbankabfrage
- Keine Daten an Template

### Template (vers-auswaehlen.html):
- 3 hardcodede Verse: Jesaja 43,1 / Jeremia 29,11 / Zefanja 3,17
- Statische Links: `/vers/jesaja-43-1/spendenart`
- Kein "Andere Verse anzeigen" Feature

## Anforderungen

### User Experience Szenarien:
1. **User findet keine passenden Verse** → Button "Andere Verse anzeigen"
2. **User legt Vers in Spendenkorb** → Automatische Ersetzung gesponserte Verse
3. **User navigiert zu Suche und zurück** → Gleiche 3 Verse wieder anzeigen
4. **User findet bei Referenz-Suche nichts** → Gleiche 3 Verse wieder anzeigen

### Technische Anforderungen:
- Session-Persistenz für Verse-IDs
- Adaptive Score-Auswahl basierend auf Verfügbarkeit
- Keyword-Bonus für positive Begriffe
- URL-Slug-Generierung für Verse

## Technische Spezifikation

### 1. Erweiterte Verse-Model-Methoden (models.py)

#### Adaptive Vers-Auswahl:
```python
@classmethod
def get_adaptive_featured_verses(cls, limit=3, exclude_ids=None):
    """Adaptive Auswahl basierend auf verfügbaren Versen"""
    exclude_ids = exclude_ids or []
    
    # 1. Finde höchsten verfügbaren Score mit genug Versen
    min_pool_size = 20  # Mindestens 20 Verse für gute Auswahl
    
    for min_score in [90, 80, 70, 60, 50, 40, 30, 20, 10, 0]:
        pool = cls.query.filter(
            cls.is_sponsored == False,
            cls.positivity_score >= min_score,
            ~cls.id.in_(exclude_ids)  # Exclude bereits verwendete
        ).limit(min_pool_size + 10).all()
        
        if len(pool) >= min_pool_size:
            break
    
    # 2. Keyword-Bonus für bessere Auswahl
    positive_keywords = [
        # Substantive
        'Liebe', 'Hoffnung', 'Frieden', 'Segen', 'Freude', 
        'Gnade', 'Trost', 'Schutz', 'Hilfe', 'Güte', 'Licht', 'Leben',
        
        # Positive Verben
        'segnen', 'lieben', 'helfen', 'trösten', 'schützen', 'führen',
        'stärken', 'bewahren', 'heilen', 'erretten', 'erlösen', 
        'freuen', 'segne', 'liebt', 'hilft', 'tröstet', 'schützt',
        'stärkt', 'bewahrt', 'heilt', 'errettet', 'erlöst'
    ]
    
    scored_verses = []
    for verse in pool:
        keyword_bonus = sum(2 for kw in positive_keywords if kw.lower() in verse.text.lower())
        final_score = verse.positivity_score + keyword_bonus
        scored_verses.append((verse, final_score))
    
    # 3. Nach Score sortieren und Top auswählen
    scored_verses.sort(key=lambda x: x[1], reverse=True)
    return [verse for verse, score in scored_verses[:limit]]
```

#### URL-Generation:
```python
@property
def url_slug(self):
    """Generate URL-friendly slug: dan-6-21"""
    return f"{self.book.lower()}-{self.chapter}-{self.verse}"

@property  
def reference(self):
    """Human readable reference: DAN 6,21"""
    return f"{self.book} {self.chapter},{self.verse}"
```

### 2. Erweiterte Route (app.py)

```python
@app.route("/vers-auswaehlen")
def vers_auswaehlen():
    """Verse selection page with session-based persistence"""
    # Check ob "andere Verse" explizit angefordert
    refresh_verses = request.args.get('refresh') == 'true'
    
    if 'featured_verse_ids' not in session or refresh_verses:
        # Neue Verse auswählen
        featured_verses = Verse.get_adaptive_featured_verses(3)
        session['featured_verse_ids'] = [v.id for v in featured_verses]
    else:
        # Bestehende Session-Verse laden
        verse_ids = session['featured_verse_ids']
        featured_verses = Verse.query.filter(Verse.id.in_(verse_ids)).all()
        
        # Check ob Verse zwischenzeitlich gesponsert wurden
        available_verses = [v for v in featured_verses if not v.is_sponsored]
        
        if len(available_verses) < len(featured_verses):
            # Ersetze gesponserte Verse
            missing_count = len(featured_verses) - len(available_verses)
            exclude_ids = [v.id for v in available_verses]
            
            new_verses = Verse.get_adaptive_featured_verses(
                missing_count, exclude_ids=exclude_ids
            )
            
            featured_verses = available_verses + new_verses
            session['featured_verse_ids'] = [v.id for v in featured_verses]
    
    return render_template("vers-auswaehlen.html", 
                         featured_verses=featured_verses)
```

### 3. Dynamisches Template (vers-auswaehlen.html)

#### Vers-Loop:
```html
<section class="section-padding">
    <div class="container">
        <div class="row g-4">
            {% for verse in featured_verses %}
            <div class="col-lg-4">
                <div class="card h-100 verse-card">
                    <div class="card-body text-center p-4">
                        <h4 class="text-primary mb-3">{{ verse.reference }}</h4>
                        <blockquote class="blockquote">
                            <p class="mb-4">"{{ verse.text }}"</p>
                            <footer class="blockquote-footer">
                                <cite title="Schlachter 1951">Schlachter 1951</cite>
                            </footer>
                        </blockquote>
                        <a href="/vers/{{ verse.url_slug }}/spendenart" 
                           class="btn btn-primary">DIESEN VERS WÄHLEN</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- "Andere Verse anzeigen" Button -->
        <div class="text-center mt-4">
            <a href="/vers-auswaehlen?refresh=true" 
               class="btn btn-outline-secondary">
                <i class="fas fa-sync-alt me-2"></i>
                Andere Verse anzeigen
            </a>
        </div>
    </div>
</section>
```

## Adaptive Auswahl-Strategie

### Score-Distribution Analysis:
```
Score >= 90: 615 Verse (5.8%)    ← Start hier
Score >= 80: 1703 Verse (16.0%)  ← Fallback 1
Score >= 70: 2354 Verse (22.1%)  ← Fallback 2
Score >= 60: 3014 Verse (28.3%)  ← Fallback 3
...
```

### Auswahl-Algorithmus:
1. **Pool-Size Check**: Mindestens 20 Verse für gute Variation
2. **Score-Fallback**: Beginne bei 90, fallback bis genug Verse verfügbar
3. **Keyword-Bonus**: +2 Punkte pro positivem Keyword
4. **Final-Ranking**: `positivity_score + keyword_bonus`

## User Experience Features

### ✅ Session-Persistenz:
- Gleiche 3 Verse über Navigation hinweg
- Nur Änderung bei explizitem "refresh=true"
- Automatische Ersetzung gesponserte Verse

### ✅ "Andere Verse anzeigen":
- User-kontrollierte Aktualisierung
- Neue 3 Verse aus dem Pool
- Exclude bereits gezeigte Verse

### ✅ Adaptive Qualität:
- Immer bestmögliche verfügbare Verse
- Keyword-Bonus für positive Begriffe
- Nachhaltige Strategie (alle Verse sponsorbar)

## Implementierungs-Schritte

### Phase 1: Models erweitern
1. `get_adaptive_featured_verses()` Methode hinzufügen
2. `url_slug` und `reference` Properties hinzufügen
3. Positive Keywords Liste definieren

### Phase 2: Route implementieren
1. Session-Management für verse_ids
2. Refresh-Parameter handling
3. Automatische Ersetzung gesponserte Verse

### Phase 3: Template anpassen
1. Hardcodede Verse durch Loop ersetzen
2. Dynamische Links mit url_slug
3. "Andere Verse anzeigen" Button hinzufügen

### Phase 4: Testing
1. Session-Persistenz testen
2. Adaptive Score-Auswahl testen
3. Keyword-Bonus Algorithmus validieren

## Testing

### Unit Tests:
```python
def test_adaptive_featured_verses():
    """Test adaptive verse selection with different score thresholds"""

def test_verse_url_slug():
    """Test URL slug generation for various verse formats"""

def test_keyword_bonus_calculation():
    """Test positive keyword bonus scoring"""
```

### Integration Tests:
```python
def test_session_persistence():
    """Test that same verses are shown across navigation"""

def test_refresh_verses():
    """Test that refresh=true shows different verses"""

def test_sponsored_verse_replacement():
    """Test automatic replacement of sponsored verses"""
```

## Nächste Schritte

### Sofort:
1. Models.py erweitern mit neuen Methoden
2. Route `/vers-auswaehlen` implementieren
3. Template dynamisch machen

### Follow-up:
1. A/B Testing für Keyword-Gewichtung
2. Analytics für Vers-Auswahl-Patterns
3. Erweiterte Personalisierung basierend auf User-Präferenzen

---

**Priorität für MVP:** Hoch  
**Geschätzte Implementierungszeit:** 1-2 Tage

## Notizen

- **Nachhaltigkeit**: Adaptive Score-Auswahl stellt sicher, dass alle Verse sponsorbar sind
- **UX-Fokus**: Session-Persistenz vermeidet Verwirrung bei Navigation
- **Intelligenz**: Keyword-Bonus bevorzugt emotional ansprechende Verse
- **Kontrolle**: User kann explizit andere Verse anfordern