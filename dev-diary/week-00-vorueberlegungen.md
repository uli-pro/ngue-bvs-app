# Woche 0: Vorüberlegungen und User-Feedback

**Zeitraum:** Vor Projektstart  
**Fokus:** Konzeptvalidierung, User-Feedback, Grundsatzentscheidungen

---

## User-Feedback Session: Preismodell und Vers-Auswahl

**Datum:** 1.8.2025  
**Dauer:** Informelles Gespräch  
**Art:** Potentielle Nutzerin befragt

### Wichtige Erkenntnisse

#### 1. Ablehnung des zweistufigen Preismodells

Die befragte Nutzerin empfindet unterschiedliche Preisebenen (100€ Standard vs. 150€ Premium) als unangemessen. Aus ihrer Perspektive wirkt es unfair, dass man mehr spenden muss, um einen Vers selbst aussuchen zu können. Sie ist der Meinung, dass die Möglichkeit der Vers-Auswahl nicht vom Spendenbetrag abhängen sollte, da dies potentielle Spender abschrecken könnte.

Diese Rückmeldung hat wichtige Implikationen für das Projekt. Es wird notwendig sein, das Preismodell zu überdenken. Als mögliche Alternative könnte ein Einheitspreis mit Auswahl-Option für alle Spender in Betracht gezogen werden. Eine andere Möglichkeit wäre, eine andere Form der Differenzierung zu finden, beispielsweise durch Zusatzleistungen anstatt die Kernfunktion einzuschränken.

#### 2. Unklarheit bei der Vers-Zuweisung im Standard-Modell

Eine kritische Frage, die im Gespräch aufkam, betrifft die genaue Funktionsweise der automatischen Vers-Zuweisung. Wir haben verschiedene Optionen diskutiert. Option A wäre eine vollautomatische Lösung, bei der das System einfach den nächsten verfügbaren Vers zuweist. Option B könnte eine Semi-Auswahl sein, bei der der User drei zufällige Verse zur Auswahl bekommt. Option C würde eine thematische Zuweisung ermöglichen, bei der User eine Präferenz angeben können, beispielsweise "Psalmen" oder "Prophetische Bücher".

Die befragte Nutzerin äußerte den Wunsch nach einer gewissen Mitsprache, auch wenn es keine vollständige Freiheit bei der Auswahl gäbe. Dies deutet darauf hin, dass eine reine Zufallszuweisung möglicherweise nicht optimal wäre.

#### 3. Herausforderung: Nicht verfügbare Wunsch-Verse

Ein weiteres wichtiges Thema war die Frage, was passiert, wenn der gewünschte Vers bereits vergeben ist. Wir haben verschiedene Lösungsansätze diskutiert. Man könnte ähnliche Verse vorschlagen, was allerdings einen entsprechenden Algorithmus erfordern würde. Alternativ könnte man Verse aus demselben Kapitel anbieten oder versuchen, thematisch verwandte Verse zu finden.

Diese Überlegungen führten zu technischen Fragen. Sollte eine Schlüsselwort-Suche implementiert werden? Wäre eine semantische Suche sinnvoll, auch wenn sie technisch anspruchsvoll ist? Ist eine Volltext-Indizierung aller Verse notwendig?

### Neue Ideen aus dem Gespräch

Während des Gesprächs entstand die Idee einer Schlüsselwort-Suche als Feature. User könnten nach Begriffen wie "Hoffnung", "Liebe" oder "Stärke" suchen, was die Vers-Auswahl persönlicher machen würde. Die technische Herausforderung dabei ist, dass alle etwa 11.000 noch zu übersetzenden Verse des Alten Testaments durchsuchbar gemacht werden müssten.

### Offene Fragen

Das Gespräch hat mehrere grundlegende Fragen aufgeworfen. Erstens muss das Preismodell möglicherweise komplett überdacht werden. Sollten wir einen Einheitspreis für alle einführen? Welche anderen Differenzierungsmerkmale könnten sinnvoll sein? Wäre eine freiwillige Mehrspende eine bessere Lösung als feste Stufen?

