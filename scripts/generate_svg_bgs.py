"""
Генератор векторных фоновых иллюстраций для кнопок интерфейса киоска.
Визуальный стандарт: Folk-Tech (Неорусский стимпанк и хай-тек).
Надписи вынесены строго сбоку вертикально по боковым кромкам,
чтобы не пересекаться и не мешать основным надписям карточек (заголовкам и подсказкам).
"""

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "static" / "images" / "buttons"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def svg_header(title="Фон кнопки"):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="100%" height="100%">
  <defs>
    <radialGradient id="bgGrad" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#1A2430" />
      <stop offset="60%" stop-color="#121820" />
      <stop offset="100%" stop-color="#0B0F14" />
    </radialGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <pattern id="techGrid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#C59A45" stroke-width="0.5" stroke-opacity="0.12" />
      <circle cx="40" cy="0" r="1" fill="#C59A45" fill-opacity="0.25" />
    </pattern>
  </defs>

  <!-- Базовый тёмный графитовый фон с сеткой станка -->
  <rect width="800" height="450" fill="url(#bgGrad)" />
  <rect width="800" height="450" fill="url(#techGrid)" />
'''


def svg_footer(left_label="ГОСТ 2.0 // ЧПУ", right_label="ТЕЛЕМЕТРИЯ // СТАНДАРТ", label_color="#C59A45"):
    return f'''  <!-- Латунная филигранная рамка и уголки Folk-Tech -->
  <rect x="12" y="12" width="776" height="426" rx="14" fill="none" stroke="#C59A45" stroke-width="1.5" stroke-opacity="0.35" />
  <rect x="18" y="18" width="764" height="414" rx="10" fill="none" stroke="#E8CA7B" stroke-width="0.7" stroke-opacity="0.2" stroke-dasharray="8 4" />
  
  <!-- Латунные заклепки по углам -->
  <circle cx="28" cy="28" r="4" fill="#C59A45" />
  <circle cx="28" cy="28" r="2" fill="#E8CA7B" />
  <circle cx="772" cy="28" r="4" fill="#C59A45" />
  <circle cx="772" cy="28" r="2" fill="#E8CA7B" />
  <circle cx="28" cy="422" r="4" fill="#C59A45" />
  <circle cx="28" cy="422" r="2" fill="#E8CA7B" />
  <circle cx="772" cy="422" r="4" fill="#C59A45" />
  <circle cx="772" cy="422" r="2" fill="#E8CA7B" />

  <!-- Вертикальные надписи строго по боковым кромкам карточки (не мешают текстам в центре) -->
  <g transform="translate(26, 225) rotate(-90)">
    <text text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="bold" fill="{label_color}" letter-spacing="3" fill-opacity="0.55">
      {left_label}
    </text>
  </g>
  <g transform="translate(774, 225) rotate(90)">
    <text text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="bold" fill="{label_color}" letter-spacing="3" fill-opacity="0.55">
      {right_label}
    </text>
  </g>
