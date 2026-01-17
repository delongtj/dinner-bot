import os
from llm.base import LLMProvider
from llm.gemini import GeminiProvider


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "claude":
        # Claude provider stub for future use
        raise NotImplementedError("Claude provider not yet implemented")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
