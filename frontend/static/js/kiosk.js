// Clean Geometric Vector Icons for Industry 2026 Touchscreen
const SVG_ICONS = {
  // Elements
  "space": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>`,
  "atom": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M20.2 20.2c2.4-2.4 2.4-6.3 0-8.7s-6.3-2.4-8.7 0-2.4 6.3 0 8.7 6.3 2.4 8.7 0Z"/><path d="M3.8 3.8c-2.4 2.4-2.4 6.3 0 8.7s6.3 2.4 8.7 0 2.4-6.3 0-8.7-6.3-2.4-8.7 0Z"/><path d="M20.2 3.8c2.4 2.4 2.4 6.3 0 8.7s-6.3 2.4-8.7 0-2.4-6.3 0-8.7 6.3-2.4 8.7 0Z"/><path d="M3.8 20.2c-2.4-2.4-2.4-6.3 0-8.7s6.3-2.4 8.7 0 2.4 6.3 0 8.7-6.3 2.4-8.7 0Z"/></svg>`,
  "robots": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><circle cx="9" cy="10" r="1.5"/><circle cx="15" cy="10" r="1.5"/><path d="M9 15h6"/><path d="M12 4V2"/><path d="M2 12h2"/><path d="M20 12h2"/></svg>`,
  "medicine": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 15 5 5 13-13-5-5-13 13Z"/><path d="m9 8 7 7"/><path d="m14.5 3.5 3 3"/><path d="m3.5 14.5 3 3"/></svg>`,
  "metal": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>`,

  // Superpowers
  "precision": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M2 12h2"/><path d="M20 12h2"/></svg>`,
  "speed": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>`,
  "power": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.01"/></svg>`,
  "mind": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04"/></svg>`,
  "care": `<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`
};

class KioskApp {
  constructor() {
    this.currentScreen = 'screen-welcome';
    this.activeSession = null;
    this.quizSchema = [];
    this.ws = null;

    // Idle Inactivity Timer (15s idle -> 5s countdown modal -> return to start)
    this.idleTimeoutMs = 15000;
    this.countdownDuration = 5;
    this.idleTimer = null;
    this.countdownInterval = null;
    this.currentCountdown = 5;
    this.isModalOpen = false;

    this.init();
  }

  async init() {
    this.bindEvents();
    this.bindIdleWatcher();
    await this.loadQuizSchema();
    this.initWebSocket();
    this.checkCurrentSession();
  }

  bindEvents() {
    document.getElementById('btn-start-session')?.addEventListener('click', () => this.startNewSession());
    document.getElementById('btn-take-photo')?.addEventListener('click', () => this.takeUsbPhoto());
    document.getElementById('btn-confirm-photo')?.addEventListener('click', () => this.confirmPhoto());
    document.getElementById('btn-retake-photo')?.addEventListener('click', () => this.retakePhoto());
    document.getElementById('btn-finish-session')?.addEventListener('click', () => this.resetToWelcome());

    // Idle Modal buttons
    document.getElementById('btn-idle-stay')?.addEventListener('click', () => this.hideIdleModal());
    document.getElementById('btn-idle-leave')?.addEventListener('click', () => {
      this.hideIdleModal();
      this.resetToWelcome();
    });
  }

  bindIdleWatcher() {
    // User touch / pointer interactions reset the 15-second idle timer
    const resetActivity = () => {
      if (!this.isModalOpen) {
        this.resetIdleTimer();
      }
    };

    window.addEventListener('touchstart', resetActivity, { passive: true });
    window.addEventListener('pointerdown', resetActivity, { passive: true });
    window.addEventListener('click', resetActivity, { passive: true });
    window.addEventListener('mousemove', resetActivity, { passive: true });
  }

  resetIdleTimer() {
    clearTimeout(this.idleTimer);

    // Only run idle timer on active quiz/interactive screens (not on welcome and not during AI generation)
    if (this.currentScreen === 'screen-welcome' || this.currentScreen === 'screen-generating') {
      return;
    }

    this.idleTimer = setTimeout(() => {
      this.showIdleModal();
    }, this.idleTimeoutMs);
  }

