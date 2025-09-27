"""
Structured PDF processing with content extraction into database schema.

Extends the basic PDF processor to extract structured content blocks,
media assets, and entities into the database for advanced querying.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import re
from uuid import UUID

from .processor import PDFProcessor
from core.domain import PDFSource, ContentMetadata, ProcessingStatus
from core.exceptions import ProcessingError
from db.repositories import (
    DocumentPageRepository, ContentBlockRepository,
    MediaAssetRepository, ExtractedEntityRepository
)

logger = logging.getLogger(__name__)


class StructuredPDFProcessor(PDFProcessor):
    """
    Enhanced PDF processor that extracts structured content.

    Builds on the basic PDF processor but also populates the database
    with structured content blocks, media assets, and extracted entities.
    """

    def __init__(self,
                 page_repo: DocumentPageRepository,
                 content_repo: ContentBlockRepository,
                 media_repo: MediaAssetRepository,
                 entity_repo: ExtractedEntityRepository):
        """Initialize structured PDF processor."""
        super().__init__()
        self.page_repo = page_repo
        self.content_repo = content_repo
        self.media_repo = media_repo
        self.entity_repo = entity_repo

    async def process(self, source: PDFSource) -> PDFSource:
        """
        Process a PDF source and extract structured content.

        Args:
            source: PDFSource entity to process

        Returns:
            Updated PDFSource with extracted content and structured data
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

            # Extract structured content into database
            document_id = await self._extract_structured_content(source.file_path, source.id)

            # Analyze content quality
            content_quality = self._analyze_content_quality(content)
            if content_quality["quality_score"] < 0.5:
                logger.warning(f"Low quality content extracted from {source.file_path}")

            # Process content for better structure
            processed_content = await self._process_content(content)

            source.mark_completed(processed_content)
            logger.info(f"Successfully processed PDF with structured extraction: {source.file_path}")

            return source

        except Exception as e:
            error_msg = f"Failed to process PDF {source.file_path}: {str(e)}"
            logger.error(error_msg)
            source.mark_failed(error_msg)
            raise ProcessingError(error_msg) from e

    async def _extract_structured_content(self, file_path: str, document_id: UUID) -> UUID:
        """
        Extract structured content from PDF into database tables.

        Args:
            file_path: Path to the PDF file
            document_id: Document ID for database records

        Returns:
            Document ID
        """
        try:
            # Use PyMuPDF for structured extraction if available
            if "pymupdf" in self.extractors:
                await self._extract_with_pymupdf_structured(file_path, document_id)
            elif "pdfplumber" in self.extractors:
                await self._extract_with_pdfplumber_structured(file_path, document_id)
            else:
                logger.warning("No structured extraction library available, falling back to basic extraction")
                await self._extract_basic_structured(file_path, document_id)

        except Exception as e:
            logger.warning(f"Structured extraction failed: {str(e)}, continuing with basic processing")

        return document_id

    async def _extract_with_pymupdf_structured(self, file_path: str, document_id: UUID) -> None:
        """Extract structured content using PyMuPDF."""
        import pymupdf as fitz

        doc = fitz.open(file_path)
        page_ids = []

        try:
            # Create document pages
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_content = page.get_text()

                # Create page record
                page_id = await self.page_repo.create(
                    document_id=document_id,
                    page_number=page_num + 1,
                    text_content=text_content,
                    metadata={"width": page.rect.width, "height": page.rect.height}
                )
                page_ids.append(page_id)

                # Extract content blocks
                blocks = page.get_text("dict")
                content_blocks = []
                order_index = 0

                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        # Text block
                        block_text = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"]

                        if block_text.strip():
                            # Determine block type
                            block_type = self._classify_text_block(block_text)

                            content_blocks.append({
                                "document_id": document_id,
                                "page_id": page_id,
                                "block_type": block_type,
                                "order_index": order_index,
                                "text_content": block_text.strip(),
                                "bbox": {
                                    "x": block["bbox"][0],
                                    "y": block["bbox"][1],
                                    "width": block["bbox"][2] - block["bbox"][0],
                                    "height": block["bbox"][3] - block["bbox"][1]
                                },
                                "metadata": {}
                            })
                            order_index += 1

                # Save content blocks
                if content_blocks:
                    await self.content_repo.create_batch(content_blocks)

                # Extract images
                images = page.get_images(full=True)
                media_assets = []

                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        # In a real implementation, you'd save the image to storage
                        # For now, we'll just record metadata
                        media_assets.append({
                            "document_id": document_id,
                            "page_id": page_id,
                            "media_type": "image",
                            "file_url": f"placeholder://{document_id}/page_{page_num + 1}/image_{img_index}",
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "format": base_image["ext"],
                            "size_bytes": len(base_image["image"]),
                            "metadata": {"bbox": img[1:5] if len(img) > 4 else None}
                        })

                # Save media assets
                if media_assets:
                    await self.media_repo.create_batch(media_assets)

            # Extract entities (basic implementation)
            await self._extract_entities_basic(document_id, page_ids)

        finally:
            doc.close()

    async def _extract_with_pdfplumber_structured(self, file_path: str, document_id: UUID) -> None:
        """Extract structured content using pdfplumber."""
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            page_ids = []

            for page_num, page in enumerate(pdf.pages):
                text_content = page.extract_text()

                # Create page record
                page_id = await self.page_repo.create(
                    document_id=document_id,
                    page_number=page_num + 1,
                    text_content=text_content,
                    metadata={"width": page.width, "height": page.height}
                )
                page_ids.append(page_id)

                # Extract content blocks
                content_blocks = []
                order_index = 0

                # Extract text by lines/blocks
                for char_block in page.chars:
                    # Group characters into blocks (simplified)
                    if char_block['text'].strip():
                        block_type = self._classify_text_block(char_block['text'])

                        content_blocks.append({
                            "document_id": document_id,
                            "page_id": page_id,
                            "block_type": block_type,
                            "order_index": order_index,
                            "text_content": char_block['text'].strip(),
                            "bbox": {
                                "x": char_block['x0'],
                                "y": char_block['top'],
                                "width": char_block['x1'] - char_block['x0'],
                                "height": char_block['bottom'] - char_block['top']
                            },
                            "metadata": {"font": char_block.get('fontname'), "size": char_block.get('size')}
                        })
                        order_index += 1

                # Save content blocks (deduplicate)
                unique_blocks = self._deduplicate_blocks(content_blocks)
                if unique_blocks:
                    await self.content_repo.create_batch(unique_blocks)

                # Extract tables
                tables = page.extract_tables()
                table_assets = []

                for table_idx, table in enumerate(tables):
                    table_assets.append({
                        "document_id": document_id,
                        "page_id": page_id,
                        "media_type": "table",
                        "file_url": f"placeholder://{document_id}/page_{page_num + 1}/table_{table_idx}",
                        "metadata": {"table_data": table}
                    })

                if table_assets:
                    await self.media_repo.create_batch(table_assets)

            # Extract entities
            await self._extract_entities_basic(document_id, page_ids)

    async def _extract_basic_structured(self, file_path: str, document_id: UUID) -> None:
        """Basic structured extraction fallback."""
        # Extract basic content and split into pages
        content = await self._extract_content(file_path)

        # Split by pages (rough approximation)
        pages = content.split('\n\n')  # Very basic page splitting

        page_ids = []
        for page_num, page_content in enumerate(pages):
            if page_content.strip():
                page_id = await self.page_repo.create(
                    document_id=document_id,
                    page_number=page_num + 1,
                    text_content=page_content
                )
                page_ids.append(page_id)

                # Create basic content blocks
                blocks = [{
                    "document_id": document_id,
                    "page_id": page_id,
                    "block_type": "paragraph",
                    "order_index": 0,
                    "text_content": page_content.strip(),
                    "metadata": {}
                }]

                await self.content_repo.create_batch(blocks)

        # Extract entities
        await self._extract_entities_basic(document_id, page_ids)

    def _classify_text_block(self, text: str) -> str:
        """Classify a text block into content type."""
        text = text.strip()

        # Check for headings
        if re.match(r'^#{1,6}\s+', text):
            return "heading"
        if text.isupper() and len(text.split()) <= 10:
            return "heading"
        if re.match(r'^[A-Z][^.!?]*$', text) and len(text.split()) <= 15:
            return "heading"

        # Check for lists
        if re.match(r'^[\s]*[-\*\+•]\s+', text):
            return "list_item"
        if re.match(r'^[\s]*\d+\.?\s+', text):
            return "list_item"

        # Check for quotes
        if text.startswith('"') and text.endswith('"'):
            return "quote"
        if text.startswith("'") and text.endswith("'"):
            return "quote"

        # Check for code (basic detection)
        if '`' in text or '    ' in text:
            return "code"

        # Default to paragraph
        return "paragraph"

    def _deduplicate_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar blocks."""
        seen = set()
        unique_blocks = []

        for block in blocks:
            text = block['text_content'].strip()
            if text and text not in seen:
                seen.add(text)
                unique_blocks.append(block)

        return unique_blocks

    async def _extract_entities_basic(self, document_id: UUID, page_ids: List[UUID]) -> None:
        """Extract basic entities like statistics and quotes."""
        entities = []

        # Get all content blocks
        blocks = await self.content_repo.get_by_document_id(document_id)

        for block in blocks:
            text = block['text_content']

            # Extract numbers (basic statistics)
            numbers = re.findall(r'\b\d+(\.\d+)?\b', text)
            for number in numbers:
                # Check if it's part of a statistic
                context = text[max(0, text.find(number) - 50):text.find(number) + len(number) + 50]

                entities.append({
                    "document_id": document_id,
                    "page_id": block['page_id'],
                    "block_id": block['id'],
                    "entity_type": "statistic",
                    "raw_text": number,
                    "normalized": {"value": number, "type": "number"},
                    "confidence": 0.8,
                    "span_start": text.find(number),
                    "span_end": text.find(number) + len(number),
                    "metadata": {"context": context}
                })

            # Extract quoted text
            quotes = re.findall(r'"([^"]*)"', text)
            for quote in quotes:
                entities.append({
                    "document_id": document_id,
                    "page_id": block['page_id'],
                    "block_id": block['id'],
                    "entity_type": "quote",
                    "raw_text": f'"{quote}"',
                    "confidence": 0.9,
                    "span_start": text.find(f'"{quote}"'),
                    "span_end": text.find(f'"{quote}"') + len(quote) + 2,
                    "metadata": {}
                })

        # Save entities
        if entities:
            await self.entity_repo.create_batch(entities)