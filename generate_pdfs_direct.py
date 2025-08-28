#!/usr/bin/env python3
"""
Direct PDF Generator für NGÜ Zertifikate
Umgeht WeasyPrint Import-Probleme durch direkte Verwendung nach dem Import
"""

import os
import sys
import time
from datetime import datetime
from decimal import Decimal

def setup_weasyprint_env():
    """Setup environment for WeasyPrint"""
    os.environ['PKG_CONFIG_PATH'] = "/opt/homebrew/lib/pkgconfig"
    os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib"
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = "/opt/homebrew/lib"

def check_weasyprint():
    """Check if WeasyPrint can be imported"""
    try:
        import weasyprint
        print("✅ WeasyPrint successfully imported")
        return True
    except Exception as e:
        print(f"❌ WeasyPrint import failed: {e}")
        return False

def create_simple_pdf_test():
    """Create a simple PDF to test WeasyPrint functionality"""
    setup_weasyprint_env()
    
    if not check_weasyprint():
        print("❌ Cannot proceed without WeasyPrint")
        return False
    
    try:
        import weasyprint
        from weasyprint import HTML, CSS
        
        # Simple HTML test
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page { size: A4; margin: 20mm; }
                body { font-family: Arial, sans-serif; }
                h1 { color: #2c5f8f; text-align: center; }
                .content { margin: 40px 0; }
            </style>
        </head>
        <body>
            <h1>NGÜ Zertifikat - Test</h1>
            <div class="content">
                <p><strong>Test-Zertifikat</strong></p>
                <p>Dies ist ein Test-PDF, um zu prüfen, ob WeasyPrint korrekt funktioniert.</p>
                <p>Generiert am: """ + datetime.now().strftime('%d.%m.%Y %H:%M') + """</p>
            </div>
        </body>
        </html>
        """
        
        # PDF generieren
        docs_dir = os.path.join(os.getcwd(), 'docs')
        test_pdf_path = os.path.join(docs_dir, 'weasyprint_test.pdf')
        
        print("🔧 Generiere Test-PDF...")
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(test_pdf_path)
        
        # Prüfen ob Datei erstellt wurde
        if os.path.exists(test_pdf_path):
            file_size = os.path.getsize(test_pdf_path)
            print(f"✅ Test-PDF erstellt: {test_pdf_path} ({file_size} bytes)")
            return True
        else:
            print("❌ Test-PDF konnte nicht erstellt werden")
            return False
            
    except Exception as e:
        print(f"❌ PDF-Generierung fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_certificate_pdfs():
    """Generate all 4 certificate PDFs"""
    setup_weasyprint_env()
    
    if not check_weasyprint():
        return False
    
    # Import WeasyPrint after environment is set
    import weasyprint
    
    docs_dir = os.path.join(os.getcwd(), 'docs')
    print(f"📁 PDF-Zielverzeichnis: {docs_dir}")
    
    certificate_types = [
        {
            'name': 'Personal Certificate',
            'filename': 'ngue_personal_certificate_example.pdf',
            'html': create_personal_certificate_html()
        },
        {
            'name': 'Group Certificate', 
            'filename': 'ngue_group_certificate_example.pdf',
            'html': create_group_certificate_html()
        },
        {
            'name': 'Gift Certificate',
            'filename': 'ngue_gift_certificate_example.pdf', 
            'html': create_gift_certificate_html()
        },
        {
            'name': 'Tax Receipt',
            'filename': 'ngue_tax_receipt_example.pdf',
            'html': create_tax_receipt_html()
        }
    ]
    
    successful_pdfs = []
    
    for cert in certificate_types:
        print(f"📄 Generiere {cert['name']}...")
        
        try:
            # PDF-Pfad
            pdf_path = os.path.join(docs_dir, cert['filename'])
            
            # HTML zu PDF
            html_doc = weasyprint.HTML(string=cert['html'])
            html_doc.write_pdf(pdf_path)
            
            # Erfolgsprüfung
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"  ✅ Erstellt: {cert['filename']} ({file_size} bytes)")
                successful_pdfs.append(cert['filename'])
            else:
                print(f"  ❌ Fehler: {cert['filename']} nicht erstellt")
                
        except Exception as e:
            print(f"  ❌ Fehler bei {cert['name']}: {e}")
    
    print(f"\n🎉 PDF-Generierung abgeschlossen!")
    print(f"✅ {len(successful_pdfs)} von 4 PDFs erfolgreich erstellt:")
    for pdf in successful_pdfs:
        print(f"   • {pdf}")
    
    return len(successful_pdfs) > 0

def create_personal_certificate_html():
    """HTML für Personal Certificate"""
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 0;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Times New Roman', serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            width: 210mm;
            height: 297mm;
            position: relative;
        }
        
        .certificate-container {
            width: 210mm;
            height: 297mm;
            position: relative;
            border: 5px solid #2c5f8f;
            box-sizing: border-box;
        }
        
        .header {
            text-align: center;
            margin-top: 30mm;
        }
        
        .title {
            font-size: 24pt;
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 10mm;
        }
        
        .subtitle {
            font-size: 16pt;
            color: #666;
            margin-bottom: 20mm;
        }
        
        .main-content {
            text-align: center;
            margin: 0 25mm;
            line-height: 1.8;
        }
        
        .donor-name {
            font-size: 20pt;
            font-weight: bold;
            color: #2c5f8f;
            margin: 15mm 0;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .amount {
            font-size: 16pt;
            font-weight: bold;
            color: #d4a574;
        }
        
        .verse-section {
            margin: 20mm 0;
            padding: 10mm;
            background: rgba(255,255,255,0.8);
            border-left: 4px solid #d4a574;
        }
        
        .verse-reference {
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 5mm;
        }
        
        .verse-text {
            font-style: italic;
            font-size: 14pt;
            line-height: 1.6;
        }
        
        .date {
            position: absolute;
            top: 25mm;
            right: 25mm;
            font-size: 12pt;
        }
        
        .footer {
            position: absolute;
            bottom: 20mm;
            width: 100%;
            text-align: center;
            font-size: 10pt;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        <div class="date">
            Ausgestellt am """ + datetime.now().strftime('%d.%m.%Y') + """
        </div>
        
        <div class="header">
            <div class="title">ZERTIFIKAT</div>
            <div class="subtitle">NGÜ Bibelvers-Sponsoring</div>
        </div>
        
        <div class="main-content">
            <p>Hiermit bestätigen wir:</p>
            
            <div class="donor-name">Max Mustermann</div>
            
            <p>hat durch eine Spende von <span class="amount">100,00 €</span></p>
            <p>die Übersetzung des folgenden Bibelverses ermöglicht:</p>
            
            <div class="verse-section">
                <div class="verse-reference">Jesaja 43,1</div>
                <div class="verse-text">
                    So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: 
                    Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!
                </div>
            </div>
            
            <p>Wir danken herzlich für diese wertvolle Unterstützung der NGÜ-Bibelübersetzung.</p>
        </div>
        
        <div class="footer">
            Peter-Schöffer-Stiftung • NGÜ Bibelübersetzung
        </div>
    </div>
</body>
</html>"""

def create_group_certificate_html():
    """HTML für Group Certificate"""
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 0; }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Times New Roman', serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            width: 210mm;
            height: 297mm;
            position: relative;
        }
        .certificate-container {
            width: 210mm;
            height: 297mm;
            position: relative;
            border: 5px solid #2c5f8f;
            box-sizing: border-box;
        }
        .header {
            text-align: center;
            margin-top: 30mm;
        }
        .title {
            font-size: 24pt;
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 10mm;
        }
        .subtitle {
            font-size: 16pt;
            color: #666;
            margin-bottom: 20mm;
        }
        .main-content {
            text-align: center;
            margin: 0 25mm;
            line-height: 1.8;
        }
        .group-name {
            font-size: 20pt;
            font-weight: bold;
            color: #2c5f8f;
            margin: 15mm 0;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .amount {
            font-size: 16pt;
            font-weight: bold;
            color: #d4a574;
        }
        .verse-section {
            margin: 20mm 0;
            padding: 10mm;
            background: rgba(255,255,255,0.8);
            border-left: 4px solid #d4a574;
        }
        .verse-reference {
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 5mm;
        }
        .verse-text {
            font-style: italic;
            font-size: 14pt;
            line-height: 1.6;
        }
        .date {
            position: absolute;
            top: 25mm;
            right: 25mm;
            font-size: 12pt;
        }
        .footer {
            position: absolute;
            bottom: 20mm;
            width: 100%;
            text-align: center;
            font-size: 10pt;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        <div class="date">
            Ausgestellt am """ + datetime.now().strftime('%d.%m.%Y') + """
        </div>
        
        <div class="header">
            <div class="title">GRUPPEN-ZERTIFIKAT</div>
            <div class="subtitle">NGÜ Bibelvers-Sponsoring</div>
        </div>
        
        <div class="main-content">
            <p>Hiermit bestätigen wir:</p>
            
            <div class="group-name">Die Evangelische Gemeinde Berlin</div>
            
            <p>hat durch eine Spende von <span class="amount">100,00 €</span></p>
            <p>die Übersetzung des folgenden Bibelverses ermöglicht:</p>
            
            <div class="verse-section">
                <div class="verse-reference">Jesaja 43,1</div>
                <div class="verse-text">
                    So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: 
                    Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!
                </div>
            </div>
            
            <p>Wir danken der Gemeinde herzlich für diese wertvolle Unterstützung der NGÜ-Bibelübersetzung.</p>
        </div>
        
        <div class="footer">
            Peter-Schöffer-Stiftung • NGÜ Bibelübersetzung
        </div>
    </div>
</body>
</html>"""

def create_gift_certificate_html():
    """HTML für Gift Certificate"""
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 0; }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Times New Roman', serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            width: 210mm;
            height: 297mm;
            position: relative;
        }
        .certificate-container {
            width: 210mm;
            height: 297mm;
            position: relative;
            border: 5px solid #2c5f8f;
            box-sizing: border-box;
        }
        .header {
            text-align: center;
            margin-top: 30mm;
        }
        .title {
            font-size: 24pt;
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 10mm;
        }
        .subtitle {
            font-size: 16pt;
            color: #666;
            margin-bottom: 20mm;
        }
        .main-content {
            text-align: center;
            margin: 0 25mm;
            line-height: 1.8;
        }
        .recipient-name {
            font-size: 20pt;
            font-weight: bold;
            color: #d4a574;
            margin: 15mm 0;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .donor-info {
            font-size: 14pt;
            color: #666;
            margin-bottom: 10mm;
        }
        .amount {
            font-size: 16pt;
            font-weight: bold;
            color: #d4a574;
        }
        .verse-section {
            margin: 20mm 0;
            padding: 10mm;
            background: rgba(255,255,255,0.8);
            border-left: 4px solid #d4a574;
        }
        .verse-reference {
            font-weight: bold;
            color: #2c5f8f;
            margin-bottom: 5mm;
        }
        .verse-text {
            font-style: italic;
            font-size: 14pt;
            line-height: 1.6;
        }
        .date {
            position: absolute;
            top: 25mm;
            right: 25mm;
            font-size: 12pt;
        }
        .footer {
            position: absolute;
            bottom: 20mm;
            width: 100%;
            text-align: center;
            font-size: 10pt;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        <div class="date">
            Ausgestellt am """ + datetime.now().strftime('%d.%m.%Y') + """
        </div>
        
        <div class="header">
            <div class="title">GESCHENK-ZERTIFIKAT</div>
            <div class="subtitle">NGÜ Bibelvers-Sponsoring</div>
        </div>
        
        <div class="main-content">
            <p>Dieses Zertifikat wurde geschenkt an:</p>
            
            <div class="recipient-name">Anna Schmidt</div>
            
            <div class="donor-info">Geschenkt von: Max Mustermann</div>
            
            <p>Durch eine Spende von <span class="amount">100,00 €</span> wurde</p>
            <p>die Übersetzung des folgenden Bibelverses ermöglicht:</p>
            
            <div class="verse-section">
                <div class="verse-reference">Jesaja 43,1</div>
                <div class="verse-text">
                    So spricht der HERR, der dich geschaffen hat, Jakob, und der dich gebildet hat, Israel: 
                    Fürchte dich nicht, denn ich habe dich erlöst; ich habe dich bei deinem Namen gerufen, du bist mein!
                </div>
            </div>
            
            <p>Ein wertvolles Geschenk für die NGÜ-Bibelübersetzung.</p>
        </div>
        
        <div class="footer">
            Peter-Schöffer-Stiftung • NGÜ Bibelübersetzung
        </div>
    </div>
</body>
</html>"""

def create_tax_receipt_html():
    """HTML für Tax Receipt"""
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 15mm; }
        body {
            font-family: 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.4;
            margin: 0;
            padding: 0;
        }
        .header {
            text-align: center;
            margin-bottom: 20mm;
            border-bottom: 2px solid #000;
            padding-bottom: 10mm;
        }
        .title {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 5mm;
        }
        .subtitle {
            font-size: 12pt;
            color: #666;
        }
        .foundation-info {
            margin-bottom: 15mm;
        }
        .donor-info {
            margin-bottom: 15mm;
        }
        .donation-details {
            margin: 15mm 0;
            border: 1px solid #ccc;
            padding: 10mm;
        }
        .amount-section {
            display: flex;
            justify-content: space-between;
            margin: 10mm 0;
        }
        .signature-section {
            margin-top: 30mm;
            display: flex;
            justify-content: space-between;
        }
        .checkbox {
            width: 4mm;
            height: 4mm;
            border: 1px solid #000;
            display: inline-block;
            margin-right: 3mm;
        }
        .checked {
            background: #000;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10mm 0;
        }
        td, th {
            border: 1px solid #000;
            padding: 2mm;
            text-align: left;
        }
        th {
            background: #f0f0f0;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">SPENDENBESCHEINIGUNG</div>
        <div class="subtitle">nach § 10b des Einkommensteuergesetzes</div>
    </div>
    
    <div class="foundation-info">
        <strong>Zuwendungsempfänger:</strong><br>
        Peter-Schöffer-Stiftung<br>
        Wormser Weg 17<br>
        67574 Osthofen<br>
        <br>
        Steuernummer: 07/456/78901<br>
        Finanzamt: Worms
    </div>
    
    <div class="donor-info">
        <strong>Spender:</strong><br>
        Max Mustermann<br>
        Musterstraße 123<br>
        12345 Berlin
    </div>
    
    <table>
        <tr>
            <th>Betrag der Zuwendung</th>
            <th>Tag der Zuwendung</th>
            <th>Art der Zuwendung</th>
        </tr>
        <tr>
            <td><strong>100,00 EUR</strong><br>(in Worten: Einhundert Euro)</td>
            <td>""" + datetime.now().strftime('%d.%m.%Y') + """</td>
            <td>Geldspende</td>
        </tr>
    </table>
    
    <div class="donation-details">
        <strong>Verwendungszweck der Spende:</strong><br>
        NGÜ Bibelübersetzung - Sponsoring Bibelvers Jesaja 43,1<br>
        <br>
        <div class="checkbox checked"></div> Es handelt sich um den Verzicht auf Erstattung von Aufwendungen<br>
        <div class="checkbox"></div> Es handelt sich um eine Spende an eine steuerbegünstigte Körperschaft<br>
        <div class="checkbox checked"></div> Die Spende dient unmittelbar gemeinnützigen Zwecken
    </div>
    
    <p>
        <strong>Bestätigung:</strong><br>
        Wir sind berechtigt, für Zuwendungen zur Förderung der Bildung und Erziehung 
        sowie für wissenschaftliche Zwecke Zuwendungsbestätigungen auszustellen.
    </p>
    
    <div class="signature-section">
        <div>
            Osthofen, """ + datetime.now().strftime('%d.%m.%Y') + """
        </div>
        <div>
            _________________________<br>
            (Unterschrift des Zuwendungsempfängers)
        </div>
    </div>
    
    <div style="margin-top: 15mm; font-size: 9pt; color: #666;">
        <strong>Hinweis:</strong> Diese Bescheinigung ist nur gültig, wenn sie maschinell erstellt wurde. 
        Wer vorsätzlich oder grob fahrlässig eine unrichtige Zuwendungsbestätigung erstellt, 
        macht sich nach § 370 Abs. 1 Nr. 1 der Abgabenordnung strafbar.
    </div>
</body>
</html>"""

if __name__ == '__main__':
    print("🚀 Starte PDF-Generierung für NGÜ Zertifikate")
    print("=" * 50)
    
    # Environment setup
    setup_weasyprint_env()
    
    # Test WeasyPrint first
    print("🔧 Teste WeasyPrint-Funktionalität...")
    if not create_simple_pdf_test():
        print("\n❌ WeasyPrint-Test fehlgeschlagen. Kann nicht fortfahren.")
        sys.exit(1)
    
    print("\n📄 Generiere Zertifikat-PDFs...")
    success = generate_certificate_pdfs()
    
    if success:
        print(f"\n✅ PDF-Generierung erfolgreich abgeschlossen!")
        print(f"📁 PDFs wurden in ./docs/ gespeichert")
    else:
        print(f"\n❌ PDF-Generierung fehlgeschlagen")
        sys.exit(1)