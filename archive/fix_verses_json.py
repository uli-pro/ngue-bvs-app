#!/usr/bin/env python3
"""
Verse JSON Cleaner - NGÜ Bibelvers-Sponsoring App

Fixes erroneous text prefixes like "(XX-XX)" or "(XXX-XX)" at the beginning of verse texts.

Usage:
    python fix_verses_json.py [--input FILE] [--output FILE] [--dry-run]
"""

import json
import re
import argparse
import os
from pathlib import Path

def fix_verse_text(text):
    """
    Remove erroneous verse reference patterns from the beginning of text.
    
    Patterns to remove:
    - (XX-XX) where X is a digit (0-9)
    - (XXX-XX) where X is a digit (0-9)
    - Any similar patterns with parentheses and dashes
    
    Args:
        text (str): Original verse text
        
    Returns:
        tuple: (cleaned_text, was_changed)
    """
    if not text or not isinstance(text, str):
        return text, False
    
    original_text = text
    
    # Pattern for any parentheses with numbers and dashes at the beginning
    # This matches: (12-34), (123-45), (1-2), (12-3), etc.
    # More flexible to catch all variations
    pattern = r'^\(\d+-\d+\)\s*'
    
    # Remove the pattern and any following whitespace
    cleaned_text = re.sub(pattern, '', text)
    
    # Check if anything was changed
    was_changed = cleaned_text != original_text
    
    return cleaned_text.strip(), was_changed

def analyze_verses_file(file_path):
    """Analyze the verses file to understand the data structure and issues."""
    
    print(f"Analyzing file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return None
    
    # Handle different JSON structures
    verses_data = None
    if 'scored_verses' in data:
        verses_data = data['scored_verses']
        data_key = 'scored_verses'
    elif 'verses' in data:
        verses_data = data['verses']
        data_key = 'verses'
    else:
        print("❌ Error: Unknown JSON structure. Expected 'verses' or 'scored_verses' key.")
        return None
    
    total_verses = len(verses_data)
    problematic_verses = []
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total verses: {total_verses}")
    print(f"   Data structure: {data_key}")
    
    # Check for problematic texts
    pattern = re.compile(r'^\(\d+-\d+\)')
    
    for i, verse in enumerate(verses_data):
        if 'text' in verse and isinstance(verse['text'], str):
            text = verse['text']
            if pattern.match(text):
                problematic_verses.append({
                    'index': i,
                    'reference': f"{verse.get('book', 'Unknown')} {verse.get('chapter', '?')},{verse.get('verse_number', verse.get('verse', '?'))}",
                    'original_text': text[:50] + "..." if len(text) > 50 else text,
                    'match': pattern.search(text).group()
                })
    
    print(f"   Problematic verses: {len(problematic_verses)}")
    
    if problematic_verses:
        print(f"\n🔍 Examples of problematic verses:")
        for i, verse in enumerate(problematic_verses[:5]):  # Show first 5
            print(f"   {i+1}. {verse['reference']}")
            print(f"      Original: {verse['original_text']}")
            print(f"      Match: {verse['match']}")
        
        if len(problematic_verses) > 5:
            print(f"   ... and {len(problematic_verses) - 5} more")
    
    return {
        'data': data,
        'verses_data': verses_data,
        'data_key': data_key,
        'total_verses': total_verses,
        'problematic_verses': problematic_verses
    }

def fix_verses_file(input_file, output_file, dry_run=False):
    """Fix the verses in the JSON file."""
    
    # Analyze first
    analysis = analyze_verses_file(input_file)
    if not analysis:
        return False
    
    data = analysis['data']
    verses_data = analysis['verses_data']
    data_key = analysis['data_key']
    problematic_verses = analysis['problematic_verses']
    
    if not problematic_verses:
        print("\n✅ No problematic verses found. File is clean!")
        return True
    
    if dry_run:
        print(f"\n🔍 DRY RUN: Would fix {len(problematic_verses)} verses")
        return True
    
    # Fix the problematic verses
    fixed_count = 0
    
    print(f"\n🔧 Fixing {len(problematic_verses)} verses...")
    
    for verse_info in problematic_verses:
        index = verse_info['index']
        verse = verses_data[index]
        
        if 'text' in verse:
            original_text = verse['text']
            cleaned_text, was_changed = fix_verse_text(original_text)
            
            if was_changed:
                verse['text'] = cleaned_text
                fixed_count += 1
                
                print(f"   ✓ Fixed: {verse_info['reference']}")
                print(f"     Before: {original_text[:60]}...")
                print(f"     After:  {cleaned_text[:60]}...")
    
    # Save the fixed file
    try:
        # Create backup of original if overwriting
        if input_file == output_file:
            backup_file = f"{input_file}.backup"
            print(f"\n📋 Creating backup: {backup_file}")
            os.rename(input_file, backup_file)
        
        print(f"\n💾 Saving fixed file: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Successfully fixed {fixed_count} verses!")
        print(f"   Input file: {input_file}")
        print(f"   Output file: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Fix verse texts with erroneous prefixes')
    parser.add_argument('--input', '-i', 
                       default='data/verses/verses.json',
                       help='Input JSON file (default: data/verses/verses.json)')
    parser.add_argument('--output', '-o',
                       help='Output JSON file (default: same as input)')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--analyze-only', '-a', action='store_true',
                       help='Only analyze the file, dont fix')
    
    args = parser.parse_args()
    
    # Resolve input file path
    input_file = Path(args.input).resolve()
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return 1
    
    # Determine output file
    if args.output:
        output_file = Path(args.output).resolve()
    else:
        output_file = input_file  # Overwrite input file
    
    print("🔧 Verse JSON Cleaner")
    print("=" * 40)
    
    if args.analyze_only:
        analysis = analyze_verses_file(input_file)
        if analysis and analysis['problematic_verses']:
            print(f"\n📋 Summary: Found {len(analysis['problematic_verses'])} verses with text issues")
            return 0
        else:
            print(f"\n✅ No issues found in the file")
            return 0
    
    # Fix the file
    success = fix_verses_file(input_file, output_file, dry_run=args.dry_run)
    
    if success:
        if not args.dry_run:
            print(f"\n🎉 File cleaning completed successfully!")
            print(f"\nNext steps:")
            print(f"1. Verify the cleaned file: {output_file}")
            print(f"2. Run the database import: python setup_db_v2.py --import-verses")
        return 0
    else:
        print(f"\n❌ File cleaning failed!")
        return 1

if __name__ == "__main__":
    exit(main())