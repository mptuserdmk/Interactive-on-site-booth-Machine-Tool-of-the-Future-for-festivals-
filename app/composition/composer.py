import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps
from app.config.settings import settings
from app.composition.qr import generate_qr_code, get_digital_card_url

class CardComposer:
    def __init__(self):
        # 1200 x 1800 px (4x6 inch / 10x15 cm print at 300 DPI)
        self.width = 1200
        self.height = 1800
        self.dpi = 300
        # Колонка QR справа снизу: текст левее этой границы (иначе адрес наезжает на QR)
        self.text_right_limit_near_qr = self.width - 70 - 220 - 20
        self._font_cache: Dict[Tuple[bool, int], ImageFont.FreeTypeFont] = {}
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

        self.bold_path = bold_font_path or "arial.ttf"
        self.regular_path = regular_font_path or "arial.ttf"
        try:
            self.font_header = self._font(True, 36)
            self.font_sub = self._font(False, 26)
            self.font_title = self._font(True, 54)
            self.font_power_label = self._font(True, 28)
            self.font_power = self._font(True, 38)
            self.font_desc = self._font(False, 32)
            self.font_loc = self._font(True, 32)
            self.font_footer = self._font(True, 28)
            self.font_small = self._font(False, 22)
            self.scalable = True
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
            self.scalable = False

    def _font(self, bold: bool, size: int) -> ImageFont.FreeTypeFont:
        key = (bold, size)
        if key not in self._font_cache:
            self._font_cache[key] = ImageFont.truetype(self.bold_path if bold else self.regular_path, size)
        return self._font_cache[key]

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
        lines: List[str] = []
        current_line: List[str] = []

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

    def fit_text(self, text: str, bold: bool, max_size: int, min_size: int, max_width: int,
                 max_lines: int, draw: ImageDraw.ImageDraw) -> Tuple[ImageFont.ImageFont, List[str]]:
        """Самый крупный кегль, при котором текст укладывается в max_width и max_lines строк (H17):
        раньше «НАЛАДЧИК ПРЕЦИЗИОННЫХ МАНИПУЛЯТОРОВ» шрифтом 54 уходил до x=1378 при ширине карточки 1200."""
        if not self.scalable:
            font = self.font_desc
            return font, self.wrap_text(text, font, max_width, draw)[:max_lines]
        for size in range(max_size, min_size - 1, -2):
            font = self._font(bold, size)
            lines = self.wrap_text(text, font, max_width, draw)
            if len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_width for l in lines):
                return font, lines
        font = self._font(bold, min_size)
        lines = self.wrap_text(text, font, max_width, draw)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            while lines[-1] and draw.textlength(lines[-1] + "…", font=font) > max_width:
                lines[-1] = lines[-1][:-1]
            lines[-1] = lines[-1].rstrip() + "…"
        return font, lines

    @staticmethod
    def _line_height(font: ImageFont.ImageFont) -> int:
        size = getattr(font, "size", 20)
        return int(size * 1.22)

    @staticmethod
    def _draw_pin(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: str):
        """Векторная метка локации вместо эмодзи 🏢 (в Arial его нет — печатался «квадратик»)."""
        r = size // 3
        cx = x + size // 2
        draw.ellipse([cx - r, y, cx + r, y + 2 * r], fill=color)
        draw.polygon([(cx - r + 2, y + r + 4), (cx + r - 2, y + r + 4), (cx, y + size)], fill=color)
        draw.ellipse([cx - r // 2 + 1, y + r // 2 + 1, cx + r // 2 - 1, y + r + r // 2 - 1], fill="#080c14")

    @staticmethod
    def short_code(session_id: str) -> str:
        """Код на карточке для сверки с историей оператора (раньше session_id[:8] = «SESS_202» у всех)."""
        return session_id.rsplit("_", 1)[-1][-6:].upper()

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
        full_width = self.width - 140

        # 1. Base card
        card = self.create_gradient_bg(accent_hex)
        draw = ImageDraw.Draw(card)

        # 2. Header (раньше «FUTURE INDUSTRY ● FUTURE INDUSTRY 2026»)
        header_font, header_lines = self.fit_text(f"СТАНОК БУДУЩЕГО  ●  {settings.FESTIVAL_NAME}", True, 36, 24,
                                                  full_width, 1, draw)
        draw.text((70, 65), header_lines[0], font=header_font, fill="#ffffff")
        draw.text((70, 115), "ПАСПОРТ ИНЖЕНЕРА БУДУЩЕГО // ID: " + self.short_code(session_id), font=self.font_sub, fill=accent_hex)

        # 3. AI Portrait Photo Placement
        photo_box = (70, 175, self.width - 70, 975)  # 1060 x 800 px
        pb_w = photo_box[2] - photo_box[0]
        pb_h = photo_box[3] - photo_box[1]

        if ai_image_path.exists():
            with Image.open(ai_image_path) as src:
                ai_img = ImageOps.exif_transpose(src).convert("RGBA")
            # Aspect fill & crop
            img_w, img_h = ai_img.size
            scale = max(pb_w / img_w, pb_h / img_h)
            new_w, new_h = max(pb_w, int(img_w * scale)), max(pb_h, int(img_h * scale))
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
        badge_font, badge_lines = self.fit_text(f"СТИХИЯ: {element_name.upper()}", False, 26, 18,
                                                badge_box[2] - badge_box[0] - 30, 1, draw)
        draw.rectangle(badge_box, fill="#080c14")
        draw.rectangle(badge_box, outline=accent_hex, width=2)
        draw.text((badge_box[0] + 15, badge_box[1] + 10), badge_lines[0], font=badge_font, fill="#ffffff")

        # 4. Details section
        y_cursor = 1015

        # Machine Name: уменьшаем кегль и/или переносим на 2 строки, но не выходим за рамку (H17)
        title_font, title_lines = self.fit_text(machine_name.upper(), True, 54, 38, full_width, 2, draw)
        for line in title_lines:
            draw.text((70, y_cursor), line, font=title_font, fill=accent_hex)
            y_cursor += self._line_height(title_font)
        y_cursor += 10

        # Superpower line
        draw.text((70, y_cursor), "СУПЕРСИЛА: ", font=self.font_power_label, fill="#8fa0b5")
        bbox_p = draw.textbbox((70, y_cursor), "СУПЕРСИЛА: ", font=self.font_power_label)
        draw.text((bbox_p[2] + 10, y_cursor - 6), power_name.upper(), font=self.font_power, fill="#ffffff")
        y_cursor += 65

        # Description (wrapped)
        desc_font, desc_lines = self.fit_text(description, False, 32, 24, 700, 4, draw)
        for line in desc_lines:
            draw.text((70, y_cursor), line, font=desc_font, fill="#d0dbe8")
            y_cursor += self._line_height(desc_font) + 3

        y_cursor += 20
        # Location / Enterprise: не заходит в колонку QR
        loc_x = 70 + 44
        loc_font, loc_lines = self.fit_text(location, True, 32, 24, self.text_right_limit_near_qr - loc_x, 2, draw)
        self._draw_pin(draw, 70, y_cursor + 2, 32, accent_hex)
        for line in loc_lines:
            draw.text((loc_x, y_cursor), line, font=loc_font, fill=accent_hex)
            y_cursor += self._line_height(loc_font)

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

        # Save result: 300 DPI в метаданных, иначе драйвер печатает в масштабе 72/96 DPI
        output_path.parent.mkdir(parents=True, exist_ok=True)
        card.convert("RGB").save(output_path, "JPEG", quality=95, dpi=(self.dpi, self.dpi))
        return output_path

card_composer = CardComposer()
