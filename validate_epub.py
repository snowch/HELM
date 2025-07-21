#!/usr/bin/env python3
"""
EPUB Validation Script
Checks the structure and validity of generated EPUB files
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def validate_epub(epub_file):
    """Validate an EPUB file structure"""
    print(f"Validating EPUB: {epub_file}")
    print("=" * 50)
    
    try:
        with zipfile.ZipFile(epub_file, 'r') as epub_zip:
            # List all files in the EPUB
            file_list = epub_zip.namelist()
            print(f"Files in EPUB: {len(file_list)}")
            
            # Check required files
            required_files = ['mimetype', 'META-INF/container.xml']
            missing_files = []
            
            for req_file in required_files:
                if req_file in file_list:
                    print(f"✓ Found: {req_file}")
                else:
                    print(f"✗ Missing: {req_file}")
                    missing_files.append(req_file)
            
            # Check mimetype
            if 'mimetype' in file_list:
                mimetype_content = epub_zip.read('mimetype').decode('utf-8')
                print(f"Mimetype: '{mimetype_content}'")
                if mimetype_content.strip() != 'application/epub+zip':
                    print("✗ Incorrect mimetype")
                else:
                    print("✓ Correct mimetype")
            
            # Check container.xml
            if 'META-INF/container.xml' in file_list:
                try:
                    container_content = epub_zip.read('META-INF/container.xml').decode('utf-8')
                    print("✓ Container.xml readable")
                    print("Container.xml content:")
                    print(container_content[:200] + "..." if len(container_content) > 200 else container_content)
                    
                    # Parse XML
                    root = ET.fromstring(container_content)
                    print("✓ Container.xml is valid XML")
                    
                except ET.ParseError as e:
                    print(f"✗ Container.xml XML parse error: {e}")
                except Exception as e:
                    print(f"✗ Container.xml error: {e}")
            
            # Check for OPF file
            opf_files = [f for f in file_list if f.endswith('.opf')]
            print(f"OPF files found: {opf_files}")
            
            if opf_files:
                opf_file = opf_files[0]
                try:
                    opf_content = epub_zip.read(opf_file).decode('utf-8')
                    print("✓ OPF file readable")
                    
                    # Parse OPF XML
                    root = ET.fromstring(opf_content)
                    print("✓ OPF file is valid XML")
                    
                    # Check for required elements
                    namespaces = {'opf': 'http://www.idpf.org/2007/opf'}
                    metadata = root.find('.//opf:metadata', namespaces)
                    manifest = root.find('.//opf:manifest', namespaces)
                    spine = root.find('.//opf:spine', namespaces)
                    
                    if metadata is not None:
                        print("✓ Found metadata section")
                    else:
                        print("✗ Missing metadata section")
                    
                    if manifest is not None:
                        items = manifest.findall('.//opf:item', namespaces)
                        print(f"✓ Found manifest with {len(items)} items")
                    else:
                        print("✗ Missing manifest section")
                    
                    if spine is not None:
                        itemrefs = spine.findall('.//opf:itemref', namespaces)
                        print(f"✓ Found spine with {len(itemrefs)} items")
                    else:
                        print("✗ Missing spine section")
                        
                except ET.ParseError as e:
                    print(f"✗ OPF XML parse error: {e}")
                except Exception as e:
                    print(f"✗ OPF error: {e}")
            
            # Check XHTML files
            xhtml_files = [f for f in file_list if f.endswith('.xhtml')]
            print(f"XHTML files found: {len(xhtml_files)}")
            
            if xhtml_files:
                # Test first XHTML file
                test_file = xhtml_files[0]
                try:
                    xhtml_content = epub_zip.read(test_file).decode('utf-8')
                    print(f"✓ Sample XHTML file ({test_file}) readable")
                    
                    # Check if it's valid XML
                    root = ET.fromstring(xhtml_content)
                    print("✓ Sample XHTML is valid XML")
                    
                except ET.ParseError as e:
                    print(f"✗ XHTML XML parse error in {test_file}: {e}")
                except Exception as e:
                    print(f"✗ XHTML error in {test_file}: {e}")
            
            print("\nFile structure:")
            for file in sorted(file_list)[:20]:  # Show first 20 files
                print(f"  {file}")
            if len(file_list) > 20:
                print(f"  ... and {len(file_list) - 20} more files")
            
            if missing_files:
                print(f"\n✗ EPUB validation failed. Missing files: {missing_files}")
                return False
            else:
                print("\n✓ Basic EPUB structure validation passed")
                return True
                
    except zipfile.BadZipFile:
        print("✗ File is not a valid ZIP file")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

def main():
    epub_files = ['HELM_Complete.epub', 'HELM_Simple.epub']
    
    for epub_file in epub_files:
        if Path(epub_file).exists():
            validate_epub(epub_file)
            print("\n" + "="*70 + "\n")
        else:
            print(f"File not found: {epub_file}")

if __name__ == '__main__':
    main()
