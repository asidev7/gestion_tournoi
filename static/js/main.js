/* ═══════════════════════════════════════════
   ADEIB U26 — Main JS  (Tailwind version)
═══════════════════════════════════════════ */

/* ── GOAL SOUND (Web Audio API) ── */
function playGoalSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Crowd roar: layered oscillators
    [200, 300, 400, 500].forEach((freq, i) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = 'sawtooth';
      o.frequency.setValueAtTime(freq, ctx.currentTime);
      o.frequency.exponentialRampToValueAtTime(freq * 0.5, ctx.currentTime + 1.2);
      g.gain.setValueAtTime(0.08, ctx.currentTime + i * 0.04);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.4);
      o.start(ctx.currentTime + i * 0.04);
      o.stop(ctx.currentTime + 1.4);
    });

    // Whistle burst
    setTimeout(() => {
      const w = ctx.createOscillator();
      const wg = ctx.createGain();
      w.connect(wg); wg.connect(ctx.destination);
      w.type = 'sine';
      w.frequency.setValueAtTime(1400, ctx.currentTime);
      w.frequency.linearRampToValueAtTime(2000, ctx.currentTime + 0.1);
      w.frequency.linearRampToValueAtTime(1600, ctx.currentTime + 0.25);
      wg.gain.setValueAtTime(0.5, ctx.currentTime);
      wg.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
      w.start(ctx.currentTime); w.stop(ctx.currentTime + 0.35);
    }, 300);
  } catch(e) {}
}

/* ── CONFETTI BURST ── */
const CONFETTI_COLORS = ['#CE1126','#FCD116','#006233','#fff','#ff6b35','#4ecdc4','#ffe66d'];
function launchConfetti(count = 80) {
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    const size = 6 + Math.random() * 10;
    el.style.cssText = `
      left:${Math.random()*100}vw;
      top:0;
      width:${size}px;
      height:${size}px;
      background:${CONFETTI_COLORS[Math.floor(Math.random()*CONFETTI_COLORS.length)]};
      border-radius:${Math.random()>.5?'50%':'2px'};
      --dur:${1.8+Math.random()*1.8}s;
      --delay:${Math.random()*.8}s;
    `;
    document.body.appendChild(el);
    el.addEventListener('animationend', () => el.remove());
  }
}

/* ── FULL SCREEN GOAL CELEBRATION ── */
function showGoalCelebration(home, away, scorer, minute, homeScore, awayScore) {
  playGoalSound();
  launchConfetti(90);

  const overlay = document.createElement('div');
  overlay.className = 'goal-overlay';
  overlay.innerHTML = `
    <div class="goal-card">
      <div class="goal-ball">⚽</div>
      <div class="goal-but-text">BUT !</div>
      <div class="goal-scorer-name">${scorer} <span style="color:#aaa;font-weight:600;font-size:.85em">${minute}'</span></div>
      <div class="goal-match-info">${home} <span style="color:#CE1126;font-weight:900">vs</span> ${away}</div>
      <div class="goal-score-badge">${homeScore} – ${awayScore}</div>
    </div>`;
  document.body.appendChild(overlay);

  // Auto-dismiss after 3.8s
  setTimeout(() => {
    overlay.classList.add('hiding');
    overlay.addEventListener('animationend', () => overlay.remove(), { once: true });
  }, 3800);

  // Also show the corner toast
  showGoalToast(home, away, scorer, minute, homeScore, awayScore);
}

/* ── CORNER TOAST (small, stays after overlay) ── */
function showGoalToast(home, away, scorer, minute, homeScore, awayScore) {
  const toast = document.createElement('div');
  toast.className = 'goal-toast';
  toast.innerHTML = `
    <div class="goal-toast-inner">
      <div class="goal-toast-icon">⚽</div>
      <div>
        <div class="goal-toast-title">But !</div>
        <div class="goal-toast-scorer">${scorer} <span style="opacity:.6;font-size:.8em">${minute}'</span></div>
        <div class="goal-toast-match">${home} <strong>${homeScore}–${awayScore}</strong> ${away}</div>
      </div>
    </div>`;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 450);
  }, 5500);
}

