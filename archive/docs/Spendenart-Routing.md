Okay, es geht wieder um eine Bibelvers-Sponsoring-App und es geht um die Implementierung einer Routenänderung. Und zwar wäre es auswählen, Spendenart auswählen. Und dann gibt es drei Seiten je nach Spendenart: Checkout Einzelspende, Checkout Gruppenspende oder Checkout Geschenk. Und in allen drei Formularen wird abgefragt, die User, die E-Mail des Users und die spendenartspezifischen Dinge wie Name der Gruppe bei der Gruppenspende und Artikel oder Name des Beschenkten, E-Mail des Beschenkten und Message an den Beschenkten bei der Geschenkspende. Plus die Spenderdaten für die Spendenbescheinigung bei der Einzelspende und bei der Geschenkspende, bei der Gruppenspende nicht, weil da gibt es keine automatische Spendenbescheinigung. Das ist der Ist-Zustand und dann gelangt man von dieser Eingabeseite aus dann in den gemeinsamen Spendenkorb, also wo dann alle Arten von Spenden an einer Stelle sind und von da aus dann weiter zur Zahlung.

Meine Vorstellung von der zukünftigen Route wäre folgendermaßen. Wer es auswählen, dann gibt es eine Seite mit Spendenart. Auf dieser Seite sind die drei Spendenarten nicht nebeneinander in drei Kästchencontainern, sondern untereinander, aber auch schön in so einem Kästen-Style, wo sie beschrieben sind und wo man dann ganz rechts diese Spendenart auswählen kann. Wenn man die Einzelspende auswählt, wird man direkt weitergeleitet zum Spendenkorb. Wenn man die Gruppenspende auswählt, dann öffnet sich unterhalb praktisch von diesem Feld oder das Feld öffnet sich, vergrößert sich und es entsteht ein Dialog, in dem man eingeben muss den Namen der Gruppe und die Artikel der Gruppe und man wird dort auch gleich informiert, dass es für Gruppenspenden keine automatische Spendenbescheinigung gibt. Und dann klickt man, dass man dann den Vers zum Spendenkorb hinzufügt.

Und bei der Geschenkspende ist das Prinzip das gleiche. Das geht dann auch wieder auf, das Kästchen wird größer und dann kann man eingeben E-Mail des Beschenkten, Name des Beschenkten, E-Mail des Beschenkten und Message an den Beschenkten. Und dann kann man eben auch klicken, da wird es den Spendenkorb hinzugefügt. So und wenn man dann beim Spendenkorb rausgeht, dann geht man noch nicht auf Zahlen, sondern dann geht man erstmal auf so ein Checkout oder wie man das dann nennen mag. Und auf der nächsten Seite gibt man dann seine Spendendaten ein.

Und dann gibt es Wahlmöglichkeiten, wenn man eine Spendenbescheinigung will und entweder eine Einzelspende oder eine Geschenkspende in seinem Warenkorb hat, dann öffnet sich das Spendendatenformular und dann gibt man seine Spendendaten ein. Wenn man keine Spendenbescheinigung will, dann bleibt dieses Formular zu. Oder wenn man nur eine Gruppenspendenwaren in einem Gruppenspendenwarenkorb hat, dann bleibt es auch zu, weil dann gibt es keine Spendenbescheinigung.

Und unterhalb dieses Teils, wo die Spendendaten eingegeben werden können und es sich dann öffnet, wenn man das eben möchte oder vielleicht auch offen ist, weiß ich noch nicht, gibt es nochmal zwei Ankreuzfelder mit ich will den Newsletter kriegen. Und ich habe die Datenschutzbestimmungen gelesen und akzeptiere sie. Und darunter gibt es dann einen Button, der einen dann zur Zahlung führt. Also dann kann man sich ja bezahlen und zahlen. Und dann öffnet sich die Seite, indem man die Zahlungsinformationen eingibt, beziehungsweise nochmal, also Überprüfte sind vorausgefüllt mit dem, was man eben schon eingegeben hat. Und das müssen wir dann je nachdem nochmal ergänzen. Genau. Soweit.



---



**Aufgabe: Redesign des Checkout-Flows für NGÜ Bibelvers-Sponsoring App**

**Aktueller Ist-Zustand:** Nach der Vers-Auswahl gibt es eine separate Seite "Spendenart auswählen", die zu drei verschiedenen Checkout-Seiten führt:

- checkout/einzelperson/daten
- checkout/gruppe/daten
- checkout/geschenk/daten

Jede Seite erfasst unterschiedliche Daten:

- **Einzelspende:** User-E-Mail + Spenderdaten für Spendenbescheinigung
- **Gruppenspende:** User-E-Mail + Gruppenname + Artikel (keine automatische Spendenbescheinigung)
- **Geschenkspende:** User-E-Mail + Name des Beschenkten + E-Mail des Beschenkten + Nachricht + Spenderdaten für Spendenbescheinigung

Anschließend gelangen alle Spendenarten in einen gemeinsamen Spendenkorb und von dort zur Zahlung.

**Gewünschter neuer Flow:**

1. **Vers auswählen** (unverändert)
2. Neue Spendenart-Seite:
   - Drei Spendenarten vertikal untereinander (nicht nebeneinander)
   - Jede in einem schönen Container/Kästen-Style
   - Beschreibung der Spendenart mit "Auswählen"-Button rechts
3. Interaktives Verhalten pro Spendenart:
   - **Einzelspende:** Direktweiterleitung zum Spendenkorb
   - **Gruppenspende:** Container erweitert sich nach unten → Eingabefelder für Gruppenname und Artikel + Hinweis "keine automatische Spendenbescheinigung" → Button "Zum Spendenkorb hinzufügen"
   - **Geschenkspende:** Container erweitert sich nach unten → Eingabefelder für Name, E-Mail und Nachricht des Beschenkten → Button "Zum Spendenkorb hinzufügen"
4. Neuer Checkout-Flow:
   - Vom Spendenkorb nicht direkt zur Zahlung
   - Zwischenseite für Spendendaten-Erfassung
   - Spendenbescheinigung-Logik:
     - Bei Einzelspende oder Geschenkspende: Option "Spendenbescheinigung gewünscht" → Formular öffnet sich
     - Bei reiner Gruppenspende: Formular bleibt geschlossen (keine Spendenbescheinigung möglich)
   - **Immer sichtbar:** Newsletter-Checkbox + Datenschutz-Checkbox
   - Button "Zur Zahlung" führt zur finalen Zahlungsseite
5. Zahlungsseite:
   - Zusammenfassung mit vorausgefüllten Daten aus vorherigen Schritten
   - Ergänzung/Korrektur bei Bedarf möglich

**Technische Anforderungen:**

- Progressive Disclosure (Container erweitern sich dynamisch)
- Conditional Logic für Spendenbescheinigungs-Formular
- State Management für verschiedene Spendenarten im Korb
- Responsive Design für Container-Erweiterungen

Bitte implementiere diesen neuen Flow und ersetze die bestehenden separaten Checkout-Seiten durch das beschriebene interaktive System.