</svg>'''


def create_care_svg():
    # Забота: Оберег, защитный купол, спасительные ладони, зелёный росток жизни, экосистема
    return svg_header("Забота") + '''
  <defs>
    <radialGradient id="careGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00FF88" stop-opacity="0.5" />
      <stop offset="50%" stop-color="#00A3FF" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#00FF88" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#E8CA7B" />
      <stop offset="40%" stop-color="#C59A45" />
      <stop offset="100%" stop-color="#005E4D" />
    </linearGradient>
  </defs>

  <!-- Световой ореол защиты -->
  <circle cx="400" cy="225" r="190" fill="url(#careGlow)" />

  <!-- Защитные концентрические орбиты оберега -->
  <circle cx="400" cy="225" r="160" fill="none" stroke="#00FF88" stroke-width="1.2" stroke-dasharray="12 6" stroke-opacity="0.4" />
  <circle cx="400" cy="225" r="130" fill="none" stroke="#E8CA7B" stroke-width="1.5" stroke-opacity="0.5" />
  <circle cx="400" cy="225" r="100" fill="none" stroke="#00A3FF" stroke-width="0.8" stroke-dasharray="4 4" stroke-opacity="0.5" />

  <!-- Орнаментальный геральдический щит оберега -->
  <g transform="translate(400, 210) scale(1.15)">
    <!-- Контур щита -->
    <path d="M 0 -85 Q 75 -85 85 -20 Q 90 60 0 100 Q -90 60 -85 -20 Q -75 -85 0 -85 Z" 
          fill="#162326" fill-opacity="0.8" stroke="url(#shieldGrad)" stroke-width="3" filter="url(#softGlow)" />
    
    <!-- Внутренний орнамент щита -->
    <path d="M 0 -70 Q 58 -70 66 -16 Q 70 48 0 80 Q -70 48 -66 -16 Q -58 -70 0 -70 Z" 
          fill="none" stroke="#00FF88" stroke-width="1.2" stroke-opacity="0.6" stroke-dasharray="6 3" />

    <!-- Заботливые бережные ладони -->
    <path d="M -45 42 C -40 20 -28 5 -12 -5 C -8 -7 -6 -2 -10 3 C -20 16 -28 32 -32 50 C -34 54 -42 54 -45 42 Z" 
          fill="#E8CA7B" fill-opacity="0.85" />
    <path d="M 45 42 C 40 20 28 5 12 -5 C 8 -7 6 -2 10 3 C 20 16 28 32 32 50 C 34 54 42 54 45 42 Z" 
          fill="#E8CA7B" fill-opacity="0.85" />

    <!-- Живой росток жизни / Биосфера по центру -->
    <path d="M 0 35 Q 0 -10 -18 -32 Q 5 -30 0 5 Z" fill="#00FF88" filter="url(#softGlow)" />
    <path d="M 0 35 Q 0 -18 18 -38 Q 2 -32 0 -2 Z" fill="#2ECC71" filter="url(#softGlow)" />
    <circle cx="0" cy="-44" r="5" fill="#E8CA7B" filter="url(#softGlow)" />
    <circle cx="0" cy="-44" r="2.5" fill="#FFFFFF" />
  </g>
