# NGÜ Bibelvers-Spenden-App

> ⚠️ **HINWEIS**: Dies ist die ursprüngliche Projektbeschreibung vom Beginn der Entwicklung. Einige technische Entscheidungen haben sich inzwischen geändert:
> - **Datenbank**: Wir verwenden jetzt PostgreSQL mit pgvector statt SQLite
> - **Bibelübersetzungen**: Nur noch Schlachter 1951 (POC zeigte 72,7% Genauigkeit vs. 18,2% mit HFA)
> - **Suche**: Semantische Suche mit Cosine Similarity statt einfacher Volltextsuche
> - **Spendenbescheinigung**: Automatische Generierung wurde als neues Feature hinzugefügt
> 
> Für aktuelle Informationen siehe README.md und CLAUDE.md. Dieses Dokument wird als historische Referenz beibehalten.

## Detaillierte Projektbeschreibung

Das Projekt ist eine Web-Applikation zur Finanzierung der Bibelübersetzung NGÜ (Neue Genfer Übersetzung) für das Alte Testament. Das Neue Testament ist bereits veröffentlicht, nun soll das Alte Testament finanziert werden. Die Grundidee besteht darin, dass Spender einzelne Bibelverse für jeweils 100 Euro "sponsern" können. Als Gegenleistung erhalten sie ein Zertifikat mit der Information, welchen spezifischen Vers sie finanziert haben - ein ideeller Gegenwert, der es den Spendern ermöglicht, auch in 50 Jahren noch zu sagen: "Ich habe Jesaja 57 Vers 2 finanziert."

## Wichtige Projektentscheidung

Nach ausführlichem User-Feedback wurde entschieden, dass es **nur ein einheitliches Preismodell** geben wird. Alle Spender zahlen 100 Euro und können sich aus dem Pool der verfügbaren Verse einen aussuchen. Es gibt keine Premium-Stufe. Diese Entscheidung basiert auf dem eindeutigen Feedback, dass unterschiedliche Preisstufen als unfair empfunden werden.

## Technische Architektur im Detail

### Technologie-Stack

Der Entwickler plant einen modernen Python-basierten Stack mit Flask als Web-Framework, da er gerade den Harvard CS50-Kurs abgeschlossen hat und mit diesen Technologien vertraut ist. SQLAlchemy wird als ORM eingesetzt, um eine Abstraktionsschicht zwischen der Anwendung und der Datenbank zu schaffen. Dies ermöglicht einen späteren Wechsel der Datenbank ohne größere Code-Änderungen. Als initiale Datenbank wird SQLite3 verwendet, mit der expliziten Option, bei wachsenden Anforderungen auf PostgreSQL oder MySQL umzusteigen. Das Frontend wird zunächst mit klassischem HTML, CSS und JavaScript (JSON für dynamische Inhalte) umgesetzt.

### Detaillierte Datenbankstruktur

Die Datenbank besteht aus drei Haupttabellen:

**Bibelvers-Tabelle**: Diese Tabelle enthält jeden einzelnen Vers des Alten Testaments als eigenen Eintrag (etwa 11.000 noch zu übersetzende Verse). Jeder Eintrag enthält die Vers-Referenz (Buch, Kapitel, Vers), einen Text-Preview für die Suchfunktion, einen Status-Indikator ob der Vers bereits gesponsert wurde, und bei gesponserten Versen einen Verweis auf die entsprechende Kauf-ID aus der Kauf-Tabelle.

**User-Tabelle**: Speichert alle registrierten Benutzer mit ihren Kontaktdaten, insbesondere E-Mail-Adressen für Newsletter und Spendenbescheinigungen. Passwörter werden gehasht und gesalzen gespeichert. Die Tabelle ermöglicht es Nutzern, ihre Spendenhistorie einzusehen und mehrere Verse über Zeit zu sammeln.

**Kauf-/Spenden-Tabelle**: Dokumentiert jede einzelne Transaktion mit Transaktions-ID von Stripe, User-ID (oder Gast-Informationen), Spendenbetrag (standardmäßig 100€), Datum und Uhrzeit der Spende, zugewiesener Bibelvers und optional Informationen für Geschenkspenden.

### Zahlungsintegration mit Stripe

Stripe wurde als Payment Service Provider gewählt, da es umfassende Zahlungsmethoden unterstützt: Kredit- und Debitkarten (Visa, Mastercard), PayPal-Integration (in Deutschland verfügbar), SEPA-Lastschrift für europäische Kunden, digitale Geldbörsen (Apple Pay, Google Pay).

Die Peter-Schöffer-Stiftung kann als gemeinnützige Organisation reduzierte Gebühren bei Stripe beantragen. Die Integration erfolgt über Webhooks, die bei jeder Transaktion automatisch ausgelöst werden und die Transaktionsdaten (E-Mail, Name, Betrag, Transaktions-ID) an die Anwendung übermitteln. Diese Daten werden automatisch in die Datenbank eingetragen, wodurch der manuelle Aufwand minimiert wird.

## Detaillierte Funktionalitäten

### Zentrales Spendenmodell

Das System bietet ein einheitliches Spendenmodell:

**Vers-Sponsoring (100 Euro)**: Jeder Spender kann sich aus allen verfügbaren Versen einen aussuchen. Die Auswahl erfolgt über eine benutzerfreundliche Suchfunktion mit verschiedenen Zugängen:
- Direkte Eingabe der Bibelstelle
- Volltextsuche nach Stichworten
- Thematische Suche (z.B. "Hoffnung", "Trost", "Mut")
- Browsing durch Bücher und Kapitel

