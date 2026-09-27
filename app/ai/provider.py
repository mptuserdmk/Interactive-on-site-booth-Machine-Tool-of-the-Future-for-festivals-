from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from app.ai.models import AIGenerationRequest, AIGenerationResult

class ImageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
