# Wireframe-Ergänzung: Gruppenspende-Feature

## Aktualisierung der Wireframes für Gruppenspende-Option

### 1. Spende-Art-Auswahl (Seite 5 - Vers-Bestätigung)

Die bestehende **Option 1** und **Option 2** werden erweitert zu drei Optionen:

```
┌─────────────────────────────────────────────────────────────────┐
│                   SPENDE-OPTIONEN                              │
│                                                                 │
│  Für wen möchten Sie diesen Vers sponsern?                    │
│                                                                 │
│  ○ Als Einzelperson (für mich selbst)                         │
│    [Icon: 👤] Sie erhalten Zertifikat und Spendenbescheinigung│
│                                                                 │
│  ○ Als Gruppe (Familie, Jugendgruppe, Verein, etc.)           │
│    [Icon: 👥] Gruppenzertifikat an Kontaktperson             │
│                                                                 │
│  ○ Als Geschenk für jemand anderen                            │
│    [Icon: 🎁] Empfänger erhält Geschenkzertifikat            │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Gruppendaten-Formular (Conditional Fields)

Wenn **"Als Gruppe"** ausgewählt wird:

```
┌─────────────────────────────────────────────────────────────────┐
│                   GRUPPENDATEN                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Artikel für Zertifikat: *                                  │ │
│  │ [Der      ▼]                                               │ │
│  │ ¤ Für grammatikalisch korrekte Formulierung                 │ │
│  │                                                             │ │
│  │ Gruppenname: *                                             │ │
│  │ [_________________________________]                       │ │
│  │ ¤ z.B. Familie Schmidt, Bibelkreis Musterhausen            │ │
│  │                                                             │ │
│  │ ┌─────────────────────────────────────────────────────────┐ │ │
│  │ │ 💡 BEISPIELE:                                          │ │ │
│  │ │ • Die Familie Schmidt                                   │ │ │
│  │ │ • Der Bibelkreis Musterhausen                          │ │ │  
│  │ │ • Das Volleyball-Team Musterdorf                       │ │ │
│  │ │ • Die Jungschar Mustertadt                             │ │ │
│  │ └─────────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │ ℹ️ Sie sind die Kontaktperson für diese Gruppenspende.    │ │
│  │    Das Zertifikat wird an Ihre E-Mail-Adresse gesendet.   │ │
│  │                                                             │ │
│  │ ⚠️ HINWEIS SPENDENBESCHEINIGUNG                            │ │
│  │    Für Gruppenspenden können wir keine automatische        │ │
│  │    Spendenbestätigung erstellen. Bei Bedarf kontaktieren  │ │
│  │    Sie uns bitte: spenden@peter-schoeffer-stiftung.de     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Mobile Wireframe - Gruppenspende

```
┌─────────────────────────┐
│    Spende-Art wählen    │
├─────────────────────────┤
│                         │
│ ○ Als Einzelperson      │
│   👤 Für mich selbst    │
│                         │
│ ● Als Gruppe            │
│   👥 Familie, Verein... │
│                         │
│   ┌───────────────────┐ │
│   │ Artikel: [Der ▼]  │ │
│   │                   │ │
│   │ Gruppenname:      │ │
│   │ [_______________] │ │
│   │                   │ │
│   │ ℹ️ Kontaktperson  │ │
│   │ ⚠️ Keine auto.    │ │
│   │   Spendenbeschein.│ │
│   └───────────────────┘ │
│                         │
│ ○ Als Geschenk          │
│   🎁 Für jemand anderen │
│                         │
├─────────────────────────┤
│      [WEITER →]         │
└─────────────────────────┘
```

### 4. Breadcrumb-Navigation Update

Bei Gruppenspende:

```
Home > Vers auswählen > Vers bestätigen > Gruppendaten > Kontaktdaten > Zahlung
```

### 5. Progress-Indicator Update

```
┌─────────────────────────────────────────────────────────────────┐
│               CHECKOUT-FORTSCHRITT                             │
│                                                                 │
│  ✓ Vers gewählt  →  ● Spendeart  →  ○ Kontaktdaten  →  ○ Zahlung│
│                                                                 │
│  Bei Gruppenspende:                                            │
│  ✓ Vers gewählt  →  ● Gruppendaten  →  ○ Kontaktdaten  →  ○ Zahlung│
└─────────────────────────────────────────────────────────────────┘
```

### 6. Zusammenfassung-Seite Update (Seite 7)

Für Gruppenspenden:

