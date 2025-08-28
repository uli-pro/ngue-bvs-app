# PDF Phase 1: Template-Struktur erstellen

**Status:** TODO  
**Priorität:** Hoch  
**Abhängigkeiten:** Keine  
**Geschätzte Zeit:** 4-6 Stunden

## Überblick

Diese Phase erstellt die HTML/CSS-Templates für WeasyPrint-basierte PDF-Generierung. Alle Templates verwenden das vorhandene certificate-background.png und präzise CSS-Positionierung.

## Aufgaben-Checkliste

### 1. Verzeichnisstruktur anlegen

- [ ] **Verzeichnis erstellen**: `templates/certificates/`
- [ ] **Verzeichnis erstellen**: `static/certificates/`
- [ ] **Hintergrundbild kopieren**: certificate-background.png nach `static/certificates/`
- [ ] **CSS-Verzeichnis**: `static/certificates/css/`

### 2. Basis-Template erstellen

- [ ] **Datei erstellen**: `templates/certificates/base_certificate.html`
- [ ] **A4-Format definieren**: 210mm x 297mm
- [ ] **Hintergrundbild einbinden**: Über CSS background-image
- [ ] **Print-CSS konfigurieren**: Ränder, Seitenumbrüche
- [ ] **Schriften definieren**: Arial/Times New Roman Fallbacks

