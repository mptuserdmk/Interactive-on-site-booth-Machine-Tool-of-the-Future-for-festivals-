import base64
import time
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.ai.provider import ImageProvider
from app.ai.models import AIGenerationRequest, AIGenerationResult
from app.ai.prompts import build_negative_prompt

class FalAiProvider(ImageProvider):
    @property
    def name(self) -> str:
        return "fal"

    async def health_check(self) -> bool:
        return bool(settings.AI_API_KEY)

    async def generate(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        start_time = time.time()
        if not settings.AI_API_KEY:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=0,
                error="AI_API_KEY for Fal.ai is not configured"
            )

        try:
            with open(request.input_photo_path, "rb") as img_f:
                b64_photo = base64.b64encode(img_f.read()).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{b64_photo}"

            headers = {
                "Authorization": f"Key {settings.AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": request.prompt,
                "negative_prompt": build_negative_prompt(),
                "image_url": data_uri,
                "strength": 0.65,
                "num_inference_steps": 28,
                "guidance_scale": 7.5
            }

            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    "https://fal.run/fal-ai/flux/dev/image-to-image",
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code != 200:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Fal.ai error {resp.status_code}: {resp.text}"
                    )
                
                data = resp.json()
                image_url = data["images"][0]["url"]
                
                # Download output image
                img_resp = await client.get(image_url)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as out_f:
                    out_f.write(img_resp.content)

            return AIGenerationResult(
                success=True,
                image_path=str(output_path),
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2)
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=str(e)
            )

class ReplicateProvider(ImageProvider):
    @property
    def name(self) -> str:
        return "replicate"

    async def health_check(self) -> bool:
        return bool(settings.AI_API_KEY)

    async def generate(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        start_time = time.time()
        if not settings.AI_API_KEY:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=0,
                error="AI_API_KEY for Replicate is not configured"
            )
        try:
            with open(request.input_photo_path, "rb") as img_f:
                b64_photo = base64.b64encode(img_f.read()).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{b64_photo}"

            headers = {
                "Authorization": f"Token {settings.AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": "a0073c1d977465ab19fa2a061486efc35fb7a14e9f9ae47f0f62d192be432e18", # SDXL Photomaker
                "input": {
                    "prompt": f"img {request.prompt}",
                    "negative_prompt": build_negative_prompt(),
                    "input_image": data_uri,
                    "num_outputs": 1
                }
            }

            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers=headers,
                    json=payload
                )
                if resp.status_code not in (200, 201):
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Replicate API error: {resp.text}"
                    )
                
                pred = resp.json()
                poll_url = pred["urls"]["get"]
                
                # Poll for completion
                while True:
                    await asyncio.sleep(1.0)
                    poll_resp = await client.get(poll_url, headers=headers)
                    pred_data = poll_resp.json()
                    status = pred_data.get("status")
                    if status == "succeeded":
                        img_url = pred_data["output"][0]
                        img_resp = await client.get(img_url)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as out_f:
                            out_f.write(img_resp.content)
                        break
                    elif status in ("failed", "canceled"):
                        return AIGenerationResult(
                            success=False,
                            provider_name=self.name,
                            duration_seconds=round(time.time() - start_time, 2),
                            error=f"Replicate status: {status}"
                        )
                    if time.time() - start_time > settings.AI_TIMEOUT_SECONDS:
                        raise TimeoutError("Replicate generation timed out")

            return AIGenerationResult(
                success=True,
                image_path=str(output_path),
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2)
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=str(e)
            )

class BothubProvider(ImageProvider):
    """
    BotHub AI Image Provider
    Documentation: https://bothub.chat/api/documentation/ru/generation/image_generation
    Base URL: https://openai.bothub.chat/v1
    Supports Russian bank cards, fast connection without VPN, and OpenAI-compatible image endpoints.
    """
    @property
    def name(self) -> str:
        return "bothub"

    async def health_check(self) -> bool:
        return bool(settings.AI_API_KEY)

    async def generate(
        self,
        request: AIGenerationRequest,
        combo: Dict[str, Any],
        output_path: Path
    ) -> AIGenerationResult:
        start_time = time.time()
        if not settings.AI_API_KEY:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=0,
                error="AI_API_KEY for Bothub is not configured. Please set AI_API_KEY in .env"
            )

        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY.strip()}"
        }

        model_name = getattr(settings, "BOTHUB_MODEL", "gemini-2.5-flash-image")

        try:
            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                # 1. If we have an input photo from the kiosk, use the /v1/images/edits endpoint
                if request.input_photo_path and Path(request.input_photo_path).exists():
                    with open(request.input_photo_path, "rb") as f:
                        img_bytes = f.read()

                    files = {
                        "image": ("photo.jpg", img_bytes, "image/jpeg")
                    }
                    data = {
                        "model": model_name,
                        "prompt": request.prompt,
                        "response_format": "url"
                    }

                    resp = await client.post(
                        "https://openai.bothub.chat/v1/images/edits",
                        headers=headers,
                        data=data,
                        files=files
                    )
                else:
                    # 2. Text-to-image generation endpoint
                    payload = {
                        "model": model_name,
                        "prompt": request.prompt,
                        "response_format": "url"
                    }
                    resp = await client.post(
                        "https://openai.bothub.chat/v1/images/generations",
                        headers={**headers, "Content-Type": "application/json"},
                        json=payload
                    )

                if resp.status_code != 200:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub API error {resp.status_code}: {resp.text}"
                    )

                res_json = resp.json()
                data_items = res_json.get("data", [])
                if not data_items:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub returned empty data list: {res_json}"
                    )

                item = data_items[0]
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if "url" in item and item["url"]:
                    img_url = item["url"]
                    # Download generated image from proxied URL
                    img_resp = await client.get(img_url)
                    with open(output_path, "wb") as out_f:
                        out_f.write(img_resp.content)
                elif "b64_json" in item and item["b64_json"]:
                    img_bytes = base64.b64decode(item["b64_json"])
                    with open(output_path, "wb") as out_f:
                        out_f.write(img_bytes)
                else:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub response missing url or b64_json: {item}"
                    )

            return AIGenerationResult(
                success=True,
                image_path=str(output_path),
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2)
            )

        except Exception as e:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=str(e)
            )

