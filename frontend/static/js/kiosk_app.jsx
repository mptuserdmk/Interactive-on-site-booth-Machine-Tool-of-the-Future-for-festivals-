/**
 * @file kiosk_app.jsx
 * @description Интерактивный выставочный комплекс «Осенний Промышленный Фестиваль Колледжей Москвы»
 * Визуальный стандарт: Неорусский стимпанк и хай-тек (Folk-Tech)
 * Разработано строго по спецификации react-presentation-design:
 * - Гармоничный синтез былинных мотивов, латуни, филиграни и станков с ЧПУ
 * - Палитра: пергамент (#FBF8F1, #F4EEDA), латунь (#C59A45, #E8CA7B), багрянец (#BA1B1D), графит (#121820)
 * - Декоративные латунные уголки BrassCorners и анимированные шестерни
 * - Телеметрия ЧПУ, калибровка 0.02 мм по ГОСТ 2.0
 * - Тактильные кнопки с поддержкой 8 состояний и таргет > 64px
 * - Полная совместимость с E2E тестами и офлайн-режимом
 */

const { useState, useEffect, useRef, useCallback } = React;

// --- API Helper с обработкой ошибок ---
async function api(url, options = {}) {
  const res = await fetch(url, options);
  let body = null;
  try { body = await res.json(); } catch (e) { /* пустой ответ */ }
  if (!res.ok) {
    const err = new Error((body && body.detail) || `Ошибка ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return body;
}

function friendlyError(e) {
  if (e && e.status === 409) return "Секунду… калибровка станка";
  if (e && e.status === 503) return "Оптический датчик не отвечает — позови мастера 📷";
  if (e instanceof TypeError) return "Нет связи со станком — позови мастера";
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
  // Роботы / ЧПУ-самоход
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
    // Графитовая панель станка
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
        «Органический синтез традиционных сказок и передовой инженерии: посмотри в оптический визор, выбери былинную стихию и отчекань паспорт мастера на станке ЧПУ!»
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

      {/* 3 Архетипичные плашки особенностей */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 sm:gap-4 mt-3 sm:mt-5 w-full max-w-3xl">
        <div className="p-2 sm:p-2.5 rounded-xl bg-parchment-card border border-brass/40 shadow-brass-sm flex items-center gap-3 text-left relative overflow-hidden">
          <BrassCorners />
          <div className="w-9 h-9 rounded-lg bg-panel-graphite text-brass flex items-center justify-center shrink-0">
            {ICONS.camera}
          </div>
          <div>
            <span className="font-mono text-[9px] sm:text-[10px] font-bold text-ruby uppercase tracking-wider block">Оптика ЧПУ</span>
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
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 14h12v8H6z" />
            </svg>
          </div>
          <div>
            <span className="font-mono text-[9px] sm:text-[10px] font-bold text-ruby uppercase tracking-wider block">Артефакт 300 DPI</span>
            <span className="font-serif font-bold text-ink-main text-xs sm:text-sm">Печать в руки</span>
          </div>
        </div>
      </div>
    </main>
  );
}

// --- ЭКРАН 2: КАМЕРА И ОПТИЧЕСКИЙ ВИЗИР (Camera Slide) ---
function CameraScreen({ isReview, sessionId, onCapture, onConfirm, onRetake, busy }) {
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isCapturing, setIsCapturing] = useState(false);
  const [flash, setFlash] = useState(false);
  const [shutterRing, setShutterRing] = useState(false);

  const handleShutter = async () => {
    setIsCapturing(true);
    setShutterRing(true);
    setFlash(true);
    setTimeout(() => setFlash(false), 200);
    setTimeout(() => setShutterRing(false), 700);

    try {
      await onCapture();
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <section className="flex-1 w-full max-w-6xl mx-auto flex flex-col gap-2 sm:gap-3 animate-fade-in h-full max-h-full overflow-hidden" aria-label="Зона фотографирования">
      {/* Шапка зоны съемки */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-1.5 border-b border-brass/40 pb-1.5 sm:pb-2 shrink-0">
        <div>
          <span className="text-[10px] sm:text-xs font-mono font-bold tracking-widest text-ruby uppercase">
            ОПТИЧЕСКИЙ БЛОК ЧПУ // КАЛИБРОВКА ОБРАЗА
          </span>
          <h2 className="text-2xl sm:text-3xl font-serif font-black tracking-tight text-ink-main mt-0.5">
            {isReview ? "ТВОЙ КАДР ОТЛИЧНЫЙ! 🌟" : "УЛЫБНИСЬ В КАМЕРУ! 📸"}
          </h2>
          <p className="font-serif italic text-xs sm:text-sm text-ink-muted">
            {isReview
              ? "Оптический слепок зафиксирован. Утверди его или перезапусти оптику станка."
              : "Взгляни в латунный визор станка и отчекань свой портрет для гильдии."}
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-panel-graphite border border-brass/50 text-brass-bright font-mono text-[10px] sm:text-xs font-bold self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-pulse"></span>
          <span>ОПТИКА: ОНЛАЙН (ГОСТ 2.0)</span>
        </div>
      </div>

      {/* 7/5 Асимметричная раскладка станка */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-5 items-stretch flex-1 min-h-0 max-h-full">
        {/* Левая 7-колоночная область видоискателя станка */}
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
                <span>ОПТИЧЕСКИЙ ДАТЧИК ЧПУ: АКТИВЕН</span>
                <span className="text-cyber-cyan">ТОЧНОСТЬ: 0.02 мм</span>
              </div>
            </div>
          )}
        </div>

        {/* Правая 5-колоночная консоль управления мастера */}
        <div className="lg:col-span-5 bg-parchment-card rounded-2xl p-3 sm:p-5 border-2 border-brass/50 shadow-brass flex flex-col justify-between relative h-full max-h-[55vh] min-h-0">
          <BrassCorners />

          <div className="space-y-2.5 sm:space-y-3">
            <div className="p-2.5 sm:p-3 rounded-xl bg-parchment border border-brass/30">
              <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block">
                Сказочный наказ мастера
              </span>
              <p className="mt-0.5 text-xs sm:text-sm font-serif italic text-ink-main leading-relaxed">
                "Держи взгляд прямой и смелый, как подобает инженеру Руси великой. Нажми рубиновый затвор, когда будешь готов!"
              </p>
            </div>

            {/* Индустриальная плашка телеметрии ЧПУ */}
            <div className="p-2.5 sm:p-3 rounded-xl bg-panel-graphite text-brass-bright border border-brass/40 flex items-center justify-between font-mono text-xs">
              <div className="flex items-center gap-2.5">
                <div className="text-brass animate-spin-slow">
                  {ICONS.gear}
                </div>
                <div>
                  <div className="font-bold text-white uppercase text-[11px] sm:text-xs">Привод оптической ячейки</div>
                  <div className="text-ink-faint text-[9px] sm:text-[10px]">Готовность 100% • Станок № 1</div>
                </div>
              </div>
              <span className="text-cyber-cyan font-bold text-xs">ОК</span>
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
                    <div className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full border-2 border-brass/70 flex items-center justify-center text-brass-bright transition-transform duration-300 ${isCapturing ? 'rotate-180 scale-75' : ''}`}>
                      {ICONS.camera}
                    </div>
                  </button>
                </div>
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

// Вертикальные технические надписи по ГОСТ/ЧПУ, расположенные сбоку карточки
const CARD_SIDE_LABELS = {
  // Стихии
  space: "ОРБИТА // КОСМОС // ЧПУ",
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
                    className={`w-full h-full object-cover object-center opacity-60 transition-transform duration-500 ease-out transform ${
                      isSelected ? 'scale-105' : 'group-hover:scale-110'
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

// --- ЭКРАН 6: ГЕНЕРАЦИЯ И СБОРКА ЧПУ («Индустрия Чудес») ---
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

        {/* Пульсирующий рубиновый кристалл в сердце станка */}
        <div className="w-8 h-8 rounded-full bg-ruby border-2 border-brass-bright flex items-center justify-center text-white shadow-brass-glow animate-pulse z-10 scale-90">
          {ICONS.sparkles}
        </div>
      </div>

      <span className="font-mono text-[10px] sm:text-xs font-bold tracking-widest text-ruby uppercase mb-1">
        ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ
      </span>

      <h2 className="font-serif font-black text-2xl sm:text-3xl md:text-4xl text-ink-main mb-1.5">
        {isComposing ? "КОМПОНУЕМ ТВОРЧЕСКИЙ ПАСПОРТ... 🖨️" : "НЕЙРОСЕТЬ ГЕНЕРИРУЕТ ОБРАЗ... ✨"}
      </h2>

      <p className="font-serif italic text-xs sm:text-sm text-ink-muted mb-3 sm:mb-4 max-w-lg">
        {isComposing
          ? "Отливаем форму паспорта в качестве 300 DPI и наносим персональный QR-код гильдии..."
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
        <div className="text-ruby font-bold animate-pulse">● {isComposing ? "Верстка паспорта 300 DPI в золотой филиграни..." : "Синтез персонажа нейросетью ЧПУ..."}</div>
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
              className="flex-1 px-2.5 py-1.5 rounded-lg bg-white border border-brass/50 font-mono text-xs sm:text-sm text-ink-main outline-none focus:ring-1 focus:ring-brass"
            />
            <button
              type="button"
              disabled={sending || !email}
              onClick={handleSendEmail}
              className="px-3 py-1.5 rounded-lg bg-ruby text-white font-mono text-[11px] font-bold uppercase tracking-wider border border-brass-bright hover:bg-ruby-dark disabled:opacity-50 cursor-pointer transition-all shadow-brass-sm"
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

// --- ЭКРАН 7: ФИНАЛЬНЫЙ ПАСПОРТ И СТАТУС ПЕЧАТИ (Result Slide) ---
function ResultScreen({ session, onFinish, autoPrint }) {
  const cardUrl = session?.final_card_path
    ? `/media/cards/${session.id}.jpg?t=${Date.now()}`
    : null;

  return (
    <section className="flex-1 w-full max-w-5xl mx-auto flex flex-col justify-between overflow-hidden gap-1.5 sm:gap-2.5 h-full max-h-full animate-fade-in" aria-label="Результат генерации">
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

        {/* Статусная плашка спулера печати */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-panel-graphite border border-brass/60 shadow-industrial text-brass-bright font-mono text-[11px] sm:text-xs self-start sm:self-auto">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-cyan animate-pulse"></span>
          <span className="font-bold tracking-wider">
            {session?.print_status === 'printed'
              ? "ПАСПОРТ НАПЕЧАТАН!"
              : session?.print_status === 'printing'
                ? "ПЕЧАТАЕМ НА ПРИНТЕРЕ..."
                : !autoPrint
                  ? "ЦИФРОВОЙ ПАСПОРТ ГОТОВ"
                  : "ГОТОВО К ВЫДАЧЕ"}
          </span>
        </div>
      </div>

      {/* 7/5 Асимметричная витрина паспорта */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-5 items-stretch flex-1 min-h-0 max-h-full">
        {/* 7 колонок: демонстрация паспорта в латунной рамке */}
        <div className="lg:col-span-7 flex items-center justify-center h-full max-h-[55vh] min-h-0">
          <div className="relative max-h-full rounded-2xl overflow-hidden shadow-industrial border-3 sm:border-4 border-brass bg-panel-graphite p-1.5 flex items-center justify-center">
            <BrassCorners />
            <div className="rounded-lg overflow-hidden border border-brass/40 max-h-[52vh] flex items-center justify-center">
              {cardUrl ? (
                <img src={cardUrl} alt="Итоговый паспорт инженера" className="max-h-[50vh] w-auto max-w-full object-contain block" />
              ) : (
                <div className="p-10 text-center font-serif text-brass-bright text-sm">Загрузка паспорта мастера...</div>
              )}
            </div>
          </div>
        </div>

        {/* 5 колонок: гербовая грамота, отправка на почту и завершение */}
        <div className="lg:col-span-5 bg-parchment-card rounded-2xl p-3 sm:p-4 border-2 border-brass/50 shadow-brass flex flex-col justify-between gap-2.5 relative h-full max-h-[55vh] min-h-0">
          <BrassCorners />

          <div className="space-y-2">
            <div className="p-2 sm:p-2.5 rounded-xl bg-parchment border border-brass/30">
              <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block">
                СУПЕРСИЛА МАСТЕРА
              </span>
              <div className="font-serif font-black text-lg sm:text-xl text-ink-main mt-0.5">
                {(session?.power_name || 'ТОЧНОСТЬ').toUpperCase()}
              </div>
            </div>

            <p className="font-serif italic text-xs sm:text-sm text-ink-main leading-relaxed line-clamp-3 sm:line-clamp-4">
              "{session?.machine_desc || "Ты стал выдающимся специалистом передовой индустрии и мастером чудес!"}"
            </p>

            <div className="p-2 rounded-xl bg-panel-graphite text-brass-bright border border-brass/40 font-mono text-[10px] sm:text-xs">
              <span className="text-ruby font-bold">📍 ГИЛЬДИЯ:</span> {session?.location || "Центральный производственный кластер"}
            </div>
          </div>

          {/* Персональный QR-код для моментальной отправки на почту и телефон */}
          <div className="p-2 sm:p-2.5 rounded-xl bg-parchment border border-brass/50 shadow-sm flex items-center gap-3 text-left">
            <img
              src={`/api/qr.png?data=${encodeURIComponent(window.location.origin + '/card/' + (session?.id || ''))}`}
              alt="QR-код паспорта"
              className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg bg-white p-1 border-2 border-brass shrink-0 shadow-sm"
            />
            <div className="flex-1 min-w-0">
              <span className="text-[9px] sm:text-[10px] font-mono uppercase font-bold tracking-wider text-ruby block">
                📱 СКАНИРУЙ QR-КОД ТЕЛЕФОНОМ
              </span>
              <p className="font-serif italic text-[11px] sm:text-xs text-ink-main leading-tight mt-0.5">
                Наведи камеру смартфона, чтобы моментально получить паспорт на свою почту и скачать в HD!
              </p>
            </div>
          </div>

          {/* Модуль рассылки интерактивной карточки на почту прямо на киоске */}
          <EmailDispatchBox sessionId={session?.id} />

          <FolkButton
            variant="primary"
            size="lg"
            onClick={onFinish}
            ariaLabel="Завершить сессию и перейти к следующему участнику"
            className="w-full py-2.5 sm:py-3 text-sm sm:text-base"
          >
            <span>СЛЕДУЮЩИЙ УЧАСТНИК 🚀</span>
          </FolkButton>
        </div>
      </div>
    </section>
  );
}

// --- ЭКРАН 8: ОШИБКА ОБОРУДОВАНИЯ (Error Screen) ---
function ErrorScreen({ session, onFinish, busy }) {
  const hasCard = Boolean(session?.final_card_path);
  return (
    <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-3xl mx-auto animate-fade-in" role="alert">
      <div className="w-24 h-24 rounded-full bg-ruby text-brass-bright border-4 border-brass flex items-center justify-center text-4xl mb-6 shadow-tactile-ruby">
        ⚙️
      </div>
      <h2 className="font-serif font-black text-4xl sm:text-5xl text-ink-main mb-3">
        {hasCard ? "КАРТОЧКА ГОТОВА, НО НЕ НАПЕЧАТАЛАСЬ" : "УПС! ЧТО-ТО ПОШЛО НЕ ТАК"}
      </h2>
      <p className="font-serif italic text-xl text-ink-muted mb-8 max-w-xl">
        {hasCard ? "Позови мастера станка — он допечатает твой паспорт за минуту." : "Позови мастера или попробуй запустить станок заново."}
      </p>
      {hasCard && (
        <div className="relative p-2 bg-panel-graphite border-2 border-brass rounded-xl mb-8">
          <BrassCorners />
          <img src={`/media/cards/${session.id}.jpg?t=${Date.now()}`} alt="Твой паспорт инженера" className="w-64 rounded shadow-industrial" />
        </div>
      )}
      <FolkButton variant="primary" size="xl" onClick={onFinish} disabled={busy} ariaLabel="Вернуться на главный экран">
        <span>НАЧАТЬ ЗАНОВО</span>
      </FolkButton>
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
          Хронометр станка отсчитывает секунды. Если не продолжить, экран вернется к началу.
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
  const [autoPrint, setAutoPrint] = useState(true);

  // Управление бездействием
  const [isIdleModalOpen, setIsIdleModalOpen] = useState(false);
  const [idleCountdown, setIdleCountdown] = useState(5);
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

  const syncPrintStatus = useCallback(async () => {
    try {
      const data = await api('/api/print/status');
      if (data && typeof data.enable_auto_print === 'boolean') {
        setAutoPrint(data.enable_auto_print);
      }
    } catch (e) { }
  }, []);

  useEffect(() => {
    syncPrintStatus();
  }, [syncPrintStatus]);

  const toggleAutoPrint = async () => {
    try {
      const res = await api('/api/print/toggle-auto-print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !autoPrint })
      });
      if (res && typeof res.enable_auto_print === 'boolean') {
        setAutoPrint(res.enable_auto_print);
        showNotice(res.enable_auto_print ? "Автопечать включена 🖨️" : "Автопечать выключена (только цифра)");
      }
    } catch (e) {
      showNotice("Не удалось изменить режим печати");
    }
  };

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

  const resetIdleTimer = useCallback(() => {
    if (isIdleModalOpen) return;
    clearTimeout(idleTimerRef.current);

    if (!session || session.status === 'IDLE' || session.status === 'GENERATING' || session.status === 'COMPOSING') {
      return;
    }

    idleTimerRef.current = setTimeout(() => {
      setIdleCountdown(5);
      setIsIdleModalOpen(true);
    }, 15000);
  }, [session, isIdleModalOpen]);

  useEffect(() => {
    const handleActivity = () => resetIdleTimer();
    window.addEventListener('touchstart', handleActivity, { passive: true });
    window.addEventListener('pointerdown', handleActivity, { passive: true });
    window.addEventListener('click', handleActivity, { passive: true });

    resetIdleTimer();

    return () => {
      window.removeEventListener('touchstart', handleActivity);
      window.removeEventListener('pointerdown', handleActivity);
      window.removeEventListener('click', handleActivity);
      clearTimeout(idleTimerRef.current);
    };
  }, [resetIdleTimer]);

  useEffect(() => {
    if (!isIdleModalOpen) return;
    countdownIntervalRef.current = setInterval(() => setIdleCountdown(prev => Math.max(0, prev - 1)), 1000);
    return () => clearInterval(countdownIntervalRef.current);
  }, [isIdleModalOpen]);

  useEffect(() => {
    if (isIdleModalOpen && idleCountdown <= 0) {
      handleReset();
    }
  }, [isIdleModalOpen, idleCountdown]);

  const handleStartSession = () => runAction(async () => {
    const sess = await api('/api/session/new', { method: 'POST' });
    setSession(sess);
  });

  const handleCapturePhoto = () => runAction(() => api('/api/camera/capture', { method: 'POST' }));
  const handleConfirmPhoto = () => runAction(() => api('/api/session/photo/confirm', { method: 'POST' }));
  const handleRetakePhoto = () => runAction(() => api('/api/session/photo/retake', { method: 'POST' }));

  const handleSelectChoice = (questionType, choiceId) => runAction(() => api('/api/session/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_type: questionType, answer_id: choiceId })
  }));

  const handleReset = async () => {
    setIsIdleModalOpen(false);
    clearInterval(countdownIntervalRef.current);
    try {
      await api('/api/session/reset', { method: 'POST' });
    } catch (e) {
      showNotice(friendlyError(e));
    }
    setSession(null);
  };

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
          subtitle="Какая былинная стихия и отрасль станка тебе ближе всего?"
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

    if (session.status === 'ERROR') {
      return <ErrorScreen session={session} onFinish={handleReset} busy={busy} />;
    }

    return <ResultScreen session={session} onFinish={handleReset} autoPrint={autoPrint} />;
  };

  return (
    <div className="w-full max-w-[1400px] mx-auto h-full max-h-screen flex flex-col justify-between p-2 sm:p-3 md:p-4 select-none relative overflow-hidden box-border">
      {/* Латунная окантовка всего презентационного киоска */}
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
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={toggleAutoPrint}
            title="Переключить отправку на печать"
            className={`px-2.5 sm:px-3 py-1 rounded-lg border font-mono text-[11px] sm:text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 select-none ${autoPrint
              ? "bg-panel-graphite text-brass-bright border-brass/50 hover:border-brass shadow-sm"
              : "bg-ruby/15 text-ruby border-ruby/40 hover:border-ruby shadow-sm"
              }`}
          >
            <span>🖨️</span>
            <span>{autoPrint ? "ПЕЧАТЬ: ВКЛ" : "ПЕЧАТЬ: ВЫКЛ"}</span>
          </button>
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
        {renderScreen()}
      </div>

      {/* Tale-Tech Bar / Фирменный подвал, выровненный по центру */}
      <footer className="shrink-0 mt-1 sm:mt-2 pt-1.5 sm:pt-2 border-t border-brass/40 w-full max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-1.5 sm:gap-6 text-[10px] sm:text-xs font-mono text-center">
        <span className="tracking-widest uppercase text-brass-dim font-bold">
          ОТ ТРАДИЦИЙ К БОЛЬШИМ ВОЗМОЖНОСТЯМ
        </span>
        <span className="hidden sm:inline text-brass/40">•</span>
        <span className="font-serif font-black text-ruby tracking-wider uppercase text-xs sm:text-sm">
          ЗНАНИЯ • ТЕХНОЛОГИИ • ЛЮДИ • БУДУЩЕЕ
        </span>
        <span className="hidden sm:inline text-brass/40">•</span>
        <span className="tracking-widest uppercase text-ink-muted">
          МОСКВА 2026
        </span>
      </footer>

      {/* Хронометр бездействия */}
      <IdleModal
        isOpen={isIdleModalOpen}
        countdown={idleCountdown}
        onStay={() => {
          setIsIdleModalOpen(false);
          clearInterval(countdownIntervalRef.current);
          resetIdleTimer();
        }}
        onLeave={() => {
          setIsIdleModalOpen(false);
          clearInterval(countdownIntervalRef.current);
          handleReset();
        }}
      />
    </div>
  );
}

// Рендер React-приложения
const rootElement = document.getElementById('react-kiosk-root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<KioskRoot />);
}
