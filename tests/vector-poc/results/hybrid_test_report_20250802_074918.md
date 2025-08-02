# Hybrid Search Test Report

**Modell**: paraphrase-multilingual-mpnet-base-v2
**Datum**: 02.08.2025 07:49
**Anzahl Verse**: 1000

## Test 1: Keyword-Queries

### Performance
- Keyword-Suche: 0.001s
- Vektor-Suche: 0.068s
- Hybrid-Suche: 0.023s

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
2. GEN.37.3 (Score: 0.560)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. PSA.119.47 (Score: 0.560)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Hoffnung'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PRO.29.20 (Score: 0.843)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.475
2. HOS.2.15 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. LAM.3.21 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Gott Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.096
   - Vektor-Score: 0.000
2. DAN.9.4 (Score: 0.165)
   - Keyword-Score: 0.023
   - Vektor-Score: 0.000
3. PRO.14.10 (Score: 0.162)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.540

#### Query: 'ewiges Leben'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. DAN.12.2 (Score: 0.700)
   - Keyword-Score: 0.185
   - Vektor-Score: 0.000
2. PSA.119.144 (Score: 0.288)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
3. LAM.3.31 (Score: 0.165)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.550

#### Query: 'Glaube Hoffnung Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PRO.14.30 (Score: 0.152)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.508
2. PRO.14.10 (Score: 0.148)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.493
3. HOS.14.4 (Score: 0.133)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.444

## Test 2: Ganze Verse als Query

### Zusammenfassung
- Hybrid am besten: 0/5
- Vektor besser als Keyword: 5/5
- Keyword besser als Vektor: 0/5

### Beispiele

**Query-Vers**: DAN.8.3
Text: Und ich hob meine Augen auf und schaute und siehe, da stand vor dem Flusse ein Widder, der hatte zwe...

**Ähnlichste Verse (Hybrid):**
1. DAN.12.5: Und ich, Daniel, schaute und siehe, da standen zwei andere da; einer an diesem, ...
2. DAN.7.8: Während ich achtgab auf die Hörner, siehe, da brach ein anderes, kleines Horn zw...
3. DAN.7.20: auch betreffs der zehn Hörner auf seinem Haupte und über das andere, das hervorb...

**Query-Vers**: LAM.3.21
Text: Dieses aber will ich meinem Herzen vorhalten, darum will ich Hoffnung fassen:...

**Ähnlichste Verse (Hybrid):**
1. PSA.119.81: Meine Seele schmachtet nach deinem Heil; ich harre auf dein Wort....
2. PSA.51.10: (051-12) Schaffe mir, o Gott, ein reines Herz und gib mir von neuem einen gewiss...
3. PSA.119.112: Ich habe mein Herz geneigt, deine Satzungen auf ewig zu erfüllen....

