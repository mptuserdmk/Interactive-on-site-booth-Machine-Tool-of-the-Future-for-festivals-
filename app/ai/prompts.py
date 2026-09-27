from typing import Dict, Any

def build_ai_prompt(combo: Dict[str, Any]) -> str:
    """Builds prompt for image-to-image or portrait stylization according to ТЗ."""
    element = combo.get("element", "technology").upper()
    power = combo.get("power", "precision").upper()
    color_name = combo.get("color_name", "azure").upper()
    theme_desc = combo.get("prompt_theme", "futuristic engineering")
    machine_name = combo.get("machine_name", "Future Engineer")

    prompt = (
        f"Create a realistic futuristic portrait photograph based on the provided student portrait. "
        f"Transform the student into a heroic young engineer and industrial creator of the future: {machine_name}. "
        f"Theme: {element}. Superpower: {power}. "
        f"Color direction & neon lighting accents: {color_name}. "
        f"Context & environment: High-tech industrial workshop, {theme_desc}, aerospace robotics, clean holographic displays, precision tools. "
        f"The student's face structure and features should remain clearly recognizable while wearing an ergonomic futuristic engineering uniform or lab suit. "
        f"Style: Cinematic, 8k, photorealistic, premium festival quality, optimistic atmosphere, soft neon glow. "
        f"Strict constraint: Do not generate any text, letters, logos, labels or typography."
    )
    return prompt

def build_negative_prompt() -> str:
    return (
        "text, watermark, logo, typography, deformed, bad anatomy, cartoon, blurry, low quality, "
        "dark apocalyptic, scary, dirty, disfigured face, extra limbs, ugly"
    )
