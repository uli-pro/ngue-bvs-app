# Wireframe-Ergänzungen für Session 3

## 1. Vers-Bestätigung: Link für weiteren Vers

**Wireframe 5** (`/verse/{verse_id}/bestaetigung`) ergänzen um:

### Position
Nach der "PREIS & WEITER" Sektion, vor dem Footer

### Textvorschlag für Link
```
┌─────────────────────────────────────────────────────────────────┐
│                   WEITERE SPONSORINGS                          │
│                                                                 │
│     💝 Verschenken Sie weitere Bibelvers-Sponsorings!         │
│                                                                 │
│              [← Weiteren Vers auswählen]                       │
└─────────────────────────────────────────────────────────────────┘
```

**Link-Text**: "← Weiteren Vers auswählen"
**Ziel**: Zurück zur Vers-Auswahl-Seite

## 2. Kapitel/Buch-Sponsoring Integration

### Empfohlene Platzierung: Homepage (Index-Seite)

**Position**: Nach dem PROJEKTINFO-Bereich, vor dem finalen CALL-TO-ACTION

### Textvorschlag
```
┌─────────────────────────────────────────────────────────────────┐
│                    GRÖSSERE SPONSORINGS                        │
│                                                                 │
│  📖 Möchten Sie ein ganzes Kapitel oder Buch sponsern?        │
│                                                                 │
│     Für größere Sponsorings (ab 1.000€) bieten wir           │
│     individuelle Lösungen und besondere Anerkennungen.        │
│                                                                 │
│              [Jetzt persönlich beraten lassen]                │
│            (Weiterleitung zu Kontaktformular/E-Mail)          │
└─────────────────────────────────────────────────────────────────┘
```

### Alternative Platzierung: Vers-Auswahl-Seite

**Position**: Am Ende der Seite, nach den Suchoptionen

### Textvorschlag (kompakter)
```
┌─────────────────────────────────────────────────────────────────┐
│                  GRÖSSERE PROJEKTE                             │
│                                                                 │
│   📚 Ganzes Kapitel oder Buch sponsern?                       │
│   Sprechen Sie uns für individuelle Lösungen an:              │
│                                                                 │
│   📧 grossspenden@peter-schoeffer-stiftung.de                 │
│   📞 +49 (0) 123 456789                                       │
└─────────────────────────────────────────────────────────────────┘
```

### FAQ-Ergänzung

Zusätzlich im FAQ-Bereich ergänzen:

**Frage**: "Kann ich auch ein ganzes Kapitel oder Buch sponsern?"

**Antwort**: "Ja! Für größere Sponsorings ab 1.000€ bieten wir individuelle Lösungen. Sie erhalten besondere Anerkennungen und können die Übersetzungsarbeit ganzer Bücher unterstützen. Kontaktieren Sie uns unter grossspenden@peter-schoeffer-stiftung.de für ein persönliches Gespräch."

## Umsetzungsnotizen

1. **Vers-Bestätigung**: Einfache Link-Ergänzung im bestehenden Wireframe
2. **Kapitel/Buch-Sponsoring**: Empfehlung Homepage-Integration für maximale Sichtbarkeit
3. **Kontakt-Infrastruktur**: Separate E-Mail-Adresse für Großspenden empfohlen
4. **FAQ-Integration**: Nahtlose Einbindung in bestehende FAQ-Struktur

## Technische Überlegungen

- Link "Weiteren Vers auswählen" sollte Session-State zurücksetzen
- Kapitel-Sponsoring benötigt separaten Workflow (außerhalb der App)
- Kontaktformular für Großspenden als eigene Seite oder externe E-Mail-Weiterleitung