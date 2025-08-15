Für meine Bibelvers-Spenden App ('/Users/ulrichprobst/Library/Mobile Documents/com~apple~CloudDocs/1 Uli Dokumente/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app') testen wir verschiedene Suchalgorithmen, damit die User möglichst schnell und einfach einen Bibelvers finden, dessen Übersetzung sie mit ihrer Spende unterstützen wollen.  

Zum dachten wir daran, eine Keyword-Suche zu implementieren, die Postgresql's Volltextsuche nutzt. Das ermöglicht es dem User, zu bestimmten Themen schnell eine Liste von Bibelversehen zu bekommen. 

Zum anderen wollten wir eine semantische Suche implementieren für den Fall, dass der User einen bestimmten Bibelvers anhand der Referenz sucht, dann aber feststellen muss, dass dieser Vers bereits eine Sponsor hatte, und er deshalb ähnliche Verse als Alternativen braucht.

Beide Suchfunktionen liefern Ergebnisse, die nicht recht brauchbar sind. Das Problem ist: Die Leute suchen positive, ermutigende, aufbauende Bibelverse. Sowohl die Keyword-Suche als auch die semantische Suche finden aber oft Verse, die zwar dieselben Begriffe (Keywords) oder semantische ähnliche Begriffe (Semantische Suche) enthalten, aber insgesamt eine ngeative Aussage haben.  

Schau dir /tests/vector-poc/results/semantic_search_report_20250802_112117.md und /tests/vector-poc/results/final_keyword_test_report_20250802_110218.md einmal selbst an. 

Für den User wäre es vielleicht die einfachste Option, wenn wir eine Liste mit 1000 Versen hätten (das wäre ein realistisches Spendenziel), die nach "Positivitätsfaktor" gerankt sind. Der User bekommt bei seinem Besuch die Top drei positiven Verse, die noch ungesponsort sind,  direkt angezeigt und kann sich daraus einen aussuchen. Das wäre sozuagen die "Default Option". Wenn er will, kann er auch eine vorbereitete Referenz eingeben. Wenn er dort nicht fündig wird, kehrt er zu den Top drei zurück. Das funktioniert aber nur, wenn unser Ranking richtig gut ist. Kriegen wir das hin?