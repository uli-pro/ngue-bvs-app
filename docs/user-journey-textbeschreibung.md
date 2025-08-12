# User Journey für die NGÜ Bibelvers-Sponsoring App (Textbeschreibung)

Die User Journey beginnt mit der **Index-Seite**. Der User wird übersichtlich und grafisch einladend über das Bibelvers-Sponsoring-Projekt der NGÜ informiert. Eine prominente Infografik (z.B. Tortendiagramm) zeigt transparent die Aufteilung der 100€ Spende. Daneben sind Call-to-Action Buttons wie "Jetzt spenden" prominent platziert. Ein Link "Mehr zur Mittelverwendung" führt zur detaillierten Transparenz-Seite. In der Navigation sind Links zu "Über die Peter-Schöffer-Stiftung", "Über die NGÜ", sowie optional "Login/Registrieren" sichtbar.

Wenn der User auf den Spenden-Button klickt, kommt er auf die Seite **"Wählen Sie Ihren Bibelvers"**. Ihm werden drei zufällig ausgewählte, positiv ermutigende Bibelverse aus dem noch ungesponserten Pool gezeigt, von denen er direkt einen auswählen kann. Diese Top-3 Verse sind speziell nach Positivität gerankt.

Unter den drei vorgeschlagenen Versen gibt es zwei alternative Optionen:

1. Ein Link "Ich möchte einen bestimmten Vers auswählen" führt zu einer Seite mit Dropdown-Menüs für Buch/Kapitel/Vers. Wenn der gewählte Vers verfügbar ist, wird er direkt angezeigt und kann ausgewählt werden. Ist er bereits vergeben, werden drei thematisch ähnliche, noch verfügbare Verse vorgeschlagen, ebenfalls nach Positivität gerankt.
2. Ein Link "Nach Thema/Stichwort suchen" führt zu einer Keyword-Suche, die ebenfalls die drei positivsten verfügbaren Verse zum eingegebenen Thema anzeigt. Ein Button "Weitere Verse anzeigen" lädt drei zusätzliche Optionen. Bei der Eingabe neuer Suchwörter beginnt die Liste von vorn.

Sobald ein Vers ausgewählt wurde, gelangt der User zur **Vers-Bestätigungsseite**. Hier sieht er seinen gewählten Vers nochmals in voller Länge und kann auswählen, ob er als Einzelspender, im Namen einer Gruppe oder Schenkender für eine andere Person agiert. Bei der Gruppenspender-Option öffnen sich zusätzliche Felder für den Gruppennamen (und deren Artikel), bei der Geschenk-Option öffnen sich zusätzliche Felder für Empfängername und eine persönliche Nachricht.

Von dort geht es zur **Datenerfassungsseite**. Hier wird IMMER die E-Mail-Adresse abgefragt (für den Zertifikatsversand). Darunter ist eine prominente Checkbox "Ich möchte eine Spendenbescheinigung erhalten" (standardmäßig aktiviert). Wenn diese aktiviert ist, erscheinen die zusätzlichen Pflichtfelder: Anrede, Vorname, Nachname, Straße, Hausnummer, PLZ, Ort. Am Ende der Seite befinden sich zwei weitere Checkboxen: "Newsletter abonnieren" und die Pflicht-Checkbox "Ich stimme der Datenschutzerklärung zu" mit Link zur Datenschutzerklärung. Ein kleiner Info-Text erklärt, dass die Spende an die Peter-Schöffer-Stiftung geht, mit Link zu mehr Informationen.

Nach dem Ausfüllen kommt der User zur **Zahlungsbestätigungsseite**. Hier sieht er eine Zusammenfassung: gewählter Vers, Spendenbetrag (100€), seine Daten, und bei Geschenk die Empfängerdaten. Ein Link "Wohin fließt meine Spende?" ist erneut vorhanden. Der Button "Jetzt verbindlich spenden" führt zu Stripe.

Bei **Stripe** wickelt der User die Zahlung ab. Bei erfolgreicher Zahlung wird er zur Danke-Seite weitergeleitet, bei Abbruch zurück zur Zahlungsbestätigungsseite mit entsprechender Meldung.

Die **Danke-Seite** bestätigt die erfolgreiche Spende und das gute Werk. Zertifikat und ggf. Spendenbescheinigung stehen zum sofortigen Download bereit. Der User wird informiert, dass beide Dokumente auch per E-Mail verschickt werden. Ein prominentes Angebot lädt zur Registrierung ein: "Registrieren Sie sich, um jederzeit auf Ihre Dokumente zugreifen und alle Ihre gesponserten Verse einsehen zu können." Darunter befinden sich Social-Media-Sharing-Buttons und der Vorschlag "Verschenken Sie ein Bibelvers-Sponsoring an Freunde und Familie" mit Link zurück zur Vers-Auswahl.

**Zusätzliche Seiten:**

Die **"Über die NGÜ"**-Seite informiert ausführlich über das Übersetzungsprojekt, seine Geschichte und Bedeutung. Prominente CTAs führen zur Vers-Auswahl.

Die **"Über die Peter-Schöffer-Stiftung"**-Seite erklärt die Stiftung als Träger des Projekts, ihre Mission und weitere Projekte. Sie macht die Verbindung zur NGÜ deutlich und schafft Vertrauen. Diese Seite ist von der Hauptnavigation, der Datenerfassung und dem Footer aus erreichbar.

Die **Transparenz-Seite "Wohin fließt meine Spende?"** zeigt detailliert die Mittelverwendung: Übersetzungskosten, Lektorat, Projektmanagement, technische Infrastruktur etc. Sie ist von der Index-Seite, der Zahlungsbestätigung und dem Footer verlinkt.

Das **User-Dashboard** (für registrierte Nutzer) zeigt eine Übersicht aller gesponserten Verse, ermöglicht den Download von Zertifikaten und Spendenbescheinigungen, verwaltet Newsletter-Einstellungen und Profildaten.

**Login/Registrierung** ist jederzeit über die Hauptnavigation erreichbar, wird aber nie erzwungen. Die Registrierung kann auch nachträglich erfolgen, indem die E-Mail-Adresse mit bereits getätigten Spenden verknüpft wird.

Die **FAQ/Hilfe-Seite** beantwortet häufige Fragen zu Spenden, Zertifikaten, Steuern, dem Übersetzungsprojekt etc. Am Ende jeder relevanten Antwort steht ein kontextbezogener CTA: Z.B. nach "Wie funktioniert das Sponsoring?" → "Jetzt Ihren Vers auswählen". Ganz unten ein prominenter Button "Überzeugt? Jetzt spenden"

**Impressum und Datenschutzerklärung** erfüllen die rechtlichen Anforderungen und sind über Footer und relevante Stellen verlinkt. Auch vom Impressum führt ein Dezenter, aber sichtbarer CTA am Ende zurück zur Verswahl-Seite. Z.B. "Zurück zur Vers-Auswahl" oder "Projekt unterstützen". (Nicht zu aufdringlich, da Impressum primär informativen Charakter hat).

**Fehlerseiten** (404, Zahlungsfehler, Timeout) bieten klare Informationen und Handlungsoptionen, immer mit Link zurück zur Startseite.

Auf allen Seiten sind Links zu den Social-Media-Kanälen (Instagram, später Facebook und TikTok) im Footer präsent. Ein Cookie-Banner erscheint beim ersten Besuch gemäß DSGVO.

Bei der technischen Umsetzung wird eine **temporäre Vers-Reservierung** (15 Minuten) implementiert, sobald ein User einen Vers auswählt und zur Datenerfassung geht, um Doppelbuchungen zu vermeiden.