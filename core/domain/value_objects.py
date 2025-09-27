"""
Value objects for the Paperclip domain.

Value objects are immutable objects that represent concepts
through their attributes rather than identity.
"""

from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectId:
    """Unique identifier for a project."""
    value: UUID
    
    @classmethod
    def generate(cls) -> "ProjectId":
        """Generate a new project ID."""
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "ProjectId":
        """Create from string representation."""
        return cls(UUID(id_str))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SourceId:
    """Unique identifier for a content source."""
    value: UUID
    
    @classmethod
    def generate(cls) -> "SourceId":
        """Generate a new source ID."""
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "SourceId":
        """Create from string representation."""
        return cls(UUID(id_str))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ChapterId:
    """Unique identifier for a chapter."""
    value: UUID
    
    @classmethod
    def generate(cls) -> "ChapterId":
        """Generate a new chapter ID."""
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "ChapterId":
        """Create from string representation."""
        return cls(UUID(id_str))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ScriptId:
    """Unique identifier for a script."""
    value: UUID
    
    @classmethod
    def generate(cls) -> "ScriptId":
        """Generate a new script ID."""
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "ScriptId":
        """Create from string representation."""
        return cls(UUID(id_str))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class VideoId:
    """Unique identifier for a video."""
    value: UUID
    
    @classmethod
    def generate(cls) -> "VideoId":
        """Generate a new video ID."""
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, id_str: str) -> "VideoId":
        """Create from string representation."""
        return cls(UUID(id_str))
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ContentMetadata:
    """Metadata associated with content sources."""
    data: Dict[str, Any]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        return self.data.get(key, default)
    
    def with_update(self, updates: Dict[str, Any]) -> "ContentMetadata":
        """Create new metadata with updates."""
        new_data = {**self.data, **updates}
        return ContentMetadata(new_data)
    
    @property
    def author(self) -> Optional[str]:
        """Get content author if available."""
        return self.data.get("author")
    
    @property
    def language(self) -> Optional[str]:
        """Get content language if detected."""
        return self.data.get("language")
    
    @property
    def word_count(self) -> Optional[int]:
        """Get total word count if calculated."""
        return self.data.get("word_count")
    
    @property
    def topics(self) -> list:
        """Get extracted topics/keywords."""
        return self.data.get("topics", [])


@dataclass(frozen=True)
class VideoConfig:
    """Configuration for video generation."""
    settings: Dict[str, Any]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.settings.get(key, default)
    
    @property
    def quality(self) -> str:
        """Get video quality setting."""
        return self.settings.get("quality", "1080p")
    
    @property
    def duration_target(self) -> Optional[float]:
        """Get target duration in minutes."""
        return self.settings.get("duration_target")
    
    @property
    def style(self) -> str:
        """Get video style setting."""
        return self.settings.get("style", "documentary")
    
    @property
    def aspect_ratio(self) -> str:
        """Get aspect ratio setting."""
        return self.settings.get("aspect_ratio", "16:9")
    
    @property
    def include_narration(self) -> bool:
        """Whether to include AI narration."""
        return self.settings.get("include_narration", True)
    
    @property
    def voice_style(self) -> str:
        """Get voice style for narration."""
        return self.settings.get("voice_style", "professional")
    
    def with_updates(self, updates: Dict[str, Any]) -> "VideoConfig":
        """Create new config with updates."""
        new_settings = {**self.settings, **updates}
        return VideoConfig(new_settings)


@dataclass(frozen=True)
class ScriptConfig:
    """Configuration for script generation."""
    settings: Dict[str, Any]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.settings.get(key, default)
    
    @property
    def tone(self) -> str:
        """Get script tone setting."""
        return self.settings.get("tone", "professional")
    
    @property
    def target_audience(self) -> str:
        """Get target audience setting."""
        return self.settings.get("target_audience", "general")
    
    @property
    def include_transitions(self) -> bool:
        """Whether to include scene transitions."""
        return self.settings.get("include_transitions", True)
    
    @property
    def max_scene_duration(self) -> float:
        """Maximum duration per scene in seconds."""
        return self.settings.get("max_scene_duration", 30.0)
    
    @property
    def include_callouts(self) -> bool:
        """Whether to include visual callouts/highlights."""
        return self.settings.get("include_callouts", True)
    
    @property
    def language(self) -> str:
        """Target language for the script."""
        return self.settings.get("language", "en")
    
    def with_updates(self, updates: Dict[str, Any]) -> "ScriptConfig":
        """Create new config with updates."""
        new_settings = {**self.settings, **updates}
        return ScriptConfig(new_settings)


@dataclass(frozen=True)
class FilePath:
    """Type-safe file path representation."""
    path: Path
    
    @classmethod
    def from_string(cls, path_str: str) -> "FilePath":
        """Create from string path."""
        return cls(Path(path_str))
    
    def __str__(self) -> str:
        return str(self.path)
    
    @property
    def exists(self) -> bool:
        """Check if file exists."""
        return self.path.exists()
    
    @property
    def size(self) -> int:
        """Get file size in bytes."""
        return self.path.stat().st_size if self.exists else 0
    
    @property
    def suffix(self) -> str:
        """Get file extension."""
        return self.path.suffix
    
    @property
    def name(self) -> str:
        """Get filename."""
        return self.path.name