Zweitens ist der Vers-Auswahl-Mechanismus noch zu klären. Wie viel Kontrolle sollten wir dem User geben? Wie finden wir die richtige Balance zwischen Einfachheit und Flexibilität?

Drittens stellen sich technische Fragen. Sollte eine Volltext-Suche von Anfang an eingeplant werden? Wie aufwendig wäre die Implementierung semantischer Ähnlichkeit?

### Action Items für Konzeptphase

- [ ] Weitere User befragen zum Preismodell
- [ ] Recherche: Wie machen es ähnliche Spendenprojekte?
- [ ] Technische Machbarkeit der Suchfunktion evaluieren
- [ ] Alternative Preismodelle skizzieren
- [ ] Vers-Datenbank auf Durchsuchbarkeit prüfen

### Reflexion

Dieses frühe Feedback ist Gold wert. Es zeigt, dass meine initialen Annahmen über das Preismodell möglicherweise die User-Erwartungen nicht treffen. Die Kern-Erkenntnis ist, dass Fairness wichtiger ist als Umsatzoptimierung. User wollen nicht das Gefühl haben, für Grundfunktionen "bestraft" zu werden.

Die Herausforderung wird sein, ein Modell zu finden, das fair und transparent ist, trotzdem Anreize für höhere Spenden schafft, technisch umsetzbar bleibt und die Einfachheit bewahrt. Die nächsten Schritte bestehen darin, mehr Feedback einzuholen und verschiedene Modelle durchzudenken, bevor ich mit der technischen Implementierung beginne.

---

## User-Feedback Session 2: Bestätigung der Erkenntnisse
**Datum:** [Heutiges Datum einfügen]  
**Dauer:** Telefonat  
**Art:** Zweite potentielle Nutzerin befragt

### Bestätigung des ersten Feedbacks

Das Gespräch mit der zweiten potentiellen Nutzerin hat die Erkenntnisse vom ersten Feedback eindrücklich bestätigt. Besonders bemerkenswert ist, dass sie ihre Wünsche völlig unabhängig äußerte, bevor ich ihr vom ersten Gespräch erzählte.

Auch sie möchte ihren Bibelvers selbst aussuchen können. Die Vorstellung, einen zufällig zugewiesenen Vers zu erhalten, empfindet sie als unbefriedigend. Sie möchte eine persönliche Verbindung zu dem Vers haben, den sie sponsert.

Ebenso wünscht sie sich, wenn der gewünschte Vers bereits vergeben ist, vergleichbare Alternativen vorgeschlagen zu bekommen. Dies bestätigt, dass ein intelligentes Vorschlagssystem ein wichtiges Feature sein wird.

### Neue Erkenntnis: Thematische Suche

Ein neuer Aspekt, den die zweite Nutzerin einbrachte, ist der Wunsch nach einer thematischen Suche. Sie merkte an, dass viele Menschen zwar wissen, dass es in der Bibel Verse zu bestimmten Themen gibt, aber nicht die genauen Bibelstellen im Kopf haben. Eine Möglichkeit, Verse nach Themen wie "Trost", "Mut", "Vergebung" oder "Hoffnung" zu suchen, wäre für sie sehr wertvoll.

Diese Anregung geht über eine reine Volltextsuche hinaus und würde eine thematische Kategorisierung oder Verschlagwortung der Verse erfordern.

### Implikationen für das Projekt

Die Tatsache, dass zwei unabhängig befragte Personen nahezu identische Wünsche äußerten, verleiht diesen Anforderungen besonderes Gewicht. Es zeichnet sich ab, dass die Vers-Auswahl ein zentrales Feature sein muss, nicht nur eine Premium-Option. Die technische Komplexität des Projekts erhöht sich dadurch erheblich, da nun eine durchsuchbare, thematisch erschlossene Datenbank aller Verse benötigt wird.

