"""
Text content processing and structured extraction.

Handles direct text input and extracts structured content blocks,
media assets, and entities into the database schema.
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
import re
from uuid import UUID

from core.domain import ContentSource, ContentMetadata, ProcessingStatus
from core.exceptions import ProcessingError
from db.repositories import (
    DocumentPageRepository, ContentBlockRepository,
    MediaAssetRepository, ExtractedEntityRepository
)

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Text processor for direct text input with structured extraction.

    Parses plain text or markdown into structured content blocks
    and populates the database schema.
    """

    def __init__(self,
                 page_repo: DocumentPageRepository,
                 content_repo: ContentBlockRepository,
                 media_repo: MediaAssetRepository,
                 entity_repo: ExtractedEntityRepository):
        """Initialize text processor."""
        self.page_repo = page_repo
        self.content_repo = content_repo
        self.media_repo = media_repo
        self.entity_repo = entity_repo

    async def process_text(self, source: ContentSource) -> ContentSource:
        """
        Process text content and extract structured data.

        Args:
            source: ContentSource with text content

        Returns:
            Updated ContentSource with processed content and structured data
        """
        try:
            source.mark_processing()

            # Get text content
            if not source.raw_content:
                raise ProcessingError("No text content provided")

            text_content = source.raw_content

            # Extract structured content into database
            document_id = await self._extract_structured_content(text_content, source.id)

            # Create metadata
            metadata = self._extract_metadata(text_content)
            source.metadata = ContentMetadata(metadata)

            # Process content for better structure (basic cleaning)
            processed_content = self._process_content(text_content)

            source.mark_completed(processed_content)
            logger.info(f"Successfully processed text content for source {source.id}")

            return source

        except Exception as e:
            error_msg = f"Failed to process text content: {str(e)}"
            logger.error(error_msg)
            source.mark_failed(error_msg)
            raise ProcessingError(error_msg) from e

    async def _extract_structured_content(self, text_content: str, document_id: UUID) -> UUID:
        """
        Extract structured content from text into database tables.

        Args:
            text_content: The text content to process
            document_id: Document ID for database records

        Returns:
            Document ID
        """
        try:
            # Create a single page for text content
            page_id = await self.page_repo.create(
                document_id=document_id,
                page_number=1,
                text_content=text_content,
                metadata={"content_type": "text", "word_count": len(text_content.split())}
            )

            # Parse content into blocks
            content_blocks = self._parse_text_blocks(text_content)

            # Add document and page IDs
            for i, block in enumerate(content_blocks):
                block.update({
                    "document_id": document_id,
                    "page_id": page_id,
                    "order_index": i
                })

            # Save content blocks
            if content_blocks:
                await self.content_repo.create_batch(content_blocks)

            # Extract entities
            await self._extract_entities(document_id, page_id, content_blocks)

            return document_id

        except Exception as e:
            logger.warning(f"Structured text extraction failed: {str(e)}")
            raise

    def _parse_text_blocks(self, text_content: str) -> List[Dict[str, Any]]:
        """
        Parse text content into structured blocks.

        Supports basic markdown and plain text structure detection.
        """
        blocks = []
        lines = text_content.split('\n')

        current_block = {"type": "paragraph", "content": "", "metadata": {}}

        for line in lines:
            line = line.rstrip()
            if not line:
                # Empty line - finish current block
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))
                    current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Check for markdown headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                # Finish previous block
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))

                # Start new heading block
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                blocks.append(self._create_block({
                    "type": "heading",
                    "content": content,
                    "metadata": {"level": level}
                }))
                current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Check for list items
            list_match = re.match(r'^[\s]*[-\*\+•]\s+(.+)$', line)
            if list_match:
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))

                blocks.append(self._create_block({
                    "type": "list_item",
                    "content": list_match.group(1),
                    "metadata": {}
                }))
                current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Check for numbered lists
            numbered_match = re.match(r'^[\s]*\d+\.?\s+(.+)$', line)
            if numbered_match:
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))

                blocks.append(self._create_block({
                    "type": "list_item",
                    "content": numbered_match.group(1),
                    "metadata": {"numbered": True}
                }))
                current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Check for quotes
            if line.startswith('> '):
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))

                blocks.append(self._create_block({
                    "type": "quote",
                    "content": line[2:],
                    "metadata": {}
                }))
                current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Check for code blocks (basic detection)
            if line.startswith('```') or line.startswith('    ') or line.startswith('\t'):
                if current_block["content"].strip():
                    blocks.append(self._create_block(current_block))

                blocks.append(self._create_block({
                    "type": "code",
                    "content": line,
                    "metadata": {}
                }))
                current_block = {"type": "paragraph", "content": "", "metadata": {}}
                continue

            # Add to current paragraph block
            if current_block["content"]:
                current_block["content"] += " " + line
            else:
                current_block["content"] = line

        # Finish last block
        if current_block["content"].strip():
            blocks.append(self._create_block(current_block))

        return blocks

    def _create_block(self, block_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized block dictionary."""
        block_type_mapping = {
            "heading": "heading",
            "paragraph": "paragraph",
            "list_item": "list_item",
            "quote": "quote",
            "code": "code"
        }

        return {
            "block_type": block_type_mapping.get(block_info["type"], "paragraph"),
            "text_content": block_info["content"].strip(),
            "metadata": block_info.get("metadata", {})
        }

    async def _extract_entities(self, document_id: UUID, page_id: UUID, blocks: List[Dict]) -> None:
        """Extract entities from content blocks."""
        entities = []

        for block in blocks:
            text = block['text_content']

            # Extract numbers (statistics)
            numbers = re.findall(r'\b\d+(\.\d+)?\b', text)
            for number in numbers:
                # Check context for percentages, currencies, etc.
                context = text[max(0, text.find(number) - 50):text.find(number) + len(number) + 50]

                entity_type = "statistic"
                normalized = {"value": number, "type": "number"}

                # Check for percentage
                if '%' in context:
                    normalized["type"] = "percentage"
                # Check for currency
                elif any(curr in context.lower() for curr in ['$€£¥']):
                    normalized["type"] = "currency"
                # Check for dates (basic)
                elif re.search(r'\b(19|20)\d{2}\b', number):
                    normalized["type"] = "date"

                entities.append({
                    "document_id": document_id,
                    "page_id": page_id,
                    "block_id": block['id'],
                    "entity_type": entity_type,
                    "raw_text": number,
                    "normalized": normalized,
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
                    "page_id": page_id,
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

    def _extract_metadata(self, text_content: str) -> Dict[str, Any]:
        """Extract metadata from text content."""
        lines = text_content.split('\n')
        word_count = len(text_content.split())
        char_count = len(text_content)

        # Estimate reading time (words per minute)
        reading_time = word_count / 200  # Average reading speed

        # Detect language (basic)
        language = "en"  # Default assumption

        # Check for markdown
        has_markdown = bool(re.search(r'^#{1,6}\s+', text_content, re.MULTILINE))

        return {
            "word_count": word_count,
            "char_count": char_count,
            "line_count": len(lines),
            "estimated_reading_time": reading_time,
            "language": language,
            "has_markdown": has_markdown,
            "content_type": "text"
        }

    def _process_content(self, text_content: str) -> str:
        """Process and clean text content."""
        if not text_content:
            return text_content

        # Basic cleaning
        lines = text_content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)

        # Rejoin with proper spacing
        processed_content = '\n\n'.join(cleaned_lines)

        # Remove excessive whitespace
        import re
        processed_content = re.sub(r'\n{3,}', '\n\n', processed_content)
        processed_content = re.sub(r' {2,}', ' ', processed_content)

        return processed_content