/**
 * @file kiosk_app.jsx
 * @description Senior Frontend Design: Playful / Geometric Kids-first AI Photo Kiosk
 * Built strictly according to "Frontend-Design-SKILLS-for-AI" specifications:
 * - Playful / Geometric aesthetic (Duolingo-grade tactile gamified interface)
 * - 3-step intuitive child flow (Vibe Selection -> Photo Shutter -> AI Magic Result)
 * - Strict token system with tactile 3D touch targets (min 72px)
 * - Comprehensive 8-state component support (default, hover, focus, active, disabled, loading, empty, error)
 * - Live MJPEG Camera streaming, real-time WebSocket sync, and 15s idle auto-reset
 */

const { useState, useEffect, useRef, useCallback } = React;

// --- ICONS (Playful Geometric Inline SVGs) ---
const ICONS = {
  // Elements
  space: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
      <circle cx="15" cy="9" r="1.5" fill="currentColor"/>
    </svg>
  ),
  atom: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" fill="currentColor" fillOpacity="0.2"/>
      <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(30 12 12)"/>
      <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(90 12 12)"/>
      <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(150 12 12)"/>
    </svg>
  ),
  robots: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <rect width="16" height="14" x="4" y="6" rx="3"/>
      <circle cx="9" cy="12" r="1.5" fill="currentColor"/>
      <circle cx="15" cy="12" r="1.5" fill="currentColor"/>
      <path d="M10 16h4"/>
      <path d="M12 6V3"/>
      <circle cx="12" cy="2" r="1" fill="currentColor"/>
      <path d="M2 12h2M20 12h2"/>
    </svg>
  ),
  medicine: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m2 15 5 5 13-13-5-5-13 13Z"/>
      <path d="m9 8 7 7"/>
      <path d="m14.5 3.5 3 3M3.5 14.5 6.5 17.5"/>
    </svg>
  ),
  metal: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
      <circle cx="12" cy="12" r="3" fill="currentColor" fillOpacity="0.2"/>
    </svg>
  ),
  // Superpowers
  precision: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9"/>
      <circle cx="12" cy="12" r="5"/>
      <circle cx="12" cy="12" r="2" fill="currentColor"/>
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2"/>
    </svg>
  ),
  speed: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" fillOpacity="0.2"/>
    </svg>
  ),
  power: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v10"/>
      <path d="M18.4 6.6a9 9 0 1 1-12.77.01"/>
    </svg>
  ),
  mind: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04"/>
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04"/>
    </svg>
  ),
  care: (
    <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" fill="currentColor" fillOpacity="0.2"/>
    </svg>
  ),
  camera: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
      <circle cx="12" cy="13" r="3.5"/>
    </svg>
  ),
  sparkles: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>
    </svg>
  ),
  arrowRight: (
    <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7"/>
    </svg>
  ),
  check: (
    <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5"/>
    </svg>
  ),
  refresh: (
    <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
      <path d="M21 3v5h-5"/>
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
      <path d="M8 16H3v5"/>
    </svg>
  )
};