```
┌─────────────────────────────────────────────────────────────────┐
│                   IHRE GRUPPENSPENDE                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Gewählter Vers:                                            │ │
│  │ Jeremia 29,11                                              │ │
│  │ "Denn ich weiß die Gedanken, die ich über euch denke..."  │ │
│  │                                                             │ │
│  │ Spende-Art: Als Gruppe                                     │ │
│  │ Gruppe: Die Familie Schmidt                                │ │
│  │ Kontaktperson: Max Mustermann                              │ │
│  │                                                             │ │
│  │ Spendenbetrag: 100,00 €                                    │ │
│  │                                                             │ │
│  │ ⚠️ Hinweis: Spendenbestätigung nur auf Anfrage            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 7. Danke-Seite Update (Seite 8)

Für Gruppenspenden:

```
┌─────────────────────────────────────────────────────────────────┐
│                  ERFOLGS-NACHRICHT                             │
│                                                                 │
│                        🎉                                      │
│                                                                 │
│        "Vielen Dank für Ihre Gruppenspende!"                  │
│                                                                 │
│  Die Familie Schmidt hat erfolgreich den Vers Jeremia 29,11    │
│      gesponsert und trägt zur Finanzierung der NGÜ bei.        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     IHRE DOKUMENTE                             │
│                                                                 │
│  Ihre Dokumente stehen sofort zum Download bereit:             │
│                                                                 │
│  📄 [Gruppenzertifikat für "Die Familie Schmidt" herunterladen]│
│                                                                 │
│  ℹ️ Das Gruppenzertifikat wurde an Ihre E-Mail-Adresse        │
│      max.mustermann@example.com versendet.                     │
│                                                                 │
│  📧 Für eine Spendenbescheinigung kontaktieren Sie uns:       │
│      spenden@peter-schoeffer-stiftung.de                      │
└─────────────────────────────────────────────────────────────────┘
```

### 8. Dashboard-Update für Gruppenspenden

```
┌─────────────────────────────────────────────────────────────────┐
│                   IHRE GESPONSERTEN VERSE                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ 👥 Gruppenspende: Die Familie Schmidt                      │ │
│  │ Jeremia 29,11 | Gesponsert am: 06.08.2025                 │ │
│  │ "Denn ich weiß die Gedanken..."                           │ │
│  │ [Gruppenzertifikat] [Spendenbestätigung anfragen] [Details]│ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ 👤 Einzelspende                                            │ │
│  │ Psalm 23,1 | Gesponsert am: 15.07.2025                    │ │
│  │ "Der HERR ist mein Hirte..."                              │ │
│  │ [Zertifikat] [Spendenbescheinigung] [Details]             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Technische Implementierung (Wireframe-Logik)

### JavaScript Form Logic

```javascript
// Pseudo-Code für Conditional Fields
function onDonationTypeChange(selectedType) {
  hideAllConditionalFields();
  
  if (selectedType === 'group') {
    showElement('#group-data-fields');
    makeRequired(['group_article', 'group_name']);
    updateProgressStep('Gruppendaten eingeben');
  } else if (selectedType === 'gift') {
    showElement('#gift-data-fields');
    makeRequired(['recipient_name', 'recipient_email']);
  } else if (selectedType === 'self') {
    updateProgressStep('Kontaktdaten eingeben');
  }
  
  updateBreadcrumb();
  updateNextButtonText();
}

function validateGroupFields() {
  const article = getValue('#group_article');
  const groupName = getValue('#group_name');
  
  if (!article) {
    showError('Bitte wählen Sie einen Artikel aus');
    return false;
  }
  
  if (groupName.length < 2 || groupName.length > 80) {
    showError('Gruppenname muss 2-80 Zeichen haben');
    return false;
  }
  
  // Live-Vorschau aktualisieren
  updatePreview(`${article} ${groupName} hat durch eine Spende...`);
  
  return true;
}
```

### CSS Classes für Styling

```css
/* Gruppenspende-spezifische Styles */
.donation-type-group {
  border-left: 4px solid #28a745;
}

.group-fields {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-top: 15px;
}

.group-examples {
  background-color: #e3f2fd;
  border-radius: 6px;
  padding: 15px;
  margin: 10px 0;
}

.group-warning {
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  padding: 12px;
}

.group-icon {
  color: #28a745;
  margin-right: 8px;
}

@media (max-width: 768px) {
  .group-fields {
    padding: 15px;
    margin-top: 10px;
  }
  
  .group-examples {
    padding: 12px;
    font-size: 0.9em;
  }
}
```

## Zusammenfassung der Wireframe-Änderungen

1. **Spende-Art-Auswahl** erweitert von 2 auf 3 Optionen
2. **Conditional Fields** für Gruppendaten mit Artikel + Gruppenname
3. **Info-Boxen** für Kontaktperson-Rolle und Spendenbestätigung-Hinweis
4. **Mobile-Layout** angepasst für 3 Optionen
5. **Progress-Indikator** und **Breadcrumbs** erweitert
6. **Zusammenfassung** und **Danke-Seite** für Gruppenspenden
7. **Dashboard-Integration** mit Gruppenkennzeichnung

Die Wireframes bleiben konsistent mit dem bestehenden Design und fügen die Gruppenspende-Option nahtlos ein.