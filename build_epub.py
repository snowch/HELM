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
from mathml_to_svg import MathMLToSVGConverter

class FixedEpubBuilder:
    def __init__(self, source_dir='.', output_file='HELM.epub', single_chapter_mode=False):
        self.source_dir = Path(source_dir)
        self.output_file = output_file
        self.chapters = []
        self.html_files = []  # Store individual HTML files instead of merged chapters
        self.image_files = []
        self.single_chapter_mode = single_chapter_mode
        # Initialize MathML to SVG converter
        self.mathml_converter = MathMLToSVGConverter(output_dir="math_images")

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
        
        if self.single_chapter_mode and chapter_dirs:
            return [chapter_dirs[0]] # Return only the first chapter
        
        return chapter_dirs

    def get_all_html_files(self, chapter_dirs):
        """Get all HTML files from all chapter directories"""
        html_files = []
        for chapter_num, section_num, chapter_title, chapter_dir in chapter_dirs:
            # Get all HTML files in this chapter directory
            chapter_html_files = sorted(chapter_dir.glob('*.html'), key=lambda f: f.name)
            for html_file in chapter_html_files:
                # Create a unique identifier for this HTML file
                file_stem = html_file.stem
                html_id = f"chapter_{chapter_num}_{section_num}_{file_stem}"
                html_files.append({
                    'id': html_id,
                    'path': html_file,
                    'chapter_num': chapter_num,
                    'section_num': section_num,
                    'chapter_title': chapter_title,
                    'chapter_dir': chapter_dir,
                    'file_title': file_stem.replace('_', ' ').title()
                })
        return html_files

    def create_mimetype(self):
        return "application/epub+zip"

    def create_container_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''

    def create_content_opf(self, html_files, image_files):
        book_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        manifest_items = []
        spine_items = []
        
        # EPUB 2.0 doesn't use nav - use NCX instead
        manifest_items.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        
        # Add individual HTML files
        for html_file in html_files:
            html_id = html_file['id']
            manifest_items.append(f'    <item id="{html_id}" href="{html_id}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'    <itemref idref="{html_id}"/>')
        
        # Add images
        for img in image_files:
            ext = os.path.splitext(img)[1].lower()
            mime = mimetypes.guess_type(img)[0] or "application/octet-stream"
            # Create a valid XML ID by replacing invalid characters with underscores
            # XML IDs must start with a letter or underscore, and can contain letters, digits, hyphens, underscores, and periods.
            # The error specifically mentions "without colons", so ensure no colons are present.
            # Also, ensure it doesn't start with a digit or hyphen.
            img_id = re.sub(r'[^a-zA-Z0-9_]', '_', img) # Replace all non-alphanumeric and non-underscore characters with underscores
            # Ensure the ID starts with a valid XML name start character (letter or underscore)
            if not re.match(r'^[a-zA-Z_]', img_id):
                img_id = '_' + img_id
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

    def create_toc_ncx(self, html_files):
        """Create NCX table of contents for EPUB 2.0"""
        book_id = str(uuid.uuid4())
        nav_points = []
        
        # Group files by chapter for hierarchical navigation
        current_chapter = None
        chapter_nav_points = []
        
        for i, html_file in enumerate(html_files):
            chapter_key = (html_file['chapter_num'], html_file['section_num'])
            play_order = i + 1
            
            # If this is a new chapter, add the previous chapter's nav points
            if current_chapter != chapter_key:
                if chapter_nav_points:
                    nav_points.extend(chapter_nav_points)
                
                # Start new chapter
                current_chapter = chapter_key
                chapter_nav_points = []
                
                # Add chapter header
                chapter_title = html.escape(f"{html_file['chapter_num']}.{html_file['section_num']} {html_file['chapter_title']}")
                chapter_nav_points.append(f'''    <navPoint id="navpoint-chapter-{html_file['chapter_num']}-{html_file['section_num']}" playOrder="{play_order}">
      <navLabel>
        <text>{chapter_title}</text>
      </navLabel>
      <content src="{html_file['id']}.xhtml"/>''')
            
            # Add individual file as sub-item if it's not the first file in chapter
            if len([f for f in html_files if (f['chapter_num'], f['section_num']) == chapter_key]) > 1:
                file_title = html.escape(html_file['file_title'])
                chapter_nav_points.append(f'''      <navPoint id="navpoint-{play_order}" playOrder="{play_order}">
        <navLabel>
          <text>{file_title}</text>
        </navLabel>
        <content src="{html_file['id']}.xhtml"/>
      </navPoint>''')
        
        # Close the last chapter
        if chapter_nav_points:
            chapter_nav_points.append('    </navPoint>')
            nav_points.extend(chapter_nav_points)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_id}"/>
    <meta name="dtb:depth" content="2"/>
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
        # Replace <main> tags with <div> tags for EPUB 2.0 compatibility
        content = re.sub(r'<main([^>]*)>', r'<div\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</main>', r'</div>', content, flags=re.IGNORECASE)
        
        # Replace <footer> tags with <div> tags for EPUB 2.0 compatibility
        # content = re.sub(r'<footer([^>]*)>', r'<div\1>', content, flags=re.IGNORECASE)
        # content = re.sub(r'</footer>', r'</div>', content, flags=re.IGNORECASE)
        # Remove HELM consortium attribution footer completely
        content = re.sub(r'<footer[^>]*>.*?</footer>', '<hr/>', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Replace <button> tags with <span> tags for EPUB 2.0 compatibility
        content = re.sub(r'<button([^>]*)>', r'<span\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</button>', r'</span>', content, flags=re.IGNORECASE)
        # Remove 'start' attribute from <ol> tags
        content = re.sub(r'<ol([^>]*) start="[^"]*"', r'<ol\1', content, flags=re.IGNORECASE)
        # Remove ARIA and data attributes for EPUB 2.0 compatibility
        content = re.sub(r' (aria-[^=]*|data-[^=]*|role)="[^"]*"', '', content, flags=re.IGNORECASE)
        # Remove all id attributes to prevent duplicates after merging
        content = re.sub(r' id="[^"]*"', '', content, flags=re.IGNORECASE)
        # Remove external links and scripts
        content = re.sub(r'<link[^>]*href="http[^"]*"[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<script[^>]*src="http[^"]*"[^>]*></script>', '', content, flags=re.IGNORECASE)
        # Remove href attributes pointing to .html files, as these are merged into single xhtml
        content = re.sub(r'href="[^"]*\.html"', '', content, flags=re.IGNORECASE)
        
        # CRITICAL: Convert MathML to SVG images for EPUB compatibility
        content = self.mathml_converter.convert_html_with_mathml(content)
        
        # Fix XML escaping issues in math-unicode spans
        def fix_math_unicode_content(match):
            span_content = match.group(1)
            # Escape XML characters in the span content
            span_content = span_content.replace('&', '&amp;')
            span_content = span_content.replace('<', '&lt;')
            span_content = span_content.replace('>', '&gt;')
            span_content = span_content.replace('"', '&quot;')
            span_content = span_content.replace("'", '&apos;')
            return f'<span class="math-unicode">{span_content}</span>'
        
        content = re.sub(r'<span class="math-unicode">(.*?)</span>', fix_math_unicode_content, content, flags=re.DOTALL)
        
        # Fix image src for EPUB: prepend chapter directory for local images
        if chapter_dir_name:
            content = re.sub(
                r'src\s*=\s*[\'"]\.?/?((figures|images)[^\'"]+)[\'"]',
                rf'src="{chapter_dir_name}/\1"',
                content
            )
        # Clean up extra whitespace
        # Replace specific ODF table elements with XHTML equivalents FIRST
        content = re.sub(r'<table:table([^>]*)>', r'<table\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</table:table>', r'</table>', content, flags=re.IGNORECASE)
        content = re.sub(r'<table:table-row([^>]*)>', r'<tr\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</table:table-row>', r'</tr>', content, flags=re.IGNORECASE)
        content = re.sub(r'<table:table-cell([^>]*)>', r'<td\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</table:table-cell>', r'</td>', content, flags=re.IGNORECASE)
        
        # Handle remaining table elements without namespace prefix
        content = re.sub(r'<table-row([^>]*)>', r'<tr\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</table-row>', r'</tr>', content, flags=re.IGNORECASE)
        content = re.sub(r'<table-cell([^>]*)>', r'<td\1>', content, flags=re.IGNORECASE)
        content = re.sub(r'</table-cell>', r'</td>', content, flags=re.IGNORECASE)
        
        # Handle any remaining ODF prefixed tags more comprehensively
        content = re.sub(r'<(/?)table:([^>\s]+)([^>]*)>', r'<\1\2\3>', content, flags=re.IGNORECASE)
        content = re.sub(r'<(/?)text:([^>\s]+)([^>]*)>', r'<\1p\3>', content, flags=re.IGNORECASE)  # Convert text: tags to p tags
        content = re.sub(r'<(/?)draw:([^>\s]+)([^>]*)>', r'<\1div\3>', content, flags=re.IGNORECASE)  # Convert draw: tags to div tags
        content = re.sub(r'<(/?)office:([^>\s]+)([^>]*)>', r'<\1div\3>', content, flags=re.IGNORECASE)  # Convert office: tags to div tags
        
        # Remove any remaining ODF-specific prefixes and attributes
        content = re.sub(r'table:[^=]*="[^"]*"', '', content) # Remove table: attributes
        content = re.sub(r'text:[^=]*="[^"]*"', '', content) # Remove text: attributes
        content = re.sub(r'draw:[^=]*="[^"]*"', '', content) # Remove draw: attributes
        content = re.sub(r'office:[^=]*="[^"]*"', '', content) # Remove office: attributes
        content = re.sub(r'fo:[^=]*="[^"]*"', '', content) # Remove fo: attributes
        content = re.sub(r'style:[^=]*="[^"]*"', '', content) # Remove style: attributes
        # Replace <p> tags containing heading elements with <div> tags for valid nesting
        content = re.sub(r'<p([^>]*)>\s*(<h[1-6][^>]*>.*?<\/h[1-6]>)\s*<\/p>', r'<div\1>\2</div>', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove specific <h4> tag with external link
        content = re.sub(r'<h4>\s*<a href="https://www.lboro.ac.uk/departments/mlsc/student-resources/helm-workbooks/">\s*View these resources in original pdf format\s*</a>\s*</h4>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Replace all heading tags with div tags to ensure valid nesting in all cases
        content = re.sub(r'<(h[1-6])([^>]*)>(.*?)<\/\1>', r'<div\2>\3</div>', content, flags=re.DOTALL | re.IGNORECASE)

        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'>\s+<', '><', content)
        return content.strip()

    def clean_svg_content(self, content):
        # Remove rdf:RDF blocks from SVG files
        content = re.sub(r'<rdf:RDF>.*?</rdf:RDF>', '', content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def create_html_file_xhtml(self, html_file_info):
        """Create XHTML content for a single HTML file"""
        html_file = html_file_info['path']
        chapter_dir = html_file_info['chapter_dir']
        chapter_num = html_file_info['chapter_num']
        section_num = html_file_info['section_num']
        chapter_title = html_file_info['chapter_title']
        file_title = html_file_info['file_title']
        
        # Create a title that includes both chapter and file info
        safe_title = html.escape(f"{chapter_num}.{section_num} {chapter_title} - {file_title}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
                # Extract content between <body> tags if present
                body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                if body_match:
                    content = self.clean_html_content(body_match.group(1), chapter_dir.name)
                else:
                    # Try to extract main content
                    main_match = re.search(r'<main[^>]*>(.*?)</main>', html_content, re.DOTALL | re.IGNORECASE)
                    if main_match:
                        content = self.clean_html_content(main_match.group(1), chapter_dir.name)
                    else:
                        content = f"<p>Could not extract content from {html_file.name}</p>"
        except Exception as e:
            content = f"<p>Error reading {html_file.name}: {html.escape(str(e))}</p>"
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:mml="http://www.w3.org/1998/Math/MathML">
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
        img.math-svg {{
            display: inline;
            vertical-align: middle;
            height: 1.2em;
            margin: 0 0.1em;
            width: auto;
        }}
        .math-unicode {{
            font-family: "STIX Two Math", "STIX", "Cambria Math", "Times New Roman", serif;
            font-size: 1em;
        }}
        .math-fallback {{
            font-family: "STIX Two Math", "STIX", "Cambria Math", "Times New Roman", serif;
            font-style: italic;
            color: #666;
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
        
        # Add existing images from chapter directories
        for _, _, _, chapter_dir in chapter_dirs:
            for root, dirs, files in os.walk(chapter_dir):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in image_exts:
                        abs_img_path = os.path.join(root, fname)
                        rel_img_path = os.path.relpath(abs_img_path, self.source_dir)
                        epub_img_path = f'OEBPS/{rel_img_path}'
                        with open(abs_img_path, 'r', encoding='utf-8') as imgf:
                            img_content = imgf.read()
                            if ext == '.svg':
                                img_content = self.clean_svg_content(img_content)
                            epub_zip.writestr(epub_img_path, img_content.encode('utf-8'))
                        image_files.append(rel_img_path)
        
        # Add generated math SVG images
        math_images_dir = Path("math_images")
        if math_images_dir.exists():
            for svg_file in math_images_dir.glob("*.svg"):
                rel_img_path = f"math_images/{svg_file.name}"
                epub_img_path = f'OEBPS/{rel_img_path}'
                with open(svg_file, 'r', encoding='utf-8') as imgf:
                    img_content = imgf.read()
                    img_content = self.clean_svg_content(img_content)
                    epub_zip.writestr(epub_img_path, img_content.encode('utf-8'))
                image_files.append(rel_img_path)
                print(f"Added math SVG: {svg_file.name}")
        
        return image_files

    def build_epub(self):
        print("Starting EPUB 2.0 build...")
        
        # Clean up math_images directory before build
        import shutil
        math_images_dir = Path("math_images")
        if math_images_dir.exists():
            shutil.rmtree(math_images_dir)
            print("Cleaned up existing math_images directory")
        
        chapter_dirs = self.get_chapter_directories()
        print(f"Found {len(chapter_dirs)} chapters")
        
        if not chapter_dirs:
            print("No HELM chapters found!")
            return False
        
        # Get all individual HTML files
        html_files = self.get_all_html_files(chapter_dirs)
        print(f"Found {len(html_files)} HTML files")
        
        with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # Add mimetype (uncompressed, must be first)
            epub_zip.writestr('mimetype', self.create_mimetype(), compress_type=zipfile.ZIP_STORED)
            
            # Add META-INF/container.xml
            epub_zip.writestr('META-INF/container.xml', self.create_container_xml())
            
            # Add individual HTML files as XHTML
            for html_file_info in html_files:
                print(f"Processing {html_file_info['path'].name} from chapter {html_file_info['chapter_num']}.{html_file_info['section_num']}")
                xhtml_content = self.create_html_file_xhtml(html_file_info)
                epub_zip.writestr(f'OEBPS/{html_file_info["id"]}.xhtml', xhtml_content)
            
            # Add images
            image_files = self.find_and_add_images(epub_zip, chapter_dirs)
            
            # Add content.opf (EPUB 2.0 format)
            epub_zip.writestr('OEBPS/content.opf', self.create_content_opf(html_files, image_files))
            
            # Add NCX table of contents (EPUB 2.0 format)
            epub_zip.writestr('OEBPS/toc.ncx', self.create_toc_ncx(html_files))
        
        print(f"EPUB 2.0 created: {self.output_file}")
        print(f"Total chapters: {len(chapter_dirs)}")
        print(f"Total HTML files: {len(html_files)}")
        return True

def main():
    # Set single_chapter_mode to True for debugging the first chapter only
    builder = FixedEpubBuilder(single_chapter_mode=True)
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
