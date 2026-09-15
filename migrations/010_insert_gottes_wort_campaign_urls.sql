-- Migration: Kampagnen-Links für das YouTube-Video „Gottes Wort in unserer Sprache" (Vortrag FeG Wetzlar)
-- Created: 2026-09-15
-- Purpose: Drei Einträge:
--   1. Kurzlink „gotteswort" – wird in allen 8 Shorts/Reels eingeblendet, leitet auf den Gesamtvortrag bei YouTube.
--   2. Direktlink für die YouTube-Beschreibung des Langvideos (Ziel /vortrag).
--   3. Direktlink für den Instagram-Bio-Link (Ziel /vortrag).
--
-- Ausführung (aus dem Projektverzeichnis ngue-bvs-app/):
--   Lokal:  sudo -u postgres psql ngue_bvs_db -f migrations/010_insert_gottes_wort_campaign_urls.sql
--   Server: docker exec -i ngue-postgres psql -U ngueapp -d ngue_db < ../migrations/010_insert_gottes_wort_campaign_urls.sql
--           (aus app-deployment/ heraus)
--
-- Idempotent: vorhandene Einträge (gleicher Slug bzw. gleicher Name) werden übersprungen.
-- Rollback: migrations/010_rollback_gottes_wort_campaign_urls.sql
--
-- HINWEIS: Wird der Vortrag bei YouTube neu hochgeladen, bekommt er eine neue Video-ID.
-- Dann im Admin nur das Ziel des Kurzlinks „gotteswort" ändern, die Shorts bleiben unverändert.

-- 1. Kurzlink in den Shorts -> Gesamtvortrag bei YouTube
INSERT INTO campaign_urls
    (name, url_type, slug, target_url, utm_source, utm_medium, utm_campaign, utm_content, notes, created_by)
SELECT
    'Gottes Wort – Shorts → Gesamtvortrag (YouTube)', 'offline', 'gotteswort',
    'https://youtu.be/8N5WuDm6PKM', 'shorts', 'social', 'gottes_wort_2026', 'zum_vortrag',
    'Wird gegen Ende jedes Shorts/Reels im Balken eingeblendet. Bei neuem YouTube-Upload hier die Ziel-URL ändern.',
    'ue.probst@gmail.com'
WHERE NOT EXISTS (SELECT 1 FROM campaign_urls WHERE slug = 'gotteswort');

-- 2. Direktlink für die YouTube-Beschreibung des Langvideos
INSERT INTO campaign_urls
    (name, url_type, slug, target_url, utm_source, utm_medium, utm_campaign, utm_content, notes, created_by)
SELECT
    'Gottes Wort – YouTube-Beschreibung Langvideo', 'online', NULL,
    'vers-patenschaft.de/vortrag', 'youtube', 'social', 'gottes_wort_2026', 'beschreibung',
    'In die Beschreibung des Langvideos eintragen („Vortrag buchen").', 'ue.probst@gmail.com'
WHERE NOT EXISTS (SELECT 1 FROM campaign_urls WHERE name = 'Gottes Wort – YouTube-Beschreibung Langvideo');

-- 3. Direktlink für den Instagram-Bio-Link
INSERT INTO campaign_urls
    (name, url_type, slug, target_url, utm_source, utm_medium, utm_campaign, utm_content, notes, created_by)
SELECT
    'Gottes Wort – Instagram-Bio', 'online', NULL,
    'vers-patenschaft.de/vortrag', 'instagram', 'social', 'gottes_wort_2026', 'bio',
    'Als Link in der Instagram-Bio, solange die Reels laufen.', 'ue.probst@gmail.com'
WHERE NOT EXISTS (SELECT 1 FROM campaign_urls WHERE name = 'Gottes Wort – Instagram-Bio');

-- Verify
SELECT url_type, slug, utm_source, utm_content, target_url
FROM campaign_urls
WHERE utm_campaign = 'gottes_wort_2026'
ORDER BY url_type, slug;
