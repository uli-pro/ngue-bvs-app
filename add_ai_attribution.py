#!/usr/bin/env python3
"""
Script zum automatischen Hinzufügen von KI-Attribution zu Python-Dateien

Dieser Code wurde mit Unterstützung von Claude (Anthropic AI) entwickelt 
- konzipiert und geprompted von Ulrich Probst
"""

import os
import re
from pathlib import Path

# Attribution Text
ATTRIBUTION = """
Dieser Code wurde mit Unterstützung von Claude (Anthropic AI) entwickelt 
- konzipiert und geprompted von Ulrich Probst"""

def add_attribution_to_file(file_path):
    """Füge Attribution zu einer Python-Datei hinzu"""
    
    # Lese Datei
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prüfe, ob Attribution bereits vorhanden
    if "Claude (Anthropic AI)" in content:
        print(f"  ⏭️  Bereits vorhanden: {file_path.name}")
        return False
    
    # Suche nach erstem docstring
    lines = content.split('\n')
    
    # Finde Start des ersten docstrings
    docstring_start = -1
    docstring_end = -1
    in_docstring = False
    quote_type = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Überspinge Shebang und empty lines
        if stripped.startswith('#!') or stripped == '':
            continue
            
        # Finde docstring
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_start = i
                quote_type = stripped[:3]
                in_docstring = True
                
                # Single-line docstring
                if stripped.endswith(quote_type) and len(stripped) > 6:
                    docstring_end = i
                    break
            else:
                # Kein docstring gefunden, füge vor erste non-comment Zeile ein
                break
        else:
            # Suche Ende des docstrings
            if quote_type in line:
                docstring_end = i
                break
    
    if docstring_start >= 0 and docstring_end >= 0:
        # Füge Attribution am Ende des docstrings hinzu (vor dem schließenden """)
        new_lines = lines[:docstring_end]
        new_lines.append(ATTRIBUTION)
        new_lines.extend(lines[docstring_end:])
        
        # Schreibe Datei zurück
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print(f"  ✅ Aktualisiert: {file_path.name}")
        return True
    
    else:
        # Kein docstring gefunden - füge einfachen Kommentar am Anfang hinzu
        new_content = f"""#!/usr/bin/env python3
\"\"\"
{ATTRIBUTION.strip()}
\"\"\"

{content}"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ Docstring hinzugefügt: {file_path.name}")
        return True

def process_directory(directory):
    """Verarbeite alle Python-Dateien in einem Verzeichnis"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"❌ Verzeichnis nicht gefunden: {directory}")
        return 0
    
    print(f"\n📁 Verarbeite: {directory}")
    
    # Finde alle Python-Dateien
    python_files = list(directory.glob("*.py"))
    
    if not python_files:
        print("  ℹ️  Keine Python-Dateien gefunden")
        return 0
    
    updated_count = 0
    for py_file in python_files:
        if add_attribution_to_file(py_file):
            updated_count += 1
    
    return updated_count

def main():
    """Hauptfunktion"""
    print("🤖 KI-Attribution zu Python-Dateien hinzufügen")
    print("=" * 50)
    
    # Verzeichnisse zu verarbeiten
    directories = [
        "tests/vector-poc",
        "tests/positivity-scoring"
    ]
    
    total_updated = 0
    
    for directory in directories:
        updated = process_directory(directory)
        total_updated += updated
    
    print(f"\n✅ Fertig! {total_updated} Dateien aktualisiert")
    
    # Git-Commit Vorschlag
    if total_updated > 0:
        print(f"\n💡 Git-Commit Vorschlag:")
        print(f'git add tests/')
        print(f'git commit -m "docs: Add AI attribution to {total_updated} Python test files"')

if __name__ == "__main__":
    main()