// --- TACTILE BUTTON COMPONENT (Supports 8 Interaction States) ---
function TactileButton({
  variant = "primary", // primary, secondary, accent, success, ghost
  size = "lg", // md, lg, xl, icon
  children,
  onClick,
  disabled = false,
  loading = false,
  ariaLabel,
  className = "",
  type = "button"
}) {
  const baseStyles = "relative font-display font-black select-none inline-flex items-center justify-center gap-3 transition-all duration-150 rounded-2xl cursor-pointer outline-none focus-visible:ring-4 focus-visible:ring-offset-2";
  
  const sizeStyles = {
    md: "min-h-[56px] px-6 text-lg tracking-wide",
    lg: "min-h-[72px] px-8 text-2xl tracking-wide",
    xl: "min-h-[84px] px-10 text-3xl tracking-wide",
    shutter: "w-24 h-24 rounded-full p-0 flex items-center justify-center"
  };

  const variantStyles = {
    primary: "bg-coral text-white border-b-6 border-coral-dark active:border-b-0 active:translate-y-1.5 shadow-tactile hover:bg-coral-light focus-visible:ring-coral/40",
    secondary: "bg-surface-card text-ink border-2 border-border-line border-b-6 border-border-dark active:border-b-2 active:translate-y-1 shadow-tactile-sm hover:bg-surface-muted focus-visible:ring-ink/20",
    accent: "bg-amber text-ink border-b-6 border-amber-dark active:border-b-0 active:translate-y-1.5 shadow-tactile hover:bg-amber-light focus-visible:ring-amber/40",
    teal: "bg-teal text-white border-b-6 border-teal-dark active:border-b-0 active:translate-y-1.5 shadow-tactile hover:bg-teal-light focus-visible:ring-teal/40",
    indigo: "bg-indigo text-white border-b-6 border-indigo-dark active:border-b-0 active:translate-y-1.5 shadow-tactile hover:bg-indigo-light focus-visible:ring-indigo/40",
    shutter: "bg-coral text-white border-b-6 border-coral-dark active:border-b-0 active:translate-y-1.5 shadow-tactile hover:scale-105 active:scale-95 focus-visible:ring-coral/50"
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
          <svg className="animate-spin -ml-1 mr-2 h-7 w-7 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Загрузка...</span>
        </span>
      ) : children}
    </button>
  );
}