Die ursprüngliche Idee eines einfachen Systems mit automatischer Vers-Zuweisung scheint nicht den User-Erwartungen zu entsprechen. Stattdessen erwarten die Nutzer ein durchdachtes Such- und Auswahlsystem, das ihnen hilft, einen persönlich bedeutsamen Vers zu finden.

---

## User-Feedback Session 3: Weitere Bestätigung und kreative Ideen
**Datum:** [Heutiges Datum einfügen]  
**Dauer:** Telefonat  
**Art:** Dritter potentieller Nutzer befragt

### Erneute Bestätigung der Kernwünsche

Das dritte Telefonat bestätigt eindeutig den sich abzeichnenden Trend. Auch dieser potentielle Nutzer äußerte unabhängig die gleichen Grundbedürfnisse wie die beiden vorherigen Gesprächspartner. Die Konsistenz dieser Rückmeldungen über drei verschiedene Personen hinweg macht deutlich, dass wir es hier mit fundamentalen User-Erwartungen zu tun haben, nicht mit Einzelmeinungen.

### Neue Idee: Kontext-basierte Alternative

Der dritte Nutzer brachte einen interessanten neuen Vorschlag für den Fall nicht verfügbarer Wunsch-Verse ein. Seiner Ansicht nach wäre es sinnvoll, den direkt vorhergehenden oder nachfolgenden Vers aus dem biblischen Zusammenhang anzubieten. Seine Begründung ist theologisch fundiert: Der Kontext eines Verses ist oft entscheidend für dessen Verständnis und Bedeutung. Ein Vers direkt davor oder danach trägt häufig die gleiche Botschaft oder ergänzt diese sinnvoll.

Diese Idee bietet eine elegante und einfach zu implementierende Alternative zur komplexeren semantischen Suche. Es wäre technisch deutlich weniger aufwendig, einfach die Verse mit der ID-1 oder ID+1 vorzuschlagen, als einen Algorithmus für thematische Ähnlichkeit zu entwickeln.

### Visuelle Animation als Motivationselement

Besonders begeistert war der Nutzer von der Idee einer visuellen Darstellung des Fortschritts. Er verwies auf die Webseite kaufnekuh.de, bei der man sehen kann, welche Teile des Tieres bereits verkauft sind. Übertragen auf unser Projekt schlug er vor, dass man visuell erleben könnte, wie ein Vers "grün wird" oder sich von Hebräisch zu Deutsch verwandelt, wenn er gesponsert wird.

Diese Animation könnte mehrere Zwecke erfüllen. Sie würde den Fortschritt des Gesamtprojekts visualisieren und könnte potentielle Spender motivieren, da sie direkt sehen, wie ihre Spende zur Vervollständigung der Übersetzung beiträgt. Außerdem würde es dem digitalen Erlebnis eine spielerische, belohnende Komponente hinzufügen.

### Technische Überlegungen zur Animation

Die Umsetzung einer solchen Animation wirft neue technische Fragen auf. Sollte dies eine Echtzeit-Animation sein, die andere Nutzer live miterleben können? Oder eine persönliche Animation nur für den Spender? Wie würde sich das auf die Performance auswirken, besonders bei mobilen Geräten? Eine mögliche Implementierung könnte eine Kombination aus CSS-Animationen und JavaScript sein, eventuell mit einer kleinen Verzögerung nach der Zahlungsbestätigung, um den "Wow-Effekt" zu maximieren.

### Reflexion

Nach drei Gesprächen zeichnet sich ein sehr klares Bild ab. Die ursprüngliche Idee eines simplen Spendensystems mit automatischer Vers-Zuweisung entspricht nicht den User-Erwartungen. Stattdessen wünschen sich alle befragten Personen ein interaktives, personalisiertes Erlebnis mit visuellen Elementen und intelligenten Auswahlmöglichkeiten. Das Projekt entwickelt sich von einer reinen Spenden-App zu einer Experience-Plattform, die den emotionalen Wert des Bibelvers-Sponsorings in den Mittelpunkt stellt.

