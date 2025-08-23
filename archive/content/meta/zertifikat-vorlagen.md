# Zertifikat-Vorlagen: Text-Varianten

## Standard-Zertifikat (Einzelperson)

### Haupttext:
**"{VORNAME} {NACHNAME} hat durch eine Spende von 100€ die Übersetzung von {VERS_REFERENZ} ermöglicht."**

### Vollständiges Zertifikat:
```
════════════════════════════════════════════════════
           VERS-SPONSORING ZERTIFIKAT
    Neue Genfer Übersetzung des Alten Testaments
════════════════════════════════════════════════════

{VORNAME} {NACHNAME}

hat durch eine Spende von 100€ die Übersetzung von

{VERS_REFERENZ}

ermöglicht.

────────────────────────────────────────────────────
{VERS_TEXT_SCHLACHTER}
────────────────────────────────────────────────────

Ihre Spende hilft dabei, das Wort Gottes für kommende 
Generationen zugänglich zu machen.

Vielen Dank für Ihre Unterstützung!

Peter-Schöffer-Stiftung
{DATUM}
════════════════════════════════════════════════════
```

## Gruppen-Zertifikat 

### Haupttext-Variation:
**"{ARTIKEL} {GRUPPENNAME} hat durch eine Spende von 100€ die Übersetzung von {VERS_REFERENZ} ermöglicht."**

### Beispiele:
- "Die Familie Schmidt hat durch eine Spende..."
- "Der Bibelkreis Musterhausen hat durch eine Spende..."
- "Das Volleyball-Team Musterdorf hat durch eine Spende..."

### Vollständiges Gruppen-Zertifikat:
```
════════════════════════════════════════════════════
           VERS-SPONSORING ZERTIFIKAT
    Neue Genfer Übersetzung des Alten Testaments
════════════════════════════════════════════════════

{ARTIKEL} {GRUPPENNAME}

hat durch eine Spende von 100€ die Übersetzung von

{VERS_REFERENZ}

ermöglicht.

────────────────────────────────────────────────────
{VERS_TEXT_SCHLACHTER}
────────────────────────────────────────────────────

Diese Gruppenspende hilft dabei, das Wort Gottes für 
kommende Generationen zugänglich zu machen.

Vielen Dank für Ihre Unterstützung!

Peter-Schöffer-Stiftung
{DATUM}
════════════════════════════════════════════════════
```

## Geschenk-Zertifikat (bleibt unverändert)

### Haupttext:
**"{EMPFAENGER_VORNAME} {EMPFAENGER_NACHNAME} hat durch eine Spende von {SPENDER_VORNAME} {SPENDER_NACHNAME} die Übersetzung von {VERS_REFERENZ} ermöglicht."**

## Template-Logik für Code

### Python Template-Logik:
```python
def get_certificate_text(donation_type, **kwargs):
    if donation_type == 'self':
        return f"{kwargs['first_name']} {kwargs['last_name']} hat durch eine Spende..."
    
    elif donation_type == 'group':
        article = kwargs['group_article'].capitalize()  # Der/Die/Das
        group_name = kwargs['group_name']
        return f"{article} {group_name} hat durch eine Spende..."
    
    elif donation_type == 'gift':
        return f"{kwargs['recipient_first_name']} {kwargs['recipient_last_name']} hat durch eine Spende von {kwargs['donor_first_name']} {kwargs['donor_last_name']}..."
```

### JavaScript Template-Vorschau:
```javascript
function previewCertificateText() {
    const donationType = document.querySelector('input[name="donation_type"]:checked').value;
    
    if (donationType === 'group') {
        const article = document.getElementById('group_article').value;
        const groupName = document.getElementById('group_name').value;
        return `${article} ${groupName} hat durch eine Spende...`;
    }
    // weitere Logik...
}
```

## PDF-Layout Anpassungen

### Gruppen-Zertifikat:
- **Schriftgröße Gruppenname:** Dynamisch je nach Länge
  - Bis 20 Zeichen: 24pt
  - 21-40 Zeichen: 20pt  
  - 41-60 Zeichen: 18pt
  - 61-80 Zeichen: 16pt

- **Layout:** 
  - Zentrierte Ausrichtung
  - Artikel und Gruppenname auf einer Zeile
  - Bei sehr langen Namen: Artikel auf eigener Zeile

### Text-Anpassungen:
- "Diese Gruppenspende hilft dabei..." statt "Ihre Spende hilft dabei..."
- Datum bleibt unverändert
- Logo und Stiftungsname bleiben gleich

## Dateiname-Konventionen

### Einzelperson:
`Zertifikat_{NACHNAME}_{VORNAME}_{VERS_REFERENZ_CLEAN}.pdf`
Beispiel: `Zertifikat_Schmidt_Hans_1Mose1-1.pdf`

### Gruppe:
`Gruppenzertifikat_{GRUPPENNAME_CLEAN}_{VERS_REFERENZ_CLEAN}.pdf`
Beispiel: `Gruppenzertifikat_Familie-Schmidt_1Mose1-1.pdf`

### Geschenk:
`Geschenkzertifikat_{EMPFAENGER_NACHNAME}_{EMPFAENGER_VORNAME}_{VERS_REFERENZ_CLEAN}.pdf`

## Farb-Schema (bleibt gleich für alle)

- **Hintergrund:** Cremeweiß (#FFFEF7)
- **Rahmen:** Dunkelblau (#1B365D)  
- **Überschrift:** Dunkelblau (#1B365D)
- **Haupttext:** Schwarz (#000000)
- **Vers-Text:** Dunkelgrau (#333333)
- **Akzente:** Gold (#D4AF37)

## Qualitätskontrolle

### Artikel-Validierung:
- System prüft grammatikalische Korrektheit
- Warnung bei ungewöhnlichen Kombinationen
- Beispiele für häufige Artikel-Gruppenname-Kombinationen

### Längen-Handling:
- Automatische Schriftgrößenanpassung
- Zeilenumbruch bei sehr langen Gruppennamen
- Maximale Zeichenanzahl: 80 (entspricht ca. 2 Zeilen bei kleinster Schrift)