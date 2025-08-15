Ich möchte den Weg des Users von der Ankunft auf der Seite bis zur erfolgreichen Spende vereinfachen: 

1) Er kommt auf /index an. Von dort wird er zu /vers-auswaehlen. /index macht das bereits sehr gut und kann so bleiben. 

2) Auf /vers-auswaehlen werden dem User drei Verse präsentiert aus denen er sofort auswählen kann. Außerdem gibt es zwei weiter Möglichkeiten, einen geeigneten Vers zu finden: a) /vers-auswaehlen/referenz  und b) vers-auswaehlen/keyword. Ist der Vers gefunden, wird der User über den Button "Diesen Vers wählen" weitergeleitet zur nächsten Seite. 
   ANMERKUNG: Die Bisher heißen die Unterseiten vers-suche/referenz und vers-suche/keyword. Diese Namen sollten geändert werden, wie auch die Namen der Routen in app.py, so dass die Nomenklatur konsistent ist.

   Für die aktuelle Version, die ja nur eine Demo ist, sollten dem Leser auf /vers-auswaehlen nur folgende drei Verse angezeigt werden: Jesaja 43,1; Jeremia 29,11; Zefanja 3,17 (Text siehe unten)

   a) Auf /vers-auswaehlen/referenz sollen ebenalls nur diese Verse anwählbar sein und dann auch angezeigt werden und Auf b) vers-auswaehlen/keyword sollten ebenfalls bei egal welchem Keyword immer diese drei Verse angezeigt werden (ähnlich wie es jetzt schon gelöst ist  - man muss nur die Verse austauschen.)

3) Auch /vers-auswahl mit seinen beiden Unterseiten ist gut gelöst und kann erstmal so bleiben.

4) Die nächste Seite heißt bisher /bestaetigung. Name und Funktion dieser Seite und Route müssen geändert werden. Es muss /spendenart heißen. Die einzige Funktion dieser Seite ist: Der User kann auswählen, ob er den Vers als Einzelspender für sich selbst, als Gruppenspende im Namen einer Gruppe oder als Geschenk für eine andere Person sponsern will. Auf dieser Seite wird in der Demo immer Jeremia 29,11 angezeigt. Diese Seite muss die drei Optionen übersichtlich präsentieren. Bei "Gruppe" muss ein Hinweis erfolgen, dass der User für eine Gruppenspende keine automatische Spendenbescheinigung bekommt, sondern dass er für eine Bescheinigung mit der Stiftung direkt Kontakt aufnehmen muss.

5) a) Wählt er Einzelspende, wird er direkt zu /checkout/einzelperson/daten geführt. Dort muss er seine E-Mail-Adresse und Kontaktdaten für die Spendenbescheinigung eingeben.

   b) Wählt er Gruppenspende, wird er zu /checkout/gruppe/daten geführt. Dort MUSS er seine E-Mail-Adresse und KANN er seine Kontaktdaten eingeben und wird noch einmal darauf hingewiesen, dass er für die Gruppenspende keine automatischen Spendenbescheinigung bekommt, sondern mit der Stiftung Kontakt aufnehmen muss.

   c) Wählt er Geschenk, wird er zu /checkout/geschenk/daten geführt. Dort muss er seine E-Mai-Adresse und Kontaktdaten für die Spendenbescheinigung angeben. Dann muss er den Namen der beschenkten Person eingeben. Dann kann er wählen, ob das Zertifikat der beschenkten Person direkt zugesandt werden soll. Wenn ja, MUSS er ihre E-Mail-Adresse eingeben und KANN eine persönliche Nachricht eingeben.

   Von allen drei Unterseiten wird man direkt zu /checkout/zusammenfassung weitergeleitet.

6) /checkout/zusammenfassung fungiert als eine Art Warenkorb. Er sieht in einer Tabellenübersicht alle in dieser Session ausgewählten Verse mit folgenden Daten:

   - Referenz und erste Worte des Verses

   -  Spendentyp für den Vers: Einzelspende, Geschenk für [NAME], Gruppenspende für [GRUPPE] 
   - Kosten (immer 100,- €). 
   - Außerdem kann er ganz rechts in der Tabelle den Vers wieder entfernen.

   Unten gibt es natürlichen Gesamtbetrag.

   Von checkout/zusammenfassung kann er entweder einen weiteren Vers auswählen (und wird zurückgeleitet zud /vers-auswaehlen) oder er wird über "Sicher spenden - GESAMTBETRAG" zu STRIPE weitergeleitet.

Für die aktuelle Demoversion wird diese Seite immer mit folgenden Daten angezeigt: Jeremia 29,11 Einzelspende, Zefanja 3,17 Geschenk für Erika Mustermann, Jesaja Gruppenspende für Teenkreis Musterdorf (ähnlich wie es auf /dashboard im Moment implementiert ist. 

Der Text von Jesaja 43:1 in der Schlachter-1915 lautet:  Und nun spricht der HERR, der dich geschaffen hat, Jakob, und der dich gemacht hat, Israel: Fürchte dich nicht, denn ich habe dich erlöst. Ich habe dich bei deinem Namen gerufen; du bist mein!

Jeremia 29,11 lautet: Denn ich weiß, was für Gedanken ich über euch habe, spricht der HERR, Gedanken des Friedens und nicht des Leides, euch eine Zukunft und eine Hoffnung zu geben. 

Zefanja 3,17 lautet: Der HERR, dein Gott, ist in deiner Mitte, ein Held, der helfen kann; er wird sich über dich freuen mit Wonne, er wird schweigen in seiner Liebe, er wird über dir jubelnd frohlocken. 

Auch auf dem /dashboard und bei /meine-verse und wo immer sonst noch Verse zu finden sind, sollten immer diese Verse verwendet werden.

Bitte schreibe alle benötigten Dateien und Routen entsprechend um und teste am Ende, ob alles funktioniert. 