---

## Grundsatzentscheidung: Einheitliches Preismodell
**Datum:** [Heutiges Datum einfügen]  
**Art:** Projektentscheidung basierend auf User-Feedback

### Die Entscheidung

Nach der Auswertung der drei User-Feedback-Sessions ist eine klare Entscheidung gefallen: **Es wird kein Premium-Sponsoring geben.** Das Projekt wird mit einem einheitlichen Preismodell umgesetzt, bei dem jeder Spender für den gleichen Betrag (100€) einen Vers sponsern kann.

### Begründung

Das eindeutige und konsistente Feedback aller befragten potentiellen Nutzer hat gezeigt, dass ein gestaffeltes Preismodell als unfair empfunden wird. Die Möglichkeit, einen Vers selbst auszuwählen, wird nicht als Premium-Feature gesehen, sondern als grundlegende Erwartung an das Sponsoring-Erlebnis. 

Die Entscheidung für ein einheitliches Modell basiert auf mehreren Faktoren. Erstens entspricht es dem Gerechtigkeitsempfinden der Nutzer, dass alle Spender die gleichen Möglichkeiten haben sollten. Zweitens vereinfacht es die User Experience erheblich, da keine verwirrenden Preisstufen erklärt werden müssen. Drittens reduziert es die technische Komplexität, da nur ein Zahlungsprozess implementiert werden muss.

### Konkrete Umsetzung

Im neuen Modell kann jeder Spender für 100€ einen Vers aus dem Pool der noch verfügbaren Verse auswählen. Die Auswahl erfolgt über eine benutzerfreundliche Suchfunktion, die verschiedene Zugänge ermöglicht: direkte Eingabe der Bibelstelle, Volltextsuche nach Stichworten, thematische Suche und Browsing durch Bücher und Kapitel.

Falls der Wunschvers bereits vergeben ist, werden intelligente Alternativen vorgeschlagen, basierend auf dem biblischen Kontext (vorheriger/nächster Vers) oder thematischer Ähnlichkeit.

### Auswirkungen auf das Projekt

Diese Grundsatzentscheidung hat weitreichende Auswirkungen auf die gesamte Projektarchitektur. Die Datenbankstruktur wird vereinfacht, da keine Unterscheidung zwischen Standard- und Premium-Käufen nötig ist. Die User Interface muss von Anfang an eine vollwertige Suchfunktion bieten. Der Fokus verschiebt sich von der Preisdifferenzierung zur Optimierung des Auswahl-Erlebnisses.

Die Herausforderung besteht nun darin, andere Wege zu finden, um Anreize für höhere Spenden zu schaffen, ohne die Kernfunktionalität einzuschränken. Mögliche Ansätze könnten freiwillige Mehrspenden, besondere Erwähnungen bei höheren Beträgen oder zusätzliche nicht-funktionale Benefits sein.

### Nächste Schritte

Die Projektdokumentation (README.md, project-description.md, development-plan.md) muss entsprechend aktualisiert werden, um diese fundamentale Änderung zu reflektieren. Alle Referenzen zu Premium-Features oder gestaffelten Preisen müssen entfernt werden. Die technische Planung kann sich nun voll auf die Implementierung einer exzellenten Such- und Auswahlfunktion konzentrieren.

---

## Technische Grundsatzentscheidungen
**Datum:** 1. August 2025  
**Art:** Architektur-Entscheidungen

### Datenbank: PostgreSQL statt SQLite

Nach eingehender Überlegung habe ich mich entschieden, direkt mit PostgreSQL zu starten, anstatt wie ursprünglich geplant mit SQLite zu beginnen. Der ausschlaggebende Faktor ist die Notwendigkeit einer effizienten Vektor-Suche für die semantische Vers-Ähnlichkeit.

