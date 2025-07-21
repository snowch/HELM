#!/usr/bin/env python3
"""
MathML to SVG converter for EPUB compatibility
Uses WeasyPrint to render MathML as SVG images
"""

import re
import os
import hashlib
from pathlib import Path
from lxml import etree, html
from weasyprint import HTML, CSS
from io import BytesIO
import base64

class MathMLToSVGConverter:
    def __init__(self, output_dir="math_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.math_counter = 0
        self.generated_images = {}
        
        # Extensive Unicode mapping for mathematical symbols
        self.unicode_math_map = {
            # Basic operators
            '+': '+',
            '−': '−',  # minus sign
            '-': '−',  # convert hyphen to proper minus
            '×': '×',
            '÷': '÷',
            '∕': '/',
            '=': '=',
            '≠': '≠',
            '±': '±',
            '∓': '∓',
            
            # Comparison operators
            '>': '>',
            '<': '<',
            '≥': '≥',
            '≤': '≤',
            '&gt;': '>',
            '&lt;': '<',
            '≈': '≈',
            '≡': '≡',
            '∝': '∝',
            
            # Set theory
            '∈': '∈',
            '∉': '∉',
            '⊂': '⊂',
            '⊃': '⊃',
            '⊆': '⊆',
            '⊇': '⊇',
            '∪': '∪',
            '∩': '∩',
            '∅': '∅',
            
            # Logic
            '∧': '∧',
            '∨': '∨',
            '¬': '¬',
            '→': '→',
            '↔': '↔',
            '∀': '∀',
            '∃': '∃',
            
            # Calculus
            '∂': '∂',
            '∇': '∇',
            '∫': '∫',
            '∮': '∮',
            '∞': '∞',
            '∑': '∑',
            '∏': '∏',
            'lim': 'lim',
            
            # Special symbols
            '|': '|',
            '∙': '•',
            '∘': '∘',
            '°': '°',
            '√': '√',
            '∛': '∛',
            '∜': '∜',
            
            # Greek letters (lowercase)
            'α': 'α', 'β': 'β', 'γ': 'γ', 'δ': 'δ', 'ε': 'ε',
            'ζ': 'ζ', 'η': 'η', 'θ': 'θ', 'ι': 'ι', 'κ': 'κ',
            'λ': 'λ', 'μ': 'μ', 'ν': 'ν', 'ξ': 'ξ', 'ο': 'ο',
            'π': 'π', 'ρ': 'ρ', 'σ': 'σ', 'τ': 'τ', 'υ': 'υ',
            'φ': 'φ', 'χ': 'χ', 'ψ': 'ψ', 'ω': 'ω',
            
            # Greek letters (uppercase)
            'Α': 'Α', 'Β': 'Β', 'Γ': 'Γ', 'Δ': 'Δ', 'Ε': 'Ε',
            'Ζ': 'Ζ', 'Η': 'Η', 'Θ': 'Θ', 'Ι': 'Ι', 'Κ': 'Κ',
            'Λ': 'Λ', 'Μ': 'Μ', 'Ν': 'Ν', 'Ξ': 'Ξ', 'Ο': 'Ο',
            'Π': 'Π', 'Ρ': 'Ρ', 'Σ': 'Σ', 'Τ': 'Τ', 'Υ': 'Υ',
            'Φ': 'Φ', 'Χ': 'Χ', 'Ψ': 'Ψ', 'Ω': 'Ω',
            
            # Superscript digits
            '⁰': '⁰', '¹': '¹', '²': '²', '³': '³', '⁴': '⁴',
            '⁵': '⁵', '⁶': '⁶', '⁷': '⁷', '⁸': '⁸', '⁹': '⁹',
            '⁺': '⁺', '⁻': '⁻', '⁼': '⁼', '⁽': '⁽', '⁾': '⁾',
            
            # Subscript digits
            '₀': '₀', '₁': '₁', '₂': '₂', '₃': '₃', '₄': '₄',
            '₅': '₅', '₆': '₆', '₇': '₇', '₈': '₈', '₉': '₉',
            '₊': '₊', '₋': '₋', '₌': '₌', '₍': '₍', '₎': '₎',
            
            # Fractions
            '½': '½', '⅓': '⅓', '⅔': '⅔', '¼': '¼', '¾': '¾',
            '⅕': '⅕', '⅖': '⅖', '⅗': '⅗', '⅘': '⅘', '⅙': '⅙',
            '⅚': '⅚', '⅛': '⅛', '⅜': '⅜', '⅝': '⅝', '⅞': '⅞',
        }
        
        # Superscript and subscript conversion maps
        self.superscripts = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
            'n': 'ⁿ', 'i': 'ⁱ', 'x': 'ˣ', 'y': 'ʸ'
        }
        
        self.subscripts = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
            '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
            '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
            'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
            'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
            'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
            'v': 'ᵥ', 'x': 'ₓ', 'y': 'ᵧ'
        }
        
        # CSS for rendering math (kept for compatibility)
        self.math_css = """
        @page { margin: 0; size: auto; }
        body { 
            margin: 0; 
            padding: 10px; 
            font-family: 'STIX Two Math', 'STIX', 'Times New Roman', serif;
            font-size: 16px;
            line-height: 1.2;
        }
        math {
            display: inline-block;
            font-family: 'STIX Two Math', 'STIX', 'Times New Roman', serif;
        }
        """

    def mathml_to_svg(self, mathml_content, inline=True):
        """Convert MathML content to SVG"""
        try:
            # Create a hash of the MathML content for caching
            content_hash = hashlib.md5(mathml_content.encode()).hexdigest()
            svg_filename = f"math_{content_hash}.svg"
            svg_path = self.output_dir / svg_filename
            
            # Return cached version if it exists
            if svg_path.exists():
                return svg_filename, svg_path.read_text()
            
            # Clean up MathML content
            mathml_content = self._clean_mathml(mathml_content)
            
            # Create HTML wrapper
            display_style = "inline" if inline else "block"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>{self.math_css}</style>
            </head>
            <body>
                <div style="display: {display_style};">
                    {mathml_content}
                </div>
            </body>
            </html>
            """
            
            # Use fallback conversion directly (WeasyPrint doesn't support SVG output)
            return self._fallback_conversion(mathml_content, svg_filename, svg_path)
                
        except Exception as e:
            print(f"Error converting MathML to SVG: {e}")
            return None, None

    def _clean_mathml(self, mathml_content):
        """Clean and prepare MathML content"""
        # Ensure proper namespace
        if 'xmlns=' not in mathml_content and '<math' in mathml_content:
            mathml_content = mathml_content.replace(
                '<math', 
                '<math xmlns="http://www.w3.org/1998/Math/MathML"'
            )
        
        # Remove problematic attributes that might cause issues
        mathml_content = re.sub(r'class="[^"]*"', '', mathml_content)
        
        return mathml_content

    def _fallback_conversion(self, mathml_content, svg_filename, svg_path):
        """Fallback conversion using simple text extraction"""
        try:
            # Ensure output directory exists
            svg_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract text content from MathML
            text_content = re.sub(r'<[^>]+>', '', mathml_content)
            text_content = text_content.strip()
            
            # Clean up excessive whitespace more aggressively
            text_content = re.sub(r'\s+', ' ', text_content)  # Replace multiple whitespace with single space
            text_content = re.sub(r'\s*([,\(\)\[\]\{\}])\s*', r'\1', text_content)  # Remove spaces around punctuation
            text_content = text_content.strip()
            
            if not text_content:
                text_content = "[math]"
            
            # Escape XML characters for SVG
            import html
            text_content = html.escape(text_content)
            
            # Remove any remaining problematic characters
            text_content = re.sub(r'[^\w\s\+\-\*\/\=\(\)\[\]\{\}\.\,\;\:\!\?\'\"\<\>\&\#\%\@\$\^\~\|\\]', '', text_content)
            
            # Estimate width based on cleaned text length (more precise approximation)
            char_width = 8  # approximate character width in pixels for 14px font
            text_width = max(len(text_content) * char_width + 8, 20)  # minimum width of 20px, add padding
            
            # Create compact SVG with text
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{text_width}" height="16" viewBox="0 0 {text_width} 16">
    <text x="1" y="12" font-family="serif" font-size="14" fill="black">{text_content}</text>
</svg>'''
            
            # Save SVG file
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            return svg_filename, svg_content
            
        except Exception as e:
            print(f"Fallback conversion failed: {e}")
            return None, None

    def _convert_to_unicode(self, mathml_content):
        """Convert simple MathML to Unicode characters"""
        try:
            # Parse MathML using lxml
            # Remove namespace for easier parsing
            clean_content = re.sub(r'xmlns="[^"]*"', '', mathml_content)
            clean_content = re.sub(r'<math[^>]*>', '<math>', clean_content)
            
            # Try to parse as XML
            try:
                root = etree.fromstring(clean_content)
                return self._parse_mathml_element(root)
            except:
                # Fallback to simple text extraction
                text_content = re.sub(r'<[^>]+>', '', mathml_content)
                return self._apply_unicode_mapping(text_content.strip())
                
        except Exception as e:
            # Final fallback
            text_content = re.sub(r'<[^>]+>', '', mathml_content)
            return self._apply_unicode_mapping(text_content.strip())

    def _parse_mathml_element(self, element):
        """Parse MathML element recursively"""
        tag = element.tag.lower()
        text = element.text or ''
        
        if tag == 'math' or tag == 'mrow':
            # Process children
            result = text
            for child in element:
                result += self._parse_mathml_element(child)
                if child.tail:
                    result += child.tail
            return result
            
        elif tag == 'mi':  # identifier
            return self._apply_unicode_mapping(text)
            
        elif tag == 'mn':  # number
            return text
            
        elif tag == 'mo':  # operator
            return self._apply_unicode_mapping(text)
            
        elif tag == 'msup':  # superscript
            children = list(element)
            if len(children) >= 2:
                base = self._parse_mathml_element(children[0])
                sup = self._parse_mathml_element(children[1])
                sup_unicode = self._to_superscript(sup)
                return f'{base}{sup_unicode}'
            return text
            
        elif tag == 'msub':  # subscript
            children = list(element)
            if len(children) >= 2:
                base = self._parse_mathml_element(children[0])
                sub = self._parse_mathml_element(children[1])
                sub_unicode = self._to_subscript(sub)
                return f'{base}{sub_unicode}'
            return text
            
        elif tag == 'mfrac':  # fraction
            children = list(element)
            if len(children) >= 2:
                num = self._parse_mathml_element(children[0])
                den = self._parse_mathml_element(children[1])
                # Try to use Unicode fractions for common cases
                if num == '1' and den == '2':
                    return '½'
                elif num == '1' and den == '3':
                    return '⅓'
                elif num == '2' and den == '3':
                    return '⅔'
                elif num == '1' and den == '4':
                    return '¼'
                elif num == '3' and den == '4':
                    return '¾'
                else:
                    return f'{num}/{den}'
            return text
            
        elif tag == 'mfenced':  # fenced expression
            open_fence = element.get('open', '(')
            close_fence = element.get('close', ')')
            content = ''
            for child in element:
                content += self._parse_mathml_element(child)
            return f'{open_fence}{content}{close_fence}'
            
        else:
            # For unknown tags, process children
            result = text
            for child in element:
                result += self._parse_mathml_element(child)
                if child.tail:
                    result += child.tail
            return result

    def _apply_unicode_mapping(self, text):
        """Apply Unicode mapping to text"""
        if not text:
            return ''
        
        # Apply character-by-character mapping
        result = ''
        for char in text:
            result += self.unicode_math_map.get(char, char)
        
        return result

    def _to_superscript(self, text):
        """Convert text to superscript Unicode characters"""
        result = ''
        for char in text:
            result += self.superscripts.get(char, char)
        return result

    def _to_subscript(self, text):
        """Convert text to subscript Unicode characters"""
        result = ''
        for char in text:
            result += self.subscripts.get(char, char)
        return result

    def _is_simple_inline_math(self, mathml_content):
        """Determine if MathML is simple enough for Unicode conversion"""
        # Check for complex structures that need SVG
        complex_tags = ['mtable', 'mroot', 'msqrt', 'munder', 'mover', 'munderover']
        
        for tag in complex_tags:
            if f'<{tag}' in mathml_content.lower():
                return False
        
        # Check if it's a simple expression (single line, few elements)
        tag_count = len(re.findall(r'<[^/][^>]*>', mathml_content))
        return tag_count <= 10  # Arbitrary threshold for "simple"

    def convert_html_with_mathml(self, html_content, base_path=""):
        """Convert HTML content using dual strategy: Unicode for inline, SVG for display"""
        def replace_mathml(match):
            try:
                mathml_content = match.group(0)
                
                # Determine if it's inline or block math based on display attribute
                inline = 'display="block"' not in mathml_content  # Default to inline unless explicitly block
                
                # Dual strategy: Unicode for simple inline math, SVG for complex/display math
                if inline:
                    # Convert to Unicode for simple inline math
                    try:
                        unicode_text = self._convert_to_unicode(mathml_content)
                        if unicode_text and unicode_text != '[math]':
                            return f'<span class="math-unicode">{unicode_text}</span>'
                    except Exception as e:
                        pass  # Fall through to SVG conversion
                
                # Convert to SVG for complex or display math
                try:
                    svg_filename, svg_content = self.mathml_to_svg(mathml_content, inline=inline)
                    
                    if svg_filename:
                        # Create relative path for EPUB
                        img_path = f"{base_path}math_images/{svg_filename}" if base_path else f"math_images/{svg_filename}"
                        
                        # Return img tag
                        alt_text = re.sub(r'<[^>]+>', '', mathml_content).strip() or "mathematical expression"
                        if inline:
                            style = "display: inline; vertical-align: middle; height: 1.2em; margin: 0 0.1em;"
                        else:
                            style = "display: block; margin: 0.5em auto; max-width: 100%;"
                        
                        return f'<img src="{img_path}" alt="{alt_text}" style="{style}" class="math-svg"/>'
                except Exception as e:
                    pass  # Fall through to fallback
                
                # Final fallback to text
                text_content = re.sub(r'<[^>]+>', '', mathml_content).strip()
                return f'<span class="math-fallback">{text_content or "[math]"}</span>'
                
            except Exception as e:
                print(f"Critical error in MathML processing: {e}")
                return f'<span class="math-error">[math error]</span>'
        
        try:
            # Replace MathML elements
            result = re.sub(
                r'<math[^>]*xmlns="http://www\.w3\.org/1998/Math/MathML"[^>]*>.*?</math>',
                replace_mathml,
                html_content,
                flags=re.DOTALL | re.IGNORECASE
            )
            
            return result
        except Exception as e:
            print(f"Critical error in HTML processing: {e}")
            return html_content  # Return original content if processing fails

    def get_generated_images(self):
        """Get list of generated image files"""
        return list(self.generated_images.values())

    def cleanup(self):
        """Clean up generated files"""
        for filename in self.generated_images.values():
            svg_path = self.output_dir / filename
            if svg_path.exists():
                svg_path.unlink()

# Test the converter
if __name__ == '__main__':
    converter = MathMLToSVGConverter()
    
    # Test cases
    test_cases = [
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><mo class="MathClass-bin">±</mo></mrow></math>',
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><mn>6</mn><mo class="MathClass-rel">&gt;</mo><mn>4</mn></mrow></math>',
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><mrow><mo class="MathClass-open">[</mo><mrow><mn>1</mn><mo class="MathClass-punc">,</mo><mn>3</mn></mrow><mo class="MathClass-close">]</mo></mrow></mrow></math>',
    ]
    
    for i, test in enumerate(test_cases):
        filename, svg_content = converter.mathml_to_svg(test)
        print(f"Test {i+1}: Generated {filename}")
        if svg_content:
            print(f"SVG length: {len(svg_content)} characters")
        print()