  showIdleModal() {
    if (this.currentScreen === 'screen-welcome' || this.currentScreen === 'screen-generating') {
      return;
    }

    this.isModalOpen = true;
    this.currentCountdown = this.countdownDuration;
    const modal = document.getElementById('idle-modal');
    const cdVal = document.getElementById('idle-countdown-val');
    
    if (modal) modal.classList.add('active');
    if (cdVal) cdVal.innerText = this.currentCountdown;

    clearInterval(this.countdownInterval);
    this.countdownInterval = setInterval(() => {
      this.currentCountdown--;
      if (cdVal) cdVal.innerText = this.currentCountdown;

      if (this.currentCountdown <= 0) {
        clearInterval(this.countdownInterval);
        this.hideIdleModal();
        this.resetToWelcome();
      }
    }, 1000);
  }

  hideIdleModal() {
    this.isModalOpen = false;
    clearInterval(this.countdownInterval);
    const modal = document.getElementById('idle-modal');
    if (modal) modal.classList.remove('active');
    this.resetIdleTimer();
  }

  async loadQuizSchema() {
    try {
      const res = await fetch('/api/quiz/schema');
      this.quizSchema = await res.json();
      this.renderQuizScreens();
    } catch (e) {
      console.error('Failed to load quiz schema', e);
    }
  }

  renderQuizScreens() {
    // 1. Elements
    const elemGrid = document.getElementById('grid-elements');
    if (elemGrid && this.quizSchema[0]) {
      elemGrid.innerHTML = this.quizSchema[0].options.map(opt => `
        <div class="touch-quiz-card" onclick="kiosk.selectChoice('element', '${opt.id}', this)">
          <div class="touch-card-icon-box">
            ${SVG_ICONS[opt.id] || ''}
          </div>
          <div class="touch-card-title">${opt.name}</div>
          <div class="touch-card-desc">${opt.hint}</div>
        </div>
      `).join('');
    }

    // 2. Powers
    const pwrGrid = document.getElementById('grid-powers');
    if (pwrGrid && this.quizSchema[1]) {
      pwrGrid.innerHTML = this.quizSchema[1].options.map(opt => `
        <div class="touch-quiz-card" onclick="kiosk.selectChoice('power', '${opt.id}', this)">
          <div class="touch-card-icon-box">
            ${SVG_ICONS[opt.id] || ''}
          </div>
          <div class="touch-card-title">${opt.name}</div>
          <div class="touch-card-desc">${opt.hint}</div>
        </div>
      `).join('');
    }

    // 3. Colors
    const colGrid = document.getElementById('grid-colors');
    if (colGrid && this.quizSchema[2]) {
      colGrid.innerHTML = this.quizSchema[2].options.map(opt => `
        <div class="touch-quiz-card touch-color-card" onclick="kiosk.selectChoice('color', '${opt.id}', this)">
          <div class="touch-color-circle" style="background: ${opt.hex}; box-shadow: 0 0 20px ${opt.hex}66;"></div>
          <div class="touch-card-title" style="color: ${opt.hex};">${opt.name}</div>
        </div>
      `).join('');
    }
  }

  updateTracker(stepIndex) {
    for (let i = 0; i < 5; i++) {
      const dot = document.getElementById(`dot-${i}`);
      if (!dot) continue;
      dot.className = 'step-indicator-pill';
      if (i === stepIndex) {
        dot.classList.add('active');
      } else if (i < stepIndex) {
        dot.classList.add('completed');
      }
    }
  }

  initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'SESSION_UPDATE') {
          this.handleSessionUpdate(msg.data);
        }
      } catch (e) {
        console.error('WS parse error', e);
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.initWebSocket(), 2000);
    };
  }

  async checkCurrentSession() {
    try {
      const res = await fetch('/api/session/active');
      const data = await res.json();
      if (data && (data.status === 'PHOTO_PENDING' || data.status === 'PHOTO_TAKEN' || data.status.startsWith('QUIZ_'))) {
        this.handleSessionUpdate(data);
      } else {
        this.showScreen('screen-welcome');
      }
    } catch (e) {
      this.showScreen('screen-welcome');
    }
  }

  showScreen(screenId) {
    document.querySelectorAll('.kiosk-screen').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active');
      this.currentScreen = screenId;
    }
    this.resetIdleTimer();
  }

  handleSessionUpdate(session) {
    this.activeSession = session;
    if (!session || session.status === 'IDLE') {
      this.showScreen('screen-welcome');
      this.updateTracker(0);
      return;
    }

    switch (session.status) {
      case 'IDLE':
        this.showScreen('screen-welcome');
        this.updateTracker(0);
        break;

      case 'PHOTO_PENDING':
        this.showScreen('screen-photo');
        this.setCameraPreviewMode('live');
        this.updateTracker(0);
        break;

      case 'PHOTO_TAKEN':
        this.showScreen('screen-photo');
        this.setCameraPreviewMode('review', session.photo_path);
        this.updateTracker(0);
        break;

      case 'QUIZ_ELEMENT':
        this.showScreen('screen-element');
        this.updateTracker(1);
        break;

      case 'QUIZ_POWER':
        this.showScreen('screen-power');
        this.updateTracker(2);
        break;

      case 'QUIZ_COLOR':
        this.showScreen('screen-color');
        this.updateTracker(3);
        break;

      case 'GENERATING':
      case 'COMPOSING':
        this.showScreen('screen-generating');
        this.updateGeneratingProgress(session);
        this.updateTracker(4);
        break;

      case 'READY_TO_PRINT':
      case 'PRINTING':
      case 'COMPLETED':
        this.showScreen('screen-result');
        this.renderResultScreen(session);
        this.updateTracker(4);
        break;

      case 'ERROR':
        alert('Ошибка: ' + (session.error_message || 'Неизвестная ошибка'));
        this.showScreen('screen-welcome');
        this.updateTracker(0);
        break;
    }
  }

  async startNewSession() {
    try {
      await new Promise(r => setTimeout(r, 300));
      const res = await fetch('/api/session/new', { method: 'POST' });
      const sess = await res.json();
      this.handleSessionUpdate(sess);
    } catch (e) {
      console.error(e);
    }
  }

  setCameraPreviewMode(mode, photoPath = null) {
    const liveImg = document.getElementById('camera-live-stream');
    const reviewImg = document.getElementById('camera-review-img');
    const liveControls = document.getElementById('camera-live-controls');
    const reviewControls = document.getElementById('camera-review-controls');

    if (mode === 'live') {
      liveImg.style.display = 'block';
      liveImg.src = '/api/camera/stream?' + Date.now();
      reviewImg.style.display = 'none';
      liveControls.style.display = 'flex';
      reviewControls.style.display = 'none';
    } else {
      liveImg.style.display = 'none';
      reviewImg.style.display = 'block';
      if (photoPath) {
        const fname = photoPath.split(/[\\/]/).pop();
        reviewImg.src = `/storage/photos/${fname}?t=${Date.now()}`;
      }
      liveControls.style.display = 'none';
      reviewControls.style.display = 'flex';
    }
  }

  async takeUsbPhoto() {
    try {
      await fetch('/api/camera/capture', { method: 'POST' });
    } catch (e) {
      console.error('Error capturing photo', e);
    }
  }

  async confirmPhoto() {
    try {
      await new Promise(r => setTimeout(r, 400));
      await fetch('/api/session/photo/confirm', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  }

  async retakePhoto() {
    try {
      await fetch('/api/session/photo/retake', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  }

  async selectChoice(questionType, choiceId, element) {
    if (this._isTransitioning) return;
    this._isTransitioning = true;

    // Visual selection highlight on tapped card
    if (element) {
      element.style.borderColor = 'var(--accent-cyan)';
      element.style.boxShadow = 'var(--glow-cyan)';
      element.style.transform = 'scale(0.96)';
    }

    // 0.5s deliberate tactile delay so user feels the choice registered
    await new Promise(r => setTimeout(r, 500));

    try {
      await fetch('/api/session/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_type: questionType,
          answer_id: choiceId
        })
      });
    } catch (e) {
      console.error(e);
    } finally {
      this._isTransitioning = false;
    }
  }

  updateGeneratingProgress(session) {
    const bar = document.getElementById('generating-bar-fill');
    const logBox = document.getElementById('ai-generation-logs');
    
    if (session.status === 'GENERATING') {
      bar.style.width = '65%';
      logBox.innerHTML = `
        <div>[01/03] ВХОДНЫЕ ПАРАМЕТРЫ: ${(session.element_name || '').toUpperCase()} / ${(session.power_name || '').toUpperCase()} / ${(session.color_name || '').toUpperCase()}</div>
        <div style="color: var(--accent-cyan); font-weight: 700;">[02/03] СИНТЕЗ НЕЙРОСЕТЕВОГО ОБРАЗА ИНЖЕНЕРА...</div>
        <div style="color: var(--text-muted);">[03/03] ОЖИДАНИЕ СБОРКИ ПАСПОРТА...</div>
      `;
    } else if (session.status === 'COMPOSING') {
      bar.style.width = '90%';
      logBox.innerHTML = `
        <div>[01/03] ВХОДНЫЕ ПАРАМЕТРЫ: ${(session.element_name || '').toUpperCase()} / ${(session.power_name || '').toUpperCase()}</div>
        <div>[02/03] СИНТЕЗ ОБРАЗА ЗАВЕРШЕН [OK]</div>
        <div style="color: var(--accent-cyan); font-weight: 700;">[03/03] РЕНДЕРИНГ ПАСПОРТА 300 DPI И ГЕНЕРАЦИЯ QR...</div>
      `;
    }
  }

  renderResultScreen(session) {
    if (session.final_card_path) {
      const fname = session.final_card_path.split(/[\\/]/).pop();
      document.getElementById('result-card-img').src = `/storage/cards/${fname}?t=${Date.now()}`;
    }

    document.getElementById('result-title').innerText = (session.machine_name || 'Инженер Будущего').toUpperCase();
    document.getElementById('result-power').innerText = `СУПЕРСИЛА // ${(session.power_name || '').toUpperCase()}`;
    document.getElementById('result-desc').innerText = session.machine_desc || '';
    document.getElementById('result-location').innerText = `ПРЕДПРИЯТИЕ: ${session.location || ''}`;
    
    const printBadge = document.getElementById('result-print-status');
    if (session.print_status === 'printed') {
      printBadge.innerText = '● ПАСПОРТ НАПЕЧАТАН НА ПРИНТЕРЕ';
      printBadge.style.color = 'var(--accent-emerald)';
      printBadge.style.borderColor = 'var(--accent-emerald)';
    } else if (session.print_status === 'printing') {
      printBadge.innerText = '● ПЕЧАТЬ НА ФОТОПРИНТЕРЕ...';
      printBadge.style.color = 'var(--accent-gold)';
      printBadge.style.borderColor = 'var(--accent-gold)';
    } else {
      printBadge.innerText = '● ГОТОВО К ПЕЧАТИ';
      printBadge.style.color = 'var(--accent-cyan)';
      printBadge.style.borderColor = 'var(--accent-cyan)';
    }
  }

  async resetToWelcome() {
    try {
      await fetch('/api/session/reset', { method: 'POST' });
      this.showScreen('screen-welcome');
      this.updateTracker(0);
    } catch (e) {
      console.error(e);
    }
  }
}

const kiosk = new KioskApp();
