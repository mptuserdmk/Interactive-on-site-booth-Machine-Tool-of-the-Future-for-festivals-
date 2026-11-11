import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.ai.provider import ImageProvider
from app.ai.mock_provider import MockProvider
from app.ai.cloud_providers import FalAiProvider, ReplicateProvider, BothubProvider
from app.ai.models import AIGenerationRequest, AIGenerationResult

logger = logging.getLogger("stanok.ai")


class AIManager:
    def __init__(self):
        self.providers: Dict[str, ImageProvider] = {
            "mock": MockProvider(),
            "bothub": BothubProvider(),
            "fal": FalAiProvider(),
            "replicate": ReplicateProvider()
        }
        self.fallback_provider = MockProvider()
        # Статистика для оператора: fallback на mock раньше был невидим (H8)
        self.stats: Dict[str, Any] = {
            "total": 0, "fallback_count": 0, "last_fallback": False,
            "last_error": None, "last_error_at": None,
        }

    def get_active_provider(self) -> ImageProvider:
        provider_key = settings.AI_PROVIDER.lower()
        return self.providers.get(provider_key, self.fallback_provider)

    def _record(self, result: AIGenerationResult, primary_error: Optional[str]):
        self.stats["total"] += 1
        self.stats["last_fallback"] = result.is_fallback
        if result.is_fallback:
            self.stats["fallback_count"] += 1
        if primary_error:
            self.stats["last_error"] = primary_error[:200]
            self.stats["last_error_at"] = time.time()

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
            logger.warning("AI provider '%s' failed for %s: %s — switching to mock fallback",
                           provider.name, request.session_id, (result.error or "")[:200])
            fallback_res = await self.fallback_provider.generate(request, combo, output_path)
            fallback_res.is_fallback = True
            self._record(fallback_res, result.error)
            return fallback_res

        self._record(result, None if result.success else result.error)
        return result


ai_manager = AIManager()