**Begründung:**
- SQLite hat keine native Unterstützung für Vektor-Operationen
- Die pgvector Extension für PostgreSQL ermöglicht effiziente Cosine-Similarity-Berechnungen direkt in der Datenbank
- Eine spätere Migration wäre aufwendig und würde Refactoring erfordern
- PostgreSQL ist nicht wesentlich komplexer in der Handhabung als SQLite
- Docker macht das lokale Setup unkompliziert

### Dual-Translation-Ansatz

Eine wichtige Entscheidung betrifft die Verwendung von zwei verschiedenen Bibelübersetzungen:

**Schlachter 1951** (gemeinfrei):
- Wird für die Anzeige in der Web-App verwendet
- Rechtlich unbedenklich, da gemeinfrei
- Klassische, wörtliche Übersetzung

**Hoffnung für Alle 2015** (urheberrechtlich geschützt):
- Wird NUR intern für die Vektorisierung verwendet
- Niemals für User sichtbar
- Moderne, dynamische Übersetzung optimiert für NLP
- Bessere Ergebnisse bei semantischer Suche erwartet

**Begründung:**
Moderne Embedding-Modelle wurden auf zeitgenössischen Texten trainiert und verstehen natürliche, moderne Sprache besser. Die HFA verwendet aktuelles Deutsch und erklärt antike Konzepte mit modernen Begriffen, was zu besseren Vektoren führt. Die rechtliche Trennung (HFA nur intern, Schlachter für Anzeige) ist sauber und vermeidet Urheberrechtsprobleme.

### Semantische Suche mit Cosine Similarity

Für die Ähnlichkeitssuche verwenden wir **Cosine Similarity**, eine bewährte Methode im NLP-Bereich:

**Was ist Cosine Similarity?**
- Misst die Ähnlichkeit zwischen zwei Vektoren anhand des Winkels zwischen ihnen
- Werte zwischen 0 (keine Ähnlichkeit) und 1 (identisch)
- Ideal für hochdimensionale Räume wie Text-Embeddings
- Unabhängig von der Vektor-Länge (nur Richtung zählt)

**Implementierung mit pgvector:**
```sql
-- Ähnliche Verse finden
SELECT 
    v.id,
    v.reference,
    v.text_schlachter,
    1 - (vv.embedding <=> $1) as similarity
FROM bibelverse v
JOIN verse_vectors vv ON v.id = vv.verse_id
WHERE v.is_sponsored = false
ORDER BY vv.embedding <=> $1
LIMIT 5;
```

**Anwendungsfälle:**
1. Alternative Verse vorschlagen, wenn Wunschvers vergeben ist
2. Thematische Suche basierend auf Stichworten
3. "Ähnliche Verse" Feature für Exploration

### Datenstruktur-Entscheidungen

**Getrennte Tabellen für Verse und Vektoren:**
- `bibelverse`: Enthält Schlachter-Text und Metadaten
- `verse_vectors`: Enthält HFA-Text und Embeddings
- Ermöglicht saubere Trennung der Übersetzungen
- Flexibilität für zukünftige Embedding-Updates

**Einheitliche Vers-Referenzen:**
- Format: "BOOK.CHAPTER.VERSE" (z.B. "GEN.1.1")
- Ermöglicht eindeutige Zuordnung zwischen Übersetzungen
- Internationale Standards-konform

### Technologie-Stack Zusammenfassung

- **Datenbank**: PostgreSQL mit pgvector
- **Backend**: Flask (Python)
- **Embedding**: Sentence-BERT oder OpenAI Embeddings (noch zu evaluieren)
- **Bibeltexte**: Schlachter 1951 (Anzeige) + HFA 2015 (Vektorisierung)
- **Suche**: Cosine Similarity für semantische Ähnlichkeit

### Offene technische Fragen

