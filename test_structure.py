#!/usr/bin/env python3
"""
Test script to verify HELM directory structure and basic functionality
"""

import os
import re
from pathlib import Path

def test_helm_structure():
    """Test the HELM directory structure"""
    print("HELM Structure Test")
    print("==================")
    
    source_dir = Path('.')
    chapter_dirs = []
    
    # Pattern to match chapter directories
    pattern = re.compile(r'^(\d+)_(\d+)_(.+)-web$')
    
    print(f"Scanning directory: {source_dir.absolute()}")
    print()
    
    for item in source_dir.iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                chapter_num = int(match.group(1))
                section_num = int(match.group(2))
                title = match.group(3).replace('_', ' ').title()
                chapter_dirs.append((chapter_num, section_num, title, item))
    
    # Sort by chapter and section number
    chapter_dirs.sort(key=lambda x: (x[0], x[1]))
    
    print(f"Found {len(chapter_dirs)} HELM chapters:")
    print()
    
    for chapter_num, section_num, title, chapter_dir in chapter_dirs[:10]:  # Show first 10
        print(f"  {chapter_num:2d}.{section_num} - {title}")
        
        # Check for HTML files
        html_files = list(chapter_dir.glob('*.html'))
        css_files = list(chapter_dir.glob('*.css'))
        img_dirs = list(chapter_dir.glob('figures'))
        
        print(f"         HTML files: {len(html_files)}")
        print(f"         CSS files:  {len(css_files)}")
        print(f"         Image dirs: {len(img_dirs)}")
        print()
    
    if len(chapter_dirs) > 10:
        print(f"  ... and {len(chapter_dirs) - 10} more chapters")
        print()
    
    # Check for index.html
    index_file = source_dir / 'index.html'
    if index_file.exists():
        print("✓ Found index.html (will be used for introduction)")
    else:
        print("✗ No index.html found")
    
    print()
    print("Structure test complete!")
    
    if chapter_dirs:
        print("✓ HELM structure looks good - ready for EPUB conversion")
        return True
    else:
        print("✗ No HELM chapters found - check directory structure")
        return False

if __name__ == '__main__':
    test_helm_structure()
