# Hybrid Search Test Report

**Modell**: paraphrase-multilingual-mpnet-base-v2
**Datum**: 02.08.2025 08:00
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
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PRO.29.20 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
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
2. LAM.3.24 (Score: 0.174)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.580
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
3. PSA.125.1 (Score: 0.164)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.545

#### Query: 'Glaube Hoffnung Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. LAM.3.24 (Score: 0.152)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.506
2. ECC.3.8 (Score: 0.133)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.444
3. DAN.12.1 (Score: 0.118)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.395

## Test 2: Ganze Verse als Query

### Zusammenfassung
- Hybrid am besten: 0/5
- Vektor besser als Keyword: 5/5
- Keyword besser als Vektor: 0/5

### Beispiele

**Query-Vers**: JOB.41.31
Text: (041-23) Es macht die Tiefe sieden wie einen Kessel, macht das Meer zu einem Salbentopf....

**Ähnlichste Verse (Hybrid):**
1. PRO.1.9: Denn sie sind ein schöner Kranz für dein Haupt und ein Geschmeide um deinen Hals...
2. JER.48.44: Wer dem Grauen entrinnt, wird in die Grube fallen; und wer aus der Grube heraufs...
3. JER.48.26: Machet es trunken; denn es hat großgetan wider den HERRN! Darum soll Moab in sei...

**Query-Vers**: JOB.42.13
Text: Er bekam auch sieben Söhne und drei Töchter....

**Ähnlichste Verse (Hybrid):**
1. JOB.42.15: Und es wurden im ganzen Lande keine so schönen Weiber gefunden wie Hiobs Töchter...

