# Entwicklungstagebuch

Ein Entwicklungstagebuch dokumentiert Ihren Lernprozess und Ihre Entscheidungen. Hier ein praktisches Format:

### Beispiel-Eintrag:

~~~markdown
# Entwicklungstagebuch - Session 8: Datenbank-Setup
**Datum:** 15.03.2024  
**Dauer:** 1,5 Stunden  
**Geplant:** SQLAlchemy-Models erstellen

## Was ich heute gemacht habe:
- Flask-SQLAlchemy installiert und konfiguriert
- Drei Models erstellt: User, BibelVerse, Purchase
- Erste Migration durchgeführt
- Testdaten eingefügt

## Code-Beispiel des Tages:
```python
class BibelVerse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book = db.Column(db.String(50), nullable=False)
    chapter = db.Column(db.Integer, nullable=False)
    verse = db.Column(db.Integer, nullable=False)
    is_sponsored = db.Column(db.Boolean, default=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
~~~

## Probleme und Lösungen:

**Problem:** Migration schlug fehl mit "table already exists"
 **Lösung:** Datenbank gelöscht und neu initialisiert. Gelernt: Bei SQLite kann man nicht einfach Spalten ändern.

## Was ich gelernt habe:

- SQLAlchemy relationships sind mächtiger als gedacht
- `db.relationship()` mit `backref` spart viel Code
- Flask-Migrate macht Datenbankänderungen viel einfacher

## Offene Fragen:

- Sollte ich einen Index auf `is_sponsored` setzen?
- Wie gehe ich mit der Vers-Reihenfolge um?

## Nächste Schritte:

- Import-Script für alle Bibelverse schreiben
- Performance mit 7000 Einträgen testen

## Hilfreiche Ressourcen:

- [Flask-SQLAlchemy Dokumentation](https://flask-sqlalchemy.palletsprojects.com/)
- Stack Overflow Thread zu Migration-Problemen

## Stimmung/Notizen:

Heute lief es richtig gut! Das Datenbank-Setup war einfacher als befürchtet.

```
### Was ins Tagebuch gehört:

**Technische Aspekte:**
- Was wurde implementiert?
- Welche Probleme traten auf?
- Wie wurden sie gelöst?
- Code-Snippets wichtiger Lösungen

**Lernprozess:**
- Was war neu für Sie?
- Was haben Sie verstanden/gelernt?
- Was ist noch unklar?

**Entscheidungen:**
- Warum haben Sie sich für Lösung A statt B entschieden?
- Welche Alternativen haben Sie verworfen?

**Ressourcen:**
- Hilfreiche Links
- Tutorials die geholfen haben
- Stack Overflow Threads

**Persönliches:**
- Wie lief die Session?
- Was war frustrierend/motivierend?

## Ja, Claude kann helfen!

Sowohl ich als auch Claude Code können Ihnen definitiv beim Verfassen helfen. So könnte das ablaufen:

**Nach jeder Session:**
```

Sie: "Ich habe heute 1,5h an Session 8 gearbeitet. Ich habe die SQLAlchemy Models für User, BibelVerse und Purchase erstellt. Dabei hatte ich Probleme mit Migrationen, weil die Tabelle schon existierte. Ich musste die DB löschen und neu machen. Kannst du mir helfen, einen Tagebucheintrag zu verfassen?"

Claude: [Erstellt einen strukturierten Eintrag basierend auf Ihren Notizen]

```
**Tipps für die Zusammenarbeit:**
- Machen Sie während der Session kurze Notizen
- Screenshots von Fehlermeldungen
- Kopieren Sie interessante Code-Snippets
- Notieren Sie Ihre Gedanken/Frustrationen

**Vorteile des Tagebuchs für CS50:**
- Zeigt Ihren Lernprozess
- Beweist, dass Sie die Arbeit selbst gemacht haben
- Dokumentiert Ihre Problemlösungsfähigkeiten
- Macht das Projekt nachvollziehbar

Das Tagebuch wird zu einer wertvollen Ressource - sowohl für Ihre CS50-Einreichung als auch für Sie selbst, wenn Sie später etwas nachschlagen müssen!
```