''' + svg_footer("ОБЕРЕГ // БЕЗОПАСНОСТЬ 100%", "ЗАЩИТА ОПЕРАТОРА // ЭКО-2.0", "#00FF88")


def create_medicine_svg():
    # Медицина: ДНК, бионика, живая вода, колбы, микромир
    return svg_header("Медицина") + '''
  <defs>
    <radialGradient id="medGlow" cx="50%" cy="225" r="50%">
      <stop offset="0%" stop-color="#00A3FF" stop-opacity="0.45" />
      <stop offset="50%" stop-color="#00FF88" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#00A3FF" stop-opacity="0" />
    </radialGradient>
  </defs>

  <circle cx="400" cy="225" r="180" fill="url(#medGlow)" />

  <g transform="translate(400, 225)" opacity="0.35">
    <circle cx="0" cy="0" r="140" fill="none" stroke="#C59A45" stroke-width="2" stroke-dasharray="14 7" />
    <circle cx="0" cy="0" r="115" fill="none" stroke="#00A3FF" stroke-width="1.2" />
  </g>

  <!-- Спираль ДНК / Биотехнологии (Folk-Tech) -->
  <g transform="translate(400, 225)">
    <path d="M -80 -130 Q -20 -90 0 -50 T 80 30 T 0 110 T -80 140" fill="none" stroke="#00A3FF" stroke-width="3" filter="url(#softGlow)" />
    <path d="M 80 -130 Q 20 -90 0 -50 T -80 30 T 0 110 T 80 140" fill="none" stroke="#00FF88" stroke-width="3" filter="url(#softGlow)" />

    <line x1="-70" y1="-115" x2="70" y2="-115" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-70" cy="-115" r="4.5" fill="#00A3FF" />
    <circle cx="70" cy="-115" r="4.5" fill="#00FF88" />
    <circle cx="0" cy="-115" r="3" fill="#E8CA7B" />

    <line x1="-45" y1="-80" x2="45" y2="-80" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-45" cy="-80" r="4.5" fill="#00FF88" />
    <circle cx="45" cy="-80" r="4.5" fill="#00A3FF" />
    <circle cx="0" cy="-80" r="3" fill="#E8CA7B" />

    <line x1="0" y1="-45" x2="0" y2="-45" stroke="#E8CA7B" stroke-width="2" />
    <circle cx="0" cy="-45" r="6" fill="#FFFFFF" filter="url(#softGlow)" />

    <line x1="-50" y1="-10" x2="50" y2="-10" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-50" cy="-10" r="4.5" fill="#00A3FF" />
    <circle cx="50" cy="-10" r="4.5" fill="#00FF88" />

    <line x1="-75" y1="25" x2="75" y2="25" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-75" cy="25" r="4.5" fill="#00FF88" />
    <circle cx="75" cy="25" r="4.5" fill="#00A3FF" />

    <line x1="-45" y1="65" x2="45" y2="65" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-45" cy="65" r="4.5" fill="#00A3FF" />
    <circle cx="45" cy="65" r="4.5" fill="#00FF88" />

    <line x1="-20" y1="100" x2="20" y2="100" stroke="#E8CA7B" stroke-width="2" stroke-opacity="0.8" />
    <circle cx="-20" cy="100" r="4" fill="#00FF88" />
    <circle cx="20" cy="100" r="4" fill="#00A3FF" />
  </g>

  <g transform="translate(620, 225) scale(0.9)">
    <circle cx="0" cy="0" r="45" fill="#1C2834" stroke="#C59A45" stroke-width="2" />
    <path d="M 0 -30 C 18 -8 24 10 24 18 C 24 30 14 38 0 38 C -14 38 -24 30 -24 18 C -24 10 -18 -8 0 -30 Z" fill="#00A3FF" fill-opacity="0.8" filter="url(#softGlow)" />
    <circle cx="-6" cy="12" r="3" fill="#FFFFFF" />
  </g>

  <g transform="translate(180, 225) scale(0.9)">
    <circle cx="0" cy="0" r="45" fill="#1C2834" stroke="#C59A45" stroke-width="2" />
    <path d="M -20 -6 L -6 -6 L -6 -20 L 6 -20 L 6 -6 L 20 -6 L 20 6 L 6 6 L 6 20 L -6 20 L -6 6 L -20 6 Z" fill="#BA1B1D" stroke="#E8CA7B" stroke-width="1.5" />
  </g>
''' + svg_footer("БИОИНЖЕНЕРИЯ // ЖИВАЯ ВОДА", "БИОНИКА ЧПУ // ЧИСТОТА 99.9%", "#00A3FF")


def create_metal_svg():
    # Металл: Кузница будущего, лазерная резка, раскалённый металл, наковальня, искры
    return svg_header("Металл") + '''
  <defs>
    <radialGradient id="forgeGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FF5500" stop-opacity="0.6" />
      <stop offset="40%" stop-color="#BA1B1D" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="moltenGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FFE600" />
      <stop offset="50%" stop-color="#FF5500" />
      <stop offset="100%" stop-color="#BA1B1D" />
    </linearGradient>
  </defs>

  <circle cx="400" cy="235" r="210" fill="url(#forgeGlow)" />

  <line x1="400" y1="20" x2="400" y2="240" stroke="#FFE600" stroke-width="3" filter="url(#glow)" />
  <line x1="400" y1="20" x2="400" y2="240" stroke="#FFFFFF" stroke-width="1.2" />

  <g stroke="#FFE600" stroke-width="1.5" opacity="0.85">
    <line x1="400" y1="240" x2="330" y2="180" stroke-dasharray="8 4" />
    <line x1="400" y1="240" x2="470" y2="175" stroke-dasharray="10 5" />
    <line x1="400" y1="240" x2="310" y2="225" />
    <line x1="400" y1="240" x2="490" y2="220" />
    <line x1="400" y1="240" x2="350" y2="280" />
    <line x1="400" y1="240" x2="460" y2="285" />
  </g>
  <circle cx="400" cy="240" r="14" fill="#FFFFFF" filter="url(#glow)" />

  <g transform="translate(400, 245)">
    <rect x="-180" y="0" width="360" height="42" rx="6" fill="#2A1D1A" stroke="url(#moltenGrad)" stroke-width="2.5" />
    <line x1="-160" y1="21" x2="160" y2="21" stroke="url(#moltenGrad)" stroke-width="4" filter="url(#softGlow)" />
  </g>

  <g transform="translate(160, 225) scale(0.85)" opacity="0.5">
    <circle cx="0" cy="0" r="60" fill="none" stroke="#C59A45" stroke-width="10" stroke-dasharray="18 12" />
    <circle cx="0" cy="0" r="30" fill="#1C232D" stroke="#E8CA7B" stroke-width="2" />
  </g>
  <g transform="translate(640, 225) scale(0.85)" opacity="0.5">
    <circle cx="0" cy="0" r="60" fill="none" stroke="#C59A45" stroke-width="10" stroke-dasharray="18 12" />
    <circle cx="0" cy="0" r="30" fill="#1C232D" stroke="#E8CA7B" stroke-width="2" />
  </g>
