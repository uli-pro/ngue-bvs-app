ROLLE: Bitte agiere als erfahrener Web-Designer und Front-End-Engineer. 

AUFGABE: Erstelle mir das grundlegende Design für meine Webseite unter Flaks.

KONTEXT: Ich will dieses Projekt in Flask entwickeln, wie ich es in Harvards cs50 gelernt habe. Bitte schau dir für das Design als Beispiel das Projekt Finance an: /Users/ulrichprobst/Nextcloud/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/week09-flask/finance. Beachte insbesondere den Inhalt der Ordner /static und /templates. 

Genau wie beim Finance-Projekt will ich 

- eine layout.html für das grundlegende Design
- Inhaltsseiten mit statischen und dynamisch erzeugten Elementen innerhalb der Layout-Form.

- Die Boostrap-Library benutzen
- eine cleane Navbar haben 

Allerdings sollen sich die Design-Farben und die Design-Sprache an die offizielle Webseite der NGÜ anlehnen: https://neuegenferuebersetzung.de/das-ubersetzungsprojek/

#### Farbpalette

- **Primärfarbe (Rot)**: `#dd3333` - Akzentfarbe für CTAs und wichtige Elemente
- **Sekundärfarbe (Dunkelgrau)**: `#323334` - Navigation und Überschriften; Footer und anderer dunkler Hintergrund für inverse Dartstellung
- **Textfarbe**: `#333333` - Haupttext
- **Textfarbe (Sekundär)**: `#666666` - Beschreibungen und Meta-Informationen
- **Textfarbe (Tertiär): ** `#ffffff`- auf Footer und anderem dunklen Hintergrudn
- **Hintergrund**: `#ffffff` - Haupthintergrund
- **Hintergrund (Sekundär)**: `#f5f5f5` - Abschnitte und Karten

- **Erfolg**: `#c60338` - Bestätigungen, Fehlermeldungen, Informationen
- **Warnung**: `#d8c5ca` - Hinweise Hintergrund

#### Schriftarten

```css
--font-family-primary: 'Poppins', sans-serif;
--font-family-heading: 'Poppins', sans-serif;
--font-family-secondary: 'Montserrat', sans-serif;
--font-family-heading-secondary: 'Montserrat', sans-serif;
--font-family-fallback: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'Courier New', Courier, monospace;
```



KONKRETE SCHRITTE: 

1. Erstelle eine layout.html mit Navbar, Footer, mobile-first-design und dem grundsätzlich nötigen Java-Script (Verwende bootstrap!)
2. Erstelle eine passendes styles.css
3. Erstelle eine Index.html unter Verwendung der Inhalte von '/Users/ulrichprobst/Nextcloud/A_Projekte/4 Probst Dienstleistungen/Software-Entwicklung/harvard-cs50/ngue-bvs-app/content/seiten'

4. Speichere alles unter /design/claude-entwurf

   



----

## 2.Prompt

Bitte lies dir nun /docs/wireframes-complete-v1.md sowie /content genau durch und erstelle alle nötigen Seiten mit den  Verlinkungen. Wenn sich die Angaben in der wireframes-Datei und  den Content-Dateien widersprechen, dann bevorzuge /content. 

Verwende statt der dynamisch erstellten Inhalte einfache Platzhalter. 

Bau die gesamte Seitenstruktur auf, so dass man alle Seiten anschauen kann - halt ohne dynamische Funktionalität.

Beachte: 
- Bitte vergiss nicht erstelle die Unterseiten und Unter-Unterseiten für die verschiedenen Spendenarten: Als Einzelperson, Als Gruppe und Als Geschenk. 
- Bitte erstelle Dummy-zertifikate und Spendenbescheinigungen für jeden Use-Case (Einzelspende, Gruppespende, Geschenk-Spende) und stelle sie auf den enstprechenden Unterseiten zur Verfügung. 
- Bitte erstelle Seiten für jeden deiner Links im Footer. Nutze dazu die Inhalte in /content.