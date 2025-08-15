Heute brauche ich dich als Datenbank-Designer. Wir wollen Postgresql und SQLAlchemy nutzen.

Bisher ist die Bibelvers-Sponsoring-App eine reine UIX-Demo mit keinerlei Datenspeicherung. Aber sie zeigt bereits alle Funktionen, die das fertige Produkt haben wird. Nur eine Funktion taucht im UI noch nicht auf, nämlich eine mögliche zukünftige Ausweitung auf Schweizer Spender.

Schau dir also erstmal die UIX-Demo nochmal gründlich an. 

Wichtig ist mir: 

- Sicherheit
- Robustheit
- Leichte Pflege
- Klare Logik

Folgende Tabellen und Felder ich mir überlegt - du machst das sicher besser. U.a. sind meine Feldnamen vermutlich oft zu lang; Und wie gut meine Logik ist, weiß ich auch nicht... Und ob ich an alles gedacht habe...


- Es gibt eine **Bibelvers-Tabelle** mit > 11.000 Einträgen. Folgende Felder sehe ich bereits:

  - vers_id
  - biblisches_buch
  - kapitel
  - vers
  - text
  - positivity_score
  - gesponsert_von
  - gesponsert_am

- Es gibt eine **Spender**-Tabelle

  - spender_id
  - email
  - anrede
  - titel
  - vorname
  - nachname
  - strasse
  - hausnummer
  - plz
  - ort
  - land
  - newsletter_abo
  - zustimmung_datenschutz

- Tabelle für alle **Einzelspenden**

  - einzelspenden_id
  - verknüpfung zu vers_id
  - verknüpfung zu spender_id
  - betrag
  - währung (EUR / CHF)

- Es gibt eine Tabelle, in der alle **Guppenspenden** abgelegt werden

  - gruppenspenden_id
  - verknüpfung zu vers_id
  - verknüpfung zu spender_id
  - betrag
  - waehrung (EUR / CHF)
  - name_gruppe
  - artikel_gruppe

- Es gibt eine Tabelle, in der alle **Geschenkspenden** abgelegt werden

  - geschenkspenden_id
  - verknüpfung zu vers_id
  - verknüpfung zu spender_id
  - betrag
  - währung (EUR / CHF)
  - beschenkter
  - email_beschenkter
  - message (an den beschenkten)
  - zertifikat
  - spendenbescheinigung

  --> ODER EINE GEMEINSAME TABELLE FÜR ALLE SPENDEN?

- Es gibt eine **Spendenkorb**-Tabelle, die als temporärer Warenkorb während der Session fungiert. 

  - spendenkorb_id
  - verknüpfung zu einzelspenden_id
  - verknüpfung zu gruppenspenden_id
  - verknüpfung zu geschenkspenden_id

- Es gibt eine Tabelle für alle **Zertifikate**

  - zertifikat_id
  - verknüpfung zu einzelspenden_id, gruppenspenden_id, geschenkspenden_id
  - art (einzelspende, gruppenspende, geschenk)
  - zertifikat_pdf

- Es gibt ein Tabelle für alle **Spendenbescheinigungen**

  - spendenbescheinigung_id
  - verknüpfung zu einzelspenden_id, gruppenspenden_id, geschenkspenden_id
  - ausstellende_organisation (Schöffer-Stiftung, Genfer Bibelgesellschaft)
  - spendenbescheinigung_pdf

- Es gibt eine **User**-Tabelle

  - user_id
  - email
  - passwort (gehascht & gesalzen :-)
  - anrede
  - titel
  - vorname
  - nachname
  - strasse
  - hausnummer
  - plz
  - ort
  - land
  - newsletter_abo
  - zustimmung_datenschutz