''' + svg_footer("МЕТАЛЛУРГИЯ // ТИТАН 3000°C", "ЛАЗЕРНЫЙ РАСКРОЙ // 12 kW", "#FF5500")


def create_precision_svg():
    # Точность: Лазерная мишень, координатная сетка, микрометр, 0.001 мм
    return svg_header("Точность") + '''
  <defs>
    <radialGradient id="precGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00A3FF" stop-opacity="0.45" />
      <stop offset="60%" stop-color="#C59A45" stop-opacity="0.15" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>

  <circle cx="400" cy="225" r="190" fill="url(#precGlow)" />

  <g transform="translate(400, 225)">
    <circle cx="0" cy="0" r="160" fill="none" stroke="#C59A45" stroke-width="1" stroke-opacity="0.3" stroke-dasharray="4 8" />
    <circle cx="0" cy="0" r="130" fill="none" stroke="#E8CA7B" stroke-width="1.5" stroke-opacity="0.6" stroke-dasharray="24 6" />
    <circle cx="0" cy="0" r="95" fill="none" stroke="#00A3FF" stroke-width="2" filter="url(#softGlow)" />
    <circle cx="0" cy="0" r="60" fill="none" stroke="#E8CA7B" stroke-width="1.2" stroke-dasharray="8 4" />
    <circle cx="0" cy="0" r="25" fill="none" stroke="#BA1B1D" stroke-width="2" />
    <circle cx="0" cy="0" r="5" fill="#00A3FF" filter="url(#glow)" />
    <circle cx="0" cy="0" r="2" fill="#FFFFFF" />

    <line x1="-180" y1="0" x2="-35" y2="0" stroke="#00A3FF" stroke-width="1.5" />
    <line x1="35" y1="0" x2="180" y2="0" stroke="#00A3FF" stroke-width="1.5" />
    <line x1="0" y1="-180" x2="0" y2="-35" stroke="#00A3FF" stroke-width="1.5" />
    <line x1="0" y1="35" x2="0" y2="180" stroke="#00A3FF" stroke-width="1.5" />

    <g stroke="#E8CA7B" stroke-width="1" opacity="0.75">
      <line x1="-120" y1="-8" x2="-120" y2="8" />
      <line x1="-90" y1="-5" x2="-90" y2="5" />
      <line x1="-60" y1="-8" x2="-60" y2="8" />
      <line x1="60" y1="-8" x2="60" y2="8" />
      <line x1="90" y1="-5" x2="90" y2="5" />
      <line x1="120" y1="-8" x2="120" y2="8" />
    </g>

    <path d="M -150 -130 L -150 -150 L -130 -150" fill="none" stroke="#BA1B1D" stroke-width="2.5" />
    <path d="M 150 -130 L 150 -150 L 130 -150" fill="none" stroke="#BA1B1D" stroke-width="2.5" />
    <path d="M -150 130 L -150 150 L -130 150" fill="none" stroke="#BA1B1D" stroke-width="2.5" />
    <path d="M 150 130 L 150 150 L 130 150" fill="none" stroke="#BA1B1D" stroke-width="2.5" />
  </g>