### Intelligente Alternative bei vergebenen Versen

Falls der Wunschvers bereits vergeben ist, bietet das System intelligente Alternativen:
- Kontextbasierte Vorschläge (vorheriger/nächster Vers)
- Verse aus demselben Kapitel
- Thematisch ähnliche Verse

### Visuelle Features

Eine animierte Darstellung zeigt, wie ein Vers beim Sponsoring "aktiviert" wird - inspiriert von kaufnekuh.de. Dies könnte eine Animation sein, bei der der Vers sich von Hebräisch zu Deutsch verwandelt oder grün aufleuchtet.

### Nutzerverwaltung und Gastspenden

Das System ist flexibel gestaltet und erlaubt sowohl registrierte Nutzer als auch Gastspenden. Gastspender müssen kein Konto anlegen, erhalten aber trotzdem ihr Zertifikat und die Spendenbescheinigung per E-Mail. Registrierte Nutzer haben zusätzliche Vorteile: Übersicht aller gesponserten Verse, erneuter Download von Zertifikaten, Verwaltung der persönlichen Daten und eine Liste zum Ausdrucken aller gesponserten Verse.

Bei nachträglicher Registrierung können frühere Gastspenden über die E-Mail-Adresse dem neuen Nutzerkonto zugeordnet werden, sodass eine vollständige Historie entsteht.

### Automatisierungsprozesse

Nach erfolgreicher Zahlung laufen mehrere automatisierte Prozesse ab: Stripe-Webhook triggert die Datenbankaktualisierung, der gesponserte Vers wird als "vergeben" markiert, ein personalisiertes Zertifikat wird generiert, E-Mail mit Zertifikat wird automatisch versandt, Spendenbescheinigung wird erstellt und verschickt, und optional wird eine Newsletter-Anmeldung angeboten.

## Integration in bestehende Infrastruktur

Die NGÜ hat bereits eine WordPress-basierte Webseite. Die Integration kann auf verschiedene Arten erfolgen:

**iFrame-Integration**: Die einfachste Lösung, bei der die Flask-Anwendung auf einem separaten Server läuft und über einen iFrame in WordPress eingebunden wird.

**Subdomain-Lösung**: Die Spendenplattform läuft unter einer eigenen Subdomain (z.B. spenden.ngu-bibel.de).

**WordPress-Plugin**: Aufwendigere Lösung, bei der die Funktionalität als WordPress-Plugin entwickelt wird.

Der Entwickler plant, zunächst die Funktionalität zu entwickeln und erst später die grafische Anpassung an das Corporate Design vorzunehmen.

## Technische Herausforderungen und Lösungsansätze

### Suchfunktionalität

Die größte technische Herausforderung ist die Implementierung einer leistungsfähigen Suchfunktion über 11.000 Verse. Dies erfordert:
- Volltext-Indizierung aller Verse
- Thematische Verschlagwortung
- Effizienter Such-Algorithmus
- Möglichkeit für unscharfe Suche

### Skalierbarkeit

SQLite3 hat Limitierungen bei gleichzeitigen Schreibzugriffen - nur ein Schreibvorgang ist gleichzeitig möglich. Bei erwarteten vielen gleichzeitigen Spenden könnte dies zu Engpässen führen. Die Verwendung von SQLAlchemy ermöglicht jedoch einen späteren nahtlosen Wechsel zu PostgreSQL oder MySQL.

### Datensicherheit und Compliance

DSGVO-konforme Speicherung und Verarbeitung von personenbezogenen Daten ist essentiell. Verschlüsselte Übertragung aller Daten (HTTPS) ist Pflicht. Keine Speicherung von Kreditkartendaten auf eigenen Servern - dies übernimmt komplett Stripe. Regelmäßige Backups der Datenbank müssen eingerichtet werden. Klare Datenschutzerklärung und Einwilligungen für Newsletter-Versand sind notwendig.

### Performance-Optimierung

Bei 11.000 Bibelvers-Einträgen müssen Datenbankabfragen optimiert werden. Indizes auf häufig abgefragte Felder (z.B. "ist_gesponsert") sollten gesetzt werden. Caching-Mechanismen für häufig abgerufene Daten könnten implementiert werden.

### Buchhaltung und rechtliche Aspekte

Die korrekte Dokumentation für Spendenbescheinigungen muss gewährleistet sein. Eine enge Abstimmung mit der Peter-Schöffer-Stiftung bezüglich Buchhaltungsprozessen ist notwendig. Die rechtliche Einordnung als Spende (trotz symbolischem Gegenwert) muss geklärt werden.

## Geplante Entwicklungsschritte

Der Entwickler plant einen iterativen Ansatz: Zunächst Entwicklung der Kernfunktionalität mit einfachem Design, Implementierung der Datenbankstruktur und grundlegenden CRUD-Operationen, Integration der Stripe-Zahlungsabwicklung und Automatisierung der Zertifikat-Generierung. Nach erfolgreichem Test folgen die Implementierung der Nutzerverwaltung, Entwicklung der Such- und Auswahlfunktionen, grafische Überarbeitung und Anpassung an NGÜ-Design sowie die finale Integration in die WordPress-Seite.

Das Projekt dient gleichzeitig als Abschlussprojekt für den Harvard CS50-Kurs, was eine gute Balance zwischen Lernerfahrung und praktischem Nutzen darstellt.