#### Code-Vorlage base_certificate.html:
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>NGÜ Zertifikat</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='certificates/css/certificate_styles.css') }}">
    <style>
        @page {
            size: A4;
            margin: 0;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Times New Roman', serif;
            background-image: url('{{ background_image_path }}');
            background-size: cover;
            background-repeat: no-repeat;
            width: 210mm;
            height: 297mm;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        {% block certificate_content %}{% endblock %}
    </div>
</body>
</html>
```

### 3. Zertifikats-Templates erstellen

#### 3.1 Persönliches Zertifikat

- [ ] **Datei erstellen**: `templates/certificates/personal_certificate.html`
- [ ] **Template-Vererbung**: Erbt von base_certificate.html
- [ ] **Textfelder positionieren**: Absolutes Positioning für alle Variablen
- [ ] **Ein-/Mehrere-Verse-Logic**: Bedingte Anzeige

#### Code-Vorlage personal_certificate.html:
```html
{% extends "certificates/base_certificate.html" %}

{% block certificate_content %}
<div class="certificate-content">
    <!-- Datum - rechts oben -->
    <div class="date-field">
        Ausgestellt am {{ donation.completed_at.strftime('%d.%m.%Y') }}
    </div>
    
    <!-- Haupttext -->
    <div class="main-text">
        <p>Hiermit bestätigen wir:</p>
        
        <p class="donor-name">
            {{ person_snapshot.first_name }} {{ person_snapshot.last_name }}
        </p>
        
        <p>hat durch eine Spende von {{ "%.2f"|format(donation.amount) }} €</p>
        
        {% if verses|length == 1 %}
            <p>die Übersetzung des folgenden Bibelverses ermöglicht:</p>
            <div class="verse-text">
                {{ verses[0].reference }}<br>
                {{ verses[0].text }}
            </div>
        {% else %}
            <p>die Übersetzung der folgenden Bibelverse ermöglicht:</p>
            {% for verse in verses %}
                <div class="verse-text">
                    {{ verse.reference }}<br>
                    {{ verse.text }}
                </div>
            {% endfor %}
        {% endif %}
    </div>
</div>
{% endblock %}
```

#### 3.2 Gruppenzertifikat

- [ ] **Datei erstellen**: `templates/certificates/group_certificate.html`
- [ ] **Gruppenname-Logic**: `group_article` + `group_name` verwenden
- [ ] **Template-Vererbung**: Von base_certificate.html

#### Code-Vorlage group_certificate.html:
```html
{% extends "certificates/base_certificate.html" %}

{% block certificate_content %}
<div class="certificate-content">
    <div class="date-field">
        Ausgestellt am {{ donation.completed_at.strftime('%d.%m.%Y') }}
    </div>
    
    <div class="main-text">
        <p>Hiermit bestätigen wir:</p>
        
        <p class="donor-name">
            {{ donation.donation_details.group_article }} {{ donation.donation_details.group_name }}
        </p>
        
        <p>hat durch eine Spende von {{ "%.2f"|format(donation.amount) }} €</p>
        
        <!-- Rest wie personal_certificate -->
    </div>
</div>
{% endblock %}
```

#### 3.3 Geschenkzertifikat

- [ ] **Datei erstellen**: `templates/certificates/gift_certificate.html`
- [ ] **Beschenkten-Name**: `recipient_first_name` + `recipient_last_name`
- [ ] **Angepasster Text**: "im Namen von..."

#### Code-Vorlage gift_certificate.html:
```html
{% extends "certificates/base_certificate.html" %}

{% block certificate_content %}
<div class="certificate-content">
    <div class="date-field">
        Ausgestellt am {{ donation.completed_at.strftime('%d.%m.%Y') }}
    </div>
    
    <div class="main-text">
        <p>Hiermit bestätigen wir:</p>
        
        <p>Durch eine Spende von {{ "%.2f"|format(donation.amount) }} €<br>
           im Namen von {{ donation.donation_details.recipient_first_name }} {{ donation.donation_details.recipient_last_name }}</p>
        
        {% if verses|length == 1 %}
            <p>wurde die Übersetzung des folgenden Bibelverses ermöglicht:</p>
        {% else %}
            <p>wurde die Übersetzung der folgenden Bibelverse ermöglicht:</p>
        {% endif %}
        
        <!-- Verse-Logic wie bei personal_certificate -->
    </div>
</div>
{% endblock %}
```

### 4. Spendenbescheinigung-Template

- [ ] **Datei erstellen**: `templates/certificates/tax_receipt.html`
- [ ] **Separates Layout**: Eigenständiges Template (nicht von base ererbend)
- [ ] **Formular-Style**: Kästchen und Linien
- [ ] **Stiftungsdaten**: Fest eingebaute Peter-Schöffer-Stiftung Daten

#### Code-Vorlage tax_receipt.html:
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Spendenbescheinigung</title>
    <style>
        @page {
            size: A4;
            margin: 20mm;
        }
        
        body {
            font-family: 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.3;
        }
        
        .form-box {
            border: 2px solid black;
            padding: 3mm;
            margin: 2mm 0;
            min-height: 8mm;
        }
        
        .checkbox {
            display: inline-block;
            width: 4mm;
            height: 4mm;
            border: 1px solid black;
            margin-right: 2mm;
        }
        
        .checked {
            background-color: black;
            color: white;
            text-align: center;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="tax-receipt">
        <h1>Bestätigung über Geldzuwendungen</h1>
        <p><em>im Sinne des § 10b des Einkommensteuergesetzes an inländische Stiftungen des privaten Rechts</em></p>
        
        <!-- Stiftungsdaten -->
        <div class="form-box">
            <strong>Peter-Schöffer-Stiftung</strong><br>
            Wormser Weg 17<br>
            67574 Osthofen<br>
            StNr. 111 111 111
        </div>
        
        <!-- Spenderdaten -->
        <div class="form-box">
            <strong>Name und Anschrift des Zuwendenden:</strong><br>
            {{ person_snapshot.first_name }} {{ person_snapshot.last_name }}<br>
            {{ person_snapshot.street }} {{ person_snapshot.house_number }}<br>
            {{ person_snapshot.postal_code }} {{ person_snapshot.city }}
        </div>
        
        <!-- Spendenbetrag -->
        <div class="form-box">
            <strong>Betrag der Zuwendung:</strong> {{ "%.2f"|format(donation.amount) }} €<br>
            <strong>- in Buchstaben -</strong> {{ amount_in_words }} Euro
        </div>
        
        <!-- Spendendatum -->
        <div class="form-box">
            <strong>Tag der Zuwendung:</strong> {{ donation.completed_at.strftime('%d. %B %Y') }}
        </div>
        
        <!-- Checkboxen -->
        <p>
            Es handelt sich um den Verzicht auf Erstattung von Aufwendungen 
            <span class="checkbox">☐</span> Ja  
            <span class="checkbox checked">☑</span> Nein
        </p>
        
        <!-- Weitere Formularfelder... -->
    </div>
</body>
</html>
```

### 5. CSS-Styles erstellen

- [ ] **Datei erstellen**: `static/certificates/css/certificate_styles.css`
- [ ] **A4-Dimensions**: Exakte mm-Angaben
- [ ] **Positioning**: Absolute Koordinaten für alle Textfelder
- [ ] **Print-Optimierung**: @media print rules

#### Code-Vorlage certificate_styles.css:
```css
/* A4-Format mit korrekten Dimensionen */
.certificate-container {
    width: 210mm;
    height: 297mm;
    position: relative;
    margin: 0;
    padding: 0;
}

/* Datum rechts oben */
.date-field {
    position: absolute;
    top: 25mm;
    right: 25mm;
    font-size: 12pt;
    color: #333;
}

/* Haupttext-Bereich */
.main-text {
    position: absolute;
    top: 120mm;
    left: 25mm;
    width: 160mm;
    text-align: center;
    line-height: 1.6;
}

/* Spendername */
.donor-name {
    font-size: 18pt;
    font-weight: bold;
    color: #2c5f8f;
    margin: 15mm 0;
    text-transform: uppercase;
}

/* Bibelverse */
.verse-text {
    margin: 10mm 0;
    padding: 5mm;
    font-style: italic;
    font-size: 14pt;
    border-left: 3px solid #f4a261;
    background-color: rgba(244, 162, 97, 0.1);
}

/* Print-Optimierung */
@media print {
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    
    @page {
        margin: 0;
        size: A4;
    }
}
```

## Datenfelder-Mapping (Korrekt)

### Person-Daten (aus person_snapshot oder person):
- **Vorname**: `person_snapshot['first_name']` oder `person.first_name`
- **Nachname**: `person_snapshot['last_name']` oder `person.last_name`
- **Straße**: `person_snapshot['street']` oder `person.street`
- **Hausnummer**: `person_snapshot['house_number']` oder `person.house_number`
- **PLZ**: `person_snapshot['postal_code']` oder `person.postal_code`
- **Stadt**: `person_snapshot['city']` oder `person.city`

### Spenden-Daten:
- **Betrag**: `donation.amount` (Decimal)
- **Datum**: `donation.completed_at` oder `donation.created_at`
- **Typ**: `donation.donation_type`

### Gruppen-Daten (wenn donation_type == 'gruppe'):
- **Artikel**: `donation.donation_details['group_article']`
- **Gruppenname**: `donation.donation_details['group_name']`

### Geschenk-Daten (wenn donation_type == 'geschenk'):
- **Beschenkter Vorname**: `donation.donation_details['recipient_first_name']`
- **Beschenkter Nachname**: `donation.donation_details['recipient_last_name']`

### Vers-Daten:
- **Referenz**: `verse.reference`
- **Text**: `verse.text`

## Testing-Hinweise

### Template-Testing (ohne Service):
```python
# Test-Context für Template-Rendering
test_context = {
    'donation': test_donation,
    'person_snapshot': test_donation.person_snapshot,
    'verses': [test_donation.verse],
    'background_image_path': '/static/certificates/certificate-background.png'
}

# Render mit Flask
with app.app_context():
    html = render_template('certificates/personal_certificate.html', **test_context)
    print(html)  # Debug-Ausgabe
```

## Nächste Schritte

Nach Abschluss dieser Phase:
1. **Phase 2**: PDFGeneratorService implementieren
2. **Templates testen**: Mit Dummy-Daten rendern
3. **WeasyPrint-Integration**: HTML zu PDF konvertieren

## Häufige Probleme

### WeasyPrint-spezifische Probleme:
- **Schriften**: System-Schriften verwenden, keine Web-Fonts
- **Bilder**: Absolute Pfade oder data: URLs
- **CSS**: Nicht alle CSS3-Features unterstützt
- **JavaScript**: Wird nicht ausgeführt

### Lösungen:
```css
/* Schrift-Fallbacks */
font-family: 'Times New Roman', 'Liberation Serif', serif;

/* Bild-Einbindung */
background-image: url('file:///absolute/path/to/image.png');
```