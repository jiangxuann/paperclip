"""
Content analysis and chapter extraction using AI.

Analyzes processed content and intelligently segments it into
logical chapters suitable for video script generation.
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from core.domain import ContentSource, Chapter, ChapterId, ProcessingStatus
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    AI-powered content analyzer that understands document structure
    and extracts semantic meaning from content.
    """
    
    def __init__(self, ai_client=None):
        """Initialize content analyzer with AI client."""
        self.ai_client = ai_client  # Will be injected with AI service
        
    async def analyze_content(self, source: ContentSource) -> Dict[str, Any]:
        """
        Analyze content structure and extract key insights.
        
        Args:
            source: ContentSource with processed content
            
        Returns:
            Analysis results including topics, structure, and metadata
        """
        if not source.processed_content:
            raise ProcessingError("No processed content available for analysis")
        
        content = source.processed_content
        
        # Basic structural analysis
        structure_analysis = self._analyze_structure(content)
        
        # AI-powered analysis if available
        ai_analysis = {}
        if self.ai_client:
            try:
                ai_analysis = await self._ai_analyze_content(content)
            except Exception as e:
                logger.warning(f"AI analysis failed: {str(e)}")
        
        # Combine analyses
        analysis = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "estimated_reading_time": self._estimate_reading_time(content),
            **structure_analysis,
            **ai_analysis,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
        
        return analysis
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze basic document structure."""
        lines = content.split('\n')
        
        # Find potential headings
        headings = []
        heading_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headings
            r'^(.+)\n=+$',       # Underlined headings
            r'^(.+)\n-+$',       # Underlined headings
            r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS headings
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in heading_patterns:
                if re.match(pattern, line):
                    headings.append({
                        "text": line,
                        "line_number": i,
                        "level": self._estimate_heading_level(line)
                    })
                    break
        
        # Analyze paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1)
        
        return {
            "headings": headings,
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": avg_paragraph_length,
            "has_clear_structure": len(headings) > 2,
        }
    
    def _estimate_heading_level(self, heading: str) -> int:
        """Estimate heading level based on formatting."""
        if heading.startswith('#'):
            return heading.count('#')
        elif heading.isupper():
            return 1
        else:
            return 2
    
    def _estimate_reading_time(self, content: str, wpm: int = 200) -> float:
        """Estimate reading time in minutes."""
        word_count = len(content.split())
        return word_count / wpm
    
    async def _ai_analyze_content(self, content: str) -> Dict[str, Any]:
        """Use AI to analyze content structure and topics."""
        
        # Prepare analysis prompt
        prompt = f"""
        Analyze the following content and provide a structured analysis:
        
        Content:
        {content[:3000]}...  # Truncate for token limits
        
        Please provide:
        1. Main topics covered (up to 10 key topics)
        2. Content type (academic paper, blog post, documentation, etc.)
        3. Target audience level (beginner, intermediate, advanced)
        4. Tone and style (formal, casual, technical, etc.)
        5. Suggested logical break points for chapters
        
        Return as JSON format.
        """
        
        # Call AI service
        response = await self.ai_client.analyze_content(prompt)
        
        # Parse and validate response
        try:
            import json
            analysis = json.loads(response)
            return {
                "ai_topics": analysis.get("topics", []),
                "content_type": analysis.get("content_type", "unknown"),
                "audience_level": analysis.get("audience_level", "general"),
                "tone": analysis.get("tone", "neutral"),
                "suggested_breaks": analysis.get("suggested_breaks", []),
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI analysis response")
            return {}


class ChapterExtractor:
    """
    Extracts logical chapters from analyzed content.
    
    Uses both rule-based and AI-powered approaches to create
    coherent chapters suitable for video script generation.
    """
    
    def __init__(self, ai_client=None, min_chapter_length: int = 300, max_chapter_length: int = 2000):
        """Initialize chapter extractor."""
        self.ai_client = ai_client
        self.min_chapter_length = min_chapter_length
        self.max_chapter_length = max_chapter_length
    
    async def extract_chapters(self, source: ContentSource, analysis: Dict[str, Any]) -> List[Chapter]:
        """
        Extract chapters from content source.
        
        Args:
            source: ContentSource with processed content
            analysis: Content analysis results
            
        Returns:
            List of Chapter entities
        """
        if not source.processed_content:
            raise ProcessingError("No processed content available for chapter extraction")
        
        content = source.processed_content
        
        # Choose extraction strategy based on content structure
        if analysis.get("has_clear_structure") and analysis.get("headings"):
            chapters = await self._extract_by_headings(source, content, analysis["headings"])
        else:
            chapters = await self._extract_by_ai_analysis(source, content, analysis)
        
        # Validate and refine chapters
        chapters = self._validate_chapters(chapters)
        
        # Add metadata to chapters
        for i, chapter in enumerate(chapters):
            chapter.order = i
            chapter.calculate_word_count()
            chapter.estimate_duration()
            
            # Extract key topics from chapter content
            chapter.key_topics = await self._extract_chapter_topics(chapter.content)
        
        return chapters
    
    async def _extract_by_headings(self, source: ContentSource, content: str, headings: List[Dict]) -> List[Chapter]:
        """Extract chapters based on document headings."""
        chapters = []
        lines = content.split('\n')
        
        # Sort headings by line number
        headings = sorted(headings, key=lambda h: h["line_number"])
        
        for i, heading in enumerate(headings):
            # Determine chapter boundaries
            start_line = heading["line_number"]
            end_line = headings[i + 1]["line_number"] if i + 1 < len(headings) else len(lines)
            
            # Extract chapter content
            chapter_lines = lines[start_line:end_line]
            chapter_content = '\n'.join(chapter_lines).strip()
            
            # Skip if too short
            if len(chapter_content.split()) < self.min_chapter_length // 5:  # Rough word estimate
                continue
            
            # Create chapter
            chapter = Chapter(
                id=ChapterId.generate(),
                project_id=source.project_id,
                source_id=source.id,
                title=self._clean_heading_text(heading["text"]),
                content=chapter_content,
                order=len(chapters),
            )
            
            chapters.append(chapter)
        
        return chapters
    
    async def _extract_by_ai_analysis(self, source: ContentSource, content: str, analysis: Dict[str, Any]) -> List[Chapter]:
        """Extract chapters using AI analysis."""
        if not self.ai_client:
            # Fallback to simple paragraph-based extraction
            return self._extract_by_paragraphs(source, content)
        
        # Use AI to suggest chapter breaks
        prompt = f"""
        Analyze this content and suggest logical chapter breaks for video script generation.
        Each chapter should be 300-2000 words and cover a coherent topic.
        
        Content:
        {content}
        
        Please suggest:
        1. Chapter titles
        2. Starting position (character index or paragraph number)
        3. Brief description of each chapter's focus
        
        Return as JSON with chapters array.
        """
        
        try:
            response = await self.ai_client.extract_chapters(prompt)
            import json
            chapter_data = json.loads(response)
            
            chapters = []
            for i, chapter_info in enumerate(chapter_data.get("chapters", [])):
                # Extract content based on AI suggestions
                chapter_content = self._extract_chapter_content(content, chapter_info)
                
                if len(chapter_content.split()) >= self.min_chapter_length // 5:
                    chapter = Chapter(
                        id=ChapterId.generate(),
                        project_id=source.project_id,
                        source_id=source.id,
                        title=chapter_info.get("title", f"Chapter {i + 1}"),
                        content=chapter_content,
                        order=i,
                    )
                    chapters.append(chapter)
            
            return chapters
            
        except Exception as e:
            logger.warning(f"AI chapter extraction failed: {str(e)}")
            return self._extract_by_paragraphs(source, content)
    
    def _extract_by_paragraphs(self, source: ContentSource, content: str) -> List[Chapter]:
        """Fallback: Extract chapters by grouping paragraphs."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chapters = []
        
        current_chapter_paras = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            para_word_count = len(paragraph.split())
            
            # Check if adding this paragraph would exceed max length
            if current_word_count + para_word_count > self.max_chapter_length // 5:  # Rough estimate
                # Create chapter from current paragraphs
                if current_chapter_paras and current_word_count >= self.min_chapter_length // 5:
                    chapter_content = '\n\n'.join(current_chapter_paras)
                    chapter = Chapter(
                        id=ChapterId.generate(),
                        project_id=source.project_id,
                        source_id=source.id,
                        title=f"Chapter {len(chapters) + 1}",
                        content=chapter_content,
                        order=len(chapters),
                    )
                    chapters.append(chapter)
                
                # Start new chapter
                current_chapter_paras = [paragraph]
                current_word_count = para_word_count
            else:
                current_chapter_paras.append(paragraph)
                current_word_count += para_word_count
        
        # Add final chapter
        if current_chapter_paras and current_word_count >= self.min_chapter_length // 5:
            chapter_content = '\n\n'.join(current_chapter_paras)
            chapter = Chapter(
                id=ChapterId.generate(),
                project_id=source.project_id,
                source_id=source.id,
                title=f"Chapter {len(chapters) + 1}",
                content=chapter_content,
                order=len(chapters),
            )
            chapters.append(chapter)
        
        return chapters
    
    def _extract_chapter_content(self, content: str, chapter_info: Dict[str, Any]) -> str:
        """Extract chapter content based on AI suggestions."""
        # This is a simplified implementation
        # In practice, you'd parse the AI's position indicators
        
        start_pos = chapter_info.get("start_position", 0)
        end_pos = chapter_info.get("end_position", len(content))
        
        return content[start_pos:end_pos].strip()
    
    def _validate_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        """Validate and refine extracted chapters."""
        valid_chapters = []
        
        for chapter in chapters:
            word_count = len(chapter.content.split())
            
            # Skip chapters that are too short
            if word_count < self.min_chapter_length // 5:
                logger.warning(f"Skipping short chapter: {chapter.title}")
                continue
            
            # Split chapters that are too long
            if word_count > self.max_chapter_length // 3:
                split_chapters = self._split_long_chapter(chapter)
                valid_chapters.extend(split_chapters)
            else:
                valid_chapters.append(chapter)
        
        return valid_chapters
    
    def _split_long_chapter(self, chapter: Chapter) -> List[Chapter]:
        """Split a chapter that's too long into smaller chapters."""
        paragraphs = chapter.content.split('\n\n')
        
        # Simple splitting by paragraph count
        mid_point = len(paragraphs) // 2
        
        first_half = Chapter(
            id=ChapterId.generate(),
            project_id=chapter.project_id,
            source_id=chapter.source_id,
            title=f"{chapter.title} - Part 1",
            content='\n\n'.join(paragraphs[:mid_point]),
            order=chapter.order,
        )
        
        second_half = Chapter(
            id=ChapterId.generate(),
            project_id=chapter.project_id,
            source_id=chapter.source_id,
            title=f"{chapter.title} - Part 2",
            content='\n\n'.join(paragraphs[mid_point:]),
            order=chapter.order + 1,
        )
        
        return [first_half, second_half]
    
    def _clean_heading_text(self, heading: str) -> str:
        """Clean heading text to create chapter title."""
        # Remove markdown symbols
        heading = re.sub(r'^#+\s*', '', heading)
        
        # Remove underline markers
        heading = re.sub(r'^=+$|^-+$', '', heading)
        
        # Capitalize properly
        if heading.isupper():
            heading = heading.title()
        
        return heading.strip()
    
    async def _extract_chapter_topics(self, content: str) -> List[str]:
        """Extract key topics from chapter content."""
        if not self.ai_client:
            # Simple keyword extraction
            words = content.lower().split()
            # This is very basic - in practice you'd use proper NLP
            common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
            word_freq = {}
            
            for word in words:
                word = re.sub(r'[^\w]', '', word)
                if len(word) > 3 and word not in common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Return top 5 words
            return sorted(word_freq.keys(), key=lambda w: word_freq[w], reverse=True)[:5]
        
        # Use AI for topic extraction
        try:
            prompt = f"""
            Extract 3-5 key topics from this chapter content:
            
            {content[:1000]}...
            
            Return as a simple list of topics.
            """
            
            response = await self.ai_client.extract_topics(prompt)
            # Parse response and return topics
            return [topic.strip() for topic in response.split('\n') if topic.strip()][:5]
            
        except Exception as e:
            logger.warning(f"AI topic extraction failed: {str(e)}")
            return []
