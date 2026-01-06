-- ============================================================================
-- Migration: Ländererweiterung für NGÜ-App (Vereinfachte Version)
-- Datum: 2026-01-05
-- Beschreibung: Fügt Country-Support hinzu, migriert Bestandsdaten via PLZ
-- ============================================================================

BEGIN;

-- Schritt 1: Sicherstellen, dass Country-Column existiert
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='persons' AND column_name='country'
    ) THEN
        ALTER TABLE persons ADD COLUMN country VARCHAR(2) DEFAULT 'DE';
        RAISE NOTICE 'Column "country" wurde hinzugefügt';
    ELSE
        RAISE NOTICE 'Column "country" existiert bereits';
    END IF;
END $$;

-- Schritt 2: Migriere Bestandsdaten basierend auf PLZ-Format
-- Logik:
--   - 4 Ziffern → CH (Schweiz)
--   - 5 Ziffern → DE (Deutschland)
--   - Andere/Leer → DE (Fallback)

UPDATE persons
SET country = CASE
    WHEN postal_code ~ '^\d{4}$' THEN 'CH'  -- 4 Ziffern = Schweiz
    WHEN postal_code ~ '^\d{5}$' THEN 'DE'  -- 5 Ziffern = Deutschland
    ELSE 'DE'  -- Fallback für leere/ungültige PLZ
END
WHERE country IS NULL OR country = '' OR country = 'DE';

-- Logging: Wie viele Datensätze wurden geändert?
DO $$
DECLARE
    ch_count INTEGER;
    de_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO ch_count FROM persons WHERE country = 'CH';
    SELECT COUNT(*) INTO de_count FROM persons WHERE country = 'DE';
    RAISE NOTICE 'Migration abgeschlossen: % CH-Adressen, % DE-Adressen', ch_count, de_count;
END $$;

-- Schritt 3: Ensure NOT NULL und Default
ALTER TABLE persons ALTER COLUMN country SET DEFAULT 'DE';
ALTER TABLE persons ALTER COLUMN country SET NOT NULL;

-- Schritt 4: Performance-Index (falls nicht bereits vorhanden)
CREATE INDEX IF NOT EXISTS idx_persons_country ON persons(country);

COMMIT;

-- ============================================================================
-- POST-MIGRATION CHECKS
-- ============================================================================

-- Check 1: Verteilung der Länder
SELECT country, COUNT(*) as anzahl
FROM persons
GROUP BY country
ORDER BY anzahl DESC;

-- Check 2: Österreich-Kandidaten (manuell prüfen)
-- Österreichische PLZ sind 4-stellig, wurden also als CH klassifiziert
SELECT id, email, postal_code, city, country
FROM persons
WHERE country = 'CH'
  AND (city ILIKE '%wien%' OR city ILIKE '%graz%' OR city ILIKE '%salzburg%'
       OR city ILIKE '%innsbruck%' OR city ILIKE '%linz%')
ORDER BY created_at DESC;