''' + svg_footer("КАЛИБРОВКА // ±0.001 ММ", "ОПТИЧЕСКИЙ ЛАЗЕР // X/Y/Z", "#00A3FF")


def create_speed_svg():
    # Скорость: Сверхзвуковой поток, молния, кинетические линии, турбина
    return svg_header("Скорость") + '''
  <defs>
    <radialGradient id="speedGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FFE600" stop-opacity="0.5" />
      <stop offset="50%" stop-color="#FF5500" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="streamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00A3FF" stop-opacity="0" />
      <stop offset="50%" stop-color="#FFE600" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#FFFFFF" />
    </linearGradient>
  </defs>

  <circle cx="450" cy="225" r="200" fill="url(#speedGlow)" />

  <g stroke="url(#streamGrad)" stroke-linecap="round">
    <line x1="80" y1="110" x2="520" y2="110" stroke-width="2" />
    <line x1="140" y1="150" x2="620" y2="150" stroke-width="3" />
    <line x1="60" y1="190" x2="560" y2="190" stroke-width="1.5" />
    <line x1="180" y1="260" x2="680" y2="260" stroke-width="3.5" />
    <line x1="90" y1="300" x2="580" y2="300" stroke-width="2" />
    <line x1="150" y1="340" x2="510" y2="340" stroke-width="1.5" />
  </g>

  <g transform="translate(420, 220)">
    <polygon points="40,-130 -50,-10 10,-10 -30,130 70,5 10,5" fill="#FFE600" stroke="#E8CA7B" stroke-width="2.5" filter="url(#softGlow)" />
    <polygon points="35,-120 -40,-15 8,-15 -20,115 55,0 8,0" fill="#FFFFFF" />
  </g>

  <g transform="translate(400, 225)" stroke="#00A3FF" fill="none" opacity="0.6">
    <path d="M 180 -120 L -60 0 L 180 120" stroke-width="2" stroke-dasharray="10 5" />
  </g>
''' + svg_footer("СКОРОСТЬ // 12 МАХ // ТУРБО", "МОЛНИЯ ПЕРУНА // ACCEL 45G", "#FFE600")


def create_power_svg():
    # Сила: Гидравлический пресс, колоссальная мощь, давление мегаватт, массивные поршни
    return svg_header("Сила") + '''
  <defs>
    <radialGradient id="powerGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#BA1B1D" stop-opacity="0.55" />
      <stop offset="50%" stop-color="#C59A45" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="pistonGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#C59A45" />
      <stop offset="50%" stop-color="#1C232D" />
      <stop offset="100%" stop-color="#8B651B" />
    </linearGradient>
  </defs>

  <circle cx="400" cy="225" r="200" fill="url(#powerGlow)" />

  <g transform="translate(400, 225)">
    <rect x="-90" y="-150" width="180" height="65" rx="6" fill="#1C232D" stroke="#C59A45" stroke-width="3" />
    <circle cx="0" cy="-118" r="16" fill="#BA1B1D" stroke="#E8CA7B" stroke-width="2" />

    <rect x="-45" y="-85" width="90" height="150" fill="url(#pistonGrad)" stroke="#E8CA7B" stroke-width="2.5" />
    <line x1="-30" y1="-85" x2="-30" y2="65" stroke="#FFFFFF" stroke-opacity="0.3" stroke-width="3" />

    <rect x="-130" y="65" width="260" height="55" rx="8" fill="#161C24" stroke="#BA1B1D" stroke-width="3.5" />
    <line x1="-120" y1="78" x2="120" y2="78" stroke="#FFE600" stroke-width="2" stroke-dasharray="14 7" />

    <g transform="translate(-180, -20) scale(0.9)">
      <circle cx="0" cy="0" r="38" fill="#161C24" stroke="#C59A45" stroke-width="3" />
      <circle cx="0" cy="0" r="30" fill="none" stroke="#E8CA7B" stroke-width="1" stroke-dasharray="6 3" />
      <line x1="0" y1="0" x2="16" y2="-18" stroke="#BA1B1D" stroke-width="2.5" />
      <circle cx="0" cy="0" r="4" fill="#C59A45" />
    </g>
    <g transform="translate(180, -20) scale(0.9)">
      <circle cx="0" cy="0" r="38" fill="#161C24" stroke="#C59A45" stroke-width="3" />
      <circle cx="0" cy="0" r="30" fill="none" stroke="#E8CA7B" stroke-width="1" stroke-dasharray="6 3" />
      <line x1="0" y1="0" x2="-18" y2="-15" stroke="#BA1B1D" stroke-width="2.5" />
      <circle cx="0" cy="0" r="4" fill="#C59A45" />
    </g>
  </g>
