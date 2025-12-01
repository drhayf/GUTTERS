"""
LLM Provider Factory

Multi-provider LLM support with automatic routing based on model selection.
Supports:
- Google Gemini (via langchain-google-genai)
- OpenRouter (via langchain-openai with custom base URL)

The factory determines which provider to use based on the model ID format:
- Models with "/" are treated as OpenRouter models
- Models matching Gemini patterns use Google
"""

from typing import Optional, Any, Dict, Union
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from .config import settings, AIModels, ModelProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory for creating LLM instances from multiple providers.
    
    Automatically routes to the correct provider based on model ID.
    Includes caching to avoid recreating LLMs for the same model.
    """
    
    _cache: Dict[str, BaseChatModel] = {}
    
    @classmethod
    def get_llm(
        cls,
        model: str,
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[BaseChatModel]:
        """
        Get an LLM instance for the specified model.
        
        Args:
            model: The model identifier (e.g., 'gemini-2.5-flash' or 'anthropic/claude-3.5-sonnet')
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response (optional)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            A LangChain chat model instance, or None if provider unavailable
        """
        # Check cache first (key includes temperature for different use cases)
        cache_key = f"{model}:{temperature}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # Determine provider
        provider = AIModels.get_provider(model)
        
        try:
            if provider == ModelProvider.GOOGLE:
                llm = cls._create_google_llm(model, temperature, max_tokens, **kwargs)
            elif provider == ModelProvider.OPENROUTER:
                llm = cls._create_openrouter_llm(model, temperature, max_tokens, **kwargs)
            else:
                logger.error(f"[LLMFactory] Unknown provider for model: {model}")
                return None
            
            if llm:
                cls._cache[cache_key] = llm
                logger.info(f"[LLMFactory] Created {provider} LLM for model: {model}")
            
            return llm
            
        except Exception as e:
            logger.error(f"[LLMFactory] Failed to create LLM for {model}: {e}")
            return None
    
    @classmethod
    def _create_google_llm(
        cls,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Optional[ChatGoogleGenerativeAI]:
        """Create a Google Gemini LLM instance."""
        if not settings.GOOGLE_API_KEY:
            logger.warning("[LLMFactory] No Google API key available")
            return None
        
        llm_kwargs = {
            "model": model,
            "temperature": temperature,
            "google_api_key": settings.GOOGLE_API_KEY,
        }
        
        if max_tokens:
            llm_kwargs["max_output_tokens"] = max_tokens
        
        return ChatGoogleGenerativeAI(**llm_kwargs, **kwargs)
    
    @classmethod
    def _create_openrouter_llm(
        cls,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Optional[ChatOpenAI]:
        """
        Create an OpenRouter LLM instance.
        
        OpenRouter uses the OpenAI-compatible API format, so we use ChatOpenAI
        with a custom base URL.
        """
        if not settings.OPENROUTER_API_KEY:
            logger.warning("[LLMFactory] No OpenRouter API key available")
            return None
        
        # OpenRouter requires extra headers for app identification
        default_headers = {
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        }
        
        llm_kwargs = {
            "model": model,
            "temperature": temperature,
            "openai_api_key": settings.OPENROUTER_API_KEY,
            "openai_api_base": settings.OPENROUTER_BASE_URL,
            "default_headers": default_headers,
        }
        
        if max_tokens:
            llm_kwargs["max_tokens"] = max_tokens
        
        return ChatOpenAI(**llm_kwargs, **kwargs)
    
    @classmethod
    def get_available_models(cls) -> Dict[str, list[str]]:
        """
        Get all available models grouped by provider.
        
        Only returns models for providers that have API keys configured.
        """
        models = {}
        
        if settings.is_google_available():
            models[ModelProvider.GOOGLE] = AIModels.GOOGLE_MODELS
        
        if settings.is_openrouter_available():
            models[ModelProvider.OPENROUTER] = AIModels.OPENROUTER_MODELS
        
        return models
    
    @classmethod
    def get_default_model(cls, role: str = "primary") -> str:
        """
        Get the best available model for a given role.
        
        Prefers Google models if available, falls back to OpenRouter.
        """
        if settings.is_google_available():
            return settings.MODELS.get_model(role)
        elif settings.is_openrouter_available():
            # Use Grok 4.1 Fast for all roles when Google is unavailable
            return AIModels.OR_GROK_41_FAST_FREE
        else:
            logger.error("[LLMFactory] No API keys configured!")
            return AIModels.GEMINI_25_FLASH  # Return something even if unavailable
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the LLM cache."""
        cls._cache.clear()
        logger.info("[LLMFactory] Cache cleared")


# Singleton factory instance
_factory_instance: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """Get the singleton LLM Factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LLMFactory()
    return _factory_instance


# Convenience function for quick access
def get_llm(model: str, **kwargs) -> Optional[BaseChatModel]:
    """Convenience wrapper for LLMFactory.get_llm()."""
    return LLMFactory.get_llm(model, **kwargs)
