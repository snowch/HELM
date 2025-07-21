#!/usr/bin/env python3
"""
Fixed EPUB 2.0 Builder for HELM content
This version creates EPUB 2.0 format to avoid validation issues
Also merges all HTML files in a chapter and includes images with correct paths.
"""

import os
import re
import zipfile
import uuid
from pathlib import Path
from datetime import datetime
import html
import mimetypes

class FixedEpubBuilder:
    def __init__(self, source_dir='.', output_file='HELM_Fixed.epub'):
        self.source_dir = Path(source_dir)
        self.output_file = output_file
        self.chapters = []
        self.image_files = []

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
        return "application/epub+zip"

    def create_container_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''

    def create_content_opf(self, chapters, image_files):
        book_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        manifest_items = []
        spine_items = []
        
        # EPUB 2.0 doesn't use nav - use NCX instead
        manifest_items.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        
        # Add chapters
        for i, (chapter_num, section_num, title, _) in enumerate(chapters):
            chapter_id = f"chapter_{chapter_num}_{section_num}"
            manifest_items.append(f'    <item id="{chapter_id}" href="{chapter_id}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'    <itemref idref="{chapter_id}"/>')
        
        # Add images
        for img in image_files:
            ext = os.path.splitext(img)[1].lower()
            mime = mimetypes.guess_type(img)[0] or "application/octet-stream"
            img_id = img.replace("/", "_").replace(".", "_")
            manifest_items.append(
                f'    <item id="{img_id}" href="{img}" media-type="{mime}"/>'
            )
        
        # EPUB 2.0 OPF format
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId" opf:scheme="UUID">{book_id}</dc:identifier>
        <dc:title>HELM: Helping Engineers Learn Mathematics</dc:title>
        <dc:creator opf:role="aut">HELM Consortium</dc:creator>
        <dc:language>en</dc:language>
        <dc:date opf:event="publication">{timestamp}</dc:date>
        <dc:rights>Creative Commons Attribution-NonCommercial 4.0 International License</dc:rights>
    </metadata>
    <manifest>
{chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
{chr(10).join(spine_items)}
    </spine>
</package>'''

    def create_toc_ncx(self, chapters):
        """Create NCX table of contents for EPUB 2.0"""
        book_id = str(uuid.uuid4())
        nav_points = []
        
        for i, (chapter_num, section_num, title, _) in enumerate(chapters):
            chapter_id = f"chapter_{chapter_num}_{section_num}"
            safe_title = html.escape(f"{chapter_num}.{section_num} {title}")
            play_order = i + 1
            nav_points.append(f'''    <navPoint id="navpoint-{play_order}" playOrder="{play_order}">
      <navLabel>
        <text>{safe_title}</text>
      </navLabel>
      <content src="{chapter_id}.xhtml"/>
    </navPoint>''')
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>HELM: Helping Engineers Learn Mathematics</text>
  </docTitle>
  <navMap>
{chr(10).join(nav_points)}
  </navMap>
</ncx>'''

    def clean_html_content(self, content, chapter_dir_name=None):
        # Remove script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # Remove navigation elements
        content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # Remove div with navigation IDs
        content = re.sub(r'<div[^>]*id="[^"]*nav[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # Remove external links and scripts
        content = re.sub(r'<link[^>]*href="http[^"]*"[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<script[^>]*src="http[^"]*"[^>]*></script>', '', content, flags=re.IGNORECASE)
        # Fix image src for EPUB: prepend chapter directory for local images
        if chapter_dir_name:
            content = re.sub(
                r'src\s*=\s*[\'"]\.?/?((figures|images)[^\'"]+)[\'"]',
                rf'src="{chapter_dir_name}/\1"',
                content
            )
        # Clean up extra whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'>\s+<', '><', content)
        return content.strip()

    def create_chapter_xhtml(self, chapter_num, section_num, title, chapter_dir):
        # Merge all HTML files in the chapter directory in sorted order
        html_files = sorted(chapter_dir.glob('*.html'), key=lambda f: f.name)
        safe_title = html.escape(f"{chapter_num}.{section_num} {title}")
        content = f"<h1>{safe_title}</h1>"

        if not html_files:
            content += f"<p>No HTML files found in {html.escape(str(chapter_dir))}</p>"
        else:
            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        # Extract content between <body> tags if present
                        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                        if body_match:
                            body_content = self.clean_html_content(body_match.group(1), chapter_dir.name)
                            content += f"\n<!-- Start: {html_file.name} -->\n{body_content}\n<!-- End: {html_file.name} -->\n"
                        else:
                            # Try to extract main content
                            main_match = re.search(r'<main[^>]*>(.*?)</main>', html_content, re.DOTALL | re.IGNORECASE)
                            if main_match:
                                main_content = self.clean_html_content(main_match.group(1), chapter_dir.name)
                                content += f"\n<!-- Start: {html_file.name} -->\n{main_content}\n<!-- End: {html_file.name} -->\n"
                            else:
                                content += f"<p>Could not extract content from {html_file.name}</p>"
                except Exception as e:
                    content += f"<p>Error reading {html_file.name}: {html.escape(str(e))}</p>"
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{safe_title}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <style type="text/css">
        body {{
            font-family: Georgia, "Times New Roman", serif;
            line-height: 1.6;
            margin: 2em;
            max-width: 40em;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{ font-size: 1.8em; }}
        h2 {{ font-size: 1.5em; }}
        h3 {{ font-size: 1.3em; }}
        h4 {{ font-size: 1.1em; }}
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        .container {{
            max-width: 100%;
        }}
        .maketitle {{
            text-align: center;
            margin-bottom: 2em;
        }}
        .titleHead {{
            font-size: 2em;
            margin-bottom: 0.5em;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        li {{
            margin: 0.5em 0;
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>'''

    def find_and_add_images(self, epub_zip, chapter_dirs):
        image_exts = {'.svg', '.png', '.jpg', '.jpeg', '.gif'}
        image_files = []
        for _, _, _, chapter_dir in chapter_dirs:
            for root, dirs, files in os.walk(chapter_dir):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in image_exts:
                        abs_img_path = os.path.join(root, fname)
                        rel_img_path = os.path.relpath(abs_img_path, self.source_dir)
                        epub_img_path = f'OEBPS/{rel_img_path}'
                        with open(abs_img_path, 'rb') as imgf:
                            epub_zip.writestr(epub_img_path, imgf.read())
                        image_files.append(rel_img_path)
        return image_files

    def build_epub(self):
        print("Starting EPUB 2.0 build...")
        chapter_dirs = self.get_chapter_directories()
        print(f"Found {len(chapter_dirs)} chapters")
        
        if not chapter_dirs:
            print("No HELM chapters found!")
            return False
        
        with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # Add mimetype (uncompressed, must be first)
            epub_zip.writestr('mimetype', self.create_mimetype(), compress_type=zipfile.ZIP_STORED)
            
            # Add META-INF/container.xml
            epub_zip.writestr('META-INF/container.xml', self.create_container_xml())
            
            # Add chapters
            for i, (chapter_num, section_num, title, chapter_dir) in enumerate(chapter_dirs):
                print(f"Processing {chapter_num}.{section_num}: {title}")
                chapter_id = f"chapter_{chapter_num}_{section_num}"
                chapter_content = self.create_chapter_xhtml(chapter_num, section_num, title, chapter_dir)
                epub_zip.writestr(f'OEBPS/{chapter_id}.xhtml', chapter_content)
            
            # Add images
            image_files = self.find_and_add_images(epub_zip, chapter_dirs)
            
            # Add content.opf (EPUB 2.0 format)
            epub_zip.writestr('OEBPS/content.opf', self.create_content_opf(chapter_dirs, image_files))
            
            # Add NCX table of contents (EPUB 2.0 format)
            epub_zip.writestr('OEBPS/toc.ncx', self.create_toc_ncx(chapter_dirs))
        
        print(f"EPUB 2.0 created: {self.output_file}")
        print(f"Total chapters: {len(chapter_dirs)}")
        return True

def main():
    builder = FixedEpubBuilder()
    success = builder.build_epub()
    if success:
        print("EPUB 2.0 build completed successfully!")
        print("This version should validate against EPUB 2.0 rules.")
    else:
        print("EPUB build failed!")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())