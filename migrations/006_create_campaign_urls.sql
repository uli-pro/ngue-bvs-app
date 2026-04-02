-- Migration: Create campaign_urls table
-- Created: 2026-04-02
-- Purpose: Zentrale UTM-URL-Verwaltung im Admin-Panel (Online + Offline)
--
-- Ausführung (aus dem Projektverzeichnis ngue-bvs-app/):
--   Lokal:  sudo -u postgres psql ngue_bvs_db -f migrations/006_create_campaign_urls.sql
--   Server: docker exec -i ngue-postgres psql -U ngueapp -d ngue_db < ../migrations/006_create_campaign_urls.sql
--           (aus app-deployment/ heraus)

-- 1. Create campaign_urls table
CREATE TABLE campaign_urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    url_type VARCHAR(10) NOT NULL DEFAULT 'online',
    slug VARCHAR(60) UNIQUE,
    target_url VARCHAR(500) NOT NULL DEFAULT 'vers-patenschaft.de',
    utm_source VARCHAR(100) NOT NULL,
    utm_medium VARCHAR(50) NOT NULL,
    utm_campaign VARCHAR(200),
    utm_content VARCHAR(200),
    utm_term VARCHAR(200),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    click_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    created_by VARCHAR(200)
);

-- 2. Index auf slug für schnelle Redirect-Lookups
CREATE INDEX ix_campaign_urls_slug ON campaign_urls (slug);

-- 3. Check-Constraint: url_type muss 'online' oder 'offline' sein
ALTER TABLE campaign_urls
    ADD CONSTRAINT chk_campaign_urls_url_type
    CHECK (url_type IN ('online', 'offline'));

-- 4. Verify migration
SELECT 'campaign_urls table created' AS status,
       (SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'campaign_urls') AS column_count;
