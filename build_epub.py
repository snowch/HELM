#!/usr/bin/env python3
"""
HELM EPUB Builder
Converts all HELM web content into a single EPUB file.
"""

import os
import re
import shutil
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from ebooklib import epub
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HELMEpubBuilder:
    def __init__(self, source_dir='.', output_file='HELM_Complete.epub'):
        self.source_dir = Path(source_dir)
        self.output_file = output_file
        self.book = epub.EpubBook()
        self.chapters = []
        self.images = set()
        self.css_files = set()
        
        # Initialize book metadata
        self.setup_book_metadata()
        
    def setup_book_metadata(self):
        """Set up basic book metadata"""
        self.book.set_identifier('helm-complete-workbook')
        self.book.set_title('HELM: Helping Engineers Learn Mathematics - Complete Workbook')
        self.book.set_language('en')
        self.book.add_author('HELM Consortium')
        self.book.add_metadata('DC', 'description', 
                              'Complete collection of HELM (Helping Engineers Learn Mathematics) workbooks converted to EPUB format.')
        self.book.add_metadata('DC', 'rights', 
                              'Creative Commons Attribution-NonCommercial 4.0 International License')
        
    def get_chapter_directories(self):
        """Get all chapter directories in order"""
        chapter_dirs = []
        
        # Pattern to match chapter directories (e.g., "1_1_math_notation_n_symbols-web")
        pattern = re.compile(r'^(\d+)_(\d+)_(.+)-web$')
        
        for item in self.source_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    chapter_num = int(match.group(1))
                    section_num = int(match.group(2))
                    title = match.group(3).replace('_', ' ').title()
                    chapter_dirs.append((chapter_num, section_num, title, item))
        
        # Sort by chapter and section number
        chapter_dirs.sort(key=lambda x: (x[0], x[1]))
        return chapter_dirs
        
    def clean_html_content(self, html_content, base_dir):
        """Clean and process HTML content for EPUB"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove external scripts and links that won't work in EPUB
        for script in soup.find_all('script'):
            if script.get('src') and ('http' in script.get('src') or 'cloudflare' in script.get('src', '')):
                script.decompose()
            elif 'cloudflare' in script.get_text().lower():
                script.decompose()
                
        # Remove external CSS links but keep local ones
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if href.startswith('http') or 'bootstrap' in href or 'jquery' in href:
                link.decompose()
            elif href and not href.startswith('http'):
                # This is a local CSS file
                css_path = base_dir / href
                if css_path.exists():
                    self.css_files.add(css_path)
        
        # Process images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('http'):
                img_path = base_dir / src
                if img_path.exists():
                    self.images.add(img_path)
                    # Update src to relative path for EPUB
                    img['src'] = f"images/{img_path.name}"
        
        # Remove navigation elements that are specific to web version
        for nav in soup.find_all('nav'):
            nav.decompose()
            
        # Remove div with id="botnav" or similar navigation
        for div in soup.find_all('div', id=re.compile(r'.*nav.*')):
            div.decompose()
            
        # Clean up MathJax configuration (keep the math content but remove config)
        for script in soup.find_all('script'):
            if script.string and 'MathJax' in script.string:
                script.decompose()
        
        # Extract main content (usually in main tag or container div)
        main_content = soup.find('main') or soup.find('div', class_='container')
        if main_content:
            return str(main_content)
        else:
            # If no main content found, return body content
            body = soup.find('body')
            return str(body) if body else str(soup)
    
    def process_chapter_directory(self, chapter_num, section_num, title, chapter_dir):
        """Process a single chapter directory"""
        logger.info(f"Processing Chapter {chapter_num}.{section_num}: {title}")
        
        # Find the main HTML file
        main_html_file = None
        html_files = []
        
        for file in chapter_dir.glob('*.html'):
            if file.name == f"{chapter_dir.name}.html":
                main_html_file = file
            html_files.append(file)
        
        if not main_html_file and html_files:
            # If no exact match, use the first HTML file
            main_html_file = html_files[0]
            
        if not main_html_file:
            logger.warning(f"No HTML file found in {chapter_dir}")
            return None
            
        # Read and process the main HTML file
        try:
            with open(main_html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"Error reading {main_html_file}: {e}")
            return None
            
        # Clean the HTML content
        cleaned_content = self.clean_html_content(html_content, chapter_dir)
        
        # Create EPUB chapter
        chapter_id = f"chapter_{chapter_num}_{section_num}"
        chapter_filename = f"{chapter_id}.xhtml"
        
        # Create full HTML document for the chapter
        full_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter_num}.{section_num} {title}</title>
    <link rel="stylesheet" type="text/css" href="styles/main.css"/>
</head>
<body>
    <h1>{chapter_num}.{section_num} {title}</h1>
    {cleaned_content}
</body>
</html>"""
        
        chapter = epub.EpubHtml(title=f"{chapter_num}.{section_num} {title}",
                               file_name=chapter_filename,
                               content=full_html)
        
        return chapter
    
    def add_css_styles(self):
        """Add CSS styles to the EPUB"""
        # Create a main CSS file combining all local CSS
        main_css_content = """
/* HELM EPUB Styles */
body {
    font-family: "Times New Roman", serif;
    line-height: 1.6;
    margin: 1em;
}

h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 { font-size: 1.8em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.3em; }
h4 { font-size: 1.1em; }

p {
    margin-bottom: 1em;
    text-align: justify;
}

.container {
    max-width: 100%;
    margin: 0 auto;
}

.maketitle {
    text-align: center;
    margin-bottom: 2em;
}

.titleHead {
    font-size: 2em;
    color: #2c3e50;
    margin-bottom: 0.5em;
}

.author {
    font-size: 1.2em;
    color: #7f8c8d;
    margin-bottom: 1em;
}

.tableofcontents {
    background-color: #f8f9fa;
    padding: 1em;
    margin: 1em 0;
    border-left: 4px solid #3498db;
}

.sectionToc, .subsectionToc {
    display: block;
    margin: 0.5em 0;
}

.sectionToc {
    font-weight: bold;
}

.subsectionToc {
    margin-left: 1em;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

.itemize1 {
    margin: 1em 0;
}

.itemize1 li {
    margin: 0.5em 0;
}

/* Math styling */
math {
    display: inline-block;
    margin: 0.2em;
}

/* Footer styling */
footer {
    margin-top: 2em;
    padding-top: 1em;
    border-top: 1px solid #bdc3c7;
    font-size: 0.9em;
    color: #7f8c8d;
}
"""
        
        # Add any local CSS files found
        for css_file in self.css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                    # Clean up CSS (remove external references)
                    css_content = re.sub(r'@import.*?;', '', css_content)
                    main_css_content += f"\n\n/* From {css_file.name} */\n{css_content}"
            except Exception as e:
                logger.warning(f"Could not read CSS file {css_file}: {e}")
        
        # Create CSS item
        nav_css = epub.EpubItem(uid="main_css",
                               file_name="styles/main.css",
                               media_type="text/css",
                               content=main_css_content)
        
        self.book.add_item(nav_css)
        
    def add_images(self):
        """Add images to the EPUB"""
        for img_path in self.images:
            try:
                with open(img_path, 'rb') as f:
                    img_content = f.read()
                
                # Determine media type
                suffix = img_path.suffix.lower()
                if suffix == '.png':
                    media_type = 'image/png'
                elif suffix in ['.jpg', '.jpeg']:
                    media_type = 'image/jpeg'
                elif suffix == '.gif':
                    media_type = 'image/gif'
                elif suffix == '.svg':
                    media_type = 'image/svg+xml'
                else:
                    media_type = 'image/png'  # default
                
                img_item = epub.EpubItem(uid=f"img_{img_path.stem}",
                                        file_name=f"images/{img_path.name}",
                                        media_type=media_type,
                                        content=img_content)
                
                self.book.add_item(img_item)
                
            except Exception as e:
                logger.warning(f"Could not add image {img_path}: {e}")
    
    def create_table_of_contents(self):
        """Create table of contents"""
        # Create introduction chapter from index.html if it exists
        index_file = self.source_dir / 'index.html'
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                cleaned_content = self.clean_html_content(html_content, self.source_dir)
                
                intro_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Introduction</title>
    <link rel="stylesheet" type="text/css" href="styles/main.css"/>