''' + svg_footer("ГИДРОПРЕСС // 10 000 ТОНН", "ДАВЛЕНИЕ 500 МПА // МОЩЬ", "#BA1B1D")


def create_mind_svg():
    # Ум: Искусственный интеллект, нейросеть, синапсы, квантовый кристалл
    return svg_header("Ум") + '''
  <defs>
    <radialGradient id="mindGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00A3FF" stop-opacity="0.55" />
      <stop offset="50%" stop-color="#E8CA7B" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>

  <circle cx="400" cy="225" r="210" fill="url(#mindGlow)" />

  <g transform="translate(400, 225)">
    <rect x="-65" y="-65" width="130" height="130" rx="16" fill="#121820" stroke="#E8CA7B" stroke-width="3" filter="url(#softGlow)" />
    <rect x="-50" y="-50" width="100" height="100" rx="10" fill="#1C2836" stroke="#00A3FF" stroke-width="1.5" />
    <circle cx="0" cy="0" r="28" fill="#00A3FF" fill-opacity="0.4" filter="url(#glow)" />
    <circle cx="0" cy="0" r="12" fill="#FFFFFF" />

    <g stroke="#00A3FF" stroke-width="2" opacity="0.85">
      <line x1="-50" y1="-50" x2="-140" y2="-120" />
      <circle cx="-140" cy="-120" r="6" fill="#E8CA7B" />
      <line x1="-140" y1="-120" x2="-210" y2="-120" />
      <circle cx="-210" cy="-120" r="4" fill="#00A3FF" />

      <line x1="50" y1="-50" x2="140" y2="-120" />
      <circle cx="140" cy="-120" r="6" fill="#E8CA7B" />
      <line x1="140" y1="-120" x2="210" y2="-120" />
      <circle cx="210" cy="-120" r="4" fill="#00A3FF" />

      <line x1="-50" y1="50" x2="-150" y2="110" />
      <circle cx="-150" cy="110" r="6" fill="#E8CA7B" />
      <line x1="-150" y1="110" x2="-220" y2="110" />
      <circle cx="-220" cy="110" r="4" fill="#00A3FF" />

      <line x1="50" y1="50" x2="150" y2="110" />
      <circle cx="150" cy="110" r="6" fill="#E8CA7B" />
      <line x1="150" y1="110" x2="220" y2="110" />
      <circle cx="220" cy="110" r="4" fill="#00A3FF" />

      <line x1="-65" y1="0" x2="-180" y2="0" />
      <circle cx="-180" cy="0" r="5" fill="#E8CA7B" />
      <line x1="65" y1="0" x2="180" y2="0" />
      <circle cx="180" cy="0" r="5" fill="#E8CA7B" />
    </g>
  </g>
