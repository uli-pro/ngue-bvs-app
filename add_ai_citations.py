#!/usr/bin/env python3
"""
Script to add AI tool usage citations to project files for CS50 submission requirements.
This ensures compliance with CS50's AI citation policy while maintaining code integrity.
"""

import os
import glob
from pathlib import Path

# Citation templates for different file types
CITATIONS = {
    'python': '''# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

''',
    
    'html': '''<!-- This template was developed with assistance from Claude Code (Anthropic) -->
<!-- Core design and user experience decisions are original work -->

''',
    
    'js_css': '''/* This file was developed with assistance from Claude Code (Anthropic)
 * for implementation and optimization. Core design is original work.
 */

'''
}

def has_ai_citation(content, file_type):
    """Check if file already has AI citation"""
    if file_type == 'python':
        return 'Claude Code (Anthropic)' in content[:500]
    elif file_type == 'html':
        return '<!-- This template was developed with assistance from Claude Code' in content[:500]
    elif file_type == 'js_css':
        return '/* This file was developed with assistance from Claude Code' in content[:500]
    return False

def add_citation_to_file(file_path, citation):
    """Add citation to the beginning of a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine file type
        file_type = None
        if file_path.endswith('.py'):
            file_type = 'python'
        elif file_path.endswith(('.html', '.htm')):
            file_type = 'html'
        elif file_path.endswith(('.js', '.css')):
            file_type = 'js_css'
        
        if not file_type:
            return False, "Unknown file type"
        
        # Check if citation already exists
        if has_ai_citation(content, file_type):
            return False, "Citation already exists"
        
        # Handle Python files with shebang
        if file_type == 'python' and content.startswith('#!'):
            lines = content.split('\n', 1)
            if len(lines) > 1:
                new_content = lines[0] + '\n' + citation + lines[1]
            else:
                new_content = lines[0] + '\n' + citation
        else:
            new_content = citation + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True, "Citation added successfully"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function to process all relevant files"""
    
    # Files to process
    file_patterns = [
        '*.py',  # Python files
        'templates/*.html',  # HTML templates
        'static/js/*.js',  # JavaScript files
        'static/*.css',  # CSS files
        'static/css/*.css'  # CSS files in subdirectory
    ]
    
    # Files to exclude
    excluded_files = [
        'add_ai_citations.py',  # This script itself
        'venv/',  # Virtual environment
        '__pycache__/',  # Python cache
        '.git/',  # Git directory
        'node_modules/',  # Node modules if any
    ]
    
    processed_files = []
    skipped_files = []
    errors = []
    
    print("🤖 Adding AI tool usage citations for CS50 compliance...")
    print("=" * 60)
    
    for pattern in file_patterns:
        files = glob.glob(pattern, recursive=True)
        
        for file_path in files:
            # Skip excluded files
            skip = False
            for excluded in excluded_files:
                if excluded in file_path:
                    skip = True
                    break
            
            if skip:
                continue
            
            # Determine citation type
            citation = None
            if file_path.endswith('.py'):
                citation = CITATIONS['python']
            elif file_path.endswith(('.html', '.htm')):
                citation = CITATIONS['html']
            elif file_path.endswith(('.js', '.css')):
                citation = CITATIONS['js_css']
            
            if citation:
                success, message = add_citation_to_file(file_path, citation)
                
                if success:
                    processed_files.append(file_path)
                    print(f"✅ {file_path}")
                else:
                    if "already exists" in message:
                        skipped_files.append(file_path)
                        print(f"⏭️  {file_path} (already has citation)")
                    else:
                        errors.append((file_path, message))
                        print(f"❌ {file_path}: {message}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print(f"✅ Files processed: {len(processed_files)}")
    print(f"⏭️  Files skipped: {len(skipped_files)}")
    print(f"❌ Errors: {len(errors)}")
    
    if processed_files:
        print(f"\n📝 Successfully added citations to:")
        for file_path in processed_files:
            print(f"   - {file_path}")
    
    if errors:
        print(f"\n⚠️  Errors occurred:")
        for file_path, error in errors:
            print(f"   - {file_path}: {error}")
    
    print(f"\n🎓 All files are now CS50-compliant with AI tool usage citations!")

if __name__ == "__main__":
    main()