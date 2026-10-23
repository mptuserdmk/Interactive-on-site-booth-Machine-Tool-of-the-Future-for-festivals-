/**
 * @file kiosk_app.jsx
 * @description Интерактивный выставочный комплекс «Осенний Промышленный Фестиваль Колледжей Москвы»
 * Визуальный стандарт: Неорусский стимпанк и хай-тек (Folk-Tech)
 * Разработано строго по спецификации react-presentation-design:
 * - Гармоничный синтез былинных мотивов, латуни, филиграни и передовых технологий
 * - Палитра: пергамент (#FBF8F1, #F4EEDA), латунь (#C59A45, #E8CA7B), багрянец (#BA1B1D), графит (#121820)
 * - Декоративные латунные уголки BrassCorners и анимированные шестерни
 * - Телеметрия лаборатории, калибровка 0.02 мм по ГОСТ 2.0
 * - Тактильные кнопки с поддержкой 8 состояний и таргет > 64px
 * - Полная совместимость с E2E тестами и офлайн-режимом
 */

const { useState, useEffect, useRef, useCallback } = React;

// --- API Helper с обработкой ошибок и таймаутами ---
async function api(url, options = {}) {
  const timeoutMs = options.timeoutMs || (url.includes('/api/camera') ? 8000 : 75000);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const fetchOptions = {
    ...options,
    signal: options.signal || controller.signal
  };
  delete fetchOptions.timeoutMs;

  try {
    const res = await fetch(url, fetchOptions);
    clearTimeout(timer);
    let body = null;
    try { body = await res.json(); } catch (e) { /* пустой ответ */ }
    if (!res.ok) {
      const err = new Error((body && body.detail) || `Ошибка ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return body;
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') {
      const timeoutErr = new Error("Время ожидания ответа истекло. Попробуйте еще раз.");
      timeoutErr.status = 504;
      throw timeoutErr;
    }
    throw err;
  }
}

function friendlyError(e) {
  if (e && e.status === 409) return "Секунду… калибровка оптического модуля";
  if (e && e.status === 503) return "Оптический датчик не отвечает — позови мастера 📷";
  if (e && e.status === 504) return "Оптический датчик не успел ответить — нажми ещё раз 📷";
  if (e instanceof TypeError) return "Нет связи со стендом — позовите координатора";
  return (e && e.message) || "Сбой привода — попробуй ещё раз";
}

// --- ДЕКОРАТИВНЫЕ ЛАТУННЫЕ УГОЛКИ (Folk-Tech Brass Corners) ---
function BrassCorners({ className = "" }) {
  return (
    <div className={`absolute inset-0 pointer-events-none ${className}`}>
      {/* Верхний левый */}
      <div className="absolute top-2.5 left-2.5 w-6 h-6 sm:w-8 sm:h-8 border-t-2 border-l-2 border-brass pointer-events-none" />
      <div className="absolute top-3.5 left-3.5 w-1.5 h-1.5 bg-brass rounded-full opacity-70 pointer-events-none" />

      {/* Верхний правый */}
      <div className="absolute top-2.5 right-2.5 w-6 h-6 sm:w-8 sm:h-8 border-t-2 border-r-2 border-brass pointer-events-none" />
      <div className="absolute top-3.5 right-3.5 w-1.5 h-1.5 bg-brass rounded-full opacity-70 pointer-events-none" />

      {/* Нижний левый */}
      <div className="absolute bottom-2.5 left-2.5 w-6 h-6 sm:w-8 sm:h-8 border-b-2 border-l-2 border-brass pointer-events-none" />
      <div className="absolute bottom-3.5 left-3.5 w-1.5 h-1.5 bg-brass rounded-full opacity-70 pointer-events-none" />

      {/* Нижний правый */}
      <div className="absolute bottom-2.5 right-2.5 w-6 h-6 sm:w-8 sm:h-8 border-b-2 border-r-2 border-brass pointer-events-none" />
      <div className="absolute bottom-3.5 right-3.5 w-1.5 h-1.5 bg-brass rounded-full opacity-70 pointer-events-none" />
    </div>
  );
}

// --- ФОНОВЫЕ ИНЖЕНЕРНЫЕ ЧЕРТЕЖИ И ОБВЯЗКА (Drafting Blueprint Watermarks & Machine Perimeter) ---
function BlueprintWatermarks() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden select-none" aria-hidden="true">
      {/* Декоративная контурная рамка комплекса по периметру экрана */}
      <div className="absolute inset-2 sm:inset-3 border border-brass/25 rounded-2xl sm:rounded-3xl pointer-events-none z-0" />
      <div className="absolute inset-3.5 sm:inset-5 border border-brass/15 rounded-xl sm:rounded-2xl pointer-events-none z-0" />

      {/* Угловые узлы комплекса с заклепками */}
      <div className="absolute top-3 left-3 w-3 h-3 rounded-full border border-brass/50 bg-brass/20 pointer-events-none z-0" />
      <div className="absolute top-3 right-3 w-3 h-3 rounded-full border border-brass/50 bg-brass/20 pointer-events-none z-0" />
      <div className="absolute bottom-3 left-3 w-3 h-3 rounded-full border border-brass/50 bg-brass/20 pointer-events-none z-0" />
      <div className="absolute bottom-3 right-3 w-3 h-3 rounded-full border border-brass/50 bg-brass/20 pointer-events-none z-0" />

      {/* Верхний центрированный калибровочный маркер */}
      <div className="absolute top-2.5 left-1/2 -translate-x-1/2 px-4 py-0.5 border-b border-brass/25 font-mono text-[9px] text-brass/45 tracking-[0.25em] uppercase pointer-events-none z-0 hidden md:block">
        ИНЖЕНЕРНАЯ ФОТОЛАБОРАТОРИЯ // КАЛИБРОВКА 0.02 ММ
      </div>

      {/* Левые чертежные лимбы и шкалы градусов */}
      <svg className="absolute -left-16 top-1/2 -translate-y-1/2 w-[380px] 2xl:w-[440px] h-[380px] 2xl:h-[440px] opacity-15 text-brass pointer-events-none z-0 hidden xl:block" viewBox="0 0 400 400" fill="none" stroke="currentColor">
        <circle cx="200" cy="200" r="190" strokeWidth="1" strokeDasharray="4 4" />
        <circle cx="200" cy="200" r="170" strokeWidth="1.5" />
        <circle cx="200" cy="200" r="130" strokeWidth="0.8" strokeDasharray="2 3" />
        <circle cx="200" cy="200" r="80" strokeWidth="1" />
        <line x1="200" y1="5" x2="200" y2="395" strokeWidth="0.8" strokeDasharray="5 5" />
        <line x1="5" y1="200" x2="395" y2="200" strokeWidth="0.8" strokeDasharray="5 5" />
        {[0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330].map(deg => (
          <line
            key={deg}
            x1="200"
            y1="10"
            x2="200"
            y2="25"
            strokeWidth="1.2"
            transform={`rotate(${deg} 200 200)`}
          />
        ))}
      </svg>

      {/* Правые чертежные лимбы и калибровка */}
      <svg className="absolute -right-16 top-1/2 -translate-y-1/2 w-[380px] 2xl:w-[440px] h-[380px] 2xl:h-[440px] opacity-15 text-brass pointer-events-none z-0 hidden xl:block" viewBox="0 0 400 400" fill="none" stroke="currentColor">
        <circle cx="200" cy="200" r="185" strokeWidth="1.2" />
        <circle cx="200" cy="200" r="160" strokeWidth="0.8" strokeDasharray="6 3" />
        <circle cx="200" cy="200" r="110" strokeWidth="1.5" />
        <circle cx="200" cy="200" r="60" strokeWidth="1" strokeDasharray="2 2" />
        <line x1="200" y1="10" x2="200" y2="390" strokeWidth="0.8" strokeDasharray="4 4" />
        <line x1="10" y1="200" x2="390" y2="200" strokeWidth="0.8" strokeDasharray="4 4" />
        {[0, 45, 90, 135, 180, 225, 270, 315].map(deg => (
          <line
            key={deg}
            x1="200"
            y1="15"
            x2="200"
            y2="35"
            strokeWidth="1.5"
            transform={`rotate(${deg} 200 200)`}
          />
        ))}
      </svg>
    </div>
  );
}

// --- ЛЕВЫЙ КИБЕР-ХОХЛОМСКОЙ ФЛАНГ (Folk-Tech Mechanical Flank) ---
function CyberKhokhlomaFlankLeft() {
  return (
    <aside
      aria-hidden="true"
      className="shrink-0 w-44 2xl:w-56 h-full flex flex-col justify-between select-none pointer-events-none hidden xl:flex relative z-10 transition-all py-1"
    >
      {/* Вертикальная направляющая ось комплекса с заклепками */}
      <div className="absolute left-8 top-12 bottom-12 w-[1px] bg-gradient-to-b from-brass/0 via-brass/40 to-brass/0 pointer-events-none -z-10" />
      <div className="absolute left-[30.5px] top-1/4 w-1.5 h-1.5 rounded-full bg-brass/70 pointer-events-none" />
      <div className="absolute left-[30.5px] top-3/4 w-1.5 h-1.5 rounded-full bg-brass/70 pointer-events-none" />

      {/* 1. Верхний узел: Сдвоенный кинематический шестеренчатый редуктор + Золотая кудрина-микросхема */}
      <div className="relative w-full flex flex-col items-start pt-1">
        <div className="mb-1 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-panel-graphite text-brass-bright border border-brass/50 shadow-brass-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-ruby animate-pulse"></span>
          <span className="font-mono text-[9px] 2xl:text-[10px] font-bold tracking-widest text-brass-bright uppercase">
            ИНЖЕНЕРНЫЙ МОДУЛЬ
          </span>
        </div>

        {/* Завитки золотой хохломы с ягодами и дорожками плат */}
        <div className="w-full relative">
          <svg viewBox="0 0 240 160" className="w-full h-auto overflow-visible drop-shadow-sm">
            <defs>
              <linearGradient id="goldKhokhGradLeft" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#F7DF94" />
                <stop offset="50%" stopColor="#C59A45" />
                <stop offset="100%" stopColor="#8B651B" />
              </linearGradient>
              <radialGradient id="rubyBerryGradLeft" cx="35%" cy="35%" r="65%">
                <stop offset="0%" stopColor="#FF5C5C" />
                <stop offset="45%" stopColor="#BA1B1D" />
                <stop offset="100%" stopColor="#5E080A" />
              </radialGradient>
            </defs>

            {/* Главные стебли кудрины */}
            <path
              d="M10,25 C60,20 95,55 80,105 C70,135 110,145 145,130 C175,115 165,75 130,70 C100,65 95,95 115,105 C130,110 140,100 135,90"
              fill="none"
              stroke="url(#goldKhokhGradLeft)"
              strokeWidth="2.8"
              strokeLinecap="round"
            />
            {/* Травные побеги (кудринка) */}
            <path d="M48,38 C68,32 92,38 102,52" fill="none" stroke="url(#goldKhokhGradLeft)" strokeWidth="1.6" strokeLinecap="round" />
            <path d="M78,105 C95,102 112,114 120,130" fill="none" stroke="url(#goldKhokhGradLeft)" strokeWidth="1.6" strokeLinecap="round" />

            {/* Кибернетические дорожки (PCB traces) */}
            <path d="M145,130 L175,130 L195,150 L220,150" fill="none" stroke="#C59A45" strokeWidth="1.4" opacity="0.85" />
            <circle cx="220" cy="150" r="3" fill="#F7DF94" stroke="#8B651B" strokeWidth="1" />
            <circle cx="220" cy="150" r="1" fill="#BA1B1D" />

            <path d="M102,52 L124,30 L158,30" fill="none" stroke="#C59A45" strokeWidth="1.4" opacity="0.85" />
            <circle cx="158" cy="30" r="2.8" fill="#BA1B1D" stroke="#F7DF94" strokeWidth="0.8" />

            {/* Резные листья хохломы */}
            <path d="M42,34 C56,20 70,28 64,46 C56,40 48,37 42,34 Z" fill="url(#goldKhokhGradLeft)" opacity="0.9" />
            <path d="M88,78 C106,70 114,84 102,99 C97,90 92,84 88,78 Z" fill="url(#goldKhokhGradLeft)" opacity="0.9" />
            <path d="M128,122 C146,114 156,126 146,139 C140,132 134,127 128,122 Z" fill="url(#goldKhokhGradLeft)" opacity="0.9" />

            {/* Рубиновые ягоды хохломы с золотым ободком */}
            <circle cx="155" cy="80" r="6.5" fill="url(#rubyBerryGradLeft)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="153" cy="78" r="1.5" fill="#FFF" opacity="0.75" />
            <circle cx="170" cy="90" r="5.5" fill="url(#rubyBerryGradLeft)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="168" cy="88" r="1.3" fill="#FFF" opacity="0.75" />
            <circle cx="158" cy="98" r="5" fill="url(#rubyBerryGradLeft)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="156" cy="96" r="1.2" fill="#FFF" opacity="0.75" />
            <circle cx="90" cy="35" r="5.5" fill="url(#rubyBerryGradLeft)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="88" cy="33" r="1.3" fill="#FFF" opacity="0.75" />
          </svg>
        </div>

        {/* Кинематическая пара шестеренок */}
        <div className="relative -mt-10 ml-2">
          {/* Большая латунная шестерня */}
          <div className="text-brass animate-spin-slow drop-shadow-md">
            <svg className="w-20 h-20 2xl:w-24 2xl:h-24" viewBox="0 0 100 100" fill="none">
              <circle cx="50" cy="50" r="42" stroke="currentColor" strokeWidth="3" />
              <circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 3" />
              <circle cx="50" cy="50" r="12" fill="#1C232D" stroke="currentColor" strokeWidth="2" />
              <circle cx="50" cy="50" r="4" fill="#BA1B1D" />
              {[...Array(12)].map((_, i) => (
                <rect
                  key={i}
                  x="46"
                  y="2"
                  width="8"
                  height="10"
                  rx="1.5"
                  fill="currentColor"
                  transform={`rotate(${i * 30} 50 50)`}
                />
              ))}
              {[...Array(6)].map((_, i) => (
                <line
                  key={i}
                  x1="50"
                  y1="20"
                  x2="50"
                  y2="38"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  transform={`rotate(${i * 60} 50 50)`}
                />
              ))}
            </svg>
          </div>

          {/* Малая сопряженная шестерня */}
          <div className="absolute -top-3 left-14 text-brass-bright animate-spin-reverse drop-shadow-sm">
            <svg className="w-12 h-12 2xl:w-14 2xl:h-14" viewBox="0 0 60 60" fill="none">
              <circle cx="30" cy="30" r="23" stroke="currentColor" strokeWidth="2.5" />
              <circle cx="30" cy="30" r="8" fill="#1C232D" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="30" cy="30" r="3" fill="#00A3FF" />
              {[...Array(8)].map((_, i) => (
                <rect
                  key={i}
                  x="27"
                  y="2"
                  width="6"
                  height="7"
                  rx="1"
                  fill="currentColor"
                  transform={`rotate(${i * 45} 30 30)`}
                />
              ))}
            </svg>
          </div>
        </div>
      </div>

      {/* 2. Центральный узел: Инженерный приборный щиток «Калибровка Лаборатории 2.0» */}
      <div className="relative w-full max-w-[240px] 2xl:max-w-[260px] bg-panel-graphite/95 rounded-xl border-2 border-brass/70 shadow-industrial p-3.5 backdrop-blur-sm">
        <BrassCorners />
        <div className="flex items-center justify-between border-b border-brass/40 pb-1.5 mb-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-ruby animate-pulse"></span>
            <span className="font-mono text-[9px] 2xl:text-[10px] font-extrabold text-brass-bright tracking-widest uppercase">
              ИНДУСТРИЯ ЧУДЕС // 2.0
            </span>
          </div>
          <span className="font-mono text-[8px] text-ink-faint">ГОСТ 2.0</span>
        </div>

        {/* Шкала микрометра */}
        <div className="flex flex-col items-center py-1">
          <svg viewBox="0 0 100 45" className="w-28 h-auto overflow-visible">
            <path d="M15,40 A35,35 0 0,1 85,40" fill="none" stroke="rgba(197, 154, 69, 0.3)" strokeWidth="4" />
            <path d="M42,40 A35,35 0 0,1 58,40" fill="none" stroke="#00A3FF" strokeWidth="4.5" />
            <line x1="20" y1="40" x2="25" y2="38" stroke="#C59A45" strokeWidth="1.5" />
            <line x1="50" y1="5" x2="50" y2="12" stroke="#BA1B1D" strokeWidth="2" />
            <line x1="80" y1="40" x2="75" y2="38" stroke="#C59A45" strokeWidth="1.5" />
            <line x1="50" y1="40" x2="48" y2="8" stroke="#F7DF94" strokeWidth="1.8" strokeLinecap="round" />
            <circle cx="50" cy="40" r="3.5" fill="#BA1B1D" stroke="#C59A45" strokeWidth="1" />
          </svg>
          <div className="mt-1 font-mono text-[10px] 2xl:text-xs font-black text-cyber-cyan tracking-wider">
            КАЛИБРОВКА: ±0.02 ММ
          </div>
          <div className="font-serif italic text-[10px] text-parchment/80 mt-0.5 text-center leading-tight">
            Оптическая юстировка фокуса
          </div>
        </div>

        <div className="mt-1.5 pt-1.5 border-t border-brass/30 flex items-center justify-between text-[8px] 2xl:text-[9px] font-mono text-brass-dim font-bold">
          <span>ЦППМ МГОК</span>
          <span className="text-ruby">● ОНЛАЙН</span>
        </div>
      </div>

      {/* 3. Нижний узел: Угловой редуктор и роспись */}
      <div className="relative w-full flex flex-col items-start pb-2">
        <div className="flex items-center gap-2">
          <div className="text-brass animate-spin-slow opacity-80">
            <svg className="w-14 h-14 2xl:w-16 2xl:h-16" viewBox="0 0 60 60" fill="none">
              <circle cx="30" cy="30" r="24" stroke="currentColor" strokeWidth="2" />
              <circle cx="30" cy="30" r="7" fill="#1C232D" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="30" cy="30" r="2.5" fill="#BA1B1D" />
              {[...Array(10)].map((_, i) => (
                <rect key={i} x="28" y="2" width="4" height="6" rx="1" fill="currentColor" transform={`rotate(${i * 36} 30 30)`} />
              ))}
            </svg>
          </div>
          <div className="text-brass-bright animate-spin-reverse opacity-70 -ml-3">
            <svg className="w-9 h-9 2xl:w-10 2xl:h-10" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="15" stroke="currentColor" strokeWidth="1.8" />
              <circle cx="20" cy="20" r="4" fill="#1C232D" stroke="currentColor" strokeWidth="1" />
              {[...Array(8)].map((_, i) => (
                <rect key={i} x="18.5" y="1" width="3" height="4" rx="0.5" fill="currentColor" transform={`rotate(${i * 45} 20 20)`} />
              ))}
            </svg>
          </div>
        </div>
        <div className="font-mono text-[9px] font-bold tracking-widest text-brass-dim uppercase mt-1 pl-1">
          МГОК • ТЕХНОЛОГИИ
        </div>
      </div>
    </aside>
  );
}

// --- ПРАВЫЙ КИБЕР-ХОХЛОМСКОЙ ФЛАНГ (Жар-Птица 2.0 & Индустрия Чудес) ---
function CyberKhokhlomaFlankRight() {
  return (
    <aside
      aria-hidden="true"
      className="shrink-0 w-44 2xl:w-56 h-full flex flex-col justify-between items-end select-none pointer-events-none hidden xl:flex relative z-10 transition-all py-1"
    >
      {/* Вертикальная направляющая ось комплекса с заклепками */}
      <div className="absolute right-8 top-12 bottom-12 w-[1px] bg-gradient-to-b from-brass/0 via-brass/40 to-brass/0 pointer-events-none -z-10" />
      <div className="absolute right-[30.5px] top-1/4 w-1.5 h-1.5 rounded-full bg-brass/70 pointer-events-none" />
      <div className="absolute right-[30.5px] top-3/4 w-1.5 h-1.5 rounded-full bg-brass/70 pointer-events-none" />

      {/* 1. Верхний узел: Перо Жар-Птицы + Девиз Фестиваля */}
      <div className="relative w-full flex flex-col items-end pt-1">
        <div className="mb-1 inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-ruby text-parchment border border-brass-bright/60 shadow-brass-sm">
          <span className="text-brass-bright font-serif text-xs">✦</span>
          <span className="font-serif italic font-bold text-xs sm:text-sm text-parchment tracking-wide">
            Технологии вдохновляют!
          </span>
        </div>

        <div className="w-full relative">
          <svg viewBox="0 0 240 160" className="w-full h-auto overflow-visible drop-shadow-sm">
            <defs>
              <linearGradient id="goldKhokhGradRight" x1="100%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#F7DF94" />
                <stop offset="50%" stopColor="#C59A45" />
                <stop offset="100%" stopColor="#8B651B" />
              </linearGradient>
              <linearGradient id="rubyFeatherGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FF4D4D" />
                <stop offset="60%" stopColor="#BA1B1D" />
                <stop offset="100%" stopColor="#8C1012" />
              </linearGradient>
              <radialGradient id="rubyBerryGradRight" cx="35%" cy="35%" r="65%">
                <stop offset="0%" stopColor="#FF5C5C" />
                <stop offset="45%" stopColor="#BA1B1D" />
                <stop offset="100%" stopColor="#5E080A" />
              </radialGradient>
            </defs>

            {/* Оперение Жар-Птицы (веерные золотые и багряные перья-лезвия) */}
            <path d="M225,20 C180,25 150,55 160,95 C168,125 130,135 95,120 C70,110 75,70 110,65 C135,60 145,85 125,98" fill="none" stroke="url(#goldKhokhGradRight)" strokeWidth="2.8" strokeLinecap="round" />

            {/* Перья с гравировкой и микросхемами */}
            <path d="M220,25 C190,30 170,50 165,70 C185,55 205,42 220,25 Z" fill="url(#rubyFeatherGrad)" stroke="#F7DF94" strokeWidth="1" opacity="0.95" />
            <path d="M205,45 C175,55 155,75 150,95 C170,80 190,65 205,45 Z" fill="url(#goldKhokhGradRight)" stroke="#BA1B1D" strokeWidth="1" opacity="0.9" />
            <path d="M185,70 C160,82 142,105 138,125 C156,108 174,92 185,70 Z" fill="url(#rubyFeatherGrad)" stroke="#F7DF94" strokeWidth="1" opacity="0.95" />

            {/* Кибернетические дорожки Жар-Птицы */}
            <path d="M95,120 L65,120 L45,140 L20,140" fill="none" stroke="#C59A45" strokeWidth="1.4" opacity="0.85" />
            <circle cx="20" cy="140" r="3" fill="#F7DF94" stroke="#8B651B" strokeWidth="1" />
            <circle cx="20" cy="140" r="1" fill="#00A3FF" />

            <path d="M140,55 L115,35 L80,35" fill="none" stroke="#C59A45" strokeWidth="1.4" opacity="0.85" />
            <circle cx="80" cy="35" r="2.8" fill="#BA1B1D" stroke="#F7DF94" strokeWidth="0.8" />

            {/* Рубиновые плоды и искры пера */}
            <circle cx="85" cy="80" r="6.5" fill="url(#rubyBerryGradRight)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="83" cy="78" r="1.5" fill="#FFF" opacity="0.75" />
            <circle cx="70" cy="92" r="5.5" fill="url(#rubyBerryGradRight)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="68" cy="90" r="1.3" fill="#FFF" opacity="0.75" />
            <circle cx="80" cy="100" r="5" fill="url(#rubyBerryGradRight)" stroke="#F7DF94" strokeWidth="1" />
            <circle cx="78" cy="98" r="1.2" fill="#FFF" opacity="0.75" />
          </svg>
        </div>

        {/* Кинематический хроно-узел Жар-Птицы */}
        <div className="relative -mt-10 mr-2">
          <div className="text-brass animate-spin-reverse drop-shadow-md">
            <svg className="w-20 h-20 2xl:w-24 2xl:h-24" viewBox="0 0 100 100" fill="none">
              <circle cx="50" cy="50" r="42" stroke="currentColor" strokeWidth="3" />
              <circle cx="50" cy="50" r="28" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 2" />
              <circle cx="50" cy="50" r="12" fill="#1C232D" stroke="currentColor" strokeWidth="2" />
              <circle cx="50" cy="50" r="4" fill="#00A3FF" />
              {[...Array(12)].map((_, i) => (
                <rect
                  key={i}
                  x="46"
                  y="2"
                  width="8"
                  height="10"
                  rx="1.5"
                  fill="currentColor"
                  transform={`rotate(${i * 30} 50 50)`}
                />
              ))}
              {[...Array(6)].map((_, i) => (
                <line
                  key={i}
                  x1="50"
                  y1="22"
                  x2="50"
                  y2="38"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  transform={`rotate(${i * 60} 50 50)`}
                />
              ))}
            </svg>
          </div>
          {/* Малая сопряженная золотая шестеренка */}
          <div className="absolute -top-3 right-14 text-brass-bright animate-spin-slow drop-shadow-sm">
            <svg className="w-12 h-12 2xl:w-14 2xl:h-14" viewBox="0 0 60 60" fill="none">
              <circle cx="30" cy="30" r="23" stroke="currentColor" strokeWidth="2.5" />
              <circle cx="30" cy="30" r="8" fill="#1C232D" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="30" cy="30" r="3" fill="#BA1B1D" />
              {[...Array(8)].map((_, i) => (
                <rect
                  key={i}
                  x="27"
                  y="2"
                  width="6"
                  height="7"
                  rx="1"
                  fill="currentColor"
                  transform={`rotate(${i * 45} 30 30)`}
                />
              ))}
            </svg>
          </div>
        </div>
      </div>

      {/* 2. Центральный узел: Манифест Фестиваля «Русская Сказка 2.0» */}
      <div className="relative w-full max-w-[240px] 2xl:max-w-[260px] bg-panel-graphite/95 rounded-xl border-2 border-brass/70 shadow-industrial p-3.5 backdrop-blur-sm text-right">
        <BrassCorners />
        <div className="flex items-center justify-between border-b border-brass/40 pb-1.5 mb-2">
          <span className="font-mono text-[8px] text-ink-faint">МОСКВА • 2026</span>
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-[9px] 2xl:text-[10px] font-extrabold text-brass-bright tracking-widest uppercase">
              ИНДУСТРИЯ ЧУДЕС
            </span>
            <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-pulse"></span>
          </div>
        </div>

        <div className="flex flex-col items-center py-0.5 text-center">
          <div className="font-serif font-black text-sm 2xl:text-base text-parchment tracking-wide">
            «РУССКАЯ СКАЗКА 2.0»
          </div>
          <div className="h-0.5 w-16 bg-gradient-to-r from-transparent via-brass to-transparent my-1"></div>
          <p className="font-serif italic text-[10px] 2xl:text-[11px] text-brass-bright/90 leading-snug">
            «Чудеса не по щучьему велению, а по инженерному расчету»
          </p>
          <div className="mt-2 inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-parchment/10 border border-brass/40 text-[8px] 2xl:text-[9px] font-mono font-bold text-parchment">
            <span>⚙️</span>
            <span>100+ ПРОФЕССИЙ</span>
          </div>
        </div>

        <div className="mt-1.5 pt-1.5 border-t border-brass/30 flex items-center justify-between text-[8px] 2xl:text-[9px] font-mono text-brass-dim font-bold">
          <span className="text-cyber-cyan">● НЕЙРОСИНТЕЗ ОБРАЗА</span>
          <span>ГИЛЬДИЯ МАСТЕРОВ</span>
        </div>
      </div>

      {/* 3. Нижний узел: Хохломская угловая виньетка и знак фестиваля */}
      <div className="relative w-full flex flex-col items-end pb-2">
        <div className="flex items-center gap-2">
          <div className="text-brass-bright animate-spin-slow opacity-70 -mr-3">
            <svg className="w-9 h-9 2xl:w-10 2xl:h-10" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="15" stroke="currentColor" strokeWidth="1.8" />
              <circle cx="20" cy="20" r="4" fill="#1C232D" stroke="currentColor" strokeWidth="1" />
              {[...Array(8)].map((_, i) => (
                <rect key={i} x="18.5" y="1" width="3" height="4" rx="0.5" fill="currentColor" transform={`rotate(${i * 45} 20 20)`} />
              ))}
            </svg>
          </div>
          <div className="text-brass animate-spin-reverse opacity-80">
            <svg className="w-14 h-14 2xl:w-16 2xl:h-16" viewBox="0 0 60 60" fill="none">
              <circle cx="30" cy="30" r="24" stroke="currentColor" strokeWidth="2" />
              <circle cx="30" cy="30" r="7" fill="#1C232D" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="30" cy="30" r="2.5" fill="#00A3FF" />
              {[...Array(10)].map((_, i) => (
                <rect key={i} x="28" y="2" width="4" height="6" rx="1" fill="currentColor" transform={`rotate(${i * 36} 30 30)`} />
              ))}
            </svg>
          </div>
        </div>
        <div className="font-mono text-[9px] font-bold tracking-widest text-brass-dim uppercase mt-1 pr-1">
          ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ
        </div>
      </div>
    </aside>
  );
}

// --- ВЕКТОРНЫЕ ИНДУСТРИАЛЬНЫЕ И СКАЗОЧНЫЕ ИКОНКИ (Folk-Tech SVGs) ---
const ICONS = {
  // Шестерня латунная (Inline SVG)
  gear: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <circle cx="12" cy="12" r="3" strokeWidth="1.5" />
    </svg>
  ),
  // Космос / Летучий корабль
  space: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
      <circle cx="15" cy="9" r="2" fill="currentColor" fillOpacity="0.3" />
    </svg>
  ),
  // Атом / Ядерный микромир
  atom: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="3" fill="currentColor" fillOpacity="0.25" />
      <ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(30 12 12)" />
      <ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(90 12 12)" />
      <ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(150 12 12)" />
    </svg>
  ),
  // Роботы / Автономные системы
  robots: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect width="16" height="14" x="4" y="6" rx="3" />
      <circle cx="9" cy="12" r="1.5" fill="currentColor" />
      <circle cx="15" cy="12" r="1.5" fill="currentColor" />
      <path strokeLinecap="round" d="M10 16h4M12 6V3" />
      <circle cx="12" cy="2" r="1.2" fill="currentColor" />
      <path strokeLinecap="round" d="M2 12h2M20 12h2" />
    </svg>
  ),
  // Медицина / Живая вода
  medicine: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="m2 15 5 5 13-13-5-5-13 13Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="m9 8 7 7M14.5 3.5 17.5 6.5M3.5 14.5 6.5 17.5" />
      <circle cx="8" cy="16" r="1" fill="currentColor" />
    </svg>
  ),
  // Металл / Кузница Данилы-Мастера
  metal: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="2.5" fill="currentColor" fillOpacity="0.25" />
    </svg>
  ),
  // Точность / Оптический микрометр
  precision: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" strokeDasharray="3 3" />
      <circle cx="12" cy="12" r="2" fill="currentColor" />
      <path strokeLinecap="round" d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  ),
  // Скорость / Сверхзвуковой ротор
  speed: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" fillOpacity="0.2" />
    </svg>
  ),
  // Сила / Гидропресс
  power: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v10" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.4 6.6a9 9 0 1 1-12.77.01" />
    </svg>
  ),
  // Ум / Кристаллический чип
  mind: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="4" y="4" width="16" height="16" rx="3" />
      <path strokeLinecap="round" d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" />
    </svg>
  ),
  // Забота / Оберег
  care: (
    <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" fill="currentColor" fillOpacity="0.25" />
    </svg>
  ),
  // Камера / Оптический визир
  camera: (
    <svg className="w-9 h-9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  ),
  // Искры / Волшебство
  sparkles: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path strokeLinecap="round" strokeLinejoin="round" d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z" />
    </svg>
  ),
  // Стрелка вправо
  arrowRight: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  ),
  // Галочка
  check: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  ),
  // Обновление / Переснять
  refresh: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
      <path d="M8 16H3v5" />
    </svg>
  )
};

// --- ЗАЩИТНЫЙ ЭКРАННЫЙ БУФЕР (Folk-Tech Error Boundary) ---
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Kiosk ErrorBoundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 w-full max-w-xl mx-auto flex flex-col items-center justify-center p-6 text-center animate-fade-in bg-parchment-card rounded-2xl border-2 border-ruby shadow-tactile-ruby relative my-auto">
          <BrassCorners />
          <div className="w-14 h-14 rounded-full bg-ruby/15 text-ruby border border-ruby/40 flex items-center justify-center mb-4">
            <span className="text-2xl font-bold">⚠️</span>
          </div>
          <h2 className="font-serif font-black text-2xl text-ink-main mb-2">
            СБОЙ ОТОБРАЖЕНИЯ ЭКРАНА
          </h2>
          <p className="font-serif italic text-sm text-ink-muted mb-6">
            Произошла ошибка при прорисовке экрана. Нажми кнопку ниже, чтобы перезапустить киоск.
          </p>
          <FolkButton
            variant="primary"
            size="lg"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              if (this.props.onReset) this.props.onReset();
              else window.location.reload();
            }}
          >
            <span>ВЕРНУТЬСЯ В НАЧАЛО</span>
          </FolkButton>
        </div>
      );
    }
    return this.props.children;
  }
}

// --- ТАКТИЛЬНАЯ ЛАТУННАЯ КНОПКА (Folk-Tech Tactile Button) ---
function FolkButton({
  variant = "primary", // primary (ruby-brass), secondary (parchment-brass), dark (graphite-brass)
  size = "lg",
  children,
  onClick,
  disabled = false,
  loading = false,
  ariaLabel,
  className = "",
  type = "button"
}) {
  const baseStyles = "relative font-mono font-bold select-none inline-flex items-center justify-center gap-3 transition-all duration-150 rounded-xl cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-brass/50";

  const sizeStyles = {
    md: "min-h-[64px] min-w-[64px] px-6 text-base tracking-wider uppercase",
    lg: "min-h-[72px] min-w-[72px] px-8 text-xl tracking-wider uppercase",
    xl: "min-h-[84px] min-w-[84px] px-10 text-2xl tracking-widest uppercase font-serif"
  };

  const variantStyles = {
    // Багряный гербовый с золотым тиснением
    primary: "bg-ruby text-white border-2 border-brass-bright border-b-6 border-ruby-dark active:border-b-2 active:translate-y-1 shadow-tactile-ruby hover:bg-[#A31618]",
    // Благородный пергамент с латунной окантовкой
    secondary: "bg-parchment-card text-ink-main border-2 border-brass border-b-6 border-brass-dim active:border-b-2 active:translate-y-1 shadow-tactile hover:bg-[#EDE5CE]",
    // Графитовая панель модуля
    dark: "bg-panel-graphite text-brass-bright border-2 border-brass/60 border-b-6 border-black active:border-b-2 active:translate-y-1 shadow-industrial hover:bg-panel-surface"
  };

  const disabledStyles = "opacity-50 cursor-not-allowed pointer-events-none border-b-2 shadow-none translate-y-0";

  return (
    <button
      type={type}
      aria-label={ariaLabel}
      disabled={disabled || loading}
      onClick={onClick}
      className={`
        ${baseStyles}
        ${sizeStyles[size] || sizeStyles.lg}
        ${variantStyles[variant] || variantStyles.primary}
        ${(disabled || loading) ? disabledStyles : ""}
        ${className}
      `}
    >
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <svg className="animate-spin -ml-1 mr-2 h-6 w-6 text-current" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>КАЛИБРОВКА...</span>
        </span>
      ) : children}
    </button>
  );
}

// --- ИНДИКАТОР ШАГОВ (Folk-Tech Step Tracker) ---
function FolkStepTracker({ currentStep }) {
  const steps = [
    { num: "01", label: "Оптика", icon: "📷" },
    { num: "02", label: "Стихия", icon: "⚙️" },
    { num: "03", label: "Сила", icon: "⚡" },
    { num: "04", label: "Палитра", icon: "🎨" },
    { num: "05", label: "Грамота", icon: "📜" }
  ];

  return (
    <nav aria-label="Прогресс создания образа" className="w-full max-w-3xl mx-auto px-2 pt-0.5 pb-1">
      <div className="flex items-center justify-between relative">
        {/* Филигранная латунная соединительная линия строго по центру кнопок */}
        <div className="absolute left-4 right-4 top-[40px] sm:top-[22px] -translate-y-1/2 h-0.5 sm:h-1 bg-brass/30 -z-0">
          <div
            className="h-full bg-brass transition-all duration-500 ease-out shadow-brass-glow"
            style={{ width: `${Math.min(100, (currentStep / (steps.length - 1)) * 100)}%` }}
          />
        </div>

        {steps.map((step, idx) => {
          const isCompleted = idx < currentStep;
          const isActive = idx === currentStep;

          return (
            <div key={idx} className="relative z-10 flex flex-col items-center">
              <div
                className={`
                  w-9 h-9 sm:w-11 sm:h-11 rounded-lg sm:rounded-xl flex items-center justify-center font-mono font-bold text-xs sm:text-sm transition-all duration-300 select-none
                  ${isActive
                    ? "bg-ruby text-brass-bright border-2 border-brass scale-105 shadow-tactile-ruby ring-2 sm:ring-4 ring-brass/25"
                    : isCompleted
                      ? "bg-panel-graphite text-brass-bright border border-brass sm:border-2 shadow-brass-sm"
                      : "bg-parchment-card text-ink-muted border border-brass/40 sm:border-2"}
                `}
              >
                {isCompleted ? <span className="scale-75 sm:scale-90">{ICONS.check}</span> : <span className="font-serif text-xs sm:text-sm">{step.num}</span>}
              </div>
              <span className={`mt-2.5 sm:mt-3 font-serif text-[11px] sm:text-[13px] md:text-sm tracking-wider select-none uppercase transition-colors ${isActive
                ? "text-ruby font-black drop-shadow-sm"
                : isCompleted
                  ? "text-brass-dim font-extrabold"
                  : "text-ink-main/80 font-bold"
                }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </nav>
  );
}

// --- ЭКРАН 1: ТИТУЛЬНЫЙ ЭКРАН (Welcome Cover Slide) ---
function WelcomeScreen({ onStart }) {
  const [lastCardSession, setLastCardSession] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loadingLast, setLoadingLast] = useState(false);
  const [errorNotice, setErrorNotice] = useState("");

  const isMaxPlatform = (window.KIOSK_CONFIG?.botPlatform || 'max').toLowerCase() !== 'telegram';
  const botUsername = (isMaxPlatform
    ? (window.KIOSK_CONFIG?.maxBotUsername || window.KIOSK_CONFIG?.telegramBotUsername || '')
    : (window.KIOSK_CONFIG?.telegramBotUsername || window.KIOSK_CONFIG?.maxBotUsername || '')).replace(/^@/, '').trim();

  const handleOpenLastCard = async () => {
    setLoadingLast(true);
    setErrorNotice("");
    try {
      const data = await api('/api/session/last-card');
      if (data && data.found && data.session) {
        setLastCardSession(data.session);
        setShowModal(true);
      } else {
        setErrorNotice("Недавних готовых паспортов не найдено");
        setTimeout(() => setErrorNotice(""), 3500);
      }
    } catch (e) {
      setErrorNotice("Не удалось запросить последний паспорт");
      setTimeout(() => setErrorNotice(""), 3500);
    } finally {
      setLoadingLast(false);
    }
  };

  const baseUrl = (window.KIOSK_CONFIG?.baseUrl || window.location.origin).replace(/\/+$/, '');
  const qrUrl = lastCardSession
    ? (botUsername
      ? (isMaxPlatform
        ? `https://max.ru/${botUsername}?start=${lastCardSession.id}`
        : `https://t.me/${botUsername}?start=${lastCardSession.id}`)
      : `${baseUrl}/card/${lastCardSession.id}`)
    : '';

  return (
    <main className="flex-1 h-full max-h-full flex flex-col items-center justify-center text-center px-4 max-w-4xl mx-auto animate-fade-in relative">
      {/* Декоративная фоновая латунная шестерня */}
      <div className="absolute -top-12 opacity-5 pointer-events-none animate-spin-slow">
        <svg className="w-80 h-80 text-brass" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
          <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z" />
        </svg>
      </div>

      {/* Партнерский штамп / Экосистема */}
      <div className="inline-flex items-center gap-2 px-3.5 py-1 sm:py-1.5 rounded-lg bg-parchment-card border border-brass/50 text-brass-dim font-mono text-[10px] sm:text-xs font-bold tracking-widest uppercase mb-2 sm:mb-3 shadow-brass-sm">
        <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-ruby"></span>
        <span>ДЕПАРТАМЕНТ ОБРАЗОВАНИЯ И НАУКИ МОСКВЫ • ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ</span>
      </div>

      {/* Монументальный былинный заголовок */}
      <h1 className="font-serif font-black text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-ink-main tracking-tight leading-tight mb-2 sm:mb-3">
        КЕМ ТЫ СТАНЕШЬ В{" "}
        <span className="relative inline-block text-ruby font-serif">
          БУДУЩЕМ?
          <span className="absolute left-0 right-0 -bottom-1 h-1 bg-brass rounded-full opacity-80"></span>
        </span>
      </h1>

      <p className="font-serif italic text-sm sm:text-base md:text-lg text-ink-muted max-w-2xl leading-relaxed mb-3 sm:mb-4">
        «Органический синтез традиционных сказок и передовой инженерии: посмотри в оптический визор, выбери былинную стихию и получи персональный цифровой паспорт инженера будущего!»
      </p>

      {/* Механический триптих шестеренок */}
      <div className="flex items-center justify-center gap-3 mb-3 sm:mb-5 pointer-events-none">
        <div className="text-brass animate-spin-slow opacity-80">
          <svg className="w-8 h-8 sm:w-10 sm:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </div>
        <div className="w-2.5 h-2.5 bg-ruby rounded-full animate-pulse shadow-brass-glow"></div>
        <div className="text-brass-dim animate-spin-reverse opacity-80">
          <svg className="w-6 h-6 sm:w-8 sm:h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </div>
      </div>

      {/* Главная кнопка старта (сохраняем aria-label для E2E тестов) */}
      <FolkButton
        variant="primary"
        size="lg"
        onClick={onStart}
        ariaLabel="Начать создание своего образа"
        className="w-full sm:w-auto min-w-[280px] sm:min-w-[340px] text-base sm:text-lg py-3 sm:py-3.5"
      >
        <span>СОЗДАТЬ ОБРАЗ МАСТЕРА</span>
        {ICONS.arrowRight}
      </FolkButton>

      {/* Кнопка вызова последнего QR-кода, если экран закрылся */}
      <div className="mt-2.5 sm:mt-3 flex flex-col items-center gap-1 z-10">
        <button
          type="button"
          onClick={handleOpenLastCard}
          disabled={loadingLast}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-parchment-card/90 hover:bg-parchment-card border border-brass/60 text-brass-dim font-mono text-[11px] sm:text-xs font-bold tracking-wide transition-all shadow-sm active:translate-y-0.5 cursor-pointer"
        >
          <span>📷</span>
          <span>{loadingLast ? "ПОИСК ПАСПОРТА..." : "ПРЕДЫДУЩИЙ QR-КОД / СКАЧАТЬ ПАСПОРТ"}</span>
        </button>
        {errorNotice && (
          <span className="font-mono text-[10px] text-ruby font-bold animate-fade-in">
            {errorNotice}
          </span>
        )}
      </div>

      {/* 3 Архетипичные плашки особенностей */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 sm:gap-4 mt-3 sm:mt-4 w-full max-w-3xl">
        <div className="p-2 sm:p-2.5 rounded-xl bg-parchment-card border border-brass/40 shadow-brass-sm flex items-center gap-3 text-left relative overflow-hidden">
          <BrassCorners />
          <div className="w-9 h-9 rounded-lg bg-panel-graphite text-brass flex items-center justify-center shrink-0">
            {ICONS.camera}
          </div>
          <div>
            <span className="font-mono text-[9px] sm:text-[10px] font-bold text-ruby uppercase tracking-wider block">Видоискатель</span>
            <span className="font-serif font-bold text-ink-main text-xs sm:text-sm">Оптический визор</span>
          </div>
        </div>

        <div className="p-2 sm:p-2.5 rounded-xl bg-parchment-card border border-brass/40 shadow-brass-sm flex items-center gap-3 text-left relative overflow-hidden">
          <BrassCorners />
          <div className="w-9 h-9 rounded-lg bg-panel-graphite text-brass-bright flex items-center justify-center shrink-0">
            {ICONS.gear}
          </div>
          <div>
            <span className="font-mono text-[9px] sm:text-[10px] font-bold text-ruby uppercase tracking-wider block">Былины & Наука</span>
            <span className="font-serif font-bold text-ink-main text-xs sm:text-sm">100 Профессий</span>
          </div>
        </div>

        <div className="p-2 sm:p-2.5 rounded-xl bg-parchment-card border border-brass/40 shadow-brass-sm flex items-center gap-3 text-left relative overflow-hidden">
          <BrassCorners />
          <div className="w-9 h-9 rounded-lg bg-panel-graphite text-brass flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 sm:w-6 sm:h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <span className="font-mono text-[9px] sm:text-[10px] font-bold text-ruby uppercase tracking-wider block">Артефакт 300 DPI</span>
            <span className="font-serif font-bold text-ink-main text-xs sm:text-sm">Цифровой паспорт</span>
          </div>
        </div>
      </div>

      {/* Модальное окно восстановления QR-кода */}
      {showModal && lastCardSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="relative w-full max-w-md bg-parchment-card border-2 border-brass rounded-2xl p-5 shadow-2xl flex flex-col items-center text-center">
            <BrassCorners />
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-ruby text-white font-mono text-[10px] font-bold uppercase tracking-wider mb-2">
              <span>ПАСПОРТ СОХРАНЁН</span>
            </div>
            <h3 className="font-serif font-black text-xl sm:text-2xl text-ink-main mb-1">
              {lastCardSession.machine_name || "ИНЖЕНЕР БУДУЩЕГО"}
            </h3>
            <p className="font-serif italic text-xs text-ink-muted mb-3 max-w-xs">
              Если экран закрылся до того, как ты отсканировал QR-код — наведи камеру смартфона сейчас!
            </p>

            <div className="bg-white p-2.5 rounded-xl border-2 border-brass shadow-md mb-3">
              <img
                src={`/api/qr.png?data=${encodeURIComponent(qrUrl)}`}
                alt="QR-код паспорта"
                className="w-48 h-48 sm:w-56 sm:h-56 object-contain"
              />
            </div>

            <div className="font-mono text-[11px] text-ink-muted mb-4 space-y-0.5">
              <div>⚡ Суперсила: <b className="text-ink-main">{lastCardSession.power_name || "Точность"}</b></div>
              <div>📍 Кластер: <b className="text-ink-main">{lastCardSession.location || "Центральный"}</b></div>
            </div>

            <FolkButton
              variant="dark"
              size="md"
              onClick={() => setShowModal(false)}
              className="w-full text-sm py-2"
            >
              <span>ПОНЯТНО, ЗАКРЫТЬ</span>
            </FolkButton>
          </div>
        </div>
      )}
    </main>
  );
}

// --- ЭКРАН 2: КАМЕРА И ОПТИЧЕСКИЙ ВИЗИР (Camera Slide) ---
function CameraScreen({ isReview, sessionId, session, onCapture, onConfirm, onRetake, busy }) {
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isCapturing, setIsCapturing] = useState(false);
  const [flash, setFlash] = useState(false);
  const [shutterRing, setShutterRing] = useState(false);

  const validation = session?.meta?.photo_validation;
  const isBlink = Boolean(validation?.blink_detected);
  const noFace = Boolean(validation && !validation.face_detected);

  const handleShutter = async () => {
    if (isCapturing || busy) return;
    setIsCapturing(true);
    setShutterRing(true);
    setFlash(true);
    setTimeout(() => setFlash(false), 200);
    setTimeout(() => setShutterRing(false), 700);

    const safetyTimer = setTimeout(() => {
      setIsCapturing(false);
    }, 6000);

    try {
      await onCapture();
    } finally {
      clearTimeout(safetyTimer);
      setIsCapturing(false);
    }
  };

  return (
    <section className="flex-1 w-full max-w-6xl mx-auto flex flex-col gap-2 sm:gap-3 animate-fade-in h-full max-h-full overflow-hidden" aria-label="Зона фотографирования">
      {/* Шапка зоны съемки */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-1.5 border-b border-brass/40 pb-1.5 sm:pb-2 shrink-0">
        <div>
          <span className="text-[10px] sm:text-xs font-mono font-bold tracking-widest text-ruby uppercase">
            ОПТИЧЕСКИЙ ВИЗОР // КАЛИБРОВКА ОБРАЗА
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-black tracking-tight text-ink-main mt-0.5">
            {!isReview
              ? "УЛЫБНИСЬ В КАМЕРУ! 📸"
              : isBlink
                ? "ОЙ, КАЖЕТСЯ, ТЫ МОРГНУЛ! 👁️"
                : noFace
                  ? "ЛИЦО НЕ В ПРИЦЕЛЕ! ⚠️"
                  : "ТВОЙ КАДР ОТЛИЧНЫЙ! 🌟"}
          </h2>
          <p className="font-serif italic text-xs sm:text-sm text-ink-muted">
            {!isReview
              ? "Взгляни в латунный визор и зафиксируй свой портрет инженера."
              : isBlink
                ? "Оптический датчик зафиксировал закрытые глаза. Рекомендуем переснять кадр, чтобы паспорт инженера получился безупречным!"
                : noFace
                  ? "Оптический сенсор не зафиксировал лицо. Встаньте прямо напротив объектива."
                  : "Оптический слепок зафиксирован. Утверди его или перезапусти визор."}
          </p>
        </div>

        {isReview && isBlink ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-ruby/20 border-2 border-ruby text-ruby font-mono text-[10px] sm:text-xs font-bold self-start sm:self-auto animate-pulse shadow-sm">
            <span className="w-2 h-2 rounded-full bg-ruby"></span>
            <span>ДАТЧИК: ОБНАРУЖЕНО МОРГАНИЕ</span>
          </div>
        ) : isReview && noFace ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-ruby/20 border-2 border-ruby text-ruby font-mono text-[10px] sm:text-xs font-bold self-start sm:self-auto animate-pulse shadow-sm">
            <span className="w-2 h-2 rounded-full bg-ruby"></span>
            <span>ДАТЧИК: ЛИЦО НЕ НАЙДЕНО</span>
          </div>
        ) : (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-panel-graphite border border-brass/50 text-brass-bright font-mono text-[10px] sm:text-xs font-bold self-start sm:self-auto">
            <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-pulse"></span>
            <span>ОПТИКА: {isReview ? "ГЛАЗА ОТКРЫТЫ (ГОСТ 2.0)" : "ОНЛАЙН (ГОСТ 2.0)"}</span>
          </div>
        )}
      </div>

      {/* 7/5 Асимметричная раскладка комплекса */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-5 items-stretch flex-1 min-h-0 max-h-full">
        {/* Левая 7-колоночная область видоискателя */}
        <div className="lg:col-span-7 relative bg-panel-graphite rounded-2xl overflow-hidden shadow-industrial border-4 border-brass/40 flex items-center justify-center h-full max-h-[55vh] min-h-0">
          <BrassCorners />

          {/* Вспышка затвора */}
          {flash && <div className="absolute inset-0 bg-white z-50 animate-fade-out pointer-events-none"></div>}

          {isReview ? (
            <img
              src={`/media/photos/${sessionId}.jpg?t=${Date.now()}`}
              alt="Сделанный снимок"
              className="w-full h-full object-cover"
            />
          ) : (
            <img
              src={`/api/camera/stream?t=${streamKey}`}
              alt="Видеопоток камеры"
              className="w-full h-full object-cover"
            />
          )}

          {/* Оптический прицел HUD с латунной шкалой */}
          {!isReview && (
            <div className="absolute inset-4 pointer-events-none border border-brass/30 rounded-xl flex flex-col items-center justify-center">
              {/* Угловые визиры — овал удлинен по высоте для анатомической формы лица и аккуратно вписан в прямоугольник */}
              <div className="w-44 h-52 sm:w-48 sm:h-56 border-2 border-dashed border-brass/60 rounded-full flex flex-col items-center justify-center relative translate-y-1 sm:translate-y-1.5">
                <span className="font-mono text-[10px] sm:text-xs font-bold text-brass-bright bg-panel-graphite/80 px-2.5 py-0.5 rounded border border-brass/40 tracking-wider">
                  ЛИЦО ЗДЕСЬ
                </span>
                <div className="absolute top-0 bottom-0 w-px bg-brass/30 pointer-events-none"></div>
                <div className="absolute left-0 right-0 h-px bg-brass/30 pointer-events-none"></div>
              </div>

              {/* Указание действия в видоискателе — расположено чуть выше над строкой телеметрии */}
              <div className="absolute bottom-[34px] sm:bottom-[36px] left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-panel-graphite/95 border border-brass/70 text-brass-bright font-mono text-xs sm:text-sm font-bold shadow-industrial animate-pulse whitespace-nowrap">
                <span>📸 Нажми кнопку для снимка</span>
              </div>

              {/* Маркер телеметрии внизу кадра */}
              <div className="absolute bottom-2.5 left-4 right-4 flex justify-between items-center font-mono text-[9px] sm:text-[10px] text-brass-bright bg-panel-graphite/85 px-2.5 py-1 rounded border border-brass/30">
                <span>ОПТИЧЕСКИЙ ДАТЧИК: АКТИВЕН</span>
                <span className="text-cyber-cyan">ТОЧНОСТЬ: 0.02 мм</span>
              </div>
            </div>
          )}
        </div>

        {/* Правая 5-колоночная консоль управления мастера */}
        <div className="lg:col-span-5 bg-parchment-card rounded-2xl p-3 sm:p-5 border-2 border-brass/50 shadow-brass flex flex-col justify-between relative h-full max-h-[55vh] min-h-0">
          <BrassCorners />

          <div className="space-y-2.5 sm:space-y-3">
            {isReview && isBlink ? (
              <div className="p-2.5 sm:p-3 rounded-xl bg-ruby/15 border-2 border-ruby text-ink-main shadow-tactile-ruby animate-pulse">
                <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block mb-0.5">
                  👁️ Оптический видоискатель
                </span>
                <p className="mt-0.5 text-xs sm:text-sm font-serif italic text-ink-main leading-relaxed">
                  "Похоже, в момент вспышки глаза закрылись! Нажми «ПЕРЕСНЯТЬ ЗАНОВО», чтобы портрет мастера получился живым и выразительным."
                </p>
              </div>
            ) : isReview && noFace ? (
              <div className="p-2.5 sm:p-3 rounded-xl bg-ruby/15 border-2 border-ruby text-ink-main shadow-tactile-ruby">
                <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block mb-0.5">
                  ⚠️ Предупреждение оптики
                </span>
                <p className="mt-0.5 text-xs sm:text-sm font-serif italic text-ink-main leading-relaxed">
                  "Оптический датчик не зафиксировал лицо в центре. Встань ровно напротив камеры и повтори снимок."
                </p>
              </div>
            ) : (
              <div className="p-2.5 sm:p-3 rounded-xl bg-parchment border border-brass/30">
                <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block">
                  Сказочный наказ мастера
                </span>
                <p className="mt-0.5 text-xs sm:text-sm font-serif italic text-ink-main leading-relaxed">
                  {isReview
                    ? "Взгляд ясный и открытый — как и подобает инженеру будущего! Утверждай снимок."
                    : "Держи взгляд прямой и смелый, как подобает инженеру Руси великой. Нажми рубиновый затвор, когда будешь готов!"}
                </p>
              </div>
            )}

            {/* Индустриальная плашка телеметрии */}
            <div className="p-2.5 sm:p-3 rounded-xl bg-panel-graphite text-brass-bright border border-brass/40 flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-2.5">
                <div className="text-brass animate-spin-slow">
                  {ICONS.gear}
                </div>
                <div>
                  <div className="font-bold text-white uppercase text-[11px] sm:text-xs">Привод оптической ячейки</div>
                  <div className="text-ink-faint text-[9px] sm:text-[10px]">
                    {isReview && isBlink ? "Обнаружено закрытие век" : "Готовность 100% • Стенд № 1"}
                  </div>
                </div>
              </div>
              <span className={`font-bold text-xs ${isReview && isBlink ? "text-ruby" : "text-cyber-cyan"}`}>
                {isReview && isBlink ? "МОРГАНИЕ" : "ОК"}
              </span>
            </div>
          </div>

          {/* Панель действий затвора */}
          <div className="pt-2 sm:pt-4">
            {!isReview ? (
              <div className="flex flex-col items-center justify-center">
                <div className="relative flex items-center justify-center">
                  {/* Мягкая внешняя пульсация готовности к нажатию */}
                  <div className="absolute inset-[-4px] rounded-full bg-ruby/25 animate-ping pointer-events-none" />

                  {/* Взрывная волна затвора при клике */}
                  {shutterRing && (
                    <div className="absolute inset-[-14px] rounded-full border-4 border-brass-bright animate-ping pointer-events-none z-20" />
                  )}

                  <button
                    type="button"
                    aria-label="Сделать фотографию"
                    disabled={isCapturing || busy}
                    onClick={handleShutter}
                    className={`
                      relative z-10 w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-ruby hover:bg-[#A31618] active:scale-90 active:border-b-2
                      border-3 sm:border-4 border-brass-bright border-b-6 sm:border-b-8 border-ruby-dark text-white flex items-center justify-center
                      shadow-tactile-ruby transition-all duration-150 cursor-pointer focus-visible:ring-4 focus-visible:ring-brass
                      ${isCapturing ? 'scale-90 brightness-125 ring-4 ring-brass' : 'hover:scale-105'}
                    `}
                  >
                    <div className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 border-brass/70 flex items-center justify-center text-brass-bright transition-transform duration-300 ${isCapturing ? 'scale-90 animate-pulse' : ''}`}>
                      {ICONS.camera}
                    </div>
                  </button>
                </div>
              </div>
            ) : isBlink ? (
              <div className="flex flex-col gap-2.5 sm:gap-3">
                <FolkButton
                  variant="primary"
                  size="md"
                  onClick={onRetake}
                  disabled={busy}
                  ariaLabel="Переснять фотографию с открытыми глазами"
                  className="w-full animate-pulse shadow-tactile-ruby"
                >
                  {ICONS.refresh}
                  <span>ПЕРЕСНЯТЬ ЗАНОВО</span>
                </FolkButton>

                <FolkButton
                  variant="secondary"
                  size="sm"
                  onClick={onConfirm}
                  loading={busy}
                  ariaLabel="Всё равно подтвердить фотографию"
                  className="w-full opacity-80 hover:opacity-100"
                >
                  <span>ОСТАВИТЬ КАК ЕСТЬ</span>
                  {ICONS.arrowRight}
                </FolkButton>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5 sm:gap-3">
                <FolkButton
                  variant="primary"
                  size="md"
                  onClick={onConfirm}
                  loading={busy}
                  ariaLabel="Подтвердить фотографию и перейти к выбору"
                  className="w-full"
                >
                  <span>ПОДТВЕРДИТЬ КАДР</span>
                  {ICONS.arrowRight}
                </FolkButton>

                <FolkButton
                  variant="secondary"
                  size="sm"
                  onClick={onRetake}
                  disabled={busy}
                  ariaLabel="Переснять фотографию"
                  className="w-full"
                >
                  {ICONS.refresh}
                  <span>ПЕРЕСНЯТЬ ЗАНОВО</span>
                </FolkButton>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

// --- ТЕМАТИЧЕСКИЕ ФОНЫ КНОПОК ВЫБОРА (Folk-Tech Button Background Art) ---
const BUTTON_BACKGROUNDS = {
  // Былинные Стихии
  space: "/static/images/buttons/space.jpg",
  atom: "/static/images/buttons/atom.jpg",
  robots: "/static/images/buttons/robots.jpg",
  medicine: "/static/images/buttons/medicine.svg",
  metal: "/static/images/buttons/metal.svg",
  // Суперсилы Мастера
  precision: "/static/images/buttons/precision.svg",
  speed: "/static/images/buttons/speed.svg",
  power: "/static/images/buttons/power.svg",
  mind: "/static/images/buttons/mind.svg",
  care: "/static/images/buttons/care.svg",
  // Гербовые Цвета
  azure: "/static/images/buttons/color_azure.svg",
  gold: "/static/images/buttons/color_gold.svg",
  emerald: "/static/images/buttons/color_emerald.svg",
  white: "/static/images/buttons/color_white.svg"
};

// Вертикальные технические надписи по ГОСТ 2.0, расположенные сбоку карточки
const CARD_SIDE_LABELS = {
  // Стихии
  space: "ОРБИТА // КОСМОС // ТЕХНОЛОГИИ",
  atom: "КВАНТ // ЯДРО // 12 ГэВ",
  robots: "КИБЕРНЕТИКА // АВТОМАТ",
  medicine: "БИОНИКА // ЖИВАЯ ВОДА",
  metal: "СПЛАВ // ЛАЗЕР // 3000°C",
  // Суперсилы
  precision: "КАЛИБР // ±0.001 ММ",
  speed: "ПРИВОД // 12 МАХ // ТУРБО",
  power: "ПРЕСС // 10 000 ТОНН",
  mind: "НЕЙРОСЕТЬ // 1.2 PF",
  care: "ОБЕРЕГ // БЕЗОПАСНОСТЬ",
  // Цвета
  azure: "ЭМАЛЬ // ЛАЗУРЬ // #00D2FF",
  gold: "ЭМАЛЬ // ЗОЛОТО // #FFD700",
  emerald: "ЭМАЛЬ // ИЗУМРУД // #00FF88",
  white: "ЭМАЛЬ // ПЛАТИНА // #FFFFFF"
};

const COLOR_HINTS = {
  azure: "Квантовое сияние фотонов и чистая энергия",
  gold: "Благородная латунь и созидательный огонь",
  emerald: "Биосферный импульс и лазерный кристалл",
  white: "Плазменная чистота и титановый сплав"
};

// --- ЭКРАНЫ 3, 4, 5: ВЫБОР СТИХИИ, СУПЕРСИЛЫ, ЦВЕТА (Selection Slide) ---
function SelectionScreen({ title, subtitle, options, selectedId, onSelect, type, busy }) {
  return (
    <section className="flex-1 w-full max-w-5xl mx-auto flex flex-col justify-between overflow-hidden gap-1.5 sm:gap-2.5 h-full max-h-full animate-fade-in" aria-label={title}>
      {/* Шапка шага выбора */}
      <div className="border-b border-brass/40 pb-1.5 sm:pb-2 flex flex-col sm:flex-row sm:items-end justify-between gap-1 shrink-0">
        <div>
          <span className="text-[10px] sm:text-xs font-mono font-bold tracking-widest text-ruby uppercase">
            {type === 'element' ? 'ШАГ 02 // БЫЛИННАЯ ОТРАСЛЬ' : type === 'power' ? 'ШАГ 03 // СУПЕРСИЛА МАСТЕРА' : 'ШАГ 04 // ГЕРБОВЫЙ ЦВЕТ'}
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-black text-ink-main mt-0.5">
            {title}
          </h2>
          <p className="font-serif italic text-xs sm:text-sm text-ink-muted">
            {subtitle}
          </p>
        </div>

        <div className="text-[10px] sm:text-xs font-mono text-brass-dim font-bold self-start sm:self-auto">
          ВЫБЕРИ 1 ВАРИАНТ
        </div>
      </div>

      {/* Сетка вариантов карточек */}
      <div className={`grid gap-2.5 sm:gap-3.5 ${type === 'color' ? 'grid-cols-2 lg:grid-cols-4' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'} flex-1 min-h-0 items-stretch`}>
        {options.map((opt) => {
          const isSelected = selectedId === opt.id;
          const bgImage = BUTTON_BACKGROUNDS[opt.id];
          const sideLabel = CARD_SIDE_LABELS[opt.id] || `ГОСТ // ${opt.id.toUpperCase()}`;
          const isColor = type === 'color';

          return (
            <button
              key={opt.id}
              type="button"
              disabled={busy}
              aria-pressed={isSelected}
              onClick={() => onSelect(opt.id)}
              aria-label={isColor ? `Выбрать цвет ${opt.name}` : `Выбрать вариант ${opt.name}`}
              className={`
                group p-3 sm:p-4 rounded-2xl bg-parchment-card border-2 transition-all duration-200 ease-out flex flex-col items-start justify-between text-left cursor-pointer outline-none h-full min-h-0 relative select-none overflow-hidden
                ${isSelected
                  ? "border-ruby border-b-6 border-ruby-dark shadow-tactile-ruby scale-[1.02] ring-3 ring-brass/30"
                  : "border-brass/40 border-b-4 sm:border-b-6 border-brass-dim hover:border-brass hover:shadow-brass active:scale-[0.98] active:border-b-2 active:translate-y-1 shadow-brass-sm"}
              `}
            >
              {/* Тематическая иллюстрация на фоне кнопки — сочная, хорошо различимая, с плавным приближением */}
              {bgImage && (
                <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl z-0">
                  <img
                    src={bgImage}
                    alt=""
                    className={`w-full h-full object-cover object-center opacity-60 transition-transform duration-500 ease-out transform ${isSelected ? 'scale-105' : 'group-hover:scale-110'
                      }`}
                  />
                  {/* Пергаментный мягкий градиент для сохранения идеального контраста текста */}
                  <div className="absolute inset-0 bg-gradient-to-t from-parchment-card/85 via-parchment-card/55 to-parchment-card/20" />
                </div>
              )}

              {/* Вертикальная техническая надпись сбоку карточки — лежит строго вдоль правого края и не мешает другим текстам */}
              <div className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 pointer-events-none select-none z-10 flex items-center justify-center">
                <span className="font-mono text-[8px] sm:text-[9.5px] tracking-[0.24em] text-brass-dim/75 font-black uppercase [writing-mode:vertical-lr] rotate-180 drop-shadow-sm border-l border-brass/25 pl-1 py-1">
                  {sideLabel}
                </span>
              </div>

              <BrassCorners className="z-10" />

              {/* Верхняя строка: Иконка / Медальон цвета и статус выбора */}
              <div className="w-full flex items-center justify-between mb-2 relative z-10 pr-6">
                {isColor ? (
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-panel-graphite border border-brass/50 flex items-center justify-center scale-90 sm:scale-100 shadow-brass-sm">
                    {/* Латунный медальон с гербовой эмалью цвета */}
                    <div
                      className="w-6 h-6 sm:w-7 sm:h-7 rounded-full border-2 border-brass shadow-sm transition-transform relative flex items-center justify-center"
                      style={{
                        backgroundColor: opt.hex,
                        boxShadow: `0 0 12px ${opt.glow || opt.hex}`
                      }}
                    >
                      <div className="w-2 h-2 rounded-full border border-white/60 opacity-80" />
                    </div>
                  </div>
                ) : (
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-panel-graphite text-brass-bright border border-brass/50 flex items-center justify-center scale-90 sm:scale-100 shadow-brass-sm">
                    {ICONS[opt.id] || ICONS.gear}
                  </div>
                )}

                {isSelected && (
                  <span className="px-2 py-0.5 rounded bg-ruby text-white font-mono text-[9px] sm:text-[10px] font-bold tracking-wider uppercase border border-brass shadow-sm">
                    ВЫБРАНО
                  </span>
                )}
              </div>

              {/* Нижняя строка: Заголовок и пояснение (отступ справа pr-7 sm:pr-8 гарантирует что они никогда не заденут вертикальную надпись) */}
              <div className="relative z-10 pr-7 sm:pr-8">
                <h3 className="font-serif font-bold text-lg sm:text-xl text-ink-main mb-1 drop-shadow-sm leading-tight">{opt.name}</h3>
                <p className="font-sans text-xs sm:text-sm text-ink-muted leading-tight line-clamp-2">{opt.hint || COLOR_HINTS[opt.id]}</p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

// --- ЭКРАН 6: ГЕНЕРАЦИЯ И СБОРКА («Индустрия Чудес») ---
function GeneratingScreen({ session }) {
  const isComposing = session?.status === 'COMPOSING';
  const progressPercent = isComposing ? 92 : 65;

  return (
    <main className="flex-1 h-full max-h-full flex flex-col items-center justify-center text-center px-4 max-w-2xl mx-auto animate-fade-in relative">
      {/* Механизм Индустрии Чудес: 3 вращающиеся латунные шестерни */}
      <div className="relative mb-3 sm:mb-4 w-28 h-28 sm:w-32 sm:h-32 flex items-center justify-center">
        {/* Большая центральная шестерня */}
        <div className="absolute inset-0 text-brass animate-spin-slow">
          <svg className="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <circle cx="12" cy="12" r="5" strokeWidth="1" />
          </svg>
        </div>

        {/* Малая противовращающаяся шестерня */}
        <div className="absolute w-16 h-16 sm:w-20 sm:h-20 text-brass-dim animate-spin-reverse">
          <svg className="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v4m0 12v4M2 12h4m12 0h4m-3.17-6.83-2.83 2.83m-8 8-2.83 2.83m0-13.66 2.83 2.83m8 8 2.83 2.83" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>

        {/* Пульсирующий рубиновый кристалл в сердце комплекса */}
        <div className="w-8 h-8 rounded-full bg-ruby border-2 border-brass-bright flex items-center justify-center text-white shadow-brass-glow animate-pulse z-10 scale-90">
          {ICONS.sparkles}
        </div>
      </div>

      <span className="font-mono text-[10px] sm:text-xs font-bold tracking-widest text-ruby uppercase mb-1">
        ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ
      </span>

      <h2 className="font-serif font-black text-2xl sm:text-3xl md:text-4xl text-ink-main mb-1.5">
        {isComposing ? "КОМПОНУЕМ ПАСПОРТ МАСТЕРА... 📜" : "НЕЙРОСЕТЬ ГЕНЕРИРУЕТ ОБРАЗ... ✨"}
      </h2>

      <p className="font-serif italic text-xs sm:text-sm text-ink-muted mb-3 sm:mb-4 max-w-lg">
        {isComposing
          ? "Формируем полиграфический паспорт в качестве 300 DPI и наносим персональный QR-код..."
          : `Синтез былинного архетипа: ${session?.element_name || 'Стихия'} + ${session?.power_name || 'Суперсила'} + ${session?.color_name || 'Цвет'}...`}
      </p>

      {/* Латунный индикатор прогресса */}
      <div className="w-full h-5 sm:h-6 bg-panel-graphite rounded-full overflow-hidden border-2 border-brass/60 shadow-industrial p-0.5 sm:p-1 max-w-md">
        <div
          className="h-full bg-gradient-to-r from-brass-dim via-brass to-brass-bright rounded-full transition-all duration-700 ease-out shadow-brass-glow"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Индустриальный лог телеметрии */}
      <div className="mt-3 sm:mt-4 px-4 py-2.5 rounded-xl bg-panel-graphite border border-brass/40 font-mono text-[11px] sm:text-xs text-brass-bright text-left w-full max-w-md shadow-industrial">
        <div className="text-cyber-cyan font-bold">✓ Оптический слепок откалиброван (ГОСТ 2.0)</div>
        <div className="text-brass-bright font-bold">✓ Входные параметры: {(session?.element_name || '').toUpperCase()}</div>
        <div className="text-ruby font-bold animate-pulse">● {isComposing ? "Верстка паспорта 300 DPI в золотой филиграни..." : "Синтез персонажа нейросетью..."}</div>
      </div>
    </main>
  );
}

// --- БЛОК РАССЫЛКИ НА EMAIL ---
function EmailDispatchBox({ sessionId }) {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sentSuccess, setSentSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const domains = ["@mail.ru", "@yandex.ru", "@gmail.com", "@bk.ru"];

  const handleDomainClick = (domain) => {
    if (!email) {
      setEmail("master" + domain);
    } else if (email.includes("@")) {
      setEmail(email.split("@")[0] + domain);
    } else {
      setEmail(email + domain);
    }
  };

  const handleSendEmail = async () => {
    if (!email || !email.includes("@")) {
      setErrorMsg("Введи корректный email (например: master@mail.ru)");
      return;
    }
    setErrorMsg("");
    setSending(true);
    try {
      const res = await fetch('/api/email/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), session_id: sessionId })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Не удалось отправить");
      }
      setSentSuccess(true);
    } catch (e) {
      setErrorMsg(e.message || "Ошибка отправки почты");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="p-2.5 sm:p-3 rounded-xl bg-parchment border border-brass/40 text-left">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby flex items-center gap-1.5">
          <span>✉️</span> ПОЛУЧИТЬ ПАСПОРТ НА EMAIL
        </span>
        {sentSuccess && (
          <span className="text-[10px] font-mono font-bold text-[#008770] flex items-center gap-1">
            ✓ ОТПРАВЛЕНО!
          </span>
        )}
      </div>

      {!sentSuccess ? (
        <div className="space-y-1.5">
          <div className="flex gap-1.5">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="имя@mail.ru"
              className="flex-1 min-w-0 px-2.5 py-1.5 rounded-lg bg-white border border-brass/50 font-mono text-xs text-ink-main outline-none focus:ring-1 focus:ring-brass"
            />
            <button
              type="button"
              disabled={sending || !email}
              onClick={handleSendEmail}
              className="shrink-0 px-2.5 py-1.5 rounded-lg bg-ruby text-white font-mono text-[10px] sm:text-[11px] font-bold uppercase tracking-wider border border-brass-bright hover:bg-ruby-dark disabled:opacity-50 cursor-pointer transition-all shadow-brass-sm"
            >
              {sending ? "..." : "ОТПРАВИТЬ"}
            </button>
          </div>

          {/* Быстрые кнопки доменов для сенсорного экрана */}
          <div className="flex gap-1 flex-wrap">
            {domains.map((dom) => (
              <button
                key={dom}
                type="button"
                onClick={() => handleDomainClick(dom)}
                className="px-1.5 py-0.5 rounded bg-parchment-card border border-brass/30 text-[9px] sm:text-[10px] font-mono text-ink-muted hover:text-ruby hover:border-ruby transition-colors"
              >
                {dom}
              </button>
            ))}
          </div>

          {errorMsg && (
            <div className="text-[10px] font-mono text-ruby font-bold mt-0.5">
              {errorMsg}
            </div>
          )}
        </div>
      ) : (
        <div className="p-1.5 rounded-lg bg-[#008770]/10 border border-[#008770]/30 text-[11px] font-mono text-[#008770] font-bold">
          ✓ Паспорт выслан на <strong>{email}</strong>!
        </div>
      )}
    </div>
  );
}

// --- ЭКРАН 7: ФИНАЛЬНЫЙ ПАСПОРТ И ПОРТАЛ ВЫДАЧИ (Result Slide) ---
function ResultScreen({ session, onFinish, onQrRevealed, onCardError }) {
  const [showQr, setShowQr] = useState(false);
  const [showEmailBox, setShowEmailBox] = useState(false);
  const isMaxPlatform = (window.KIOSK_CONFIG?.botPlatform || 'max').toLowerCase() !== 'telegram';
  const initialUsername = isMaxPlatform
    ? (window.KIOSK_CONFIG?.maxBotUsername || window.KIOSK_CONFIG?.telegramBotUsername || '')
    : (window.KIOSK_CONFIG?.telegramBotUsername || window.KIOSK_CONFIG?.maxBotUsername || '');
  const [botUsername, setBotUsername] = useState(initialUsername.replace(/^@/, '').trim());
  const qrRevealDelay = Number(window.KIOSK_CONFIG?.qrRevealDelayMs || 1500);

  useEffect(() => {
    if (!session?.final_card_path) {
      if (onCardError) onCardError();
    }
  }, [session?.final_card_path, onCardError]);

  useEffect(() => {
    if (!botUsername) {
      api('/api/health')
        .then(data => {
          const u = isMaxPlatform
            ? (data?.diagnostics?.max_bot?.username || data?.diagnostics?.telegram?.username)
            : (data?.diagnostics?.telegram?.username || data?.diagnostics?.max_bot?.username);
          if (u) setBotUsername(u.replace(/^@/, '').trim());
        })
        .catch(() => { });
    }
  }, [botUsername, isMaxPlatform]);

  const cardUrl = session?.final_card_path
    ? `/media/cards/${session.id}.jpg?t=${Date.now()}`
    : null;

  const hasBot = Boolean(botUsername);
  const baseUrl = (window.KIOSK_CONFIG?.baseUrl || window.location.origin).replace(/\/+$/, '');

  const qrDestination = hasBot
    ? (isMaxPlatform
      ? `https://max.ru/${botUsername}?start=${session?.id || ''}`
      : `https://t.me/${botUsername}?start=${session?.id || ''}`)
    : `${baseUrl}/card/${session?.id || ''}`;

  // Предзагрузка QR-кода в кеш браузера, пока створки еще сомкнуты
  useEffect(() => {
    if (qrDestination) {
      const preloadImg = new Image();
      preloadImg.src = `/api/qr.png?data=${encodeURIComponent(qrDestination)}`;
    }
  }, [qrDestination]);

  useEffect(() => {
    setShowQr(false);
    const timer = setTimeout(() => {
      setShowQr(true);
      if (onQrRevealed) onQrRevealed();
    }, qrRevealDelay);
    return () => clearTimeout(timer);
  }, [session?.id, qrRevealDelay]);

  return (
    <section className="flex-1 w-full max-w-6xl xl:max-w-7xl mx-auto flex flex-col justify-between overflow-hidden gap-1.5 sm:gap-2.5 h-full max-h-full animate-fade-in" aria-label="Результат генерации">
      {/* Шапка результата */}
      <div className="border-b border-brass/40 pb-1.5 sm:pb-2 flex flex-col sm:flex-row sm:items-end justify-between gap-1.5 shrink-0">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-ruby text-white font-mono text-[10px] sm:text-xs font-bold uppercase tracking-widest border border-brass mb-1">
            <span>🎉 ОБРАЗ УСПЕШНО СОЗДАН!</span>
          </div>
          <h2 className="font-serif font-black text-2xl sm:text-3xl text-ink-main">
            {session?.machine_name || "ИНЖЕНЕР БУДУЩЕГО"}
          </h2>
        </div>

        {/* Статусная плашка цифрового паспорта */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-panel-graphite border border-brass/60 shadow-industrial text-brass-bright font-mono text-[11px] sm:text-xs self-start sm:self-auto">
          <span className="w-2.5 h-2.5 rounded-full bg-brass-bright animate-pulse"></span>
          <span className="font-bold tracking-wider">
            ЦИФРОВОЙ ПАСПОРТ ГОТОВ 📜
          </span>
        </div>
      </div>

      {/* 3-створчатый раскладной триптих (без скролла) */}
      <div className="flex flex-row items-center justify-center flex-1 min-h-0 max-h-full w-full overflow-hidden py-1">
        {/* СТВОРКА 1 (СЛЕВА): Паспорт инженера в латунной рамке */}
        <div
          className="flex items-center justify-center shrink-0 max-h-[62vh] min-h-0"
          style={{
            transition: 'all 750ms cubic-bezier(0.16, 1, 0.3, 1)'
          }}
        >
          <div className="relative max-h-full rounded-2xl overflow-hidden shadow-industrial border-3 sm:border-4 border-brass bg-panel-graphite p-1.5 flex items-center justify-center">
            <BrassCorners />
            <div className="rounded-lg overflow-hidden border border-brass/40 max-h-[59vh] flex items-center justify-center bg-black/20">
              {cardUrl ? (
                <img
                  src={cardUrl}
                  alt="Итоговый паспорт инженера"
                  className="max-h-[57vh] w-auto max-w-full object-contain block rounded"
                  onError={() => {
                    if (onCardError) onCardError();
                  }}
                />
              ) : (
                <div className="p-10 text-center font-serif text-brass-bright text-sm">
                  Подготовка паспорта мастера...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* СТВОРКА 2 (ПО ЦЕНТРУ): Механический портал с QR-кодом Telegram (раздвигает створки) */}
        <div
          className="shrink-0 flex flex-col justify-between items-center text-center relative bg-parchment-card rounded-2xl border-2 border-brass/60 shadow-brass select-none max-h-[62vh]"
          style={{
            maxWidth: showQr ? '320px' : '0px',
            width: showQr ? '300px' : '0px',
            opacity: showQr ? 1 : 0,
            transform: showQr ? 'scale(1)' : 'scale(0.85)',
            padding: showQr ? '14px 16px' : '0px',
            marginLeft: showQr ? '10px' : '0px',
            marginRight: showQr ? '10px' : '0px',
            borderWidth: showQr ? '2px' : '0px',
            pointerEvents: showQr ? 'auto' : 'none',
            overflow: 'hidden',
            transition: 'all 750ms cubic-bezier(0.16, 1, 0.3, 1)'
          }}
        >
          <BrassCorners />

          {/* Верхний бейдж портала */}
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-ruby/10 border border-ruby/30 text-ruby font-mono text-[10px] font-bold uppercase tracking-wider mb-1.5 shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-ruby animate-pulse"></span>
            <span>{hasBot ? (isMaxPlatform ? "МЕССЕНДЖЕР МАКС" : "TELEGRAM БОТ") : "ЦИФРОВАЯ КАРТА"}</span>
          </div>

          {/* Белая подложка с QR-кодом */}
          <div className="p-2 bg-white rounded-xl border-2 border-brass shadow-sm inline-block shrink-0 my-auto">
            <img
              src={`/api/qr.png?data=${encodeURIComponent(qrDestination)}`}
              alt="QR-код для получения карточки"
              className="w-[170px] h-[170px] sm:w-[185px] sm:h-[185px] block object-contain"
            />
          </div>

          {/* Текстовые инструкции */}
          <div className="mt-1.5 space-y-0.5 shrink-0">
            <span className="text-[11px] sm:text-xs font-mono uppercase font-bold tracking-wider text-ruby block">
              {hasBot ? (isMaxPlatform ? "📱 НАВЕДИТЕ КАМЕРУ — МАКС" : "📱 НАВЕДИТЕ КАМЕРУ — TELEGRAM") : "📱 НАВЕДИТЕ КАМЕРУ СМАРТФОНА"}
            </span>
            <p className="font-serif italic text-[11px] sm:text-xs text-ink-main leading-tight max-w-[240px] mx-auto">
              {hasBot
                ? (isMaxPlatform
                  ? "Отсканируй QR, чтобы мгновенно получить карточку в мессенджере МАКС!"
                  : "Отсканируй QR, чтобы мгновенно получить карточку в Telegram!")
                : "Отсканируй QR смартфоном, чтобы открыть и скачать карточку в HD!"}
            </p>
          </div>
        </div>

        {/* СТВОРКА 3 (СПРАВА): Грамота мастера, Email и кнопка «Следующий участник» */}
        <div
          className="shrink-0 w-[290px] sm:w-[320px] max-w-[340px] bg-parchment-card rounded-2xl p-3.5 sm:p-4 border-2 border-brass/50 shadow-brass flex flex-col justify-between gap-2.5 relative max-h-[62vh]"
          style={{
            transition: 'all 750ms cubic-bezier(0.16, 1, 0.3, 1)'
          }}
        >
          <BrassCorners />

          {/* Блок характеристик (Суперсила + Гильдия) */}
          <div className="space-y-2">
            <div className="p-2 sm:p-2.5 rounded-xl bg-parchment border border-brass/30">
              <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block">
                СУПЕРСИЛА МАСТЕРА
              </span>
              <div className="font-serif font-black text-base sm:text-xl text-ink-main mt-0.5">
                {(session?.power_name || 'ТОЧНОСТЬ').toUpperCase()}
              </div>
            </div>

            <div className="p-1.5 sm:p-2 rounded-xl bg-panel-graphite text-brass-bright border border-brass/40 font-mono text-[10px] sm:text-xs">
              <span className="text-ruby font-bold">📍 ГИЛЬДИЯ:</span> {session?.location || "Центральный производственный кластер"}
            </div>
          </div>

          {/* Опциональный модуль Email рассылки */}
          <div className="my-auto py-1">
            {!showEmailBox ? (
              <button
                type="button"
                onClick={() => setShowEmailBox(true)}
                className="w-full text-[11px] font-mono text-ink-muted hover:text-ruby underline text-center transition-colors cursor-pointer py-1 block"
              >
                ✉️ Или отправить паспорт на Email
              </button>
            ) : (
              <EmailDispatchBox sessionId={session?.id} />
            )}
          </div>

          {/* Кнопка завершения сессии */}
          <FolkButton
            variant="primary"
            size="md"
            onClick={onFinish}
            ariaLabel="Завершить сессию и перейти к следующему участнику"
            className="w-full py-2.5 sm:py-3 text-sm sm:text-base shrink-0"
          >
            <span>СЛЕДУЮЩИЙ УЧАСТНИК 🚀</span>
          </FolkButton>
        </div>
      </div>
    </section>
  );
}

// --- ЭКРАН 8: ОШИБКА ГЕНЕРАЦИИ / ОБОРУДОВАНИЯ (Error Screen) ---
function ErrorScreen({ session, onFinish, onRetry, busy }) {
  const isAiError = session?.meta?.error_code === 'ai_generation_failed' || Boolean(onRetry);
  return (
    <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-3xl mx-auto animate-fade-in relative z-20" role="alert">
      <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-ruby text-brass-bright border-4 border-brass flex items-center justify-center text-3xl sm:text-4xl mb-5 shadow-tactile-ruby">
        ⚙️
      </div>
      <h2 className="font-serif font-black text-3xl sm:text-4xl md:text-5xl text-ink-main mb-3">
        {isAiError ? "СБОЙ СИНТЕЗА ОБРАЗА" : "УПС! ЧТО-ТО ПОШЛО НЕ ТАК"}
      </h2>
      <p className="font-serif italic text-base sm:text-lg text-ink-muted mb-7 max-w-xl">
        {isAiError
          ? "Не удалось сгенерировать фото. Пожалуйста, попробуйте еще раз."
          : (session?.error_message || "Позовите координатора стенда или попробуйте запустить лабораторию заново.")}
      </p>

      <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md justify-center">
        {onRetry && (
          <FolkButton
            variant="primary"
            size="xl"
            onClick={onRetry}
            disabled={busy}
            ariaLabel="Попробовать снова сгенерировать фото"
            className="flex-1"
          >
            <span>ПОПРОБОВАТЬ СНОВА</span>
          </FolkButton>
        )}
        <FolkButton
          variant={onRetry ? "secondary" : "primary"}
          size="xl"
          onClick={onFinish}
          disabled={busy}
          ariaLabel="Вернуться на главный экран"
          className="flex-1"
        >
          <span>В НАЧАЛО</span>
        </FolkButton>
      </div>
    </main>
  );
}

// --- МОДАЛЬНОЕ ОКНО БЕЗДЕЙСТВИЯ (Folk-Tech Chronometer Modal) ---
function IdleModal({ isOpen, countdown, onStay, onLeave }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6 animate-fade-in">
      <div className="bg-parchment-card border-4 border-brass rounded-3xl p-8 sm:p-10 max-w-lg w-full text-center shadow-2xl animate-scale-up relative">
        <BrassCorners />

        {/* Хронометр отсчета */}
        <div className="w-24 h-24 rounded-full bg-ruby text-white font-mono font-black text-5xl flex items-center justify-center mx-auto mb-6 border-4 border-brass-bright shadow-tactile-ruby">
          {countdown}
        </div>

        <h3 className="font-serif font-black text-3xl sm:text-4xl text-ink-main mb-3">
          ТЫ ЕЩЁ ЗДЕСЬ? 😊
        </h3>

        <p className="font-serif italic text-lg text-ink-muted mb-8">
          Хронометр отсчитывает секунды. Если не продолжить, экран вернется к началу.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <FolkButton
            variant="primary"
            size="lg"
            onClick={onStay}
            ariaLabel="Продолжить работу с киоском"
            className="flex-1"
          >
            <span>ПРОДОЛЖИТЬ</span>
          </FolkButton>

          <FolkButton
            variant="secondary"
            size="lg"
            onClick={onLeave}
            ariaLabel="Вернуться на главный экран"
            className="flex-1"
          >
            <span>В НАЧАЛО</span>
          </FolkButton>
        </div>
      </div>
    </div>
  );
}

// --- ГЛАВНОЕ ПРИЛОЖЕНИЕ КИОСКА (Kiosk Root) ---
function KioskRoot() {
  const [session, setSession] = useState(null);
  const [quizSchema, setQuizSchema] = useState([]);
  const [cardLoadError, setCardLoadError] = useState(false);

  // Управление бездействием (Folk-Tech Chronometer Controller)
  const [isIdleModalOpen, setIsIdleModalOpen] = useState(false);
  const [idleCountdown, setIdleCountdown] = useState(10);
  const isIdleModalOpenRef = useRef(false);
  const idleTimerRef = useRef(null);
  const countdownIntervalRef = useRef(null);

  // Связь и обратная связь
  const [connected, setConnected] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const busyRef = useRef(false);
  const noticeTimerRef = useRef(null);

  const showNotice = useCallback((text) => {
    setNotice(text);
    clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setNotice(null), 4000);
  }, []);

  const syncActiveSession = useCallback(async () => {
    try {
      const data = await api('/api/session/active');
      setSession(data && data.status !== 'IDLE' ? data : null);
    } catch (e) { /* обработка через статус связи */ }
  }, []);

  const runAction = useCallback(async (fn) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      showNotice(friendlyError(e));
      if (e && e.status === 409) syncActiveSession();
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }, [showNotice, syncActiveSession]);

  useEffect(() => {
    let timer;
    const load = () => api('/api/quiz/schema').then(setQuizSchema).catch(() => { timer = setTimeout(load, 3000); });
    load();
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    let ws = null;
    let timer = null;
    let attempt = 0;
    let stopped = false;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        attempt = 0;
        setConnected(true);
        syncActiveSession();
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'SESSION_UPDATE') {
            setSession(msg.data && msg.data.status !== 'IDLE' ? msg.data : null);
          }
        } catch (e) {
          console.error("WS parse error", e);
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) timer = setTimeout(connect, Math.min(10000, 1000 * 2 ** attempt++));
      };
      ws.onerror = () => ws.close();
    };
    connect();

    return () => {
      stopped = true;
      clearTimeout(timer);
      if (ws) ws.close();
    };
  }, [syncActiveSession]);

  const handleReset = useCallback(async () => {
    clearInterval(countdownIntervalRef.current);
    clearTimeout(idleTimerRef.current);
    isIdleModalOpenRef.current = false;
    setIsIdleModalOpen(false);
    setIdleCountdown(10);
    setCardLoadError(false);
    try {
      await api('/api/session/reset', { method: 'POST' });
    } catch (e) {
      showNotice(friendlyError(e));
    }
    setSession(null);
  }, [showNotice]);

  const startCountdown = useCallback(() => {
    isIdleModalOpenRef.current = true;
    setIsIdleModalOpen(true);
    setIdleCountdown(10);
    clearInterval(countdownIntervalRef.current);
    countdownIntervalRef.current = setInterval(() => {
      setIdleCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownIntervalRef.current);
          isIdleModalOpenRef.current = false;
          setIsIdleModalOpen(false);
          handleReset();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [handleReset]);

  const resetIdleTimer = useCallback(() => {
    if (isIdleModalOpenRef.current) return;
    clearTimeout(idleTimerRef.current);

    if (!session || session.status === 'IDLE' || session.status === 'GENERATING' || session.status === 'COMPOSING') {
      return;
    }

    // На экране результата даём 45 секунд, чтобы посетитель успел спокойно навести камеру и отсканировать QR
    const timeoutDuration = (session.status === 'COMPLETED' || session.status === 'READY_TO_PRINT' || session.status === 'PRINTING') ? 45000 : 15000;

    idleTimerRef.current = setTimeout(() => {
      startCountdown();
    }, timeoutDuration);
  }, [session, startCountdown]);

  const handleStay = useCallback(() => {
    clearInterval(countdownIntervalRef.current);
    isIdleModalOpenRef.current = false;
    setIsIdleModalOpen(false);
    setIdleCountdown(10);
    resetIdleTimer();
  }, [resetIdleTimer]);

  const handleLeave = useCallback(() => {
    clearInterval(countdownIntervalRef.current);
    clearTimeout(idleTimerRef.current);
    isIdleModalOpenRef.current = false;
    setIsIdleModalOpen(false);
    setIdleCountdown(10);
    handleReset();
  }, [handleReset]);

  useEffect(() => {
    const handleActivity = () => {
      if (!isIdleModalOpenRef.current) {
        resetIdleTimer();
      }
    };
    window.addEventListener('touchstart', handleActivity, { passive: true });
    window.addEventListener('pointerdown', handleActivity, { passive: true });
    window.addEventListener('click', handleActivity, { passive: true });

    resetIdleTimer();

    return () => {
      window.removeEventListener('touchstart', handleActivity);
      window.removeEventListener('pointerdown', handleActivity);
      window.removeEventListener('click', handleActivity);
      clearTimeout(idleTimerRef.current);
      clearInterval(countdownIntervalRef.current);
    };
  }, [resetIdleTimer]);

  const handleStartSession = () => runAction(async () => {
    setCardLoadError(false);
    const sess = await api('/api/session/new', { method: 'POST' });
    setSession(sess);
  });

  const handleCapturePhoto = () => runAction(async () => {
    await api('/api/camera/capture', { method: 'POST' });
    await syncActiveSession();
  });
  const handleConfirmPhoto = () => runAction(async () => {
    const res = await api('/api/session/photo/confirm', { method: 'POST' });
    if (res && res.session) setSession(res.session);
    else await syncActiveSession();
  });
  const handleRetakePhoto = () => runAction(async () => {
    const res = await api('/api/session/photo/retake', { method: 'POST' });
    if (res && res.session) setSession(res.session);
    else await syncActiveSession();
  });

  const handleSelectChoice = (questionType, choiceId) => runAction(async () => {
    const res = await api('/api/session/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_type: questionType, answer_id: choiceId })
    });
    if (res && res.session) setSession(res.session);
    else await syncActiveSession();
  });

  const handleRetryGeneration = () => runAction(async () => {
    setCardLoadError(false);
    const res = await api('/api/session/retry-generation', { method: 'POST' });
    if (res && res.session) setSession(res.session);
    else await syncActiveSession();
  });

  const getStepIndex = () => {
    if (!session || session.status === 'IDLE') return 0;
    if (session.status === 'PHOTO_PENDING' || session.status === 'PHOTO_TAKEN') return 0;
    if (session.status === 'QUIZ_ELEMENT') return 1;
    if (session.status === 'QUIZ_POWER') return 2;
    if (session.status === 'QUIZ_COLOR') return 3;
    return 4;
  };

  const renderScreen = () => {
    if (!session || session.status === 'IDLE') {
      return <WelcomeScreen onStart={handleStartSession} />;
    }

    if (session.status === 'PHOTO_PENDING') {
      return (
        <CameraScreen
          isReview={false}
          busy={busy}
          session={session}
          onCapture={handleCapturePhoto}
          onConfirm={handleConfirmPhoto}
          onRetake={handleRetakePhoto}
        />
      );
    }

    if (session.status === 'PHOTO_TAKEN') {
      return (
        <CameraScreen
          isReview={true}
          busy={busy}
          sessionId={session.id}
          session={session}
          onCapture={handleCapturePhoto}
          onConfirm={handleConfirmPhoto}
          onRetake={handleRetakePhoto}
        />
      );
    }

    if (session.status === 'QUIZ_ELEMENT') {
      return (
        <SelectionScreen
          title="ВЫБЕРИ СВОЙ ВАЙБ 🚀"
          subtitle="Какая былинная стихия и отрасль инженерии тебе ближе всего?"
          options={quizSchema[0]?.options || []}
          selectedId={session.element}
          busy={busy}
          onSelect={(id) => handleSelectChoice('element', id)}
          type="element"
        />
      );
    }

    if (session.status === 'QUIZ_POWER') {
      return (
        <SelectionScreen
          title="ВЫБЕРИ СУПЕРСИЛУ ⚡"
          subtitle="Какая богатырская способность поможет совершать инженерные открытия?"
          options={quizSchema[1]?.options || []}
          selectedId={session.power}
          busy={busy}
          onSelect={(id) => handleSelectChoice('power', id)}
          type="power"
        />
      );
    }

    if (session.status === 'QUIZ_COLOR') {
      return (
        <SelectionScreen
          title="ВЫБЕРИ ЦВЕТ ОБРАЗА 🎨"
          subtitle="Какая гербовая эмаль подчеркнет твой стиль и оборудование?"
          options={quizSchema[2]?.options || []}
          selectedId={session.color}
          busy={busy}
          onSelect={(id) => handleSelectChoice('color', id)}
          type="color"
        />
      );
    }

    if (session.status === 'GENERATING' || session.status === 'COMPOSING') {
      return <GeneratingScreen session={session} />;
    }

    if (session.status === 'ERROR' || cardLoadError) {
      return (
        <ErrorScreen
          session={session}
          onFinish={handleReset}
          onRetry={handleRetryGeneration}
          busy={busy}
        />
      );
    }

    return (
      <ResultScreen
        session={session}
        onFinish={handleReset}
        onQrRevealed={resetIdleTimer}
        onCardError={() => setCardLoadError(true)}
      />
    );
  };

  return (
    <div className="w-full h-full max-h-screen relative overflow-hidden flex items-center justify-center p-1 sm:p-2.5 box-border">
      {/* Тонкие фоновые чертежные лимбы и шкалы градусов по периметру */}
      <BlueprintWatermarks />

      {/* Единая гармоничная выставочная станция (Фланг Левый + Центральная Консоль + Фланг Правый) */}
      <div className="relative w-full max-w-[1720px] 2xl:max-w-[1900px] h-full max-h-[890px] 2xl:max-h-[950px] my-auto mx-auto flex items-stretch justify-center gap-3 xl:gap-5 z-20">
        {/* Левый кибер-хохломской фланг (Folk-Tech тотем) */}
        <CyberKhokhlomaFlankLeft />

        {/* Центральное интерактивное пространство киоска (пропорциональная сцена) */}
        <div className="flex-1 w-full max-w-[1360px] 2xl:max-w-[1460px] h-full my-auto mx-auto flex flex-col justify-between p-2.5 sm:p-3.5 md:p-4 select-none relative z-20 overflow-hidden box-border bg-parchment/90 backdrop-blur-[2px] rounded-2xl border border-brass/35 sm:border-2 sm:border-brass/45 shadow-tactile transition-all">
          {/* Латунная окантовка центрального интерактивного пространства */}
          <BrassCorners className="z-20 pointer-events-none" />

          {/* Потеря связи со стендом */}
          {!connected && (
            <div role="status" className="fixed top-0 inset-x-0 z-50 bg-ruby text-white text-center font-mono font-bold text-xs sm:text-sm py-2 border-b-2 border-brass-bright shadow-tactile-ruby">
              НЕТ СВЯЗИ СО СТЕНДОМ — ПЕРЕПОДКЛЮЧАЕМСЯ…
            </div>
          )}

          {/* Сообщение об ошибке действия */}
          {notice && (
            <div role="alert" className="fixed bottom-16 left-1/2 -translate-x-1/2 z-50 bg-panel-graphite text-brass-bright font-mono font-bold text-sm sm:text-base px-6 py-3 rounded-xl border-2 border-ruby shadow-tactile-ruby">
              {notice}
            </div>
          )}

          {/* Верхний статус-бар */}
          <header className="shrink-0 mb-1 sm:mb-2 pb-1.5 sm:pb-2 border-b border-brass/30 flex items-center justify-between text-[11px] sm:text-xs font-mono text-brass-dim">
            <div className="flex items-center gap-2 sm:gap-3">
              <span className="w-2 h-2 rounded-full bg-ruby"></span>
              <span className="font-bold tracking-widest uppercase truncate max-w-[280px] sm:max-w-none">
                ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ
              </span>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 text-brass/75 font-mono text-[10px] sm:text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-brass-bright animate-pulse" />
              <span className="uppercase tracking-widest hidden sm:inline">МАСТЕРСКАЯ БУДУЩЕГО</span>
            </div>
          </header>

          {/* Индикатор шагов */}
          {session && session.status !== 'IDLE' && (
            <div className="shrink-0 mb-1 sm:mb-2">
              <FolkStepTracker currentStep={getStepIndex()} />
            </div>
          )}

          {/* Рабочий холст слайда */}
          <div className="flex-1 min-h-0 w-full flex items-center justify-center my-auto overflow-hidden">
            <ErrorBoundary onReset={handleReset}>
              {renderScreen()}
            </ErrorBoundary>
          </div>

          {/* Tale-Tech Bar / Фирменный подвал по канону презентации фестиваля */}
          <footer className="shrink-0 mt-1 sm:mt-2 pt-1.5 sm:pt-2 border-t border-brass/40 w-full max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-1.5 sm:gap-6 text-[10px] sm:text-xs font-mono text-center">
            <div className="flex items-center gap-1.5 text-brass-dim font-bold tracking-widest uppercase">
              <svg className="w-3.5 h-3.5 text-brass inline-block shrink-0 animate-spin-slow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
              <span>ОТ ТРАДИЦИЙ К БОЛЬШИМ ВОЗМОЖНОСТЯМ</span>
            </div>
            <span className="hidden sm:inline text-brass/40">•</span>
            <div className="flex items-center gap-1.5 font-serif font-black text-ruby tracking-wider uppercase text-xs sm:text-sm">
              <svg className="w-3.5 h-3.5 text-brass inline-block shrink-0 fill-current" viewBox="0 0 24 24">
                <path d="M12 0l2.8 8.5L23.5 12l-8.7 2.8L12 23.5l-2.8-8.7L0.5 12l8.7-2.8z" />
              </svg>
              <span>ЗНАНИЯ • ТЕХНОЛОГИИ • ЛЮДИ • БУДУЩЕЕ</span>
            </div>
            <span className="hidden sm:inline text-brass/40">•</span>
            <span className="tracking-widest uppercase text-ink-muted">
              МОСКВА 2026
            </span>
          </footer>

          {/* Хронометр бездействия */}
          <IdleModal
            isOpen={isIdleModalOpen}
            countdown={idleCountdown}
            onStay={handleStay}
            onLeave={handleLeave}
          />
        </div>

        {/* Правый кибер-хохломской фланг (Жар-Птица 2.0 & Индустрия чудес) */}
        <CyberKhokhlomaFlankRight />
      </div>
    </div>
  );
}

// Рендер React-приложения с защитой ErrorBoundary
const rootElement = document.getElementById('react-kiosk-root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <ErrorBoundary>
      <KioskRoot />
    </ErrorBoundary>
  );
}
