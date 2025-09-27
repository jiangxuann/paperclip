"""
PDF processing and content extraction.

Handles PDF parsing, text extraction, and metadata analysis
using multiple extraction strategies for robustness.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from core.domain import PDFSource, ContentMetadata, ProcessingStatus
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Advanced PDF processor with multiple extraction strategies.
    
    Inspired by Open Notebook's content processing but specialized for PDF documents.
    Uses multiple libraries for robust extraction across different PDF types.
    """
    
    def __init__(self):
        """Initialize PDF processor with extraction libraries."""
        self.extractors = self._initialize_extractors()
    
    def _initialize_extractors(self) -> Dict[str, Any]:
        """Initialize PDF extraction libraries."""
        extractors = {}
        
        # Try to import PDF libraries
        try:
            import PyPDF2
            extractors['pypdf2'] = PyPDF2
        except ImportError:
            logger.warning("PyPDF2 not available")
        
        try:
            import pdfplumber
            extractors['pdfplumber'] = pdfplumber
        except ImportError:
            logger.warning("pdfplumber not available")
        
        try:
            import pymupdf as fitz
            extractors['pymupdf'] = fitz
        except ImportError:
            logger.warning("PyMuPDF not available")
        
        if not extractors:
            raise ProcessingError("No PDF extraction libraries available")
        
        return extractors
    
    async def process_pdf(self, source: PDFSource) -> PDFSource:
        """
        Process a PDF source and extract content.
        
        Args:
            source: PDFSource entity to process
            
        Returns:
            Updated PDFSource with extracted content
        """
        try:
            source.mark_processing()
            
            # Validate file exists
            if not Path(source.file_path).exists():
                raise ProcessingError(f"PDF file not found: {source.file_path}")
            
            # Extract content using best available method
            content = await self._extract_content(source.file_path)
            
            # Extract metadata
            metadata = await self._extract_metadata(source.file_path)
            
            # Update source with results
            source.raw_content = content
            source.metadata = ContentMetadata(metadata)
            source.page_count = metadata.get("page_count")
            source.file_size = metadata.get("file_size")
            
            # Analyze content quality
            content_quality = self._analyze_content_quality(content)
            if content_quality["quality_score"] < 0.5:
                logger.warning(f"Low quality content extracted from {source.file_path}")
            
            # Process content for better structure
            processed_content = await self._process_content(content)
            
            source.mark_completed(processed_content)
            logger.info(f"Successfully processed PDF: {source.file_path}")
            
            return source
            
        except Exception as e:
            error_msg = f"Failed to process PDF {source.file_path}: {str(e)}"
            logger.error(error_msg)
            source.mark_failed(error_msg)
            raise ProcessingError(error_msg) from e
    
    async def _extract_content(self, file_path: str) -> str:
        """Extract text content from PDF using best available method."""
        
        # Try extractors in order of preference
        extraction_methods = [
            ("pdfplumber", self._extract_with_pdfplumber),
            ("pymupdf", self._extract_with_pymupdf),
            ("pypdf2", self._extract_with_pypdf2),
        ]
        
        last_error = None
        
        for method_name, extractor_func in extraction_methods:
            if method_name not in self.extractors:
                continue
                
            try:
                content = await extractor_func(file_path)
                if content and len(content.strip()) > 100:  # Minimum content threshold
                    logger.info(f"Successfully extracted content using {method_name}")
                    return content
                else:
                    logger.warning(f"{method_name} extracted insufficient content")
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to extract with {method_name}: {str(e)}")
                continue
        
        # If all methods failed
        if last_error:
            raise ProcessingError(f"All PDF extraction methods failed. Last error: {str(last_error)}")
        else:
            raise ProcessingError("No suitable PDF extraction method available")
    
    async def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract content using pdfplumber (best for complex layouts)."""
        import pdfplumber
        
        content_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text
                text = page.extract_text()
                if text:
                    content_parts.append(text)
                
                # Extract tables if present
                tables = page.extract_tables()
                for table in tables:
                    # Convert table to text representation
                    table_text = self._table_to_text(table)
                    content_parts.append(f"\n[TABLE]\n{table_text}\n[/TABLE]\n")
        
        return "\n\n".join(content_parts)
    
    async def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract content using PyMuPDF (good for general PDFs)."""
        import pymupdf as fitz
        
        content_parts = []
        
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            if text:
                content_parts.append(text)
        
        doc.close()
        return "\n\n".join(content_parts)
    
    async def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract content using PyPDF2 (fallback method)."""
        import PyPDF2
        
        content_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    content_parts.append(text)
        
        return "\n\n".join(content_parts)
    
    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {
            "file_path": file_path,
            "file_size": Path(file_path).stat().st_size,
        }
        
        # Try to get PDF-specific metadata
        try:
            if "pdfplumber" in self.extractors:
                metadata.update(await self._get_pdfplumber_metadata(file_path))
            elif "pymupdf" in self.extractors:
                metadata.update(await self._get_pymupdf_metadata(file_path))
            elif "pypdf2" in self.extractors:
                metadata.update(await self._get_pypdf2_metadata(file_path))
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {str(e)}")
        
        return metadata
    
    async def _get_pdfplumber_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata using pdfplumber."""
        import pdfplumber
        
        with pdfplumber.open(file_path) as pdf:
            return {
                "page_count": len(pdf.pages),
                "creator": pdf.metadata.get("Creator"),
                "producer": pdf.metadata.get("Producer"),
                "title": pdf.metadata.get("Title"),
                "author": pdf.metadata.get("Author"),
                "subject": pdf.metadata.get("Subject"),
                "creation_date": pdf.metadata.get("CreationDate"),
            }
    
    async def _get_pymupdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata using PyMuPDF."""
        import pymupdf as fitz
        
        doc = fitz.open(file_path)
        metadata = {
            "page_count": doc.page_count,
            **doc.metadata
        }
        doc.close()
        return metadata
    
    async def _get_pypdf2_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata using PyPDF2."""
        import PyPDF2
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = {"page_count": len(pdf_reader.pages)}
            
            if pdf_reader.metadata:
                metadata.update({
                    "title": pdf_reader.metadata.get("/Title"),
                    "author": pdf_reader.metadata.get("/Author"),
                    "subject": pdf_reader.metadata.get("/Subject"),
                    "creator": pdf_reader.metadata.get("/Creator"),
                    "producer": pdf_reader.metadata.get("/Producer"),
                    "creation_date": pdf_reader.metadata.get("/CreationDate"),
                })
            
            return metadata
    
    def _analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze the quality of extracted content."""
        if not content:
            return {"quality_score": 0.0, "issues": ["No content extracted"]}
        
        issues = []
        
        # Check for common extraction issues
        char_count = len(content)
        word_count = len(content.split())
        
        # Too short
        if char_count < 500:
            issues.append("Content too short")
        
        # Too many special characters (indicates OCR issues)
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / char_count
        if special_char_ratio > 0.3:
            issues.append("High special character ratio")
        
        # Repeated characters (extraction artifacts)
        if any(char * 10 in content for char in ".-_|"):
            issues.append("Repeated character artifacts")
        
        # Calculate quality score
        quality_score = 1.0
        if char_count < 500:
            quality_score -= 0.5
        if special_char_ratio > 0.3:
            quality_score -= 0.3
        if word_count < 50:
            quality_score -= 0.2
        
        quality_score = max(0.0, quality_score)
        
        return {
            "quality_score": quality_score,
            "char_count": char_count,
            "word_count": word_count,
            "special_char_ratio": special_char_ratio,
            "issues": issues,
        }
    
    async def _process_content(self, content: str) -> str:
        """Process and clean extracted content."""
        if not content:
            return content
        
        # Basic cleaning
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and page numbers
            if not line or line.isdigit():
                continue
            
            # Skip lines with only special characters
            if all(not c.isalnum() for c in line):
                continue
            
            cleaned_lines.append(line)
        
        # Rejoin with proper spacing
        processed_content = '\n'.join(cleaned_lines)
        
        # Remove excessive whitespace
        import re
        processed_content = re.sub(r'\n{3,}', '\n\n', processed_content)
        processed_content = re.sub(r' {2,}', ' ', processed_content)
        
        return processed_content
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table data to readable text format."""
        if not table:
            return ""
        
        # Simple table formatting
        text_lines = []
        for row in table:
            if row and any(cell for cell in row if cell):  # Skip empty rows
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                text_lines.append(row_text)
        
        return "\n".join(text_lines)
