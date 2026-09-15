-- Rollback zu 010: Kurzlinks der Kampagne gottes_wort_2026 entfernen
DELETE FROM campaign_urls WHERE utm_campaign = 'gottes_wort_2026';
SELECT COUNT(*) AS verbleibend FROM campaign_urls WHERE utm_campaign = 'gottes_wort_2026';
