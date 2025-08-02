# Hybrid Search Test Report

**Modell**: paraphrase-multilingual-mpnet-base-v2
**Datum**: 02.08.2025 07:56
**Anzahl Verse**: 1000

## Test 1: Keyword-Queries

### Performance
- Keyword-Suche: 0.001s
- Vektor-Suche: 0.068s
- Hybrid-Suche: 0.021s

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
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
2. PSA.119.127 (Score: 0.690)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.433
3. GEN.37.3 (Score: 0.560)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Hoffnung'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. LAM.3.29 (Score: 0.877)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.589
2. PRO.29.20 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000
3. HOS.2.15 (Score: 0.700)
   - Keyword-Score: 0.061
   - Vektor-Score: 0.000

#### Query: 'Gott Liebe'
**Überlappung Keyword/Vektor**: 1 Verse

**Top 3 Hybrid-Ergebnisse:**
1. HOS.3.1 (Score: 0.700)
   - Keyword-Score: 0.096
   - Vektor-Score: 0.000
2. DAN.9.4 (Score: 0.350)
   - Keyword-Score: 0.023
   - Vektor-Score: 0.618
3. PRO.15.11 (Score: 0.179)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.597

#### Query: 'ewiges Leben'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. DAN.12.2 (Score: 0.700)
   - Keyword-Score: 0.185
   - Vektor-Score: 0.000
2. PSA.119.144 (Score: 0.288)
   - Keyword-Score: 0.076
   - Vektor-Score: 0.000
3. PSA.119.111 (Score: 0.168)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.558

#### Query: 'Glaube Hoffnung Liebe'
**Überlappung Keyword/Vektor**: 0 Verse

**Top 3 Hybrid-Ergebnisse:**
1. PSA.119.25 (Score: 0.166)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.552
2. PSA.119.28 (Score: 0.151)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.504
3. PSA.119.81 (Score: 0.149)
   - Keyword-Score: 0.000
   - Vektor-Score: 0.496

## Test 2: Ganze Verse als Query

### Zusammenfassung
- Hybrid am besten: 0/5
- Vektor besser als Keyword: 5/5
- Keyword besser als Vektor: 0/5

### Beispiele

**Query-Vers**: PSA.119.11
Text: Ich habe dein Wort in meinem Herzen geborgen, auf daß ich nicht an dir sündige....

**Ähnlichste Verse (Hybrid):**
1. PSA.119.17: Gewähre deinem Knecht, daß ich lebe und dein Wort befolge!...
2. PSA.119.34: Unterweise mich, so will ich dein Gesetz bewahren und es von ganzem Herzen befol...
3. PSA.119.44: Und ich will dein Gesetz stets bewahren, immer und ewiglich....

**Query-Vers**: LAM.5.4
Text: Unser Wasser trinken wir um Geld, unser Holz kommt uns gegen Bezahlung zu....

**Ähnlichste Verse (Hybrid):**
1. JER.10.3: Denn die Satzungen der Heiden sind nichtig. Denn ein Holz ist's, das man im Wald...
2. ECC.2.6: Ich machte mir Wasserteiche, um daraus den sprossenden Baumwald zu tränken....
3. JER.49.12: Denn so spricht der HERR: Siehe, die, welche nicht dazu verurteilt waren, den Ke...