1. **Embedding-Modell**: Welches Modell liefert die besten Ergebnisse für deutsche Bibeltexte?
2. **Vektor-Dimensionen**: 384 (Sentence-BERT) oder 1536 (OpenAI)?
3. **Performance**: Wie schnell sind Vektor-Suchen bei ~11.000 Versen?
4. **Caching**: Brauchen wir Redis für häufige Suchanfragen?
5. **Batch-Vektorisierung**: Wie organisieren wir den initialen Import?

### Reflexion

Diese technischen Entscheidungen erhöhen zwar die initiale Komplexität, schaffen aber eine solide Grundlage für die gewünschten Features. Der Dual-Translation-Ansatz ist eine elegante Lösung für das Spannungsfeld zwischen optimaler Suche und rechtlichen Beschränkungen. PostgreSQL mit pgvector gibt uns Enterprise-Level-Fähigkeiten für semantische Suche, die mit SQLite nicht möglich wären.

---

## Vector Search Proof of Concept - Überraschende Ergebnisse
**Datum:** 01.08.2025  
**Art:** Technischer Test

### Testziel

Vor der Hauptentwicklung wollten wir validieren:
1. Funktioniert semantische Suche mit deutschen Bibeltexten?
2. Liefert HFA 2015 bessere Ergebnisse als Schlachter 1951?
3. Welches Embedding-Modell ist optimal?
4. Ist die Performance akzeptabel?

### Testergebnisse

**Getestete Modelle:**
- paraphrase-multilingual-MiniLM-L12-v2 (384 Dimensionen)
- paraphrase-multilingual-mpnet-base-v2 (768 Dimensionen)

**Überraschende Erkenntnis:**

| Modell | Schlachter 1951 | HFA 2015 |
|--------|-----------------|----------|
| MiniLM (384d) | 54,5% | 9,1% |
| MPNet (768d) | **72,7%** | 18,2% |

Die Schlachter 1951 performt dramatisch besser als die moderne HFA 2015!

### Analyse der Ergebnisse

**Warum Schlachter besser funktioniert:**
1. **Konsistente Terminologie**: Wörtliche Übersetzungen verwenden durchgängig dieselben Begriffe
2. **Weniger Paraphrasierung**: Klarere semantische Signale für das Modell
3. **Strukturierte Sprache**: Die formellere Sprache könnte besser zu Trainingsdaten passen

**Ist 72,7% Genauigkeit ausreichend?**
Ja! Aus mehreren Gründen:
- Test zählte nur Top-3 Ergebnisse (in der App zeigen wir 5-10)
- Abstrakte Queries wie "Angst überwinden" sind schwieriger als konkrete Suchen
- Zusätzliche Kontext-basierte Alternativen (vorheriger/nächster Vers) erhöhen Trefferquote
- Hybrid-Ansatz mit Keyword-Matching möglich

### Neue technische Entscheidung

**Wir verwenden nur Schlachter 1951:**
- Bessere Suchergebnisse (72,7% vs. 18,2%)
- Deutlich einfachere Architektur
- Keine rechtlichen Komplikationen
- Ein Datenbestand statt zwei

**Optimales Setup:**
- Modell: paraphrase-multilingual-mpnet-base-v2
- Dimensionen: 768
- Übersetzung: Schlachter 1951
- Datenbank: PostgreSQL mit pgvector

### Auswirkungen auf das Projekt

1. **Vereinfachte Datenstruktur**: Keine separate HFA-Tabelle nötig
2. **Einfacherer Import**: Nur eine Quelle zu parsen
3. **Klarere Lizenzlage**: Nur gemeinfreie Texte
4. **Bessere Performance**: Ein Vektorraum statt zwei

### Nächste Schritte

1. Größerer Test mit 100+ Versen zur Validierung
2. Import-Script für alle Schlachter-HTML-Dateien
3. Performance-Tests mit vollständigem Datensatz
4. Feintuning der Suchparameter

---

## Enthusiastisches Feedback vom Auftraggeber
**Datum:** 1.August 2025  
**Art:** Feature-Anforderung per E-Mail