/* ── ANIMATE SCORE NUMBER ── */
function flashScore(el) {
  if (!el) return;
  el.classList.remove('score-flash');
  void el.offsetWidth; // reflow
  el.classList.add('score-flash');
  el.addEventListener('animationend', () => el.classList.remove('score-flash'), { once: true });
}

/* ── LIVE SCORE POLLING (homepage / all pages with #liveScoreContainer) ── */
let prevScores = {};

function pollLive() {
  fetch('/api/live-scores/')
    .then(r => r.json())
    .then(data => {
      const container    = document.getElementById('liveScoreContainer');
      const ticker       = document.getElementById('liveTicker');
      const tickerText   = document.getElementById('tickerText');
      const navLiveBadge = document.getElementById('navLiveBadge');

      if (data.matches.length === 0) {
        if (container) container.innerHTML = emptyLive();
        if (ticker) ticker.style.display = 'none';
        if (navLiveBadge) navLiveBadge.style.display = 'none';
        prevScores = {};
        return;
      }

      // Detect new goals
      data.matches.forEach(m => {
        const prev = prevScores[m.id];
        if (prev) {
          if (m.home_score > prev.home_score)
            showGoalCelebration(m.home, m.away, m.home, '?', m.home_score, m.away_score);
          if (m.away_score > prev.away_score)
            showGoalCelebration(m.home, m.away, m.away, '?', m.home_score, m.away_score);
        }
        prevScores[m.id] = { home_score: m.home_score, away_score: m.away_score };
      });

      if (container) container.innerHTML = data.matches.map(m => liveCard(m)).join('');

      if (ticker && tickerText) {
        ticker.style.display = 'flex';
        tickerText.innerHTML = data.matches.map(m =>
          `⚽ ${m.home} <strong>${m.home_score}–${m.away_score}</strong> ${m.away}`
        ).join('&nbsp;&nbsp;|&nbsp;&nbsp;');
      }
      if (navLiveBadge) {
        navLiveBadge.textContent = data.matches.length;
        navLiveBadge.style.display = 'inline-flex';
      }
    }).catch(() => {});
}

function liveCard(m) {
  const homeLogo = m.home_logo
    ? `<img src="${m.home_logo}" class="w-10 h-10 rounded-full object-cover border border-gray-200" alt="">`
    : `<div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 text-xs">⚽</div>`;
  const awayLogo = m.away_logo
    ? `<img src="${m.away_logo}" class="w-10 h-10 rounded-full object-cover border border-gray-200" alt="">`
    : `<div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 text-xs">⚽</div>`;
  return `<a href="/matches/${m.id}/" class="block no-underline">
    <div class="bg-white rounded-xl border-l-4 border-red-500 p-3 mb-2 hover:bg-gray-50 transition-colors">
      <div class="flex items-center justify-between mb-2">
        <span class="live-pill"><span class="live-dot"></span>LIVE</span>
      </div>
      <div class="grid grid-cols-3 items-center gap-2">
        <div class="flex flex-col items-center gap-1">${homeLogo}<span class="text-xs font-bold text-center leading-tight">${m.home}</span></div>
        <div class="text-center"><span class="text-2xl font-black text-red-600 tracking-widest live-score-number">${m.home_score}–${m.away_score}</span></div>
        <div class="flex flex-col items-center gap-1">${awayLogo}<span class="text-xs font-bold text-center leading-tight">${m.away}</span></div>
      </div>
    </div>
  </a>`;
}

function emptyLive() {
  return `<div class="bg-white rounded-xl border border-gray-100 p-6 text-center text-gray-400 text-sm">
    <div class="text-3xl mb-2">📡</div>Aucun match en direct
  </div>`;
}

/* ── MATCH DETAIL LIVE POLLING ── */
let prevDetailScores = { home: null, away: null };

