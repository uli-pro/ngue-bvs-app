-- Migration: Create speaker_requests table
-- Created: 2026-09-10
-- Purpose: Referenten-Anfragen von Gemeinden über das Formular /vortrag speichern
--
-- Ausführung (aus dem Projektverzeichnis ngue-bvs-app/):
--   Lokal:  sudo -u postgres psql ngue_bvs_db -f migrations/009_create_speaker_requests.sql
--   Server: docker exec -i ngue-postgres psql -U ngueapp -d ngue_db < ../migrations/009_create_speaker_requests.sql
--           (aus app-deployment/ heraus)
--
-- Hinweis: Nummer 008 ist auf dem Branch feature/brevo-newsletter vergeben (Newsletter-Tracking).

CREATE TABLE speaker_requests (
    id SERIAL PRIMARY KEY,
    organization VARCHAR(200) NOT NULL,
    contact_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    postal_code VARCHAR(10),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(10) NOT NULL DEFAULT 'DE',
    event_type VARCHAR(20) NOT NULL,
    event_date DATE,
    preferred_date VARCHAR(200),
    participants VARCHAR(50),
    audience VARCHAR(200),
    topic TEXT NOT NULL,
    tech_available VARCHAR(20),
    photo_consent VARCHAR(10),
    referral_source VARCHAR(200),
    privacy_consent BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'neu',
    admin_notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX ix_speaker_requests_status ON speaker_requests (status);

ALTER TABLE speaker_requests
    ADD CONSTRAINT chk_speaker_requests_status
    CHECK (status IN ('neu', 'kontakt', 'termin', 'abgeschlossen', 'abgesagt'));

ALTER TABLE speaker_requests
    ADD CONSTRAINT chk_speaker_requests_event_type
    CHECK (event_type IN ('gottesdienst', 'vortrag', 'seminar', 'sonstiges'));

SELECT 'speaker_requests table created' AS status,
       (SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'speaker_requests') AS column_count;
