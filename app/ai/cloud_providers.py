import asyncio
import base64
import io
import logging
import re
import ssl
import time
import httpx
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image, ImageOps
from app.config.settings import settings, normalize_proxy_url
from app.ai.provider import ImageProvider
from app.ai.models import AIGenerationRequest, AIGenerationResult
from app.ai.prompts import build_negative_prompt

logger = logging.getLogger("stanok.ai")
MAX_AI_IMAGE_BYTES = 20 * 1024 * 1024
_PLACEHOLDER_KEY = re.compile(r"ваш|ключ|your|api[_-]?key|changeme|xxx|<|>|example", re.IGNORECASE)


def get_ai_ssl_context() -> Union[ssl.SSLContext, bool]:
    """
    Гибридный SSL-контекст: системные сертификаты ОС (Windows / Linux)
    + доверенный бандл НУЦ Минцифры РФ (app/bot/certs/russian_trusted_ca.pem).
    Если в .env задано AI_SSL_VERIFY=false — отключает проверку для DPI-сетей.
    """
    if not getattr(settings, "AI_SSL_VERIFY", True):
        return False
    try:
        ctx = ssl.create_default_context()
        ctx.load_default_certs()
        ca_path = settings.BASE_DIR / "app" / "bot" / "certs" / "russian_trusted_ca.pem"
        if ca_path.is_file():
            ctx.load_verify_locations(cafile=str(ca_path))
        return ctx
    except Exception as e:
        logger.warning("Could not build custom SSL context (%s), falling back to default certifi", e)
        return True


class ProviderError(Exception):
    pass


def api_key_looks_valid(key: str) -> bool:
    """Плейсхолдер из .env.example («ваш_bothub_api_ключ») раньше считался рабочим ключом (H9)."""
    if not key or key != key.strip() or len(key) < 16:
        return False
    if not key.isascii() or not key.isprintable() or any(ch.isspace() for ch in key):
        return False
    return not _PLACEHOLDER_KEY.search(key)


def short_error(resp: httpx.Response) -> str:
    """В ошибку попадает только код и начало тела — не весь ответ провайдера (S8)."""
    return f"HTTP {resp.status_code}: {resp.text[:120]!r}"


def _validate_and_save(content: bytes, output_path: Path):
    if len(content) > MAX_AI_IMAGE_BYTES:
        raise ProviderError(f"изображение слишком большое: {len(content)} байт")
    try:
        with Image.open(io.BytesIO(content)) as im:
            im.verify()
    except Exception as e:
        raise ProviderError(f"провайдер вернул не изображение: {type(e).__name__}") from e
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)


async def download_image(client: httpx.AsyncClient, url: str, output_path: Path):
    """Скачивание результата: 404/HTML/«гигабайт» раньше сохранялись как *_ai.jpg с success=True,
    fallback не срабатывал, а композиция падала → ERROR."""
    async with client.stream("GET", url) as resp:
        if resp.status_code != 200:
            raise ProviderError(f"скачивание результата: HTTP {resp.status_code}")
        chunks, size = [], 0
        async for chunk in resp.aiter_bytes():
            size += len(chunk)
            if size > MAX_AI_IMAGE_BYTES:
                raise ProviderError("изображение слишком большое")
            chunks.append(chunk)
    await asyncio.to_thread(_validate_and_save, b"".join(chunks), output_path)


class FalAiProvider(ImageProvider):
    @property
    def name(self) -> str:
        return "fal"

    async def health_check(self) -> bool:
        return api_key_looks_valid(settings.AI_API_KEY)

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
                        error=f"Fal.ai error {short_error(resp)}"
                    )
                
                data = resp.json()
                image_url = data["images"][0]["url"]
                
                # Download output image
                await download_image(client, image_url, output_path)

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
                error=f"{type(e).__name__}: {str(e)[:200]}"
            )

