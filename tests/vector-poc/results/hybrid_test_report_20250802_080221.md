# Hybrid Search Test Report

**Modell**: paraphrase-multilingual-mpnet-base-v2
**Datum**: 02.08.2025 08:02
**Anzahl Verse**: 1000

## Test 1: Keyword-Queries

### Performance
- Keyword-Suche: 0.001s
- Vektor-Suche: 0.066s
- Hybrid-Suche: 0.022s

### Detaillierte Ergebnisse

#### Query: 'Gott'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. ISA.37.4 (Score: 0.700)
   - Keyword-Score: 0.083
   - Vektor-Score: 0.000
2. PSA.51.14 (Score: 0.643)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
3. DAN.9.4 (Score: 0.643)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000

#### Query: 'Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
2. GEN.22.2 (Score: 0.560)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. PSA.119.163 (Score: 0.560)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Hoffnung'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. LAM.3.21 (Score: 0.930)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.767
2. PRO.29.20 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. JOB.41.9 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Gott Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.096
   - Vektor-Score: 0.000
2. PSA.51.17 (Score: 0.195)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.651
3. DAN.9.9 (Score: 0.193)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.643

#### Query: 'ewiges Leben'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. DAN.12.2 (Score: 0.700)
   - Keyword-Score: 0.185
   - Vektor-Score: 0.000
2. PSA.119.144 (Score: 0.467)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.595
3. PSA.119.160 (Score: 0.155)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.517

#### Query: 'Glaube Hoffnung Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. LAM.3.21 (Score: 0.220)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.734

## Test 2: Ganze Verse als Query

### Zusammenfassung
- Hybrid am besten: 0/5
- Vektor besser als Keyword: 5/5
- Keyword besser als Vektor: 0/5

### Beispiele

**Query-Vers**: JOB.42.17
Text: Und Hiob starb alt und lebenssatt....

**Ähnlichste Verse (Hybrid):**
1. JOB.32.1: Da hörten jene drei Männer auf, Hiob zu antworten, weil er in seinen Augen gerec...
2. JER.4.25: Ich schaute hin: und siehe, da war kein Mensch mehr, und alle Vögel des Himmels ...
3. PRO.14.14: Ein abtrünniges Herz bekommt genug von seinen eigenen Wegen und ebenso ein guter...

**Query-Vers**: JOB.32.1
Text: Da hörten jene drei Männer auf, Hiob zu antworten, weil er in seinen Augen gerecht war....

**Ähnlichste Verse (Hybrid):**
1. JOB.42.17: Und Hiob starb alt und lebenssatt....
2. DAN.8.12: Und ein Heer ward gesetzt über das beständige [Opfer], durch Übertretung; und di...
3. JER.4.25: Ich schaute hin: und siehe, da war kein Mensch mehr, und alle Vögel des Himmels ...

