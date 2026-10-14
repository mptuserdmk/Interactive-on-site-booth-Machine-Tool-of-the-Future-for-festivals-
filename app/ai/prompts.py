from typing import Dict, Any

def build_ai_prompt(combo: Dict[str, Any]) -> str:
    """Builds prompt for image-to-image or portrait stylization according to ТЗ."""
    element = combo.get("element", "technology").upper()
    power = combo.get("power", "precision").upper()
    color_name = combo.get("color_name", "azure").upper()
    theme_desc = combo.get("prompt_theme", "futuristic engineering")
    machine_name = combo.get("machine_name", "Future Engineer")

    prompt = (
        f"Transform the person from the photo into a heroic young cybernetic engineer and industrial creator of the future: {machine_name}. "
        f"Keep the exact face, facial features, hair, and identity of the person in the photo clearly recognizable and photorealistic. "
        f"Dress the person in an ergonomic futuristic engineering suit or exoskeleton with neon {color_name} lighting accents. "
        f"Theme: {element}. Superpower: {power}. "
        f"Setting: High-tech industrial workshop, {theme_desc}, aerospace robotics, clean holographic displays, precision tools. "
        f"Style: Cinematic portrait, 8k, photorealistic, heroic lighting, soft neon glow. "
        f"Strict constraint: Do not add any text, typography, letters, logos or watermarks."
    )
    return prompt

def build_negative_prompt() -> str:
    return (
        "text, watermark, logo, typography, deformed, bad anatomy, cartoon, blurry, low quality, "
        "dark apocalyptic, scary, dirty, disfigured face, extra limbs, ugly"
    )
