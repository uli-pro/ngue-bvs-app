-- Migration 012: Tabellen der Weihnachtskarten-Aktion (in der Datenbank ngue_karten!)
-- Created: 2026-09-16
-- Purpose: card_campaign (Einstellungen, eine Zeile) und card_requests (Bestellungen)
--
-- Ausführung als Benutzer karten in ngue_karten (NICHT in ngue_db):
--   Lokal:  psql -U karten -h localhost -d ngue_karten -f migrations/012_create_card_requests.sql
--   Server: docker exec -i ngue-postgres psql -U karten -d ngue_karten < ../migrations/012_create_card_requests.sql
--
-- Rollback: DROP TABLE card_requests; DROP TABLE card_campaign;

CREATE TABLE card_campaign (
    id INTEGER PRIMARY KEY,
    is_open BOOLEAN NOT NULL DEFAULT FALSE,
    max_households INTEGER NOT NULL DEFAULT 100,
    closes_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_count INTEGER NOT NULL DEFAULT 0,
    deleted_newsletter_count INTEGER NOT NULL DEFAULT 0,
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT chk_card_campaign_single_row CHECK (id = 1)
);

-- Eine Zeile: geschlossen, 100 Haushalte, Ende 27.11.2026 23:59 Berlin = 22:59 UTC
INSERT INTO card_campaign (id, is_open, max_households, closes_at)
VALUES (1, FALSE, 100, '2026-11-27 22:59:00');

CREATE TABLE card_requests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address_extra VARCHAR(200),
    street VARCHAR(200) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'DE',
    email VARCHAR(255),
    newsletter BOOLEAN NOT NULL DEFAULT FALSE,
    privacy_consent BOOLEAN NOT NULL DEFAULT FALSE,
    dedupe_address VARCHAR(300) NOT NULL UNIQUE,   -- Land|PLZ|Straße|Nachname, normalisiert
    dedupe_email VARCHAR(255) UNIQUE,
    possible_duplicate_of INTEGER,                 -- ähnliche Adresse, anderer Nachname (Admin prüft)
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT chk_card_requests_country CHECK (country IN ('DE', 'AT', 'CH'))
);

SELECT 'card_campaign und card_requests angelegt' AS status,
       (SELECT COUNT(*) FROM card_campaign) AS campaign_rows;