</head>
<body>
    {cleaned_content}
</body>
</html>"""
                
                intro_chapter = epub.EpubHtml(title="Introduction",
                                            file_name="introduction.xhtml",
                                            content=intro_html)
                
                self.book.add_item(intro_chapter)
                self.chapters.insert(0, intro_chapter)
                
            except Exception as e:
                logger.warning(f"Could not process index.html: {e}")
    
    def build_epub(self):
        """Build the complete EPUB"""
        logger.info("Starting EPUB build process...")
        
        # Get all chapter directories
        chapter_dirs = self.get_chapter_directories()
        logger.info(f"Found {len(chapter_dirs)} chapters")
        
        # Process each chapter
        for chapter_num, section_num, title, chapter_dir in chapter_dirs:
            chapter = self.process_chapter_directory(chapter_num, section_num, title, chapter_dir)
            if chapter:
                self.book.add_item(chapter)
                self.chapters.append(chapter)
        
        # Add CSS styles
        self.add_css_styles()
        
        # Add images
        self.add_images()
        
        # Create table of contents
        self.create_table_of_contents()
        
        # Set up navigation
        self.book.toc = self.chapters
        
        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        
        # Set spine
        self.book.spine = ['nav'] + self.chapters
        
        # Write EPUB file
        logger.info(f"Writing EPUB to {self.output_file}")
        epub.write_epub(self.output_file, self.book, {})
        
        logger.info(f"EPUB build complete! Output: {self.output_file}")
        logger.info(f"Total chapters: {len(self.chapters)}")
        logger.info(f"Total images: {len(self.images)}")
        logger.info(f"Total CSS files: {len(self.css_files)}")

def main():
    parser = argparse.ArgumentParser(description='Build HELM content as EPUB')
    parser.add_argument('--source', '-s', default='.', 
                       help='Source directory containing HELM content (default: current directory)')
    parser.add_argument('--output', '-o', default='HELM_Complete.epub',
                       help='Output EPUB filename (default: HELM_Complete.epub)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if required dependencies are available
    try:
        import ebooklib
        from bs4 import BeautifulSoup
    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.error("Please install required packages:")
        logger.error("pip install ebooklib beautifulsoup4 lxml")
        return 1
    
    # Build the EPUB
    builder = HELMEpubBuilder(args.source, args.output)
    try:
        builder.build_epub()
        return 0
    except Exception as e:
        logger.error(f"Error building EPUB: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
