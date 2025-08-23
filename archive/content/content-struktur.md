# Content-Struktur für NGÜ Bibelvers-Sponsoring App

## Verzeichnisstruktur

```
content/
├── seiten/
│   ├── index.md                    # Homepage-Inhalte
│   ├── verse-auswahl.md           # Vers-Auswahl-Seite
│   ├── ueber-ngue.md              # Über die NGÜ
│   ├── ueber-stiftung.md          # Über die Peter-Schöffer-Stiftung
│   ├── transparenz.md             # Transparenz/Mittelverwendung
│   ├── faq.md                     # FAQ-Bereich
│   ├── impressum.md               # Impressum
│   └── datenschutz.md             # Datenschutzerklärung
├── formulare/
│   ├── eingabefelder.md           # Labels, Platzhalter, Hilfen
│   ├── validierungen.md           # Validierungsmeldungen
│   └── bestaetigung.md            # Bestätigungstexte
├── email-templates/
│   ├── zertifikat-versand.md      # E-Mail-Template für Zertifikat
│   ├── spendenbescheinigung.md    # E-Mail-Template für Bescheinigung
│   ├── willkommen.md              # Willkommens-E-Mail (Registration)
│   └── newsletter.md              # Newsletter-Template
├── fehler-nachrichten/
│   ├── validierung.md             # Form-Validierungsfehler
│   ├── system.md                  # System-/Server-Fehler
│   ├── zahlung.md                 # Zahlungs-Fehler
│   └── allgemein.md               # Allgemeine Fehlermeldungen
├── ui-texte/
│   ├── buttons.md                 # Button-Beschriftungen
│   ├── navigation.md              # Menü und Navigation
│   ├── labels.md                  # Labels und Beschriftungen
│   └── tooltips.md                # Hilfe-Tooltips
└── meta/
    ├── seo-titles.md              # SEO-Titel für alle Seiten
    ├── meta-descriptions.md       # Meta-Descriptions
    └── alt-texte.md               # Alt-Texte für Bilder
```

## Kategorisierung nach Priorität

### Kritisch (P1) - Session 3
- **Hauptseiten**: Homepage, Vers-Auswahl, Über NGÜ, Über Stiftung
- **FAQ**: Kompletter FAQ-Bereich
- **E-Mail-Templates**: Zertifikat-Versand, Spendenbescheinigung

### Important (P2) - Session 4
- **Formulare**: Alle Eingabefelder und Validierungen
- **Fehler-Nachrichten**: Zahlungsfehler, Validierungsfehler
- **UI-Texte**: Buttons, Navigation

### Optional (P3) - Session 5
- **Meta**: SEO-Optimierung
- **Impressum/Datenschutz**: Anpassung der Vorlagen

## Textrichtlinien

### Tonalität
- **Vertrauensvoll**: Seriös und transparent
- **Persönlich**: Direkte Ansprache mit "Sie"
- **Motivierend**: Positive Wortwahl ohne Druck
- **Klar**: Einfache, verständliche Sprache

### Kernbotschaften
- **Mission**: Moderne, verständliche Bibelübersetzung ermöglichen
- **Transparenz**: Vollständige Offenlegung der Mittelverwendung
- **Einfachheit**: 100€ sponsern einen kompletten Vers
- **Impact**: Direkte Unterstützung eines wichtigen Projekts
- **Persönlich**: Individuelles Zertifikat als Dankeschön

### Sprachstil
- Aktive Formulierungen statt Passiv
- Konkrete Zahlen und Fakten
- Emotionale Verbindung ohne Übertreibung
- Kurze, prägnante Sätze
- Positive Handlungsaufforderungen

## Nächste Schritte

1. **Homepage-Texte** (index.md) - Hero-Bereich, Projektinfo, CTA
2. **Vers-Auswahl-Texte** (verse-auswahl.md) - Einleitungen, Erklärungen
3. **FAQ-Bereich** (faq.md) - Alle wichtigen Fragen und Antworten
4. **E-Mail-Templates** - Zertifikat und Spendenbescheinigung
5. **Über-Seiten** - NGÜ und Stiftungs-Beschreibungen

Jede Datei wird mit YAML-Frontmatter für Metadaten und strukturierten Markdown-Content erstellt.