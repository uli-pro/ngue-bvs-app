# Prompts für die ngue-bvs-app Entwicklung

Dieser Ordner enthält alle Prompts, die für die Entwicklung der ngue-bvs-app verwendet werden.

## Struktur

### `/claude-code/`
Prompts für Claude Code - hauptsächlich für automatisierte Entwicklungsaufgaben:
- Initial Setup und Projektstruktur
- Datenbank-Schema und Migrationen
- Automatisierte Tests
- Build- und Deployment-Prozesse

### `/development/`
Prompts für die allgemeine Entwicklung mit Claude:
- Feature-Entwicklung
- UI/UX-Komponenten
- Debugging und Problemlösung
- Architektur-Entscheidungen

## Namenskonventionen

- Verwende aussagekräftige, beschreibende Namen
- Nutze Bindestriche statt Unterstriche: `feature-semantic-search.md`
- Füge bei Bedarf Versionsnummern hinzu: `database-schema-v2.md`

## Best Practices

1. **Strukturiere deine Prompts klar:**
   - Kontext/Hintergrund
   - Spezifische Aufgabe
   - Erwartete Ergebnisse
   - Relevante Constraints

2. **Verweise auf relevante Dateien:**
   - Nutze relative Pfade vom Projekt-Root
   - Erwähne spezifische Funktionen oder Klassen

3. **Dokumentiere Erfolge:**
   - Füge Kommentare hinzu, was gut funktioniert hat
   - Notiere, welche Anpassungen nötig waren

## Beispiel-Prompt-Struktur

```markdown
# [Titel des Prompts]

## Kontext
[Beschreibe den aktuellen Stand und warum diese Aufgabe nötig ist]

## Aufgabe
[Spezifische Anweisungen, was entwickelt/geändert werden soll]

## Relevante Dateien
- `/path/to/file1.py`
- `/path/to/file2.js`

## Erwartetes Ergebnis
[Beschreibe, wie das Endergebnis aussehen soll]

## Zusätzliche Hinweise
[Constraints, Best Practices, oder spezielle Anforderungen]
```
