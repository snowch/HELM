#!/usr/bin/env python3
"""
Simple EPUB Builder for HELM content
This version uses only standard library modules for testing
"""

import os
import re
import zipfile
import uuid
from pathlib import Path
from datetime import datetime

class SimpleEpubBuilder:
    def __init__(self, source_dir='.', output_file='HELM_Simple.epub'):
        self.source_dir = Path(source_dir)
        self.output_file = output_file
        self.chapters = []
        
    def get_chapter_directories(self):
        """Get all chapter directories in order"""
        chapter_dirs = []
        pattern = re.compile(r'^(\d+)_(\d+)_(.+)-web$')
        
        for item in self.source_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    chapter_num = int(match.group(1))
                    section_num = int(match.group(2))
                    title = match.group(3).replace('_', ' ').title()
                    chapter_dirs.append((chapter_num, section_num, title, item))
        
        chapter_dirs.sort(key=lambda x: (x[0], x[1]))
        return chapter_dirs
    
    def create_mimetype(self):
        """Create mimetype file"""
        return "application/epub+zip"
    
    def create_container_xml(self):
        """Create META-INF/container.xml"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
    
    def create_content_opf(self, chapters):
        """Create content.opf file"""
        book_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        manifest_items = []
        spine_items = []
        
        # Add chapters to manifest and spine
        for i, (chapter_num, section_num, title, _) in enumerate(chapters):
            chapter_id = f"chapter_{chapter_num}_{section_num}"
            manifest_items.append(f'    <item id="{chapter_id}" href="{chapter_id}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'    <itemref idref="{chapter_id}"/>')
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="BookId">{book_id}</dc:identifier>
        <dc:title>HELM: Helping Engineers Learn Mathematics</dc:title>
        <dc:creator>HELM Consortium</dc:creator>
        <dc:language>en</dc:language>
        <dc:date>{timestamp}</dc:date>
        <dc:rights>Creative Commons Attribution-NonCommercial 4.0 International License</dc:rights>
        <meta property="dcterms:modified">{timestamp}</meta>
    </metadata>
    <manifest>
{chr(10).join(manifest_items)}
    </manifest>
    <spine>
{chr(10).join(spine_items)}
    </spine>
</package>'''
    
    def create_chapter_xhtml(self, chapter_num, section_num, title, chapter_dir):
        """Create XHTML file for a chapter"""
        # Try to read the main HTML file
        main_html_file = None
        for file in chapter_dir.glob('*.html'):
            if file.name == f"{chapter_dir.name}.html":
                main_html_file = file
                break
        
        if not main_html_file:
            html_files = list(chapter_dir.glob('*.html'))
            if html_files:
                main_html_file = html_files[0]
        
        content = f"<h1>{chapter_num}.{section_num} {title}</h1>"
        
        if main_html_file:
            try:
                with open(main_html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    # Extract content between <body> tags if present
                    body_start = html_content.find('<body')
                    body_end = html_content.find('</body>')
                    if body_start != -1 and body_end != -1:
                        body_start = html_content.find('>', body_start) + 1
                        body_content = html_content[body_start:body_end]
                        # Remove scripts and external links
                        body_content = re.sub(r'<script[^>]*>.*?</script>', '', body_content, flags=re.DOTALL)
                        body_content = re.sub(r'<nav[^>]*>.*?</nav>', '', body_content, flags=re.DOTALL)
                        content += body_content
            except Exception as e:
                content += f"<p>Error reading content: {e}</p>"
        else:
            content += f"<p>No HTML file found in {chapter_dir}</p>"
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter_num}.{section_num} {title}</title>
    <style type="text/css">
        body {{ font-family: serif; line-height: 1.6; margin: 1em; }}
        h1, h2, h3, h4 {{ color: #2c3e50; }}
        p {{ margin-bottom: 1em; }}
    </style>
</head>
<body>
    {content}
</body>
</html>'''
    
    def build_epub(self):
        """Build the EPUB file"""
        print("Starting simple EPUB build...")
        
        # Get chapters
        chapter_dirs = self.get_chapter_directories()
        print(f"Found {len(chapter_dirs)} chapters")
        
        if not chapter_dirs:
            print("No HELM chapters found!")
            return False
        
        # Create EPUB zip file
        with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # Add mimetype (uncompressed)
            epub_zip.writestr('mimetype', self.create_mimetype(), compress_type=zipfile.ZIP_STORED)
            
            # Add META-INF/container.xml
            epub_zip.writestr('META-INF/container.xml', self.create_container_xml())
            
            # Add content.opf
            epub_zip.writestr('OEBPS/content.opf', self.create_content_opf(chapter_dirs))
            
            # Add chapters
            for chapter_num, section_num, title, chapter_dir in chapter_dirs:
                print(f"Processing {chapter_num}.{section_num}: {title}")
                chapter_id = f"chapter_{chapter_num}_{section_num}"
                chapter_content = self.create_chapter_xhtml(chapter_num, section_num, title, chapter_dir)
                epub_zip.writestr(f'OEBPS/{chapter_id}.xhtml', chapter_content)
        
        print(f"EPUB created: {self.output_file}")
        print(f"Total chapters: {len(chapter_dirs)}")
        return True

def main():
    builder = SimpleEpubBuilder()
    success = builder.build_epub()
    if success:
        print("Simple EPUB build completed successfully!")
    else:
        print("EPUB build failed!")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())