### Reaktion auf das Projekt

Daniel von der Peter-Schöffer-Stiftung hat sehr enthusiastisch auf das Projekt reagiert: "Finde es mega! Lass uns das unbedingt machen!" Diese Begeisterung ist eine großartige Bestätigung für die bisherige Arbeit.

### Neue Anforderung: Automatische Spendenbescheinigung

Eine wichtige neue Anforderung wurde hinzugefügt: Die App soll nicht nur das Zertifikat, sondern auch eine offizielle Spendenbescheinigung automatisch generieren und versenden.

**Benötigte Daten für die Spendenbescheinigung:**
- Anrede (Herr, Frau, Eheleute, Firma)
- Vorname
- Nachname
- Straße, Nr.
- PLZ
- Ort
- E-Mail-Adresse
- Spendenbetrag
- Spendendatum
- Spenden-Projekt: NGÜ
- Einverständnis zur Verarbeitung der Daten

### Technische Implikationen

Diese Anforderung hat mehrere Auswirkungen auf die Entwicklung:

1. **Erweiterte Datenerfassung**: Das Checkout-Formular muss deutlich mehr Felder enthalten
2. **Datenbank-Schema**: Die User- und GuestDonor-Tabellen müssen erweitert werden
3. **PDF-Generierung**: Zwei PDFs statt einem (Zertifikat + Spendenbescheinigung)
4. **Nummerierung**: Fortlaufende Spendenbescheinigungsnummern müssen generiert werden
5. **Compliance**: Offizielle Anforderungen für Spendenbescheinigungen müssen erfüllt werden

### Vorteile der Automatisierung

Die automatische Generierung und der Versand beider Dokumente zusammen bietet mehrere Vorteile:
- Sofortige Zustellung an den Spender
- Keine manuelle Nachbearbeitung nötig
- Konsistente Formatierung und Nummerierung
- Reduzierter Verwaltungsaufwand für die Stiftung
- Professioneller Eindruck beim Spender

### Nächste Schritte

1. Template für Spendenbescheinigung designen (rechtliche Anforderungen prüfen)
2. Checkout-Formular um alle benötigten Felder erweitern
3. Validierung für Adressdaten implementieren
4. System für fortlaufende Nummerierung entwickeln
5. Zwei-PDF-Generierung und -Versand implementieren



---

## Umfangreiche Tests der Suchfunktionen
**Datum:** 2. August 2025
**Art:** Technische Tests und Erkenntnisse

### Systematisches Test-Vorgehen

Nach unbefriedigenden ersten Ergebnissen haben wir einen systematischen Ansatz mit drei verschiedenen Datensätzen gewählt:
1. **100 Verse** - Kleines Test-Dataset für schnelle Iterationen
2. **1.000 Verse** - Mittleres Test-Dataset für aussagekräftige Tests
3. **11.000 Verse** - Komplettes reales Dataset (alle unübersetzten Bücher)

### Extended Test mit Vector POC

**Erste Ergebnisse mit 100 Versen:**
- Performance: Exzellent (0.055s pro Vers, 10 Min für 11.000 Verse)
- Suchqualität: Enttäuschend
  - Nur 25% Precision@1
  - Mean Reciprocal Rank: 0.280 (statt erwarteter 72.7%)
  - Klagelieder und Daniel überrepräsentiert in Ergebnissen

**Erkenntnisse:**
- Kleine Testmengen (100 Verse) können Ergebnisse verzerren
- Biblische Sprache ist Herausforderung für generische Embedding-Modelle
- Schlachter 1951 verwendet alte deutsche Sprache
- "Erwartete Treffer" basierend auf Keywords != semantische Treffer

### Hybrid-Suche Entwicklung

**Zwei fundamentale Use Cases identifiziert:**

1. **"Ähnlichste Verse finden"**
   - Input: Kompletter Vers
   - Ziel: Semantisch ähnliche Alternativen
   - Ideale Methode: Reine Vektor-Suche (90% Gewicht)

