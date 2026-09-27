from pathlib import Path
from typing import Dict, Any
from app.config.settings import settings
from app.ai.provider import ImageProvider
from app.ai.mock_provider import MockProvider
from app.ai.cloud_providers import FalAiProvider, ReplicateProvider
from app.ai.models import AIGenerationRequest, AIGenerationResult

class AIManager:
    def __init__(self):
        self.providers: Dict[str, ImageProvider] = {
            "mock": MockProvider(),
            "fal": FalAiProvider(),
            "replicate": ReplicateProvider()
        }
        self.fallback_provider = MockProvider()

    def get_active_provider(self) -> ImageProvider:
        provider_key = settings.AI_PROVIDER.lower()
        return self.providers.get(provider_key, self.fallback_provider)

    async def generate_image(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        provider = self.get_active_provider()
        result = await provider.generate(request, combo, output_path)
        
        # Automatic fallback if primary AI provider failed and fallback is enabled
        if not result.success and settings.AI_FALLBACK_ON_ERROR and provider.name != "mock":
            print(f"Primary AI Provider '{provider.name}' failed: {result.error}. Switching to Fallback Provider...")
            fallback_res = await self.fallback_provider.generate(request, combo, output_path)
            fallback_res.is_fallback = True
            return fallback_res
            
        return result

ai_manager = AIManager()
