# Woche 2: Frontend Design & Account-Implementation

## 11. August 2025 - Session 4A & 4B

Über das Wochenende hatte ich bereits einen Großteil des Frontends implementiert und eine funktionsfähige Website-Demo erstellt. Heute habe ich für die Demo das Account-System implementiert. Für Demo-Zwecke habe ich den Login-Prozess vereinfacht, sodass beliebige E-Mail/Passwort-Kombinationen akzeptiert werden und automatisch ein Dashboard-Zugang gewährt wird.

Im zweiten Teil des Tages konzentrierte ich mich auf UI-Verbesserungen und Content-Updates. Die ursprünglich geplante Übersetzungsfortschritts-Anzeige wurde wieder entfernt, da die Datenpflege für 11.000 Verse zu aufwändig gewesen wäre. Außerdem aktualisierte ich die Kontaktdaten der Peter-Schöffer-Stiftung auf die neue Adresse in Osthofen und vereinheitlichte alle E-Mail-Adressen auf die Domain @schoeffer.org. Telefonnummern wurden komplett entfernt, da diese nicht verfügbar sind. Abschließend bereinigte ich die Navigation durch das Entfernen des "Projektpartner" Menüpunkts.

Ich habe gemerkt, wie hilfreich für das Frontend-Design die Flask-Struktur ist, die wir in CS50 gelernt haben mit /static und /templates und insbesondere der layout.html. Die Template-Vererbung über `layout.html` ermöglicht es, konsistente Navigation und Design-Elemente über alle Seiten zu haben, während individuelle Inhalte durch Jinja2-Blöcke eingefügt werden. 

