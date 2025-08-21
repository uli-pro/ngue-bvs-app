# Nächste Schritte

- Stripe Zahlungen robuster und sicherer? machen (Claude planen lassen)
- Spendenart-Route ändern: Eingabe der Spenderdaten erst ganz am Schluss, vor dem "Sicher zahlen"; Zertifikat geht immer auch an Geschenkspender. D.h. der Text muss lauten: Soll das Zertifikat auch direkt an den Beschenkten gehen? Sonst geht es nur an Sie, damit Sie es selbst überreichen könne.
- Spendenkorb: Bei Geschenkversen Möglichkeit die Message und E-Mail nochmal zu editieren.
- PDF-Generator implementieren
- E-Mail-Engine implementieren
- User-Verwaltung fertig implementieren:
  - reales Dashboard
  - reale "meine Verse"
  - Möglichkeit Messages anzuzeigen



---

# Entscheidungen im Team

- Können wir die Webseiten zusammenführen? 

- Plan: Bis Weihnachten in eine integrierte Webseite zusammenführen.

- Über Hubspot tracken

- Verlage, 

- Mailgun

- Ionos -> hosting

- App lean machen.

- Landing-Page für Sponsoring-Projekt -> 3 Infos 

  - 100% fließen ins ÜbersetzungsPROJEKT? 
  - 10% fließen in allgemeine Kosten / Übersetzungsprojekt -> FAQ's

- Kommunikation

  - Ich rede mit Uwe 
  - Daniel redet mit Christophe (sobald er von mir den Alpha-Link bekommt)

- Roadmap: Beta bis Ende September
  Produktion bis Ende Oktober

- Design Zertifikat

  - Logo Schoeffer oben

  - Genfer Bibelgesellschaft / Brunnen

    --> Niki macht Design

- Spendenbescheinigung: mach ich.

- Mailgun-Zugang

- Mail: suppport@schoeffer.org

- Hubspot Cookies -> 

- Cookie-Einwilligung programmieren

- Link zu Schoeffer-Stiftung -> Link unter Hero-Section

- Bilder 

- NGÜ-Text muss in Database -> Wenn Text eingepflegt, werden Spender informiert.

- 





---

# Rückmeldungen zur UIX

## Allgemein & Meta

#### allgemein

  > Spendenart-Route

- Farben müssen vereinheitlicht werden (css) -> Color Picker Complementing / Contrasting (Canva) https://www.canva.com/colors/color-wheel/
- Passwort-Hashing: argon2id
- Eine Art Liveticker, wer zuletzt wie viele Verse gesponsert hat.
- Bilder von NGUE einpflegen 
- Wie groß ist der Spendenbedarf -> abklären

#### zertifikate

- 

---

## Seiten

#### /bestaetigung

#### /checkout/erfolg

- 

#### /checkout/einzelspende/daten

- Ab dem zweiten Vers in einer Sitzung die Daten nicht mehr eingeben müssen
- Ebenso nicht, wenn die Person sich einloggt (selbst wenn sie die Daten in dieser Sitzung nicht eingegeben hatte)

*Das gilt für alle drei /daten-Seiten*.

#### /checkout/gruppe/daten

#### /checkout/geschenk/daten

#### /spendenkorb

- Bezahlmöglichkeiten Grafisch darstellen (u.a. Paypal, wenn Stripe das anbietet)
- Alert bei Entfernung: möchten sie *diesen* *einzelspende/geschenk/gruppe* wirklich aus dem *Warenkorb* entfernen?

#### /dashboard

- Button "Alle anzeigen" -> "Verse anzeigen"

#### /datenschutz

- Farben
- Text

#### /faq

- Suche funktioniert noch nicht.

#### /impressum

- E-Mail / Link anklickbar machen
- Registereintrag
- Steuerliche Angaben
- Technische Umsetzung (:-))
- EU-Streitschlichtung

#### /index

- Aktueller Projektstand -> anders formulieren, damit klar wird, dass schon große Teile der NGE übersetzt sind.

#### /layout

- footer: Links zu Social Media
- footer: Link zur Peter-Schöffer-Stifung klickbar machen

#### /login

- 

#### /meine-verse

- Karusell zum Display.

#### /register

- Später: Felder mit den Daten aus dem Kauf vorausfüllen (und andersherum)

#### /spendenart 

- Spende für mich selbst anders formulieren

#### /transparenz

- Den gesamten Text kritisch auf Sachaussagen hin prüfen.
- Zweiten CTA-Button einfügen

#### /ueber-ngue

- Zweiten CTA-Button einfügen

#### /ueber-stiftung

- 