function pollMatchDetail(matchId, homeTeam, awayTeam) {
  fetch(`/api/matches/${matchId}/goals/`)
    .then(r => r.json())
    .then(d => {
      const homeEl  = document.getElementById('detail-home-score');
      const awayEl  = document.getElementById('detail-away-score');
      const goalLog = document.getElementById('detail-goal-log');

      // Score changed?
      if (prevDetailScores.home !== null) {
        if (d.home_score > prevDetailScores.home) {
          flashScore(homeEl);
          showGoalCelebration(homeTeam, awayTeam, homeTeam, '?', d.home_score, d.away_score);
        }
        if (d.away_score > prevDetailScores.away) {
          flashScore(awayEl);
          showGoalCelebration(homeTeam, awayTeam, awayTeam, '?', d.home_score, d.away_score);
        }
      }
      prevDetailScores = { home: d.home_score, away: d.away_score };

      // Update score
      if (homeEl) homeEl.textContent = d.home_score;
      if (awayEl) awayEl.textContent = d.away_score;

      // Update goal log
      if (goalLog && d.goals) {
        goalLog.innerHTML = d.goals.length === 0
          ? `<div class="text-center py-8 text-gray-400 text-sm"><div class="text-3xl mb-2">⚽</div>Aucun but</div>`
          : d.goals.map(g => `
            <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-50 last:border-b-0 text-sm goal-row-new">
              ${g.team === homeTeam
                ? `<div class="flex-1 text-right font-bold">${g.player}${g.is_penalty?' <span class="text-xs text-gray-400">(P)</span>':''}${g.is_own_goal?' <span class="text-xs text-red-400">(CSC)</span>':''}</div>
                   <div class="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-black shrink-0" style="background:#006233">${g.minute}'</div>
                   <div class="flex-1"></div>`
                : `<div class="flex-1"></div>
                   <div class="w-9 h-9 rounded-full flex items-center justify-center bg-gray-100 text-gray-600 text-xs font-black shrink-0">${g.minute}'</div>
                   <div class="flex-1 font-bold">${g.player}${g.is_penalty?' <span class="text-xs text-gray-400">(P)</span>':''}${g.is_own_goal?' <span class="text-xs text-red-400">(CSC)</span>':''}</div>`
              }
              <span class="text-base shrink-0">⚽</span>
            </div>`).join('');
      }

      // Auto-stop if finished
      if (d.status === 'FINISHED') clearInterval(window._matchPollInterval);
    }).catch(() => {});
}

/* ── AUTO-DISMISS ALERTS ── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.auto-dismiss').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Active nav
  const path = window.location.pathname;
  document.querySelectorAll('[data-nav]').forEach(a => {
    const href = a.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) a.classList.add('nav-active');
    if (href === '/' && path === '/') a.classList.add('nav-active');
  });

  // Sidebar active
  document.querySelectorAll('[data-sidebar]').forEach(a => {
    const href = a.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/admin-panel/') a.classList.add('sidebar-active');
    if (href === '/admin-panel/' && path === '/admin-panel/') a.classList.add('sidebar-active');
  });

  // Mobile sidebar
  const toggle  = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('adminSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('-translate-x-full');
      overlay && overlay.classList.toggle('hidden');
    });
    overlay && overlay.addEventListener('click', () => {
      sidebar.classList.add('-translate-x-full');
      overlay.classList.add('hidden');
    });
  }

  // Mobile nav
  document.getElementById('mobileToggle')?.addEventListener('click', () => {
    document.getElementById('mobileMenu')?.classList.toggle('hidden');
  });

  // Prediction radio
  document.querySelectorAll('.pred-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.pred-option').forEach(o => o.classList.remove('pred-selected'));
      opt.classList.add('pred-selected');
      opt.querySelector('input[type=radio]')?.click();
    });
    if (opt.querySelector('input[type=radio]')?.checked) opt.classList.add('pred-selected');
  });

  // Goals bar animation
  document.querySelectorAll('[data-bar]').forEach(el => {
    const w = el.getAttribute('data-bar');
    setTimeout(() => { el.style.width = w + '%'; }, 200);
  });

  // Confirm delete
  document.querySelectorAll('.confirm-delete').forEach(f => {
    f.addEventListener('submit', e => { if (!confirm('Confirmer la suppression ?')) e.preventDefault(); });
  });

  // Homepage live polling
  if (document.getElementById('liveScoreContainer') || document.getElementById('liveTicker')) {
    pollLive();
    setInterval(pollLive, 15000);
  }

  // Match detail polling (triggered by inline script in match_detail.html)
});