class ReplicateProvider(ImageProvider):
    @property
    def name(self) -> str:
        return "replicate"

    async def health_check(self) -> bool:
        return api_key_looks_valid(settings.AI_API_KEY)

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
                        error=f"Replicate API error {short_error(resp)}"
                    )
                
                pred = resp.json()
                poll_url = pred["urls"]["get"]
                
                # Poll for completion
                while True:
                    await asyncio.sleep(1.0)
                    poll_resp = await client.get(poll_url, headers=headers)
                    if poll_resp.status_code != 200:
                        raise ProviderError(f"Replicate poll {short_error(poll_resp)}")
                    pred_data = poll_resp.json()
                    status = pred_data.get("status")
                    if status == "succeeded":
                        img_url = pred_data["output"][0]
                        await download_image(client, img_url, output_path)
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
                error=f"{type(e).__name__}: {str(e)[:200]}"
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
        return api_key_looks_valid(settings.AI_API_KEY)

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

        model_name = getattr(settings, "BOTHUB_MODEL", "gemini-3.1-flash-lite-image")

        base_url = (getattr(settings, "BOTHUB_API_BASE", "https://openai.bothub.chat/v1") or "https://openai.bothub.chat/v1").rstrip("/")
        edits_url = f"{base_url}/images/edits"
        generations_url = f"{base_url}/images/generations"

        async def _attempt_generation(verify_ssl: Union[ssl.SSLContext, bool]) -> AIGenerationResult:
            proxy_url = normalize_proxy_url(getattr(settings, "BOTHUB_PROXY", None))
            async with httpx.AsyncClient(
                timeout=settings.AI_TIMEOUT_SECONDS,
                verify=verify_ssl,
                proxy=proxy_url,
                trust_env=False
            ) as client:
                # 1. If we have an input photo from the kiosk, use the /v1/images/edits endpoint
                if request.input_photo_path and Path(request.input_photo_path).exists():
                    with Image.open(request.input_photo_path) as im:
                        im = ImageOps.exif_transpose(im).convert("RGB")
                        im.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=85)
                        img_bytes = buf.getvalue()

                    files = {
                        "image": ("photo.jpg", img_bytes, "image/jpeg")
                    }
                    data = {
                        "model": model_name,
                        "prompt": request.prompt,
                        "response_format": "url"
                    }

                    resp = await client.post(
                        edits_url,
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
                        generations_url,
                        headers={**headers, "Content-Type": "application/json"},
                        json=payload
                    )

                if resp.status_code != 200:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub API error {short_error(resp)}"
                    )

                res_json = resp.json()
                data_items = res_json.get("data", [])
                if not data_items:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error="Bothub returned empty data list"
                    )

                item = data_items[0]
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if "url" in item and item["url"]:
                    img_url = item["url"]
                    # Download generated image from proxied URL
                    await download_image(client, img_url, output_path)
                elif "b64_json" in item and item["b64_json"]:
                    img_bytes = base64.b64decode(item["b64_json"])
                    await asyncio.to_thread(_validate_and_save, img_bytes, output_path)
                else:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub response missing url or b64_json (keys: {sorted(item)[:5]})"
                    )

            return AIGenerationResult(
                success=True,
                image_path=str(output_path),
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2)
            )

        ssl_ctx = get_ai_ssl_context()
        try:
            return await _attempt_generation(ssl_ctx)
        except (httpx.ConnectError, ssl.SSLError) as ssl_err:
            err_str = str(ssl_err)
            # Если возникла ошибка сертификатов (Минцифры / фестивальный прокси / DPI) и SSL был включен:
            if ssl_ctx is not False and any(tok in err_str.upper() for tok in ("CERTIFICATE", "SSL", "WRONG", "VERIFY", "HANDSHAKE")):
                logger.warning("BotHub SSL verification failed (%s). Retrying with verify=False fallback...", ssl_err)
                try:
                    return await _attempt_generation(False)
                except Exception as retry_err:
                    return AIGenerationResult(
                        success=False,
                        provider_name=self.name,
                        duration_seconds=round(time.time() - start_time, 2),
                        error=f"Bothub SSL Fallback Error: {retry_err}"
                    )
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=f"Bothub ConnectError: {ssl_err}"
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                provider_name=self.name,
                duration_seconds=round(time.time() - start_time, 2),
                error=f"{type(e).__name__}: {str(e)[:200]}"
            )

