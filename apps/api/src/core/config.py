import os
from typing import Literal, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# MODEL PROVIDER DEFINITIONS
# ============================================================================

class ModelProvider:
    """Supported model providers."""
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    
    @classmethod
    def all(cls) -> list[str]:
        return [cls.GOOGLE, cls.OPENROUTER]


class AIModels:
    """Available AI models with their identifiers."""
    # Google Gemini models
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    GEMINI_25_FLASH = "gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"
    GEMINI_25_FLASH_LITE = "gemini-2.5-flash-lite"
    
    # OpenRouter models
    # Add your own OpenRouter models here as needed
    OR_GROK_41_FAST_FREE = "x-ai/grok-4.1-fast:free"
    
    # Ordered list for UI display - Google models
    GOOGLE_MODELS = [
        GEMINI_3_PRO_PREVIEW,
        GEMINI_25_PRO,
        GEMINI_25_FLASH,
        GEMINI_25_FLASH_LITE,
    ]
    
    # OpenRouter models
    OPENROUTER_MODELS = [
        OR_GROK_41_FAST_FREE,
    ]
    
    ALL_MODELS = GOOGLE_MODELS + OPENROUTER_MODELS
    
    # Speed rankings (for automatic fallback selection)
    SPEED_ORDER = [
        GEMINI_25_FLASH_LITE,  # Fastest Google
        OR_GROK_41_FAST_FREE,  # Fast OpenRouter (free)
        GEMINI_25_FLASH,
        GEMINI_25_PRO,
        GEMINI_3_PRO_PREVIEW,  # Slowest
    ]
    
    @classmethod
    def is_valid(cls, model: str) -> bool:
        # Also accept any openrouter model format
        if model in cls.ALL_MODELS:
            return True
        # OpenRouter uses provider/model format
        if "/" in model:
            return True
        return False
    
    @classmethod
    def get_provider(cls, model: str) -> str:
        """Determine which provider a model belongs to."""
        if model in cls.GOOGLE_MODELS:
            return ModelProvider.GOOGLE
        if model in cls.OPENROUTER_MODELS or "/" in model:
            return ModelProvider.OPENROUTER
        # Default to Google for backward compatibility
        return ModelProvider.GOOGLE
    
    @classmethod
    def get_faster_model(cls, current: str) -> Optional[str]:
        """Get the next faster model for fallback."""
        if current not in cls.SPEED_ORDER:
            return cls.GEMINI_25_FLASH_LITE
        idx = cls.SPEED_ORDER.index(current)
        if idx == 0:
            return None  # Already fastest
        return cls.SPEED_ORDER[idx - 1]


class ModelConfig(BaseModel):
    """
    Dynamic Model Configuration
    
    This configuration can be overridden per-request from the frontend.
    Allows users to select which models to use for different purposes.
    """
    # Core model assignments
    primary_model: str = Field(
        default=AIModels.GEMINI_25_FLASH,
        description="Main conversation model (highest quality)"
    )
    fast_model: str = Field(
        default=AIModels.GEMINI_25_FLASH_LITE,
        description="Real-time operations (pattern detection, probes)"
    )
    synthesis_model: str = Field(
        default=AIModels.GEMINI_25_PRO,
        description="Deep insight generation"
    )
    fallback_model: str = Field(
        default=AIModels.GEMINI_25_FLASH_LITE,
        description="Backup when others fail"
    )
    
    # Preferences
    auto_fallback: bool = Field(
        default=True,
        description="Automatically try fallback on rate limit"
    )
    
    def get_model(self, role: str) -> str:
        """Get model for a specific role."""
        role_map = {
            'primary': self.primary_model,
            'fast': self.fast_model,
            'synthesis': self.synthesis_model,
            'fallback': self.fallback_model,
        }
        return role_map.get(role, self.primary_model)
    
    def validate_models(self) -> "ModelConfig":
        """Validate all models are valid, replace invalid with defaults."""
        if not AIModels.is_valid(self.primary_model):
            self.primary_model = AIModels.GEMINI_25_FLASH
        if not AIModels.is_valid(self.fast_model):
            self.fast_model = AIModels.GEMINI_25_FLASH_LITE
        if not AIModels.is_valid(self.synthesis_model):
            self.synthesis_model = AIModels.GEMINI_25_PRO
        if not AIModels.is_valid(self.fallback_model):
            self.fallback_model = AIModels.GEMINI_25_FLASH_LITE
        return self


