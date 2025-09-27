"""
AI and video provider configuration.

Manages API keys and settings for various AI services
used throughout the application.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: Optional[str] = Field(None, description="OpenAI API key")
    model: str = Field("gpt-4", description="Default OpenAI model")
    max_tokens: int = Field(4000, description="Maximum tokens per request")
    temperature: float = Field(0.7, description="Generation temperature")
    base_url: Optional[str] = Field(None, description="Custom base URL for OpenAI-compatible APIs")
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    class Config:
        env_prefix = "PROVIDERS_OPENAI_"


class AnthropicConfig(BaseModel):
    """Anthropic Claude API configuration."""
    api_key: Optional[str] = Field(None, description="Anthropic API key")
    model: str = Field("claude-3-sonnet-20240229", description="Default Claude model")
    max_tokens: int = Field(4000, description="Maximum tokens per request")
    temperature: float = Field(0.7, description="Generation temperature")
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v
    
    class Config:
        env_prefix = "PROVIDERS_ANTHROPIC_"


class RunwayConfig(BaseModel):
    """Runway ML video generation configuration."""
    api_key: Optional[str] = Field(None, description="Runway API key")
    model: str = Field("gen3a_turbo", description="Default Runway model")
    max_duration: int = Field(10, description="Maximum video duration in seconds")
    default_aspect_ratio: str = Field("1280:768", description="Default aspect ratio")
    
    class Config:
        env_prefix = "PROVIDERS_RUNWAY_"


class PikaConfig(BaseModel):
    """Pika Labs video generation configuration."""
    api_key: Optional[str] = Field(None, description="Pika API key")
    max_duration: int = Field(3, description="Maximum video duration in seconds")
    default_aspect_ratio: str = Field("16:9", description="Default aspect ratio")
    
    class Config:
        env_prefix = "PROVIDERS_PIKA_"


class LumaConfig(BaseModel):
    """Luma AI video generation configuration."""
    api_key: Optional[str] = Field(None, description="Luma API key")
    max_duration: int = Field(5, description="Maximum video duration in seconds")
    default_aspect_ratio: str = Field("16:9", description="Default aspect ratio")
    
    class Config:
        env_prefix = "PROVIDERS_LUMA_"


class TemplateConfig(BaseModel):
    """Template-based video generation configuration."""
    templates_dir: str = Field("templates", description="Templates directory")
    output_dir: str = Field("output/template_videos", description="Template video output directory")
    default_style: str = Field("educational", description="Default template style")
    enable_tts: bool = Field(True, description="Enable text-to-speech for narration")
    tts_voice: str = Field("en-US-AriaNeural", description="TTS voice to use")
    
    class Config:
        env_prefix = "PROVIDERS_TEMPLATE_"


class ProviderConfig(BaseModel):
    """
    Configuration for all AI and video providers.
    
    Centralizes provider settings and provides validation
    for API keys and configuration options.
    """
    
    # AI Providers
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    
    # Video Providers
    runway: RunwayConfig = Field(default_factory=RunwayConfig)
    pika: PikaConfig = Field(default_factory=PikaConfig)
    luma: LumaConfig = Field(default_factory=LumaConfig)
    template: TemplateConfig = Field(default_factory=TemplateConfig)
    
    # General settings
    default_ai_provider: str = Field("openai", description="Default AI provider for content processing")
    default_video_provider: str = Field("template", description="Default video provider")
    retry_attempts: int = Field(3, description="Number of retry attempts for failed API calls")
    retry_delay: float = Field(1.0, description="Delay between retry attempts in seconds")
    
    @validator("default_ai_provider")
    def validate_ai_provider(cls, v):
        valid_providers = ["openai", "anthropic"]
        if v not in valid_providers:
            raise ValueError(f"Default AI provider must be one of: {valid_providers}")
        return v
    
    @validator("default_video_provider")
    def validate_video_provider(cls, v):
        valid_providers = ["runway", "pika", "luma", "template"]
        if v not in valid_providers:
            raise ValueError(f"Default video provider must be one of: {valid_providers}")
        return v
    
    def get_ai_provider_config(self, provider_name: str) -> Optional[BaseModel]:
        """Get configuration for a specific AI provider."""
        provider_map = {
            "openai": self.openai,
            "anthropic": self.anthropic,
        }
        return provider_map.get(provider_name)
    
    def get_video_provider_config(self, provider_name: str) -> Optional[BaseModel]:
        """Get configuration for a specific video provider."""
        provider_map = {
            "runway": self.runway,
            "pika": self.pika,
            "luma": self.luma,
            "template": self.template,
        }
        return provider_map.get(provider_name)
    
    def get_available_ai_providers(self) -> list[str]:
        """Get list of available AI providers (with API keys configured)."""
        available = []
        
        if self.openai.api_key:
            available.append("openai")
        if self.anthropic.api_key:
            available.append("anthropic")
        
        return available
    
    def get_available_video_providers(self) -> list[str]:
        """Get list of available video providers (with API keys configured)."""
        available = ["template"]  # Template provider is always available
        
        if self.runway.api_key:
            available.append("runway")
        if self.pika.api_key:
            available.append("pika")
        if self.luma.api_key:
            available.append("luma")
        
        return available
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate provider configuration and return status."""
        issues = []
        warnings = []
        
        # Check if at least one AI provider is configured
        ai_providers = self.get_available_ai_providers()
        if not ai_providers:
            issues.append("No AI providers configured - at least one is required")
        
        # Check if default providers are available
        if self.default_ai_provider not in ai_providers:
            warnings.append(f"Default AI provider '{self.default_ai_provider}' is not configured")
        
        video_providers = self.get_available_video_providers()
        if self.default_video_provider not in video_providers:
            warnings.append(f"Default video provider '{self.default_video_provider}' is not configured")
        
        # Check for potential issues
        if len(ai_providers) == 1:
            warnings.append("Only one AI provider configured - consider adding a backup")
        
        if len(video_providers) == 1:
            warnings.append("Only template video provider available - consider configuring AI video providers")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "available_ai_providers": ai_providers,
            "available_video_providers": video_providers,
        }
    
    class Config:
        env_prefix = "PROVIDERS_"
