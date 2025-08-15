Ich möchte gerne die > 11.000 Verse, die wir zum Sponsoring zur Verfügung stellen, mit einem Positivity-Score versehen. Diesen Score brauchen wir, um dem User stets Verse mit einer möglichst positiven Botschaft vorzuschlagen. 

Es ist wahrscheinlicher, dass er einen Vers sponsert, der sagt: "Denn ich weiß, was für Gedanken ich über euch habe, spricht der HERR, Gedanken des Friedens und nicht des Leides, euch eine Zukunft und eine Hoffnung zu geben." (Jer 29,11) als einen Vers sponsert, der lautet: "Er aber sprach: Greift sie lebendig! Und sie griffen sie lebendig und erstachen sie bei dem Brunnen am Hirtenhause, zweiundvierzig Mann; und er ließ nicht einen von ihnen übrig." (2KI.10.14).

Unsere Tests haben gezeigt, dass der einzige Weg zu einem einigermaßen brauchbaren Positivitäsranking über die Bewertung durch ein großes LLM führt. D.h. das LLM muss jeden einzelnen Vers anschauen und seine Positivität auf einer Skala von 1-100? (oder 1-10?) scoren. Dieser Score wird mit dem Vers im Database gespeichert. 

Die Verse mit einer positiven Botschaft sind in unserem Textkorpus klar in der Minderheit. Deshalb müssen wir bei unserem Scoring am positiven Ende und in der Mitte so differenziert wie möglich sein, um möglichst viele gut vermittelbare Verse zu identifizieren und differenziert zu ranken.

Angesichts der Beschränkung, aus dem Text eines einzigen (manchmal recht kurzen) Bibelverses ein verlässliches Positivitäts-Ranking zu errechnen,  ist das durchaus herausfordernd.

Bisherige Tests: 

In /tests/vector-poc/final_verses_data.json findest du Text und Referenz aller > 11.000 Verse. In /tests/positivity-scoring/llm_scorer_test.py findest du die Datei, die wir in unseren Tests verwendet haben, um ein Subset von 100 Versen zu testen.

Das für die LLMs verwendete Prompt lautete: 

````
self.system_prompt = """Du bist ein Experte für biblische Texte. Bewerte Bibelverse für eine Spenden-App, 
wo Menschen positive, ermutigende Verse sponsern können.

Bewertungskriterien:
- 90-100: Sehr positiv - Verheißungen, Segen, Trost, Ermutigung, Gottes Liebe
- 70-89: Positiv - Hoffnung, Glaube, Weisheit, gute Lehre
- 50-69: Neutral - Historisch, beschreibend, lehrreich ohne starke Emotion
- 30-49: Gemischt - Enthält sowohl positive als auch negative Elemente
- 10-29: Negativ - Warnungen, Tadel, Gericht
- 0-9: Sehr negativ - Tod, Zerstörung, Strafe, Zorn

Antworte NUR mit einer Zahl zwischen 0 und 100."""
````

Die besseren Resultate der beiden getesteten LLMs lieferte Anthropics Claude 3 Haiku. Vergleiche /tests/positivity-scoring/results/llm_anthropic_analysis_20250802_131928.md vs  llm_openai_analysis_20250802_133045.md



AUFGABE: 
Bitte entwickle einen Plan, wie wir alle 11.000 Verse mit einem zuverlässigen positivity-score versehen können. Bedenke unter anderem: 

- Wie muss das Prompt beschaffen sein? Welche (zustätzlichen?) Stichworte wären nötige Würden Beispiele helfen oder würden sie die Kosten unnötig in die Höhe treiben? 
- Da die Verse seriell hintereinander verarbeitet werden: Gäbe es einen Weg, den Inhalt der vorhergehenden 3-5 Verse und der nachfolgenden 1-2 Verse mit in die Bewertung einzubeziehen? 
- Welches LLM sollen wir verwenden? Reicht Claude 3 Haiku oder würde eine höheres Modell signifikant bessere Werte erzielen?
- Wie stellen wir sicher, dass 11.000 Anfragen alle abgearbeitet werden können, ohne dass es zu Ausfällen / Ablehnung der Anfragen seitens Anthropic kommt?

Denke darüber hinaus an Aspekte, die ich bisher nicht sehe. Plane gründlich und weise!