class HRMConfig(BaseModel):
    """
    Hierarchical Reasoning Model Configuration
    
    Inspired by sapientinc/HRM architecture with:
    - H-Level (High-Level Planning): Slow, abstract reasoning
    - L-Level (Low-Level Execution): Rapid, detailed computation
    - ACT (Adaptive Computation Time): Dynamic reasoning depth
    """
    
    # Master toggle
    enabled: bool = Field(default=False, description="Enable/disable HRM reasoning layer (disabled for testing)")
    
    # Thinking mode
    thinking_level: Literal["low", "high"] = Field(
        default="high",
        description="low = fast single-pass, high = deep multi-pass reasoning"
    )
    
    # Hierarchical Processing (inspired by sapientinc H/L modules)
    h_cycles: int = Field(
        default=2, ge=1, le=4,
        description="High-level planning iterations (abstract strategy)"
    )
    l_cycles: int = Field(
        default=2, ge=1, le=4,
        description="Low-level execution iterations (detailed computation)"
    )
    
    # Adaptive Computation Time (ACT)
    max_reasoning_depth: int = Field(
        default=4, ge=1, le=16,
        description="Maximum reasoning iterations before halting"
    )
    halt_threshold: float = Field(
        default=0.85, ge=0.5, le=1.0,
        description="Confidence threshold to halt early"
    )
    
    # Beam Search / Candidate Scoring
    candidate_count: int = Field(
        default=3, ge=2, le=8,
        description="Number of solution candidates to generate"
    )
    beam_size: int = Field(
        default=2, ge=1, le=5,
        description="Top candidates to keep after scoring"
    )
    score_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="Minimum score to consider a candidate viable"
    )
    
    # Visualization / Debugging
    show_reasoning_trace: bool = Field(
        default=False,
        description="Include reasoning steps in response"
    )
    verbose_logging: bool = Field(
        default=False,
        description="Enable detailed HRM logging"
    )

class Settings:
    """Global application settings."""
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("EXPO_PUBLIC_GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    OPENROUTER_API_KEY: str = os.getenv("EXPO_PUBLIC_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""
    
    # OpenRouter configuration
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_APP_NAME: str = "Project Sovereign"
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "https://github.com/project-sovereign")
    
    # Default model configuration (can be overridden per-request)
    MODELS: ModelConfig = ModelConfig()
    
    # Check which providers are available
    @classmethod
    def is_google_available(cls) -> bool:
        return bool(cls.GOOGLE_API_KEY)
    
    @classmethod
    def is_openrouter_available(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        providers = []
        if cls.is_google_available():
            providers.append(ModelProvider.GOOGLE)
        if cls.is_openrouter_available():
            providers.append(ModelProvider.OPENROUTER)
        return providers
    
    # Convenience aliases for backward compatibility
    @property
    def PRIMARY_MODEL(self) -> str:
        return self.MODELS.primary_model
    
    @property
    def FAST_MODEL(self) -> str:
        return self.MODELS.fast_model
    
    @property
    def SYNTHESIS_MODEL(self) -> str:
        return self.MODELS.synthesis_model
    
    @property
    def FALLBACK_MODEL(self) -> str:
        return self.MODELS.fallback_model
    
    @property
    def LLM_MODEL(self) -> str:
        """Alias for PRIMARY_MODEL for backward compatibility."""
        return self.MODELS.primary_model
    
    HRM: HRMConfig = HRMConfig()
    
    REPL_SLUG: str = os.getenv("REPL_SLUG", "")
    REPL_OWNER: str = os.getenv("REPL_OWNER", "")
    REPLIT_DOMAINS: str = os.getenv("REPLIT_DOMAINS", "")
    REPLIT_DEV_DOMAIN: str = os.getenv("REPLIT_DEV_DOMAIN", "")
    
    API_PREFIX: str = "/api/python"
    FASTAPI_PORT: int = 8000
    
    @classmethod
    def get_allowed_origins(cls) -> list[str]:
        origins = [
            "http://localhost:5000", 
            "http://0.0.0.0:5000",
            "http://localhost:8081",  # Metro bundler default
            "http://127.0.0.1:5000",
            "http://127.0.0.1:8081",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        
        # Allow all local network IPs for mobile development
        # This is safe for development but should be restricted in production
        origins.append("*")  # Allow all origins in dev
        
        if cls.REPLIT_DOMAINS:
            for domain in cls.REPLIT_DOMAINS.split(","):
                origins.append(f"https://{domain.strip()}")
        
        if cls.REPLIT_DEV_DOMAIN:
            origins.append(f"https://{cls.REPLIT_DEV_DOMAIN}")
        
        if cls.REPL_SLUG and cls.REPL_OWNER:
            origins.append(f"https://{cls.REPL_SLUG}.{cls.REPL_OWNER}.repl.co")
            origins.append(f"https://{cls.REPL_SLUG}--{cls.REPL_OWNER}.repl.co")
        
        return list(set(origins))

settings = Settings()