''' + svg_footer("НЕЙРОСЕТЬ // 1.2 PFLOPS", "КВАНТОВЫЙ РАЗУМ // 100B", "#00A3FF")


# --- БОГАТЫЕ ПОЛНОФОРМАТНЫЕ ФОНЫ ДЛЯ ВЫБОРА ЦВЕТА ---

def create_color_azure_svg():
    # Лазурный: Квантовые волны, лазурит, кристалл фотонов
    return svg_header("Лазурный") + '''
  <defs>
    <radialGradient id="azureGlow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#00D2FF" stop-opacity="0.55" />
      <stop offset="45%" stop-color="#0077B6" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>
  <circle cx="400" cy="225" r="210" fill="url(#azureGlow)" />

  <!-- Лазурные энергетические кольца и кристаллические грани -->
  <g transform="translate(400, 225)">
    <circle cx="0" cy="0" r="140" fill="none" stroke="#00D2FF" stroke-width="1.8" stroke-dasharray="16 8" stroke-opacity="0.6" />
    <circle cx="0" cy="0" r="100" fill="none" stroke="#E8CA7B" stroke-width="1.2" stroke-opacity="0.5" />
    <circle cx="0" cy="0" r="65" fill="#00D2FF" fill-opacity="0.2" stroke="#00D2FF" stroke-width="2" filter="url(#glow)" />
    
    <!-- Грани кристалла лазурита -->
    <polygon points="0,-75 55,-25 35,55 -35,55 -55,-25" fill="#0A2540" stroke="#00D2FF" stroke-width="2" />
    <polygon points="0,-50 35,-15 22,35 -22,35 -35,-15" fill="#00D2FF" fill-opacity="0.5" stroke="#FFFFFF" stroke-width="1" />
    <circle cx="0" cy="0" r="8" fill="#FFFFFF" filter="url(#softGlow)" />

    <!-- Лазерные лучи рефракции -->
    <g stroke="#00D2FF" stroke-width="1.5" stroke-opacity="0.7">
      <line x1="-160" y1="-90" x2="-60" y2="-30" />
      <line x1="160" y1="-90" x2="60" y2="-30" />
      <line x1="-160" y1="90" x2="-60" y2="30" />
      <line x1="160" y1="90" x2="60" y2="30" />
    </g>
  </g>
''' + svg_footer("ГЕРБОВАЯ ЭМАЛЬ // ЛАЗУРЬ", "КВАНТОВОЕ СИЯНИЕ // #00D2FF", "#00D2FF")


def create_color_gold_svg():
    # Золотой: Расплавленное золото, имперская латунь, солнце ЧПУ
    return svg_header("Золотой") + '''
  <defs>
    <radialGradient id="goldGlow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#FFD700" stop-opacity="0.6" />
      <stop offset="45%" stop-color="#C59A45" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>
  <circle cx="400" cy="225" r="210" fill="url(#goldGlow)" />

  <!-- Латунное золотое солнце с шестеренчатыми лучами -->
  <g transform="translate(400, 225)">
    <circle cx="0" cy="0" r="145" fill="none" stroke="#C59A45" stroke-width="2" stroke-dasharray="24 8" stroke-opacity="0.7" />
    <circle cx="0" cy="0" r="110" fill="none" stroke="#E8CA7B" stroke-width="1.5" stroke-opacity="0.6" />
    
    <!-- Солнечная корона из латунных зубьев -->
    <g stroke="#FFD700" stroke-width="2" opacity="0.85">
      <line x1="0" y1="-140" x2="0" y2="-90" />
      <line x1="0" y1="90" x2="0" y2="140" />
      <line x1="-140" y1="0" x2="-90" y2="0" />
      <line x1="90" y1="0" x2="140" y2="0" />
      <line x1="-100" y1="-100" x2="-65" y2="-65" />
      <line x1="65" y1="65" x2="100" y2="100" />
      <line x1="100" y1="-100" x2="65" y2="-65" />
      <line x1="-65" y1="65" x2="-100" y2="100" />
    </g>

    <!-- Центральный золотой слиток / медальон -->
    <circle cx="0" cy="0" r="55" fill="#241B08" stroke="#FFD700" stroke-width="3" filter="url(#softGlow)" />
    <circle cx="0" cy="0" r="38" fill="#C59A45" fill-opacity="0.5" stroke="#FFE600" stroke-width="1.5" />
    <circle cx="0" cy="0" r="16" fill="#FFFFFF" filter="url(#glow)" />
  </g>
