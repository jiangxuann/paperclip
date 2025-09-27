"""
URL content processing and web scraping.

Handles web content extraction, cleaning, and analysis
with support for various content types and formats.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime

from core.domain import URLSource, ContentMetadata, ProcessingStatus
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class URLProcessor:
    """
    Advanced URL processor with intelligent content extraction.
    
    Supports multiple extraction strategies for different website types
    and handles various content formats (articles, documentation, blogs, etc.).
    """
    
    def __init__(self, timeout: int = 30):
        """Initialize URL processor."""
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.extractors = self._initialize_extractors()
    
    def _initialize_extractors(self) -> Dict[str, Any]:
        """Initialize content extraction libraries."""
        extractors = {}
        
        # Try to import web scraping libraries
        try:
            from bs4 import BeautifulSoup
            extractors['beautifulsoup'] = BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available")
        
        try:
            import trafilatura
            extractors['trafilatura'] = trafilatura
        except ImportError:
            logger.warning("Trafilatura not available")
        
        try:
            from readability import Document
            extractors['readability'] = Document
        except ImportError:
            logger.warning("python-readability not available")
        
        if not extractors:
            raise ProcessingError("No web content extraction libraries available")
        
        return extractors
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Paperclip/1.0; +https://paperclip.ai)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def process_url(self, source: URLSource) -> URLSource:
        """
        Process a URL source and extract content.
        
        Args:
            source: URLSource entity to process
            
        Returns:
            Updated URLSource with extracted content
        """
        try:
            source.mark_processing()
            
            # Validate URL
            if not self._is_valid_url(source.url):
                raise ProcessingError(f"Invalid URL: {source.url}")
            
            # Create session if not exists
            if not self.session:
                async with self:
                    return await self._do_process_url(source)
            else:
                return await self._do_process_url(source)
                
        except Exception as e:
            error_msg = f"Failed to process URL {source.url}: {str(e)}"
            logger.error(error_msg)
            source.mark_failed(error_msg)
            raise ProcessingError(error_msg) from e
    
    async def _do_process_url(self, source: URLSource) -> URLSource:
        """Internal URL processing logic."""
        
        # Fetch content
        html_content, response_metadata = await self._fetch_content(source.url)
        
        # Extract structured content
        content = await self._extract_content(html_content, source.url)
        
        # Extract metadata
        metadata = await self._extract_metadata(html_content, source.url, response_metadata)
        
        # Update source with results
        source.raw_content = html_content
        source.metadata = ContentMetadata(metadata)
        source.scraped_at = datetime.utcnow()
        
        # Set title if not already set
        if not source.title and metadata.get("title"):
            source.title = metadata["title"]
        
        # Analyze content quality
        content_quality = self._analyze_content_quality(content)
        if content_quality["quality_score"] < 0.5:
            logger.warning(f"Low quality content extracted from {source.url}")
        
        # Process content for better structure
        processed_content = await self._process_content(content)
        
        source.mark_completed(processed_content)
        logger.info(f"Successfully processed URL: {source.url}")
        
        return source
    
    async def _fetch_content(self, url: str) -> tuple[str, Dict[str, Any]]:
        """Fetch HTML content from URL."""
        try:
            async with self.session.get(url) as response:
                # Check response status
                if response.status >= 400:
                    raise ProcessingError(f"HTTP {response.status}: {response.reason}")
                
                # Get content
                html_content = await response.text()
                
                # Response metadata
                response_metadata = {
                    "status_code": response.status,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(html_content),
                    "final_url": str(response.url),  # After redirects
                    "headers": dict(response.headers),
                }
                
                return html_content, response_metadata
                
        except aiohttp.ClientError as e:
            raise ProcessingError(f"Failed to fetch URL: {str(e)}")
    
    async def _extract_content(self, html_content: str, url: str) -> str:
        """Extract main content from HTML using best available method."""
        
        # Try extractors in order of preference
        extraction_methods = [
            ("trafilatura", self._extract_with_trafilatura),
            ("readability", self._extract_with_readability),
            ("beautifulsoup", self._extract_with_beautifulsoup),
        ]
        
        last_error = None
        
        for method_name, extractor_func in extraction_methods:
            if method_name not in self.extractors:
                continue
                
            try:
                content = await extractor_func(html_content, url)
                if content and len(content.strip()) > 200:  # Minimum content threshold
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
            raise ProcessingError(f"All content extraction methods failed. Last error: {str(last_error)}")
        else:
            raise ProcessingError("No suitable content extraction method available")
    
    async def _extract_with_trafilatura(self, html_content: str, url: str) -> str:
        """Extract content using Trafilatura (best for articles)."""
        import trafilatura
        
        content = trafilatura.extract(
            html_content,
            url=url,
            include_comments=False,
            include_tables=True,
            include_links=False,
            deduplicate=True,
        )
        
        return content or ""
    
    async def _extract_with_readability(self, html_content: str, url: str) -> str:
        """Extract content using python-readability."""
        from readability import Document
        
        doc = Document(html_content)
        content = doc.summary()
        
        # Strip HTML tags
        if "beautifulsoup" in self.extractors:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text()
        
        return content
    
    async def _extract_with_beautifulsoup(self, html_content: str, url: str) -> str:
        """Extract content using BeautifulSoup (fallback method)."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content areas
        main_content = None
        
        # Common content selectors
        content_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '#content',
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element
                break
        
        # Fallback to body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text
        content = main_content.get_text(separator='\n', strip=True)
        
        return content
    
    async def _extract_metadata(self, html_content: str, url: str, response_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from HTML and response."""
        metadata = {
            "url": url,
            "scraped_at": datetime.utcnow().isoformat(),
            **response_metadata,
        }
        
        # Parse HTML for metadata
        if "beautifulsoup" in self.extractors:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Basic metadata
                title = soup.find('title')
                if title:
                    metadata["title"] = title.get_text().strip()
                
                # Meta tags
                meta_tags = soup.find_all('meta')
                for meta in meta_tags:
                    name = meta.get('name') or meta.get('property')
                    content = meta.get('content')
                    
                    if name and content:
                        # Standard meta tags
                        if name in ['description', 'keywords', 'author']:
                            metadata[name] = content
                        
                        # Open Graph tags
                        elif name.startswith('og:'):
                            metadata[name] = content
                        
                        # Twitter Card tags
                        elif name.startswith('twitter:'):
                            metadata[name] = content
                
                # Language
                html_tag = soup.find('html')
                if html_tag and html_tag.get('lang'):
                    metadata["language"] = html_tag.get('lang')
                
                # Structured data (JSON-LD)
                json_ld_scripts = soup.find_all('script', type='application/ld+json')
                if json_ld_scripts:
                    metadata["structured_data_count"] = len(json_ld_scripts)
                
            except Exception as e:
                logger.warning(f"Failed to extract HTML metadata: {str(e)}")
        
        return metadata
    
    def _analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze the quality of extracted content."""
        if not content:
            return {"quality_score": 0.0, "issues": ["No content extracted"]}
        
        issues = []
        
        # Check for common extraction issues
        char_count = len(content)
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Too short
        if char_count < 500:
            issues.append("Content too short")
        
        # Too many repeated lines (navigation, footers)
        lines = content.split('\n')
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(unique_lines) < len(lines) * 0.7:
            issues.append("High content repetition")
        
        # Check for navigation artifacts
        nav_keywords = ['home', 'about', 'contact', 'menu', 'login', 'register']
        nav_line_count = sum(1 for line in lines if any(keyword in line.lower() for keyword in nav_keywords))
        if nav_line_count > line_count * 0.2:
            issues.append("Navigation artifacts present")
        
        # Calculate quality score
        quality_score = 1.0
        if char_count < 500:
            quality_score -= 0.4
        if word_count < 100:
            quality_score -= 0.3
        if len(unique_lines) < len(lines) * 0.7:
            quality_score -= 0.3
        
        quality_score = max(0.0, quality_score)
        
        return {
            "quality_score": quality_score,
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "unique_line_ratio": len(unique_lines) / max(len(lines), 1),
            "issues": issues,
        }
    
    async def _process_content(self, content: str) -> str:
        """Process and clean extracted content."""
        if not content:
            return content
        
        # Basic cleaning
        lines = content.split('\n')
        cleaned_lines = []
        
        prev_line = ""
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip duplicate consecutive lines
            if line == prev_line:
                continue
            
            # Skip very short lines (likely navigation)
            if len(line) < 10 and not line.endswith('.'):
                continue
            
            # Skip lines that look like navigation
            nav_patterns = ['home', 'about', 'contact', 'menu', 'login', 'sign up']
            if len(line) < 50 and any(pattern in line.lower() for pattern in nav_patterns):
                continue
            
            cleaned_lines.append(line)
            prev_line = line
        
        # Rejoin with proper spacing
        processed_content = '\n\n'.join(cleaned_lines)
        
        # Remove excessive whitespace
        import re
        processed_content = re.sub(r'\n{3,}', '\n\n', processed_content)
        processed_content = re.sub(r' {2,}', ' ', processed_content)
        
        return processed_content
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
