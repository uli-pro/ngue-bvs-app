# Woche 0: Vorüberlegungen und User-Feedback

**Zeitraum:** Vor Projektstart  
**Fokus:** Konzeptvalidierung, User-Feedback, Grundsatzentscheidungen

---

## User-Feedback Session: Preismodell und Vers-Auswahl
**Datum:** [Heutiges Datum einfügen]  
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
