# Geschenk-Versand-Option - Formular-Texte

## Überschrift-Bereich:
**"Versand-Option für Ihr Geschenk"**

## Erklärungstext:
Wie möchten Sie das Zertifikat übermitteln?

## Radio-Button Optionen:

### Option 1 (Standard - vorausgewählt):
☑️ **Zertifikat direkt an Empfänger senden**  
*Das personalisierte Zertifikat wird sofort per E-Mail an den Empfänger gesendet. Sie erhalten eine Kopie sowie Ihre Spendenbescheinigung.*

### Option 2:
☐ **Zertifikat an mich senden (für persönliche Übergabe)**  
*Sie erhalten das Zertifikat per E-Mail und können es bei passender Gelegenheit persönlich überreichen. Der Empfänger wird nicht benachrichtigt.*

## Zusätzlicher Hinweistext:
ℹ️ **Hinweis:** Bei der persönlichen Übergabe-Option können Sie das Timing der Geschenk-Übergabe selbst bestimmen.

---

## Technische Implementierung:

### HTML-Struktur:
```html
<fieldset class="geschenk-versand">
    <legend>Versand-Option für Ihr Geschenk</legend>
    <p class="help-text">Wie möchten Sie das Zertifikat übermitteln?</p>
    
    <div class="radio-group">
        <label class="radio-option">
            <input type="radio" name="versand_option" value="direkt" checked>
            <span class="radio-label">Zertifikat direkt an Empfänger senden</span>
            <span class="help-text">Das personalisierte Zertifikat wird sofort per E-Mail an den Empfänger gesendet. Sie erhalten eine Kopie sowie Ihre Spendenbescheinigung.</span>
        </label>
        
        <label class="radio-option">
            <input type="radio" name="versand_option" value="persoenlich">
            <span class="radio-label">Zertifikat an mich senden (für persönliche Übergabe)</span>
            <span class="help-text">Sie erhalten das Zertifikat per E-Mail und können es bei passender Gelegenheit persönlich überreichen. Der Empfänger wird nicht benachrichtigt.</span>
        </label>
    </div>
    
    <div class="info-box">
        <i class="icon-info"></i>
        <span>Bei der persönlichen Übergabe-Option können Sie das Timing der Geschenk-Übergabe selbst bestimmen.</span>
    </div>
</fieldset>
```

### Validierung:
- Pflichtfeld: Ja
- Standard-Auswahl: "direkt"
- JavaScript-Handling für E-Mail-Template-Auswahl erforderlich

### Auswirkungen auf E-Mail-Versand:
- **"direkt"**: Verwendet `geschenk-empfaenger.md` und `geschenk-schenker-mit-versand.md`
- **"persoenlich"**: Verwendet nur `geschenk-schenker-ohne-versand.md`