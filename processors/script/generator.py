"""
AI-powered script generation for video content.

Generates engaging video scripts from chapter content using
customizable templates and AI models.
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json

from core.domain import Chapter, Script, ScriptId, ScriptTemplate, ScriptConfig, ProcessingStatus
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """
    AI-powered script generator that creates engaging video scripts
    from chapter content using customizable templates.
    """
    
    def __init__(self, ai_client=None):
        """Initialize script generator with AI client."""
        self.ai_client = ai_client
        self.templates = self._load_script_templates()
    
    def _load_script_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load script generation templates."""
        return {
            ScriptTemplate.EDUCATIONAL: {
                "name": "Educational",
                "description": "Clear, structured educational content with examples",
                "structure": [
                    "hook", "introduction", "main_content", "examples", 
                    "key_takeaways", "conclusion", "call_to_action"
                ],
                "tone": "informative and engaging",
                "pacing": "moderate",
                "include_transitions": True,
            },
            ScriptTemplate.DOCUMENTARY: {
                "name": "Documentary",
                "description": "Narrative-driven documentary style",
                "structure": [
                    "opening_statement", "context", "main_narrative", 
                    "supporting_evidence", "conclusion"
                ],
                "tone": "authoritative and compelling",
                "pacing": "thoughtful",
                "include_transitions": True,
            },
            ScriptTemplate.PRESENTATION: {
                "name": "Presentation",
                "description": "Professional presentation format",
                "structure": [
                    "agenda", "introduction", "main_points", 
                    "supporting_details", "summary", "next_steps"
                ],
                "tone": "professional and clear",
                "pacing": "structured",
                "include_transitions": False,
            },
            ScriptTemplate.TUTORIAL: {
                "name": "Tutorial",
                "description": "Step-by-step instructional content",
                "structure": [
                    "overview", "prerequisites", "step_by_step", 
                    "tips_and_tricks", "troubleshooting", "wrap_up"
                ],
                "tone": "helpful and encouraging",
                "pacing": "step-by-step",
                "include_transitions": True,
            },
            ScriptTemplate.SUMMARY: {
                "name": "Summary",
                "description": "Concise summary of key points",
                "structure": [
                    "overview", "key_points", "implications", "conclusion"
                ],
                "tone": "concise and focused",
                "pacing": "quick",
                "include_transitions": False,
            },
        }
    
    async def generate_script(self, chapter: Chapter, template: ScriptTemplate = ScriptTemplate.EDUCATIONAL, 
                            config: Optional[ScriptConfig] = None) -> Script:
        """
        Generate a video script from a chapter.
        
        Args:
            chapter: Chapter entity with content
            template: Script template to use
            config: Optional script configuration
            
        Returns:
            Generated Script entity
        """
        if not chapter.content:
            raise ProcessingError("Chapter has no content for script generation")
        
        if not self.ai_client:
            raise ProcessingError("AI client not available for script generation")
        
        # Use default config if not provided
        if not config:
            config = ScriptConfig({})
        
        # Create script entity
        script = Script(
            id=ScriptId.generate(),
            project_id=chapter.project_id,
            chapter_id=chapter.id,
            title=f"Script: {chapter.title}",
            content="",  # Will be filled by generation
            template=template,
            config=config,
        )
        
        try:
            script.status = ProcessingStatus.PROCESSING
            start_time = datetime.utcnow()
            
            # Generate script content
            script_content, generation_stats = await self._generate_script_content(
                chapter, template, config
            )
            
            # Update script with results
            script.content = script_content
            script.estimated_duration = self._estimate_script_duration(script_content)
            script.scene_count = self._count_scenes(script_content)
            
            # Mark as completed with stats
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            script.mark_generated(
                model=generation_stats.get("model", "unknown"),
                stats={
                    **generation_stats,
                    "generation_time": generation_time,
                }
            )
            
            logger.info(f"Generated script for chapter: {chapter.title}")
            return script
            
        except Exception as e:
            error_msg = f"Failed to generate script for chapter {chapter.title}: {str(e)}"
            logger.error(error_msg)
            script.status = ProcessingStatus.FAILED
            raise ProcessingError(error_msg) from e
    
    async def _generate_script_content(self, chapter: Chapter, template: ScriptTemplate, 
                                     config: ScriptConfig) -> tuple[str, Dict[str, Any]]:
        """Generate script content using AI."""
        
        # Get template configuration
        template_config = self.templates[template]
        
        # Build generation prompt
        prompt = self._build_generation_prompt(chapter, template_config, config)
        
        # Call AI service
        response = await self.ai_client.generate_script(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )
        
        # Parse response
        script_content = response.get("content", "")
        generation_stats = {
            "model": response.get("model", "unknown"),
            "prompt_tokens": response.get("prompt_tokens", 0),
            "completion_tokens": response.get("completion_tokens", 0),
        }
        
        # Post-process script
        script_content = self._post_process_script(script_content, template_config, config)
        
        return script_content, generation_stats
    
    def _build_generation_prompt(self, chapter: Chapter, template_config: Dict[str, Any], 
                               config: ScriptConfig) -> str:
        """Build AI prompt for script generation."""
        
        # Base prompt structure
        prompt_parts = [
            f"Generate a {template_config['name'].lower()} video script from the following content.",
            "",
            f"**Content to adapt:**",
            f"Title: {chapter.title}",
            f"Content: {chapter.content}",
            "",
            f"**Script Requirements:**",
            f"- Style: {template_config['description']}",
            f"- Tone: {config.tone}",
            f"- Target audience: {config.target_audience}",
            f"- Language: {config.language}",
        ]
        
        # Add duration target if specified
        if config.get("duration_target"):
            duration = config.get("duration_target")
            prompt_parts.append(f"- Target duration: {duration} minutes")
        
        # Add structure requirements
        structure = template_config["structure"]
        prompt_parts.extend([
            "",
            f"**Script Structure:**",
            f"Follow this structure: {' → '.join(structure)}",
        ])
        
        # Add specific instructions
        prompt_parts.extend([
            "",
            f"**Instructions:**",
            f"1. Create engaging, conversational narration",
            f"2. Include visual cues in [brackets] for video production",
            f"3. Break content into logical scenes",
            f"4. Make it suitable for {template_config['pacing']} pacing",
        ])
        
        if config.include_transitions:
            prompt_parts.append("5. Include smooth transitions between sections")
        
        if config.include_callouts:
            prompt_parts.append("6. Add [CALLOUT: text] for important points to highlight")
        
        # Add formatting requirements
        prompt_parts.extend([
            "",
            f"**Format:**",
            f"Use this format:",
            f"",
            f"# Scene 1: [Scene Title]",
            f"[Visual description]",
            f"",
            f"**Narration:**",
            f"Your spoken narration here...",
            f"",
            f"[CALLOUT: Important point] (if applicable)",
            f"",
            f"---",
            f"",
            f"# Scene 2: [Scene Title]",
            f"...",
        ])
        
        return "\n".join(prompt_parts)
    
    def _post_process_script(self, script_content: str, template_config: Dict[str, Any], 
                           config: ScriptConfig) -> str:
        """Post-process generated script content."""
        
        # Basic cleaning
        script_content = script_content.strip()
        
        # Ensure proper scene breaks
        if "---" not in script_content:
            # Add scene breaks based on structure
            scenes = script_content.split("\n\n")
            if len(scenes) > 1:
                script_content = "\n\n---\n\n".join(scenes)
        
        # Validate script structure
        if not script_content.startswith("#"):
            script_content = f"# Scene 1: Introduction\n\n{script_content}"
        
        # Add timing estimates
        script_content = self._add_timing_estimates(script_content)
        
        return script_content
    
    def _add_timing_estimates(self, script_content: str) -> str:
        """Add timing estimates to script scenes."""
        scenes = script_content.split("---")
        processed_scenes = []
        
        for i, scene in enumerate(scenes):
            scene = scene.strip()
            if not scene:
                continue
            
            # Estimate scene duration based on narration length
            narration_text = self._extract_narration_text(scene)
            scene_duration = self._estimate_narration_duration(narration_text)
            
            # Add timing info
            if scene.startswith("#"):
                lines = scene.split("\n")
                lines[0] += f" ({scene_duration:.1f}s)"
                scene = "\n".join(lines)
            
            processed_scenes.append(scene)
        
        return "\n\n---\n\n".join(processed_scenes)
    
    def _extract_narration_text(self, scene: str) -> str:
        """Extract narration text from scene."""
        lines = scene.split("\n")
        narration_lines = []
        in_narration = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("**Narration:**"):
                in_narration = True
                continue
            elif line.startswith("**") and in_narration:
                in_narration = False
            elif line.startswith("[") and line.endswith("]"):
                # Skip visual cues
                continue
            elif in_narration and line:
                narration_lines.append(line)
        
        return " ".join(narration_lines)
    
    def _estimate_narration_duration(self, text: str, wpm: int = 150) -> float:
        """Estimate narration duration in seconds."""
        word_count = len(text.split())
        return (word_count / wpm) * 60
    
    def _estimate_script_duration(self, script_content: str) -> float:
        """Estimate total script duration in minutes."""
        scenes = script_content.split("---")
        total_duration = 0
        
        for scene in scenes:
            narration_text = self._extract_narration_text(scene)
            scene_duration = self._estimate_narration_duration(narration_text)
            
            # Add buffer time for visuals
            visual_buffer = 5  # 5 seconds per scene for visual content
            total_duration += scene_duration + visual_buffer
        
        return total_duration / 60  # Convert to minutes
    
    def _count_scenes(self, script_content: str) -> int:
        """Count number of scenes in script."""
        return len([s for s in script_content.split("---") if s.strip()])
    
    async def generate_batch_scripts(self, chapters: List[Chapter], 
                                   template: ScriptTemplate = ScriptTemplate.EDUCATIONAL,
                                   config: Optional[ScriptConfig] = None) -> List[Script]:
        """Generate scripts for multiple chapters in batch."""
        
        scripts = []
        
        # Process chapters concurrently (with reasonable limit)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent generations
        
        async def generate_single_script(chapter: Chapter) -> Script:
            async with semaphore:
                return await self.generate_script(chapter, template, config)
        
        # Create tasks
        tasks = [generate_single_script(chapter) for chapter in chapters]
        
        # Execute with progress logging
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                script = await task
                scripts.append(script)
                logger.info(f"Generated script {i + 1}/{len(chapters)}")
            except Exception as e:
                logger.error(f"Failed to generate script {i + 1}: {str(e)}")
                continue
        
        return scripts
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available script templates."""
        return {
            template.value: {
                "name": config["name"],
                "description": config["description"],
                "structure": config["structure"],
                "tone": config["tone"],
            }
            for template, config in self.templates.items()
        }
