-- Migration: Kurzlinks für das YouTube-Video „Gottes Wort in unserer Sprache" (Vortrag FeG Wetzlar)
-- Created: 2026-09-15
-- Purpose: 8 Kurzlinks (einer pro Short/Reel, Ziel: Landingpage /vortrag) plus ein Kurzlink,
--          der in den Shorts eingeblendet wird und auf den Gesamtvortrag verweist.
--
-- Ausführung (aus dem Projektverzeichnis ngue-bvs-app/):
--   Lokal:  sudo -u postgres psql ngue_bvs_db -f migrations/010_insert_gottes_wort_campaign_urls.sql
--   Server: docker exec -i ngue-postgres psql -U ngueapp -d ngue_db < ../migrations/010_insert_gottes_wort_campaign_urls.sql
--           (aus app-deployment/ heraus)
--
-- Idempotent: bereits vorhandene Slugs werden übersprungen (ON CONFLICT DO NOTHING).
-- Rollback: migrations/010_rollback_gottes_wort_campaign_urls.sql
--
-- NACH DEM YOUTUBE-UPLOAD: Ziel-URL des Kurzlinks „gotteswort" im Admin auf die
-- YouTube-URL des Gesamtvortrags ändern. Bis dahin zeigt er auf /vortrag.

INSERT INTO campaign_urls
    (name, url_type, slug, target_url, utm_source, utm_medium, utm_campaign, utm_content, notes, created_by)
VALUES
    ('Gottes Wort – Gesamtvortrag (Einblendung in Shorts)', 'offline', 'gotteswort',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'zum_vortrag',
     'Wird gegen Ende jedes Shorts/Reels im Balken eingeblendet. Ziel nach YouTube-Upload auf die Video-URL des Gesamtvortrags ändern.',
     'ue.probst@gmail.com'),
    ('Gottes Wort – Short 01 Ehepaar', 'offline', 'gotteswort1',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_01_ehepaar',
     'Datei short-01-ehepaar.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 02 Hebräer', 'offline', 'gotteswort2',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_02_hebraeer',
     'Datei short-02-hebraeer.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 03 Paulus', 'offline', 'gotteswort3',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_03_paulus',
     'Datei short-03-paulus.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 04 Klagelieder', 'offline', 'gotteswort4',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_04_klagelieder',
     'Datei short-04-klagelieder.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 05 Stille Post', 'offline', 'gotteswort5',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_05_stille_post',
     'Datei short-05-stille-post.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 06 Jesaja', 'offline', 'gotteswort6',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_06_jesaja',
     'Datei short-06-jesaja.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 07 Chef', 'offline', 'gotteswort7',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_07_chef',
     'Datei short-07-chef.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com'),
    ('Gottes Wort – Short 08 Kommunikation', 'offline', 'gotteswort8',
     'vers-patenschaft.de/vortrag', 'shorts', 'social', 'gottes_wort_2026', 'short_08_kommunikation',
     'Datei short-08-kommunikation.mp4 (YouTube Short + Instagram Reel)', 'ue.probst@gmail.com')
ON CONFLICT (slug) DO NOTHING;

-- Verify
SELECT slug, utm_content, target_url
FROM campaign_urls
WHERE utm_campaign = 'gottes_wort_2026'
ORDER BY slug;
