#!/bin/bash

# HELM EPUB Builder Script
# This script builds all HELM content into a single EPUB file

set -e  # Exit on any error

echo "HELM EPUB Builder"
echo "=================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not found."
    echo "Please install pip and try again."
    exit 1
fi

# Install required packages if not already installed
echo "Checking and installing required Python packages..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Run the EPUB builder
echo ""
echo "Building EPUB from HELM content..."
echo ""

# Pass all command line arguments to the Python script
python3 build_epub.py "$@"

echo ""
echo "EPUB build process completed!"
echo ""
echo "You can now open the generated EPUB file with any EPUB reader."
echo "Popular EPUB readers include:"
echo "  - Calibre (cross-platform)"
echo "  - Apple Books (macOS/iOS)"
echo "  - Adobe Digital Editions"
echo "  - Google Play Books"
echo "  - Amazon Kindle (with conversion)"
