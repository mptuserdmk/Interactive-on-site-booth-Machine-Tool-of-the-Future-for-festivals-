import asyncio
import time
from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFilter
from app.ai.provider import ImageProvider
from app.ai.models import AIGenerationRequest, AIGenerationResult

class MockProvider(ImageProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def health_check(self) -> bool:
        return True

    async def generate(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        start_time = time.time()
        # Realistic simulation delay (1.5 seconds)
        await asyncio.sleep(1.5)

        try:
            input_path = Path(request.input_photo_path)
            if input_path.exists():
                img = Image.open(input_path).convert("RGBA")
            else:
                # Create a placeholder if input photo is somehow missing
                img = Image.new("RGBA", (1024, 1024), (20, 25, 40, 255))
                draw = ImageDraw.Draw(img)
                draw.text((300, 500), "FUTURE ENGINEER", fill="#00d2ff")

            # 1. Enhance contrast and sharpness
            img = ImageEnhance.Contrast(img).enhance(1.25)
            img = ImageEnhance.Sharpness(img).enhance(1.3)

            # 2. Add futuristic cyber tint matching chosen color
            accent_hex = combo.get("color_hex", "#00d2ff")
            # Parse hex to RGB
            hex_str = accent_hex.lstrip('#')
            rgb_accent = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
            
            overlay = Image.new("RGBA", img.size, (*rgb_accent, 45))
            tinted = Image.alpha_composite(img, overlay)

            # 3. Add subtle futuristic overlay lines & elements
            draw = ImageDraw.Draw(tinted)
            w, h = tinted.size
            
            # Sci-fi corner brackets
            for x, y in [(40, 40), (w - 40, 40), (40, h - 40), (w - 40, h - 40)]:
                dx = 60 if x == 40 else -60
                dy = 60 if y == 40 else -60
                draw.line([(x, y), (x + dx, y)], fill=(*rgb_accent, 220), width=4)
                draw.line([(x, y), (x, y + dy)], fill=(*rgb_accent, 220), width=4)

            # Subtle scanlines
            for y_line in range(0, h, 12):
                draw.line([(0, y_line), (w, y_line)], fill=(255, 255, 255, 8), width=1)

            # 4. Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tinted.convert("RGB").save(output_path, "JPEG", quality=95)

            duration = time.time() - start_time
            return AIGenerationResult(
                success=True,
                image_path=str(output_path),
                provider_name=self.name,
                duration_seconds=round(duration, 2)
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=str(e)
            )
