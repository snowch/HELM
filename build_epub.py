#!/usr/bin/env python3
"""
Fixed EPUB Builder for HELM content
This version addresses common EPUB validation issues
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
        manifest_items.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
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
        <itemref idref="nav"/>
{chr(10).join(spine_items)}
    </spine>
</package>'''

    def create_nav_xhtml(self, chapters):
        nav_items = []
        for chapter_num, section_num, title, _ in chapters:
            chapter_id = f"chapter_{chapter_num}_{section_num}"
            safe_title = html.escape(f"{chapter_num}.{section_num} {title}")
            nav_items.append(f'        <li><a href="{chapter_id}.xhtml">{safe_title}</a></li>')
        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Table of Contents</title>
    <meta charset="utf-8"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
{chr(10).join(nav_items)}
        </ol>
    </nav>
</body>
</html>'''

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
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{safe_title}</title>
    <meta charset="utf-8"/>
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
        print("Starting fixed EPUB build...")
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
            # Add chapters (needed before images to fix manifest)
            for i, (chapter_num, section_num, title, chapter_dir) in enumerate(chapter_dirs):
                print(f"Processing {chapter_num}.{section_num}: {title}")
                chapter_id = f"chapter_{chapter_num}_{section_num}"
                chapter_content = self.create_chapter_xhtml(chapter_num, section_num, title, chapter_dir)
                epub_zip.writestr(f'OEBPS/{chapter_id}.xhtml', chapter_content)
            # Add images
            image_files = self.find_and_add_images(epub_zip, chapter_dirs)
            # Add content.opf (needs image file list)
            epub_zip.writestr('OEBPS/content.opf', self.create_content_opf(chapter_dirs, image_files))
            # Add navigation document
            epub_zip.writestr('OEBPS/nav.xhtml', self.create_nav_xhtml(chapter_dirs))
        print(f"Fixed EPUB created: {self.output_file}")
        print(f"Total chapters: {len(chapter_dirs)}")
        return True

def main():
    builder = FixedEpubBuilder()
    success = builder.build_epub()
    if success:
        print("Fixed EPUB build completed successfully!")
        print("This version should be compatible with most EPUB readers.")
    else:
        print("EPUB build failed!")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())