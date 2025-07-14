"""
PDF processing and text extraction module
"""

import logging
from pathlib import Path
import re
import PyPDF2
import pdfplumber
from typing import List, Dict, Optional, Tuple
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class PDFProcessor:
    """Handle PDF processing and text extraction"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("PDF processor initialized")
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Extracted text
        """
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if path.suffix.lower() not in config.SUPPORTED_PDF_FORMATS:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        # Try pdfplumber first (better for complex layouts)
        try:
            text = self._extract_with_pdfplumber(pdf_path)
            if text and len(text.strip()) > 100:  # Reasonable amount of text
                self.logger.info(f"Successfully extracted text with pdfplumber: {len(text)} chars")
                return text
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Fall back to PyPDF2
        try:
            text = self._extract_with_pypdf2(pdf_path)
            self.logger.info(f"Successfully extracted text with PyPDF2: {len(text)} chars")
            return text
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction also failed: {e}")
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Extracted text
        """
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    # Extract text
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(f"--- Page {i+1} ---\n{page_text}")
                    
                    # Also try to extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = self._format_table(table)
                            text_parts.append(f"\n[Table on page {i+1}]\n{table_text}")
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting page {i+1} with pdfplumber: {e}")
                    continue
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Extracted text
        """
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {i+1} ---\n{page_text}")
                except Exception as e:
                    self.logger.warning(f"Error extracting page {i+1} with PyPDF2: {e}")
                    continue
        
        return "\n\n".join(text_parts)
    
    def extract_pages(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict[int, str]:
        """Extract specific pages from PDF
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: List of page numbers to extract (1-indexed), None for all
            
        Returns:
            dict: Page number to text mapping
        """
        pages_text = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Determine which pages to extract
                if page_numbers is None:
                    page_numbers = list(range(1, total_pages + 1))
                else:
                    # Validate page numbers
                    page_numbers = [p for p in page_numbers if 1 <= p <= total_pages]
                
                for page_num in page_numbers:
                    try:
                        page = pdf.pages[page_num - 1]  # 0-indexed
                        text = page.extract_text()
                        if text:
                            pages_text[page_num] = text
                    except Exception as e:
                        self.logger.warning(f"Error extracting page {page_num}: {e}")
                        continue
            
        except Exception as e:
            self.logger.error(f"Error extracting pages: {e}")
            raise
        
        return pages_text
    
    def extract_tables(self, pdf_path: str) -> List[Dict[str, any]]:
        """Extract tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            list: List of table data with metadata
        """
        tables_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        tables = page.extract_tables()
                        
                        for j, table in enumerate(tables):
                            if table and len(table) > 1:  # At least header + 1 row
                                table_info = {
                                    'page': i + 1,
                                    'table_index': j,
                                    'data': table,
                                    'formatted': self._format_table(table)
                                }
                                tables_data.append(table_info)
                                
                    except Exception as e:
                        self.logger.warning(f"Error extracting tables from page {i+1}: {e}")
                        continue
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            raise
        
        self.logger.info(f"Extracted {len(tables_data)} tables from PDF")
        return tables_data
    
    def extract_images(self, pdf_path: str) -> List[Dict[str, any]]:
        """Extract embedded images from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            list: List of image metadata (not implemented in basic version)
        """
        # Note: Full image extraction requires additional libraries
        # This is a placeholder for future enhancement
        self.logger.info("Image extraction not implemented in basic version")
        return []
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, any]:
        """Get PDF metadata and information
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict: PDF information
        """
        info = {
            'path': pdf_path,
            'filename': Path(pdf_path).name,
            'size_bytes': Path(pdf_path).stat().st_size,
            'pages': 0,
            'metadata': {}
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Page count
                info['pages'] = len(pdf_reader.pages)
                
                # Metadata
                if pdf_reader.metadata:
                    info['metadata'] = {
                        'title': getattr(pdf_reader.metadata, 'title', None),
                        'author': getattr(pdf_reader.metadata, 'author', None),
                        'subject': getattr(pdf_reader.metadata, 'subject', None),
                        'creator': getattr(pdf_reader.metadata, 'creator', None),
                        'producer': getattr(pdf_reader.metadata, 'producer', None),
                        'creation_date': str(getattr(pdf_reader.metadata, 'creation_date', None)),
                        'modification_date': str(getattr(pdf_reader.metadata, 'modification_date', None))
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting PDF info: {e}")
        
        return info
    
    def search_text(self, pdf_path: str, search_terms: List[str], case_sensitive: bool = False) -> Dict[str, List[Tuple[int, str]]]:
        """Search for terms in PDF
        
        Args:
            pdf_path: Path to PDF file
            search_terms: List of terms to search for
            case_sensitive: Whether search is case sensitive
            
        Returns:
            dict: Term to list of (page_num, context) tuples
        """
        results = {term: [] for term in search_terms}
        
        try:
            # Extract all pages
            pages_text = self.extract_pages(pdf_path)
            
            for page_num, text in pages_text.items():
                # Prepare text for searching
                search_text = text if case_sensitive else text.lower()
                
                for term in search_terms:
                    search_term = term if case_sensitive else term.lower()
                    
                    # Find all occurrences
                    if search_term in search_text:
                        # Get context around the term
                        contexts = self._get_search_contexts(text, term, case_sensitive)
                        
                        for context in contexts:
                            results[term].append((page_num, context))
            
        except Exception as e:
            self.logger.error(f"Error searching PDF: {e}")
            raise
        
        return results
    
    def _format_table(self, table: List[List[str]]) -> str:
        """Format table data as text
        
        Args:
            table: Table data as list of lists
            
        Returns:
            str: Formatted table
        """
        if not table:
            return ""
        
        # Calculate column widths
        col_widths = []
        for col_idx in range(len(table[0])):
            max_width = max(len(str(row[col_idx]) if col_idx < len(row) else "") for row in table)
            col_widths.append(min(max_width, 30))  # Cap at 30 chars
        
        # Format rows
        formatted_rows = []
        for row_idx, row in enumerate(table):
            formatted_cells = []
            for col_idx, cell in enumerate(row):
                if col_idx < len(col_widths):
                    cell_str = str(cell) if cell else ""
                    cell_str = cell_str[:col_widths[col_idx]]  # Truncate if needed
                    formatted_cells.append(cell_str.ljust(col_widths[col_idx]))
            
            formatted_rows.append(" | ".join(formatted_cells))
            
            # Add separator after header
            if row_idx == 0:
                separator = "-+-".join("-" * w for w in col_widths)
                formatted_rows.append(separator)
        
        return "\n".join(formatted_rows)
    
    def _get_search_contexts(self, text: str, term: str, case_sensitive: bool = False, context_chars: int = 50) -> List[str]:
        """Get context snippets around search term
        
        Args:
            text: Full text to search
            term: Search term
            case_sensitive: Whether search is case sensitive
            context_chars: Characters of context on each side
            
        Returns:
            list: Context snippets
        """
        contexts = []
        
        # Prepare for search
        search_text = text if case_sensitive else text.lower()
        search_term = term if case_sensitive else term.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = search_text.find(search_term, start)
            if pos == -1:
                break
            
            # Extract context
            context_start = max(0, pos - context_chars)
            context_end = min(len(text), pos + len(term) + context_chars)
            
            context = text[context_start:context_end]
            
            # Add ellipsis if truncated
            if context_start > 0:
                context = "..." + context
            if context_end < len(text):
                context = context + "..."
            
            contexts.append(context)
            
            start = pos + 1
        
        return contexts
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi')
        text = text.replace('ﬂ', 'fl')
        text = text.replace('™', 'TM')
        text = text.replace('®', '(R)')
        
        # Remove page headers/footers patterns
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'\d+\s*\|\s*Page', '', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(\w)', r'\1 \2', text)
        
        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()


def detect_text_structure(text: str) -> Dict[str, any]:
    """Detect structure in extracted text
    
    Args:
        text: Extracted text
        
    Returns:
        dict: Detected structure information
    """
    structure = {
        'has_table_of_contents': False,
        'sections': [],
        'has_tables': False,
        'has_lists': False,
        'likely_datasheet': False
    }
    
    lines = text.split('\n')
    
    # Check for table of contents
    toc_keywords = ['table of contents', 'contents', 'index']
    for line in lines[:50]:  # Check first 50 lines
        if any(keyword in line.lower() for keyword in toc_keywords):
            structure['has_table_of_contents'] = True
            break
    
    # Detect sections (numbered or with keywords)
    section_pattern = re.compile(r'^(\d+\.?\d*\s+[A-Z][A-Za-z\s]+|[A-Z][A-Z\s]+:)')
    for i, line in enumerate(lines):
        if section_pattern.match(line.strip()):
            structure['sections'].append({
                'line_num': i,
                'title': line.strip()
            })
    
    # Check for tables (simple heuristic)
    if '|' in text or re.search(r'\s{2,}\S+\s{2,}\S+', text):
        structure['has_tables'] = True
    
    # Check for lists
    if re.search(r'^\s*[\-•▪*]\s+', text, re.MULTILINE):
        structure['has_lists'] = True
    
    # Check if likely datasheet
    datasheet_keywords = ['electrical characteristics', 'pin configuration', 'absolute maximum ratings',
                         'recommended operating conditions', 'timing diagram', 'package']
    keyword_count = sum(1 for keyword in datasheet_keywords if keyword in text.lower())
    if keyword_count >= 3:
        structure['likely_datasheet'] = True
    
    return structure


def clean_pdf_text(raw_text: str) -> str:
    """Clean extracted PDF text
    
    Args:
        raw_text: Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    processor = PDFProcessor()
    return processor.clean_text(raw_text)


if __name__ == "__main__":
    # Test the PDF processor
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample PDF if provided
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        processor = PDFProcessor()
        
        print(f"Testing PDF processor with: {pdf_path}")
        
        # Get info
        info = processor.get_pdf_info(pdf_path)
        print(f"\nPDF Info:")
        print(f"  Pages: {info['pages']}")
        print(f"  Size: {info['size_bytes'] / 1024:.1f} KB")
        
        # Extract text
        text = processor.extract_text(pdf_path)
        print(f"\nExtracted text length: {len(text)} characters")
        print(f"First 500 characters:\n{text[:500]}...")
        
        # Detect structure
        structure = detect_text_structure(text)
        print(f"\nDetected structure:")
        print(f"  Has TOC: {structure['has_table_of_contents']}")
        print(f"  Sections found: {len(structure['sections'])}")
        print(f"  Likely datasheet: {structure['likely_datasheet']}")
    else:
        print("Usage: python pdf_processor.py <pdf_file>")