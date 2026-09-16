-- Migration 011: Eigene Datenbank für die Weihnachtskarten-Aktion anlegen
-- Created: 2026-09-16
-- Purpose: Getrennte Datenbank ngue_karten mit eigenem Benutzer "karten". Der Benutzer
--          hat auf ngue_db keine Rechte, ngueapp hat auf ngue_karten keine Rechte.
--
-- Läuft als Superuser (postgres). Vorher das Passwort unten ersetzen!
--
-- Ausführung:
--   Lokal:  sudo -u postgres psql -f migrations/011_karten_datenbank_anlegen.sql
--   Server: docker exec -i ngue-postgres psql -U ngueapp -d postgres < ../migrations/011_karten_datenbank_anlegen.sql
--           (aus app-deployment/ heraus; ngueapp ist im Container Superuser)
--   Danach: 012_create_card_requests.sql als Benutzer karten in ngue_karten ausführen.
--
-- Lokal ist der App-Benutzer "uli", nicht "ngueapp": dann unten die REVOKE-Zeile für ngueapp
-- streichen oder "ngueapp" durch "uli" ersetzen.

CREATE ROLE karten LOGIN PASSWORD 'HIER_PASSWORT_EINSETZEN';

CREATE DATABASE ngue_karten OWNER karten ENCODING 'UTF8' TEMPLATE template0;

-- Standardrechte für PUBLIC entfernen: niemand außer Owner und Superuser darf sich verbinden
REVOKE ALL ON DATABASE ngue_karten FROM PUBLIC;
-- karten darf die Spenden-Datenbank nicht einmal öffnen
REVOKE ALL ON DATABASE ngue_db FROM karten;
REVOKE CONNECT ON DATABASE ngue_db FROM karten;

SELECT 'ngue_karten angelegt, Benutzer karten' AS status;
