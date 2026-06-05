from .base import AIProvider
from .ollama import OllamaProvider
# from .gemini import GeminiProvider # Future import

def get_ai_provider(provider_name: str, model_name: str = None) -> AIProvider:
    """
    Factory function to get the appropriate AI Provider instance based on the name.
    """
    provider_name = provider_name.lower()
    
    if provider_name == "ollama":
        # model_name might be None if we're just fetching the list of models in settings
        if model_name:
            return OllamaProvider(model_name=model_name)
        return OllamaProvider()
        
    # elif provider_name == "gemini":
    #     return GeminiProvider(model_name=model_name)
        
    else:
        raise ValueError(f"Unsupported AI Provider: {provider_name}")
