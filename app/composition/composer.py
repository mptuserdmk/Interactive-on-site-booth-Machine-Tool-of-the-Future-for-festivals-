import os
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from app.config.settings import settings
from app.composition.qr import generate_qr_code, get_digital_card_url

class CardComposer:
    def __init__(self):
        # 1200 x 1800 px (4x6 inch / 10x15 cm print at 300 DPI)
        self.width = 1200
        self.height = 1800
        self._load_fonts()

    def _load_fonts(self):
        # Find available system fonts on Windows or fallback
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/calibrib.ttf"
        ]
        
        bold_font_path = None
        regular_font_path = None
        
        for fp in font_paths:
            if os.path.exists(fp):
                if "bd" in fp.lower() or "b.ttf" in fp.lower():
                    if not bold_font_path:
                        bold_font_path = fp
                else:
                    if not regular_font_path:
                        regular_font_path = fp
        
        if not bold_font_path and regular_font_path:
            bold_font_path = regular_font_path
        if not regular_font_path and bold_font_path:
            regular_font_path = bold_font_path

        try:
            self.font_header = ImageFont.truetype(bold_font_path or "arial.ttf", 36)
            self.font_sub = ImageFont.truetype(regular_font_path or "arial.ttf", 26)
            self.font_title = ImageFont.truetype(bold_font_path or "arial.ttf", 54)
            self.font_power_label = ImageFont.truetype(bold_font_path or "arial.ttf", 28)
            self.font_power = ImageFont.truetype(bold_font_path or "arial.ttf", 38)
            self.font_desc = ImageFont.truetype(regular_font_path or "arial.ttf", 32)
            self.font_loc = ImageFont.truetype(bold_font_path or "arial.ttf", 32)
            self.font_footer = ImageFont.truetype(bold_font_path or "arial.ttf", 28)
            self.font_small = ImageFont.truetype(regular_font_path or "arial.ttf", 22)
        except Exception:
            # Fallback to default
            self.font_header = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_power_label = ImageFont.load_default()
            self.font_power = ImageFont.load_default()
            self.font_desc = ImageFont.load_default()
            self.font_loc = ImageFont.load_default()
            self.font_footer = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def create_gradient_bg(self, accent_hex: str) -> Image.Image:
        base = Image.new("RGBA", (self.width, self.height), "#080c14")
        draw = ImageDraw.Draw(base)
        
        # Subtle technological grid lines
        grid_color = (25, 35, 55, 120)
        for x in range(0, self.width, 60):
            draw.line([(x, 0), (x, self.height)], fill=grid_color, width=1)
        for y in range(0, self.height, 60):
            draw.line([(0, y), (self.width, y)], fill=grid_color, width=1)
            
        # Outer techno card border
        draw.rectangle([30, 30, self.width - 30, self.height - 30], outline=accent_hex, width=3)
        draw.rectangle([40, 40, self.width - 40, self.height - 40], outline=(60, 80, 110, 180), width=1)
        
        # Corner cyber accents
        c_len = 50
        for (cx, cy) in [(30, 30), (self.width - 30, 30), (30, self.height - 30), (self.width - 30, self.height - 30)]:
            dx = c_len if cx == 30 else -c_len
            dy = c_len if cy == 30 else -c_len
            draw.line([(cx, cy), (cx + dx, cy)], fill=accent_hex, width=7)
            draw.line([(cx, cy), (cx, cy + dy)], fill=accent_hex, width=7)
            
        return base

    def wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def compose_card(
        self,
        session_id: str,
        ai_image_path: Path,
        combo: Dict[str, Any],
        output_path: Path
    ) -> Path:
        accent_hex = combo.get("color_hex", "#00d2ff")
        element_name = combo.get("element_name", "ИНЖЕНЕР")
        power_name = combo.get("power_name", "ТОЧНОСТЬ")
        machine_name = combo.get("machine_name", "СТАНОК БУДУЩЕГО")
        description = combo.get("description", "Создаёт инновации будущего.")
        location = combo.get("location", "Передовой производственный центр")
        
        # 1. Base card
        card = self.create_gradient_bg(accent_hex)
        draw = ImageDraw.Draw(card)

        # 2. Header
        header_text = f"FUTURE INDUSTRY  ●  {settings.FESTIVAL_NAME}"
        draw.text((70, 65), header_text, font=self.font_header, fill="#ffffff")
        draw.text((70, 115), "ПАСПОРТ ИНЖЕНЕРА БУДУЩЕГО // ID: " + session_id[:8].upper(), font=self.font_sub, fill=accent_hex)
        
        # 3. AI Portrait Photo Placement
        photo_box = (70, 175, self.width - 70, 975)  # 1060 x 800 px
        pb_w = photo_box[2] - photo_box[0]
        pb_h = photo_box[3] - photo_box[1]
        
        if ai_image_path.exists():
            with Image.open(ai_image_path) as ai_img:
                ai_img = ai_img.convert("RGBA")
                # Aspect fill & crop
                img_w, img_h = ai_img.size
                scale = max(pb_w / img_w, pb_h / img_h)
                new_w, new_h = int(img_w * scale), int(img_h * scale)
                ai_resized = ai_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center crop
                left = (new_w - pb_w) // 2
                top = (new_h - pb_h) // 2
                cropped = ai_resized.crop((left, top, left + pb_w, top + pb_h))
                card.paste(cropped, (photo_box[0], photo_box[1]))
        
        # Frame over AI image
        draw.rectangle(photo_box, outline=accent_hex, width=4)
        
        # Badge on photo
        badge_box = [photo_box[0] + 25, photo_box[3] - 70, photo_box[0] + 360, photo_box[3] - 20]
        draw.rectangle(badge_box, fill="#080c14")
        draw.rectangle(badge_box, outline=accent_hex, width=2)
        draw.text((badge_box[0] + 20, badge_box[1] + 10), f"СТИХИЯ: {element_name.upper()}", font=self.font_sub, fill="#ffffff")

        # 4. Details section
        y_cursor = 1015
        
        # Machine Name
        draw.text((70, y_cursor), machine_name.upper(), font=self.font_title, fill=accent_hex)
        y_cursor += 75
        
        # Superpower line
        draw.text((70, y_cursor), "СУПЕРСИЛА: ", font=self.font_power_label, fill="#8fa0b5")
        bbox_p = draw.textbbox((70, y_cursor), "СУПЕРСИЛА: ", font=self.font_power_label)
        draw.text((bbox_p[2] + 10, y_cursor - 6), power_name.upper(), font=self.font_power, fill="#ffffff")
        y_cursor += 65
        
        # Description (wrapped)
        desc_lines = self.wrap_text(description, self.font_desc, 700, draw)
        for line in desc_lines:
            draw.text((70, y_cursor), line, font=self.font_desc, fill="#d0dbe8")
            y_cursor += 42
        
        y_cursor += 20
        # Location / Enterprise
        draw.text((70, y_cursor), f"🏢 {location}", font=self.font_loc, fill=accent_hex)

        # 5. QR Code & Digital Link (Bottom Right)
        qr_url = get_digital_card_url(session_id)
        qr_img = generate_qr_code(qr_url, size=220)
        
        qr_x = self.width - 70 - 220
        qr_y = self.height - 70 - 260
        
        # White background box for QR to scan reliably
        draw.rectangle([qr_x - 10, qr_y - 10, qr_x + 230, qr_y + 230], fill="#ffffff", outline=accent_hex, width=2)
        card.paste(qr_img, (qr_x, qr_y), qr_img)
        
        draw.text((qr_x - 20, qr_y + 238), "Забери digital-карту", font=self.font_small, fill="#8fa0b5")

        # 6. Footer (Bottom Left)
        draw.text((70, self.height - 110), f"{settings.FESTIVAL_HASHTAG}  ●  СТАНОК БУДУЩЕГО", font=self.font_footer, fill="#ffffff")
        draw.text((70, self.height - 70), "Создано на интерактивном стенде распределения профессий будущего", font=self.font_small, fill="#5a708a")

        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        card.convert("RGB").save(output_path, "JPEG", quality=95)
        return output_path

card_composer = CardComposer()