''' + svg_footer("ГЕРБОВАЯ ЭМАЛЬ // ЗОЛОТО", "БЛАГОРОДНАЯ ЛАТУНЬ // #FFD700", "#FFD700")


def create_color_emerald_svg():
    # Изумрудный: Малахит, биосферный кристалл, лазерное квантовое свечение
    return svg_header("Изумрудный") + '''
  <defs>
    <radialGradient id="emeraldGlow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#00FF88" stop-opacity="0.55" />
      <stop offset="45%" stop-color="#005E4D" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>
  <circle cx="400" cy="225" r="210" fill="url(#emeraldGlow)" />

  <!-- Малахитовые геометрические узоры и кристаллические друзы -->
  <g transform="translate(400, 225)">
    <circle cx="0" cy="0" r="145" fill="none" stroke="#00FF88" stroke-width="1.5" stroke-dasharray="12 6" stroke-opacity="0.6" />
    <circle cx="0" cy="0" r="110" fill="none" stroke="#E8CA7B" stroke-width="1.2" stroke-opacity="0.5" />
    
    <!-- Изумрудная призма -->
    <polygon points="0,-80 65,-20 40,65 -40,65 -65,-20" fill="#0C241D" stroke="#00FF88" stroke-width="2.5" filter="url(#softGlow)" />
    <polygon points="0,-55 42,-15 28,42 -28,42 -42,-15" fill="#00FF88" fill-opacity="0.4" stroke="#70FFB8" stroke-width="1.2" />
    <circle cx="0" cy="0" r="10" fill="#FFFFFF" filter="url(#glow)" />

    <!-- Векторные ветви малахитовой филиграни -->
    <g stroke="#00FF88" stroke-width="1.2" opacity="0.65" fill="none">
      <path d="M -160 0 Q -110 -60 -65 -20" />
      <path d="M 160 0 Q 110 -60 65 -20" />
      <path d="M -160 0 Q -110 60 -40 65" />
      <path d="M 160 0 Q 110 60 40 65" />
    </g>
  </g>
''' + svg_footer("ГЕРБОВАЯ ЭМАЛЬ // ИЗУМРУД", "МАЛАХИТОВЫЙ КРИСТАЛЛ // #00FF88", "#00FF88")


def create_color_white_svg():
    # Белый: Платиновое сияние, титан, чистый фотонный спектр
    return svg_header("Белый") + '''
  <defs>
    <radialGradient id="whiteGlow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.65" />
      <stop offset="35%" stop-color="#E0E7FF" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#121820" stop-opacity="0" />
    </radialGradient>
  </defs>
  <circle cx="400" cy="225" r="210" fill="url(#whiteGlow)" />

  <!-- Платиновая звездная оптика и призматические кольца -->
  <g transform="translate(400, 225)">
    <circle cx="0" cy="0" r="150" fill="none" stroke="#FFFFFF" stroke-width="1" stroke-opacity="0.4" stroke-dasharray="6 6" />
    <circle cx="0" cy="0" r="120" fill="none" stroke="#E8CA7B" stroke-width="1.5" stroke-opacity="0.6" stroke-dasharray="24 6" />
    <circle cx="0" cy="0" r="85" fill="none" stroke="#00A3FF" stroke-width="1" stroke-opacity="0.4" />

    <!-- Восьмиконечная полярная звезда ЧПУ -->
    <polygon points="0,-85 18,-25 80,-15 32,22 45,82 0,45 -45,82 -32,22 -80,-15 -18,-25" 
             fill="#182230" stroke="#FFFFFF" stroke-width="2.5" filter="url(#glow)" />
    <polygon points="0,-60 12,-18 55,-10 22,15 30,58 0,32 -30,58 -22,15 -55,-10 -12,-18" 
             fill="#FFFFFF" fill-opacity="0.85" />
    <circle cx="0" cy="0" r="12" fill="#FFFFFF" filter="url(#glow)" />
  </g>
''' + svg_footer("ГЕРБОВАЯ ЭМАЛЬ // ПЛАТИНА", "ЧИСТЫЙ ТИТАНОВЫЙ СПЛАВ // #FFFFFF", "#FFFFFF")


def main():
    files = {
        "care.svg": create_care_svg(),
        "medicine.svg": create_medicine_svg(),
        "metal.svg": create_metal_svg(),
        "precision.svg": create_precision_svg(),
        "speed.svg": create_speed_svg(),
        "power.svg": create_power_svg(),
        "mind.svg": create_mind_svg(),
        "color_azure.svg": create_color_azure_svg(),
        "color_gold.svg": create_color_gold_svg(),
        "color_emerald.svg": create_color_emerald_svg(),
        "color_white.svg": create_color_white_svg(),
    }

    for name, content in files.items():
        p = OUT_DIR / name
        p.write_text(content, encoding="utf-8")
        print(f"Generated: {p.name}")


if __name__ == "__main__":
    main()
