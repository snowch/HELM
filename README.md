# HELM EPUB Builder

This project provides a comprehensive script to convert all HELM (Helping Engineers Learn Mathematics) web content into a single, well-formatted EPUB file.

## Overview

The HELM EPUB Builder processes all the individual chapter directories and combines them into a single EPUB file that can be read on any EPUB-compatible device or application. The script automatically:

- Discovers all HELM chapter directories
- Processes HTML content and cleans it for EPUB format
- Includes images and CSS styling
- Creates a proper table of contents
- Generates navigation structure
- Produces a complete EPUB file

## Features

- **Automatic Discovery**: Finds all HELM chapter directories based on naming pattern
- **Content Cleaning**: Removes web-specific elements (external scripts, navigation, etc.)
- **Image Processing**: Includes all local images with proper EPUB formatting
- **CSS Integration**: Combines local CSS files and adds EPUB-optimized styling
- **Mathematical Content**: Preserves MathML mathematical expressions
- **Proper Structure**: Creates chapters in correct order with navigation
- **Metadata**: Includes proper book metadata and licensing information

## Requirements

- Python 3.6 or higher
- pip (Python package installer)

The following Python packages will be automatically installed:
- `ebooklib` (>= 0.18)
- `beautifulsoup4` (>= 4.9.0)
- `lxml` (>= 4.6.0)

## Installation

1. Clone or download this repository to your HELM content directory
2. Ensure you have Python 3 and pip installed
3. The required packages will be installed automatically when you run the script

## Usage

### Simple Usage (Recommended)

Run the shell script which handles everything automatically:

```bash
./build_helm_epub.sh
```

This will:
- Install required Python packages
- Build the EPUB from all content in the current directory
- Create `HELM_Complete.epub` in the current directory

### Alternative EPUB Builders

If you encounter dependency issues or EPUB compatibility problems, you have two alternative builders:

#### Simple EPUB Builder
Uses only Python standard library (no external dependencies):

```bash
python3 simple_epub_builder.py
```

This creates `HELM_Simple.epub` with basic formatting.

#### Fixed EPUB Builder
Addresses common EPUB validation issues and improves compatibility:

```bash
python3 fixed_epub_builder.py
```

This creates `HELM_Fixed.epub` with improved EPUB 3.0 compliance and better reader compatibility.

### Advanced Usage

You can also run the Python script directly with custom options:

```bash
python3 build_epub.py [options]
```

#### Options

- `--source`, `-s`: Source directory containing HELM content (default: current directory)
- `--output`, `-o`: Output EPUB filename (default: `HELM_Complete.epub`)
- `--verbose`, `-v`: Enable verbose logging
- `--help`, `-h`: Show help message

#### Examples

```bash
# Build EPUB with custom output name
python3 build_epub.py --output "My_HELM_Book.epub"

# Build from different source directory
python3 build_epub.py --source "/path/to/helm/content" --output "HELM.epub"

# Enable verbose logging
python3 build_epub.py --verbose
```

### Using the Shell Script with Options

The shell script passes all arguments to the Python script:

```bash
# Custom output filename
./build_helm_epub.sh --output "Custom_HELM.epub"

# Verbose mode
./build_helm_epub.sh --verbose

# Custom source and output
./build_helm_epub.sh --source "/other/path" --output "HELM_Book.epub"
```

## Project Structure

The script expects the following directory structure:

```
.
├── build_epub.py              # Main Python script
├── build_helm_epub.sh         # Shell wrapper script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── index.html                 # Main index (optional, used for introduction)
├── 1_1_math_notation_n_symbols-web/
│   ├── 1_1_math_notation_n_symbols-web.html
│   ├── *.css
│   ├── figures/
│   └── ...
├── 1_2_indices-web/
├── 2_1_basic_concpts_of_functions-web/
└── ... (other chapter directories)
```

## Output

The script generates a complete EPUB file containing:

1. **Introduction** (from index.html if present)
2. **All Chapters** in numerical order (1.1, 1.2, 2.1, etc.)
3. **Images** from all chapters
4. **Styling** optimized for EPUB readers
5. **Navigation** with proper table of contents
6. **Metadata** including author, license, and description

## EPUB Features

The generated EPUB includes:

- Proper chapter structure and navigation
- Embedded images with responsive sizing
- Mathematical expressions (MathML preserved)
- Clean, readable typography
- Table of contents
- Metadata for library organization
- Cross-platform compatibility

## Supported EPUB Readers

The generated EPUB works with most EPUB readers including:

- **Calibre** (Windows, macOS, Linux)
- **Apple Books** (macOS, iOS)
- **Adobe Digital Editions** (Windows, macOS)
- **Google Play Books** (Android, Web)
- **Amazon Kindle** (with conversion via Calibre)
- **Kobo** readers
- **Barnes & Noble Nook**

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```
   Error: Missing required dependency: No module named 'ebooklib'
   ```
   Solution: Run `pip3 install -r requirements.txt`

2. **Permission Denied**
   ```
   Permission denied: ./build_helm_epub.sh
   ```
   Solution: Run `chmod +x build_helm_epub.sh`

3. **No Chapters Found**
   ```
   Found 0 chapters
   ```
   Solution: Ensure you're in the correct directory with HELM content

4. **Image Loading Issues**
   - Check that image paths in HTML are relative
   - Ensure image files exist in the expected locations

### Verbose Mode

For debugging, use verbose mode to see detailed processing information:

```bash
./build_helm_epub.sh --verbose
```

This will show:
- Which chapters are being processed
- Image and CSS files being included
- Any warnings or errors encountered

## Customization

### Modifying Styles

The script includes default CSS styling optimized for EPUB readers. To customize:

1. Edit the `main_css_content` variable in `build_epub.py`
2. Add your custom CSS rules
3. Rebuild the EPUB

### Adding Custom Metadata

To modify book metadata, edit the `setup_book_metadata()` method in the `HELMEpubBuilder` class.

### Processing Additional Content

To include additional HTML files or modify content processing, edit the relevant methods in the `HELMEpubBuilder` class.

## License

This script is provided under the same Creative Commons Attribution-NonCommercial 4.0 International License as the original HELM content.

The original HELM content was created by the [HELM Consortium](https://www.lboro.ac.uk/departments/mlsc/student-resources/helm-workbooks/consortium-members/).

## Contributing

Feel free to submit issues or pull requests to improve the EPUB builder. Common areas for enhancement:

- Better mathematical expression handling
- Additional output formats
- Enhanced styling options
- Performance improvements
- Error handling improvements

## Support

For issues with the EPUB builder script, please check the troubleshooting section above. For issues with the original HELM content, please contact the HELM Consortium.
