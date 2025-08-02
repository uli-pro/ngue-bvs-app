# Hybrid Search Test Report

**Modell**: paraphrase-multilingual-mpnet-base-v2
**Datum**: 02.08.2025 08:04
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
1. PSA.119.163 (Score: 0.709)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.497
2. PSA.119.47 (Score: 0.702)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.473
3. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000

#### Query: 'Hoffnung'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PRO.29.20 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
2. JOB.41.9 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. HOS.2.15 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Gott Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.096
   - Vektor-Score: 0.000
2. PRO.15.9 (Score: 0.189)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.632
3. DAN.9.4 (Score: 0.165)
   - Keyword-Score: 0.023
   - Vektor-Score: 0.000

#### Query: 'ewiges Leben'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. DAN.12.2 (Score: 0.875)
   - Keyword-Score: 0.185
   - Vektor-Score: 0.582
2. PSA.119.144 (Score: 0.288)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
3. ECC.1.4 (Score: 0.187)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.622

#### Query: 'Glaube Hoffnung Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PSA.119.50 (Score: 0.154)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.515
2. ECC.3.8 (Score: 0.133)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.444
3. ECC.2.1 (Score: 0.127)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.423

## Test 2: Ganze Verse als Query

### Zusammenfassung
- Hybrid am besten: 0/5
- Vektor besser als Keyword: 5/5
- Keyword besser als Vektor: 0/5

### Beispiele

**Query-Vers**: LAM.2.4
Text: Er spannte seinen Bogen wie ein Feind, stellte sich mit seiner Rechten wie ein Widersacher und macht...

**Ähnlichste Verse (Hybrid):**
1. LAM.2.3: In seinem grimmigen Zorn hieb er jedes Horn von Israel ab, zog vor dem Feinde se...
2. LAM.1.13: Er sandte ein Feuer von der Höhe, das alle meine Gebeine durchdrungen hat; er sp...
3. DAN.8.4: Ich sah, wie der Widder gegen Westen, Norden und Süden stieß und daß kein Tier v...

**Query-Vers**: PRO.28.12
Text: Wenn die Gerechten triumphieren, so ist die Herrlichkeit groß; wenn aber die Gottlosen obenauf komme...

**Ähnlichste Verse (Hybrid):**
1. PRO.29.6: In der Übertretung des Bösewichts ist ein Fallstrick; aber der Gerechte wird jau...
2. JOB.40.2: Will der Tadler mit dem Allmächtigen hadern? Wer Gott zurechtweisen will, antwor...
3. LAM.3.38: Geht nicht aus dem Munde des Höchsten das Böse und das Gute hervor?...