2. **"Keyword-Suche"**
   - Input: 1-3 Keywords
   - Ziel: Verse mit diesen Begriffen
   - Ideale Methode: Keyword + Vektor kombiniert

**Implementierte Lösung:**
- Dynamische Gewichtung basierend auf Query-Länge
- 1-2 Wörter: 80% Keyword, 20% Vektor
- 3-5 Wörter: 50% Keyword, 50% Vektor  
- 6+ Wörter: 20% Keyword, 80% Vektor

### Keyword-Tests mit finalen Daten

**Test-Setup:**
- 50 häufigste biblische Suchbegriffe ("Liebe", "Gott", "Glaube", etc.)
- 15 Kombinationen aus zwei Keywords
- 10 Kombinationen aus drei Keywords
- Volltext-Suche mit PostgreSQL

**Ergebnisse:**
- Keyword-Suche funktioniert zufriedenstellend
- AND-Verknüpfung bei Kombinationen sinnvoller als OR
- Performance auch bei 11.000 Versen sehr gut

### Semantische Suche mit beliebten Versen

**Test mit 15 populären Bibelversen:**
- Suche nach den 5 ähnlichsten Versen für jeden Testvers
- Cosine Similarity mit 768-dimensionalen Vektoren
- Fortschrittsanzeige beim Embedding-Generieren (5-10 Min für 11.000 Verse)

### Die große Erkenntnis: Das Positivitäts-Problem

**Kritisches Problem identifiziert:**
Sowohl Keyword- als auch semantische Suche liefern oft negative oder schwierige Verse als Top-Ergebnisse, obwohl Nutzer nach positiven, ermutigenden Versen suchen.

**Beispiele aus den Tests:**
- Suche nach "Hoffnung" → Verse über Verzweiflung und Gericht
- Suche nach "Liebe" → Verse über Gottes Zorn
- Semantisch ähnlich zu Trost-Versen → Klage-Verse

### Lösungsansätze für das Positivitäts-Problem

1. **Sentiment-basiertes Ranking** - Positive Verse bevorzugen
2. **Kategorisierung** - Verse in Kategorien einteilen (Verheißung, Warnung, etc.)
3. **Kontext-erweiterte Embeddings** - [POSITIV] oder [GERICHT] Tags
4. **Zwei-Stufen-Suche** - Erst suchen, dann nach Positivität re-ranken
5. **Gewichtete Scores** - Positive Begriffe boosten, negative penalisieren

### Neue Strategie: Kuratierte Top-1000-Liste

**Konzept:**
- 1000 positive Verse vorab nach Positivitätsfaktor ranken
- User bekommt standardmäßig Top 3 ungesponserte positive Verse
- Optional: Eigene Suche/Referenz-Eingabe möglich
- Fallback auf Top 3 wenn eigene Suche erfolglos

**Vorteile:**
- Einfachste User Experience
- Garantiert positive, ermutigende Verse
- Realistisches Spendenziel (1000 Verse)

### Wichtigste technische Learnings

1. **Arbeite mit realen Daten** - Auch kleine Testsets sollten aus echten Daten stammen
2. **Test-Datasets können täuschen** - 100er Subset liefert andere Ergebnisse als 11.000er Set
3. **Biblische Texte sind speziell** - Generische NLP-Modelle haben Schwierigkeiten
4. **Sentiment matters** - Technische Ähnlichkeit ≠ emotionale Ähnlichkeit
5. **LLMs sind überlegen** - Für gutes Positiv-Ranking braucht es große Sprachmodelle

### Nächste Schritte

1. **Prompt-Optimierung** für Positivitäts-Ranking mit LLM
2. **Datensatz erstellen** mit Positivitäts-Index für alle 11.000 Verse
3. **Evaluierung** verschiedener LLMs für diese Aufgabe
4. **Integration** des Rankings in die Suchfunktion 