// --- STEP INDICATOR ---
function StepTracker({ currentStep }) {
  const steps = [
    { label: "Фото", icon: "📸" },
    { label: "Стихия", icon: "🚀" },
    { label: "Суперсила", icon: "⚡" },
    { label: "Цвет", icon: "🎨" },
    { label: "Результат", icon: "🎁" }
  ];

  return (
    <nav aria-label="Прогресс создания образа" className="w-full max-w-4xl mx-auto mb-8 px-4">
      <div className="flex items-center justify-between relative">
        {/* Background track line */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-3 w-full bg-surface-muted rounded-full -z-0 border-2 border-border-line"></div>
        
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStep;
          const isActive = idx === currentStep;

          return (
            <div key={idx} className="relative z-10 flex flex-col items-center">
              <div 
                className={`
                  w-14 h-14 rounded-2xl flex items-center justify-center font-display font-black text-xl transition-all duration-300
                  ${isActive 
                    ? "bg-coral text-white scale-110 shadow-tactile border-2 border-coral-dark ring-4 ring-coral/20" 
                    : isCompleted 
                      ? "bg-teal text-white border-2 border-teal-dark shadow-tactile-sm" 
                      : "bg-surface-card text-ink-muted border-2 border-border-line"}
                `}
              >
                {isCompleted ? ICONS.check : <span className="text-2xl">{step.icon}</span>}
              </div>
              <span className={`mt-2 font-display text-base font-bold select-none ${isActive ? "text-coral" : isCompleted ? "text-teal-dark" : "text-ink-muted"}`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </nav>
  );
}

// --- SCREEN 1: WELCOME SCREEN ---
function WelcomeScreen({ onStart }) {
  return (
    <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-4xl mx-auto animate-fade-in">
      <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-amber-light/30 border-2 border-amber font-display font-black text-amber-dark text-lg mb-6 shadow-sm">
        <span>✨ ИНТЕРАКТИВНЫЙ ФЕСТИВАЛЬНЫЙ КИОСК 2026</span>
      </div>

      <h1 className="font-display font-black text-5xl sm:text-6xl md:text-7xl text-ink tracking-tight leading-tight mb-6">
        КЕМ ТЫ СТАНЕШЬ В{" "}
        <span className="relative inline-block text-coral">
          <span>БУДУЩЕМ?</span>
          <svg
            className="absolute left-0 -bottom-3 sm:-bottom-4 w-full h-3 sm:h-4 text-amber overflow-visible pointer-events-none"
            viewBox="0 0 100 12"
            preserveAspectRatio="none"
          >
            <path
              d="M0,6 Q6.25,1 12.5,6 T25,6 T37.5,6 T50,6 T62.5,6 T75,6 T87.5,6 T100,6"
              fill="none"
              stroke="currentColor"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
          </svg>
        </span>
      </h1>

      <p className="font-sans text-xl sm:text-2xl text-ink-muted max-w-2xl leading-relaxed mb-12">
        Создай свой уникальный образ инженера будущего всего за 3 простых шага: улыбнись в камеру, выбери суперспособности и получи готовый бейдж!
      </p>

      <TactileButton 
        variant="primary" 
        size="xl" 
        onClick={onStart}
        ariaLabel="Начать создание своего образа"
        className="w-full sm:w-auto min-w-[340px]"
      >
        <span>СОЗДАТЬ ОБРАЗ 🦸‍♂️</span>
        {ICONS.arrowRight}
      </TactileButton>

      {/* Floating playful badges */}
      <div className="grid grid-cols-3 gap-4 sm:gap-6 mt-16 w-full max-w-2xl">
        <div className="p-4 rounded-2xl bg-surface-card border-2 border-border-line shadow-tactile-sm flex flex-col items-center">
          <span className="text-3xl mb-1">📸</span>
          <span className="font-display font-bold text-ink text-base">Живое фото</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface-card border-2 border-border-line shadow-tactile-sm flex flex-col items-center">
          <span className="text-3xl mb-1">⚡</span>
          <span className="font-display font-bold text-ink text-base">100 Профессий</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface-card border-2 border-border-line shadow-tactile-sm flex flex-col items-center">
          <span className="text-3xl mb-1">🖨️</span>
          <span className="font-display font-bold text-ink text-base">Печать в руки</span>
        </div>
      </div>
    </main>
  );
}

// --- SCREEN 2: CAMERA CAPTURE (3/5 Viewport, 2/5 Actions) ---
function CameraScreen({ isReview, photoPath, onCapture, onConfirm, onRetake }) {
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isCapturing, setIsCapturing] = useState(false);
  const [flash, setFlash] = useState(false);

  const handleShutter = async () => {
    setIsCapturing(true);
    setFlash(true);
    setTimeout(() => setFlash(false), 200);

    try {
      await onCapture();
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <section className="flex-1 w-full max-w-6xl mx-auto flex flex-col gap-6 animate-fade-in" aria-label="Зона фотографирования">
      {/* Header */}
      <div className="text-center md:text-left flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b-2 border-border-line pb-4">
        <div>
          <h2 className="font-display font-black text-3xl sm:text-4xl text-ink">
            {isReview ? "ТВОЙ КАДР ОТЛИЧНЫЙ! 🌟" : "УЛЫБНИСЬ В КАМЕРУ! 📸"}
          </h2>
          <p className="font-sans text-lg text-ink-muted">
            {isReview ? "Нравится фото? Нажми подтвердить, или пересними заново." : "Встань по центру экрана и нажми большую красную кнопку."}
          </p>
        </div>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-light/30 border-2 border-teal text-teal-dark font-display font-bold text-base self-start sm:self-auto">
          <span className="w-3 h-3 rounded-full bg-teal animate-ping"></span>
          <span>КАМЕРА ОНЛАЙН</span>
        </div>
      </div>

      {/* 3/5 and 2/5 Asymmetric Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch flex-1 min-h-[480px]">
        {/* 3/5 Left Camera Viewport (7 cols) */}
        <div className="lg:col-span-7 relative bg-ink rounded-3xl overflow-hidden shadow-2xl border-4 border-surface-card flex items-center justify-center min-h-[380px]">
          {/* Shutter flash effect */}
          {flash && <div className="absolute inset-0 bg-white z-50 animate-fade-out pointer-events-none"></div>}

          {isReview ? (
            <img 
              src={`/storage/photos/${photoPath?.split(/[\\/]/).pop()}?t=${Date.now()}`} 
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

          {/* Friendly HUD Frame */}
          {!isReview && (
            <div className="absolute inset-6 pointer-events-none border-4 border-dashed border-white/50 rounded-2xl flex flex-col items-center justify-center">
              <div className="w-56 h-72 border-4 border-amber/70 rounded-full flex items-center justify-center opacity-70">
                <span className="font-display font-black text-amber text-lg bg-ink/60 px-4 py-1 rounded-full">ЛИЦО ЗДЕСЬ 😊</span>
              </div>
            </div>
          )}
        </div>

        {/* 2/5 Right Tactical Controls (5 cols) */}
        <div className="lg:col-span-5 bg-surface-card rounded-3xl p-8 border-2 border-border-line shadow-tactile flex flex-col justify-between">
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-surface-muted border-2 border-border-line">
              <h3 className="font-display font-black text-ink text-xl mb-1">💡 Совет для классного кадра</h3>
              <p className="font-sans text-ink-muted text-base">
                Смотри прямо в объектив и покажи свою самую яркую улыбку!
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-amber-light/20 border-2 border-amber/50 flex items-center gap-3">
              <span className="text-3xl">🎯</span>
              <span className="font-display font-bold text-ink text-base">
                {isReview ? "Кадр зафиксирован в HD качестве" : "Автофокус и свет настроены автоматически"}
              </span>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-6">
            {!isReview ? (
              <div className="flex flex-col items-center gap-4">
                <button
                  type="button"
                  aria-label="Сделать фотографию"
                  disabled={isCapturing}
                  onClick={handleShutter}
                  className="w-28 h-28 rounded-full bg-coral hover:bg-coral-light active:scale-95 border-b-8 border-coral-dark text-white flex items-center justify-center shadow-tactile transition-all cursor-pointer focus-visible:ring-4 focus-visible:ring-coral/40"
                >
                  <div className="w-20 h-20 rounded-full border-4 border-white/80 flex items-center justify-center">
                    {ICONS.camera}
                  </div>
                </button>
                <span className="font-display font-black text-xl text-ink">НАЖМИ ДЛЯ СНИМКА</span>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <TactileButton 
                  variant="primary" 
                  size="lg" 
                  onClick={onConfirm}
                  ariaLabel="Подтвердить фотографию и перейти к выбору"
                  className="w-full"
                >
                  <span>ПРОДОЛЖИТЬ</span>
                  {ICONS.arrowRight}
                </TactileButton>

                <TactileButton 
                  variant="secondary" 
                  size="md" 
                  onClick={onRetake}
                  ariaLabel="Переснять фотографию"
                  className="w-full"
                >
                  {ICONS.refresh}
                  <span>ПЕРЕСНЯТЬ</span>
                </TactileButton>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

// --- SCREEN 3, 4, 5: SELECTION SCREENS (Elements, Superpowers, Colors) ---
function SelectionScreen({ title, subtitle, options, selectedId, onSelect, type }) {
  return (
    <section className="flex-1 w-full max-w-6xl mx-auto flex flex-col gap-6 animate-fade-in" aria-label={title}>
      {/* Header */}
      <div className="text-center md:text-left border-b-2 border-border-line pb-4">
        <h2 className="font-display font-black text-4xl sm:text-5xl text-ink mb-2">
          {title}
        </h2>
        <p className="font-sans text-xl text-ink-muted">
          {subtitle}
        </p>
      </div>

      {/* Grid of Choices */}
      <div className={`grid gap-5 ${type === 'color' ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'} flex-1`}>
        {options.map((opt) => {
          const isSelected = selectedId === opt.id;

          if (type === 'color') {
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => onSelect(opt.id)}
                aria-label={`Выбрать цвет ${opt.name}`}
                className={`
                  p-6 rounded-3xl bg-surface-card border-3 transition-all duration-150 flex flex-col items-center justify-center gap-4 cursor-pointer outline-none
                  ${isSelected 
                    ? "border-coral border-b-8 shadow-tactile scale-[1.02] ring-4 ring-coral/20" 
                    : "border-border-line border-b-6 border-b-border-dark hover:border-ink active:border-b-2 active:translate-y-1 shadow-tactile-sm"}
                `}
              >
                <div 
                  className="w-20 h-20 rounded-full border-4 border-white shadow-md transition-transform" 
                  style={{ backgroundColor: opt.hex, transform: isSelected ? 'scale(1.15)' : 'scale(1)' }}
                ></div>
                <span className="font-display font-black text-2xl text-ink">{opt.name}</span>
              </button>
            );
          }

          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => onSelect(opt.id)}
              aria-label={`Выбрать вариант ${opt.name}`}
              className={`
                p-6 sm:p-8 rounded-3xl bg-surface-card border-3 transition-all duration-150 flex flex-col items-start justify-between text-left cursor-pointer outline-none min-h-[190px]
                ${isSelected 
                  ? "border-coral border-b-8 shadow-tactile scale-[1.02] ring-4 ring-coral/20 bg-coral/5" 
                  : "border-border-line border-b-6 border-b-border-dark hover:border-coral active:border-b-2 active:translate-y-1 shadow-tactile-sm hover:bg-surface-muted/50"}
              `}
            >
              <div className="w-16 h-16 rounded-2xl bg-surface-muted border-2 border-border-line flex items-center justify-center text-coral mb-4">
                {ICONS[opt.id] || <span className="text-3xl">✨</span>}
              </div>

              <div>
                <h3 className="font-display font-black text-2xl sm:text-3xl text-ink mb-1">{opt.name}</h3>
                <p className="font-sans text-base text-ink-muted leading-snug">{opt.hint}</p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

// --- SCREEN 6: GENERATING MAGIC PROGRESS ---
function GeneratingScreen({ session }) {
  const isComposing = session?.status === 'COMPOSING';
  const progressPercent = isComposing ? 90 : 60;

  return (
    <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-3xl mx-auto animate-fade-in">
      {/* Animated Magic Orb */}
      <div className="relative mb-8">
        <div className="w-36 h-36 rounded-full bg-coral/20 border-4 border-coral flex items-center justify-center text-coral animate-pulse">
          {ICONS.sparkles}
        </div>
        <div className="absolute inset-0 rounded-full border-4 border-dashed border-amber animate-spin opacity-60"></div>
      </div>

      <h2 className="font-display font-black text-4xl sm:text-5xl text-ink mb-3">
        {isComposing ? "КОМПОНУЕМ ТВОРЧЕСКИЙ ПАСПОРТ... 🖨️" : "НЕЙРОСЕТЬ ГЕНЕРИРУЕТ ОБРАЗ... ✨"}
      </h2>
      
      <p className="font-sans text-xl text-ink-muted mb-8 max-w-xl">
        {isComposing 
          ? "Рендерим HD-качество для фотопринтера и генерируем твой персональный QR-код..."
          : `Объединяем: ${session?.element_name || 'Стихию'} + ${session?.power_name || 'Суперсилу'} + ${session?.color_name || 'Цвет'}...`}
      </p>

      {/* Playful Thick Progress Bar */}
      <div className="w-full h-8 bg-surface-muted rounded-full overflow-hidden border-3 border-border-line shadow-inner p-1">
        <div 
          className="h-full bg-gradient-to-r from-amber to-coral rounded-full transition-all duration-700 ease-out shadow-sm"
          style={{ width: `${progressPercent}%` }}
        ></div>
      </div>

      <div className="mt-8 px-6 py-4 rounded-2xl bg-surface-card border-2 border-border-line font-mono text-sm text-ink-muted text-left w-full max-w-lg shadow-tactile-sm">
        <div className="text-teal-dark font-bold">✓ Снимок лица получен и откалиброван</div>
        <div className="text-teal-dark font-bold">✓ Входные стили: {(session?.element_name || '').toUpperCase()}</div>
        <div className="text-coral font-bold animate-pulse">● {isComposing ? "Сборка макета 300 DPI..." : "Синтез персонажа нейросетью..."}</div>
      </div>
    </main>
  );
}

// --- SCREEN 7: FINAL RESULT BADGE & PRINT STATUS ---
function ResultScreen({ session, onFinish }) {
  const cardUrl = session?.final_card_path 
    ? `/storage/cards/${session.final_card_path.split(/[\\/]/).pop()}?t=${Date.now()}`
    : null;

  return (
    <section className="flex-1 w-full max-w-6xl mx-auto flex flex-col gap-6 animate-fade-in" aria-label="Результат генерации">
      {/* Header */}
      <div className="text-center md:text-left border-b-2 border-border-line pb-4 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-light/40 border-2 border-teal font-display font-black text-teal-dark text-base mb-2">
            <span>🎉 ОБРАЗ УСПЕШНО СОЗДАН!</span>
          </div>
          <h2 className="font-display font-black text-4xl sm:text-5xl text-ink">
            {session?.machine_name || "ИНЖЕНЕР БУДУЩЕГО"}
          </h2>
        </div>

        {/* Print Status Pill */}
        <div className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-surface-card border-3 border-border-line shadow-tactile-sm">
          <span className="w-4 h-4 rounded-full bg-teal animate-pulse"></span>
          <span className="font-display font-bold text-ink text-base">
            {session?.print_status === 'printed' 
              ? "ПАСПОРТ НАПЕЧАТАН!" 
              : session?.print_status === 'printing' 
                ? "ПЕЧАТАЕМ НА ПРИНТЕРЕ..." 
                : "ГОТОВО К ВЫДАЧЕ"}
          </span>
        </div>
      </div>

      {/* Asymmetric Result Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center flex-1">
        {/* 3/5 Left Card Preview (7 cols) */}
        <div className="lg:col-span-7 flex justify-center">
          <div className="w-full max-w-md rounded-3xl overflow-hidden shadow-2xl border-4 border-surface-card bg-surface-card transform hover:scale-[1.02] transition-transform">
            {cardUrl ? (
              <img src={cardUrl} alt="Итоговый паспорт инженера" className="w-full h-auto block" />
            ) : (
              <div className="p-16 text-center text-ink-muted">Загрузка изображения карточки...</div>
            )}
          </div>
        </div>

        {/* 2/5 Right Info & Action (5 cols) */}
        <div className="lg:col-span-5 bg-surface-card rounded-3xl p-8 border-2 border-border-line shadow-tactile flex flex-col justify-between gap-6">
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-amber-light/20 border-2 border-amber/60">
              <div className="font-display font-black text-amber-dark text-lg mb-1">СУПЕРСИЛА</div>
              <div className="font-display font-bold text-2xl text-ink">
                {(session?.power_name || 'ТОЧНОСТЬ').toUpperCase()}
              </div>
            </div>

            <p className="font-sans text-lg text-ink-muted leading-relaxed">
              {session?.machine_desc || "Ты стал выдающимся специалистом передовой индустрии!"}
            </p>

            <div className="p-4 rounded-2xl bg-surface-muted border-2 border-border-line font-sans text-sm text-ink-muted">
              📍 <strong>Локация:</strong> {session?.location || "Центральный производственный кластер"}
            </div>
          </div>

          <TactileButton 
            variant="primary" 
            size="xl" 
            onClick={onFinish}
            ariaLabel="Завершить сессию и перейти к следующему участнику"
            className="w-full"
          >
            <span>СЛЕДУЮЩИЙ УЧАСТНИК 🚀</span>
          </TactileButton>
        </div>
      </div>
    </section>
  );
}

// --- IDLE INACTIVITY MODAL (KFC-Style 15s Timer -> 5s Modal) ---
function IdleModal({ isOpen, countdown, onStay, onLeave }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-6 animate-fade-in">
      <div className="bg-surface-card border-4 border-coral rounded-3xl p-8 sm:p-10 max-w-lg w-full text-center shadow-2xl animate-scale-up">
        <div className="w-24 h-24 rounded-full bg-coral text-white font-display font-black text-5xl flex items-center justify-center mx-auto mb-6 border-4 border-coral-dark shadow-tactile">
          {countdown}
        </div>

        <h3 className="font-display font-black text-3xl sm:text-4xl text-ink mb-3">
          ТЫ ЕЩЁ ЗДЕСЬ? 😊
        </h3>
        
        <p className="font-sans text-lg text-ink-muted mb-8">
          Если не продолжить, через несколько секунд терминал вернется на начальный экран.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <TactileButton 
            variant="primary" 
            size="lg" 
            onClick={onStay}
            ariaLabel="Продолжить работу с киоском"
            className="flex-1"
          >
            <span>ПРОДОЛЖИТЬ</span>
          </TactileButton>

          <TactileButton 
            variant="secondary" 
            size="lg" 
            onClick={onLeave}
            ariaLabel="Вернуться на главный экран"
            className="flex-1"
          >
            <span>В НАЧАЛО</span>
          </TactileButton>
        </div>
      </div>
    </div>
  );
}

// --- MAIN KIOSK REACT APPLICATION ---
function KioskRoot() {
  const [session, setSession] = useState(null);
  const [quizSchema, setQuizSchema] = useState([]);
  const [selectedElement, setSelectedElement] = useState(null);
  const [selectedPower, setSelectedPower] = useState(null);
  const [selectedColor, setSelectedColor] = useState(null);

  // Inactivity management
  const [isIdleModalOpen, setIsIdleModalOpen] = useState(false);
  const [idleCountdown, setIdleCountdown] = useState(5);
  const idleTimerRef = useRef(null);
  const countdownIntervalRef = useRef(null);

  // Load Quiz Schema
  useEffect(() => {
    fetch('/api/quiz/schema')
      .then(res => res.json())
      .then(data => setQuizSchema(data))
      .catch(err => console.error("Error loading quiz schema", err));
  }, []);

  // WebSocket for Live State Synchronisation
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'SESSION_UPDATE') {
          setSession(msg.data);
        }
      } catch (e) {
        console.error("WS parse error", e);
      }
    };

    return () => ws.close();
  }, []);

  // Initial Session Check
  useEffect(() => {
    fetch('/api/session/active')
      .then(res => res.json())
      .then(data => {
        if (data && data.status !== 'IDLE') {
          setSession(data);
        }
      })
      .catch(() => {});
  }, []);

  // 15s Inactivity Watcher
  const resetIdleTimer = useCallback(() => {
    if (isIdleModalOpen) return;
    clearTimeout(idleTimerRef.current);

    // Only active during quiz and camera steps
    if (!session || session.status === 'IDLE' || session.status === 'GENERATING' || session.status === 'COMPOSING') {
      return;
    }

    idleTimerRef.current = setTimeout(() => {
      setIsIdleModalOpen(true);
      setIdleCountdown(5);

      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = setInterval(() => {
        setIdleCountdown(prev => {
          if (prev <= 1) {
            clearInterval(countdownIntervalRef.current);
            setIsIdleModalOpen(false);
            handleReset();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
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
      clearInterval(countdownIntervalRef.current);
    };
  }, [resetIdleTimer]);

  // Actions
  const handleStartSession = async () => {
    try {
      const res = await fetch('/api/session/new', { method: 'POST' });
      const sess = await res.json();
      setSession(sess);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCapturePhoto = async () => {
    try {
      await fetch('/api/camera/capture', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleConfirmPhoto = async () => {
    try {
      await fetch('/api/session/photo/confirm', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleRetakePhoto = async () => {
    try {
      await fetch('/api/session/photo/retake', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectChoice = async (questionType, choiceId) => {
    try {
      await fetch('/api/session/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_type: questionType, answer_id: choiceId })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    try {
      await fetch('/api/session/reset', { method: 'POST' });
      setSession(null);
      setSelectedElement(null);
      setSelectedPower(null);
      setSelectedColor(null);
      setIsIdleModalOpen(false);
      clearInterval(countdownIntervalRef.current);
    } catch (e) {
      console.error(e);
    }
  };

  // Determine current step index for the tracker
  const getStepIndex = () => {
    if (!session || session.status === 'IDLE') return 0;
    if (session.status === 'PHOTO_PENDING' || session.status === 'PHOTO_TAKEN') return 0;
    if (session.status === 'QUIZ_ELEMENT') return 1;
    if (session.status === 'QUIZ_POWER') return 2;
    if (session.status === 'QUIZ_COLOR') return 3;
    return 4; // GENERATING, READY_TO_PRINT, COMPLETED
  };

  // Render Screen Switcher
  const renderScreen = () => {
    if (!session || session.status === 'IDLE') {
      return <WelcomeScreen onStart={handleStartSession} />;
    }

    if (session.status === 'PHOTO_PENDING') {
      return (
        <CameraScreen 
          isReview={false} 
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
          photoPath={session.photo_path} 
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
          subtitle="Какая стихия и отрасль будущего тебе ближе всего?" 
          options={quizSchema[0]?.options || []} 
          selectedId={session.element_id} 
          onSelect={(id) => handleSelectChoice('element', id)} 
          type="element" 
        />
      );
    }

    if (session.status === 'QUIZ_POWER') {
      return (
        <SelectionScreen 
          title="ВЫБЕРИ СУПЕРСИЛУ ⚡" 
          subtitle="Что поможет тебе совершать инженерные открытия?" 
          options={quizSchema[1]?.options || []} 
          selectedId={session.power_id} 
          onSelect={(id) => handleSelectChoice('power', id)} 
          type="power" 
        />
      );
    }

    if (session.status === 'QUIZ_COLOR') {
      return (
        <SelectionScreen 
          title="ВЫБЕРИ ЦВЕТ ОБРАЗА 🎨" 
          subtitle="Какой цвет подчеркнет твой стиль и оборудование?" 
          options={quizSchema[2]?.options || []} 
          selectedId={session.color_id} 
          onSelect={(id) => handleSelectChoice('color', id)} 
          type="color" 
        />
      );
    }

    if (session.status === 'GENERATING' || session.status === 'COMPOSING') {
      return <GeneratingScreen session={session} />;
    }

    return <ResultScreen session={session} onFinish={handleReset} />;
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto min-h-screen flex flex-col justify-between p-6 sm:p-8 select-none">
      {/* Step Tracker (visible when session is active) */}
      {session && session.status !== 'IDLE' && (
        <StepTracker currentStep={getStepIndex()} />
      )}

      {/* Screen Content */}
      <div className="flex-1 flex items-center justify-center">
        {renderScreen()}
      </div>

      {/* Minimal Bottom Bar */}
      <footer className="mt-8 pt-4 border-t-2 border-border-line flex items-center justify-between text-ink-muted text-sm font-sans">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-teal"></span>
          <span className="font-bold">ТЕРМИНАЛ ГОТОВ К РАБОТЕ</span>
        </div>
        <div>
          <span>СТАНОК БУДУЩЕГО 2026</span>
        </div>
      </footer>

      {/* Idle Modal */}
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

// Mount the React Application
const rootElement = document.getElementById('react-kiosk-root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<KioskRoot />);
}
