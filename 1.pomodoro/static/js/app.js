/* ─────────────────────────────────────────────
   Pomodoro Timer – Frontend JS
   ───────────────────────────────────────────── */

// ─── State ───────────────────────────────────
const MODES = {
  pomodoro:   { label: 'ポモドーロ',  minutes: 25 },
  shortBreak: { label: '短い休憩',    minutes: 5  },
  longBreak:  { label: '長い休憩',    minutes: 15 },
};

let currentMode   = 'pomodoro';
let totalSeconds  = MODES.pomodoro.minutes * 60;
let remainSeconds = totalSeconds;
let running       = false;
let timerId       = null;
let sessionCount  = 0;
let prevLevel     = 1;

// Chart.js インスタンス
let statsChart = null;
let chartMode  = 'week'; // 'week' | 'month'

// ─── DOM refs ────────────────────────────────
const timerDisplay  = document.getElementById('timerDisplay');
const startBtn      = document.getElementById('startBtn');
const resetTimerBtn = document.getElementById('resetTimerBtn');
const sessionCountEl= document.getElementById('sessionCount');
const streakDisplay = document.getElementById('streakDisplay');
const todayDisplay  = document.getElementById('todayDisplay');
const weeklyDisplay = document.getElementById('weeklyDisplay');
const levelCircle   = document.getElementById('levelCircle');
const levelTitle    = document.getElementById('levelTitle');
const xpBar         = document.getElementById('xpBar');
const xpText        = document.getElementById('xpText');
const totalXpDisplay= document.getElementById('totalXpDisplay');
const totalPomodorosDisplay = document.getElementById('totalPomodorosDisplay');
const badgeGrid     = document.getElementById('badgeGrid');
const statsSummary  = document.getElementById('statsSummary');
const overlay       = document.getElementById('completeOverlay');
const xpGainText    = document.getElementById('xpGainText');
const levelUpMsg    = document.getElementById('levelUpMsg');
const newBadgesList = document.getElementById('newBadgesList');
const overlayCloseBtn = document.getElementById('overlayCloseBtn');

// ─── Level titles ─────────────────────────────
const LEVEL_TITLES = [
  '見習いフォーカス',    // level 1
  '集中の旅人',          // level 2
  'ポモドーロ戦士',      // level 3
  '集中の達人',          // level 4
  '時間の守護者',        // level 5
  '深集中の騎士',        // level 6
  'フロー状態の賢者',    // level 7
  '生産性の英雄',        // level 8
  '究極の集中者',        // level 9
  'ポモドーロ・マスター', // level 10+
];
function getLevelTitle(level) {
  const index = Math.min(level - 1, LEVEL_TITLES.length - 1);
  return LEVEL_TITLES[index] || `レベル${level}の達人`;
}

// ─── Timer ───────────────────────────────────
function formatTime(secs) {
  const m = String(Math.floor(secs / 60)).padStart(2, '0');
  const s = String(secs % 60).padStart(2, '0');
  return `${m}:${s}`;
}

function updateTimerDisplay() {
  timerDisplay.textContent = formatTime(remainSeconds);
  document.title = `${formatTime(remainSeconds)} – 🍅 ポモドーロ`;
}

function setMode(mode) {
  currentMode   = mode;
  totalSeconds  = MODES[mode].minutes * 60;
  remainSeconds = totalSeconds;
  stopTimer();
  updateTimerDisplay();
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  const btnId = mode === 'pomodoro' ? 'pomodoroBtn'
    : mode === 'shortBreak' ? 'shortBreakBtn' : 'longBreakBtn';
  document.getElementById(btnId).classList.add('active');
}

function startTimer() {
  if (running) return;
  running = true;
  startBtn.textContent = '⏸ 一時停止';
  timerId = setInterval(() => {
    remainSeconds--;
    updateTimerDisplay();
    if (remainSeconds <= 0) {
      clearInterval(timerId);
      running = false;
      startBtn.textContent = '▶ スタート';
      if (currentMode === 'pomodoro') {
        sessionCount++;
        sessionCountEl.textContent = `セッション: ${sessionCount}`;
        onPomodoroComplete();
      }
    }
  }, 1000);
}

function pauseTimer() {
  clearInterval(timerId);
  running = false;
  startBtn.textContent = '▶ スタート';
}

function stopTimer() {
  clearInterval(timerId);
  running = false;
  startBtn.textContent = '▶ スタート';
}

function resetTimer() {
  stopTimer();
  remainSeconds = totalSeconds;
  updateTimerDisplay();
}

startBtn.addEventListener('click', () => {
  running ? pauseTimer() : startTimer();
});
resetTimerBtn.addEventListener('click', resetTimer);

document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const minutes = parseInt(btn.dataset.minutes, 10);
    const mode = minutes === 25 ? 'pomodoro' : minutes === 5 ? 'shortBreak' : 'longBreak';
    setMode(mode);
  });
});

// ─── API calls ───────────────────────────────
async function fetchState() {
  const res = await fetch('/api/state');
  return res.json();
}

async function postComplete() {
  const res = await fetch('/api/complete', { method: 'POST' });
  return res.json();
}

// ─── UI updaters ─────────────────────────────
function updateHUD(state) {
  streakDisplay.textContent = `🔥 ${state.streak}日連続`;
  todayDisplay.textContent  = `📅 今日: ${state.today_count}回`;
  weeklyDisplay.textContent = `📊 今週: ${state.weekly_total}回`;

  levelCircle.textContent = `Lv.${state.level}`;
  levelTitle.textContent  = getLevelTitle(state.level);
  const pct = state.xp_needed > 0 ? Math.round(state.current_xp / state.xp_needed * 100) : 0;
  xpBar.style.width = `${pct}%`;
  xpText.textContent = `${state.current_xp} / ${state.xp_needed} XP`;
  totalXpDisplay.textContent = `累計 XP: ${state.total_xp}`;
  totalPomodorosDisplay.textContent = `累計ポモドーロ: ${state.total_pomodoros}回`;
}

function renderBadges(badges) {
  badgeGrid.innerHTML = '';
  badges.forEach(b => {
    const el = document.createElement('div');
    el.className = `badge-item ${b.earned ? 'earned' : 'locked'}`;
    el.innerHTML = `
      <div class="badge-icon">${b.icon}</div>
      <div class="badge-name">${b.name}</div>
      <div class="badge-desc">${b.description}</div>
    `;
    badgeGrid.appendChild(el);
  });
}

function renderStats(state) {
  const data = chartMode === 'week' ? state.weekly_chart : state.monthly_chart;
  const labels = data.labels;
  const counts = data.counts;
  const total  = counts.reduce((a, b) => a + b, 0);
  const max    = Math.max(...counts, 1);
  const avg    = counts.length ? (total / counts.length).toFixed(1) : 0;
  const activeDays = counts.filter(c => c > 0).length;

  statsSummary.innerHTML = `
    <div class="stat-item">
      <div class="stat-value">${total}</div>
      <div class="stat-label">合計ポモドーロ</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${activeDays}</div>
      <div class="stat-label">活動日数</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${avg}</div>
      <div class="stat-label">1日平均</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${max}</div>
      <div class="stat-label">最大/日</div>
    </div>
  `;

  if (statsChart) statsChart.destroy();
  const ctx = document.getElementById('statsChart').getContext('2d');
  statsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'ポモドーロ回数',
        data: counts,
        backgroundColor: counts.map(c => c > 0 ? 'rgba(231,76,60,.8)' : 'rgba(255,255,255,.1)'),
        borderColor: 'rgba(231,76,60,1)',
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8892a4', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { ticks: { color: '#8892a4', stepSize: 1 }, grid: { color: 'rgba(255,255,255,.05)' }, beginAtZero: true },
      },
    },
  });
}

// ─── Pomodoro complete flow ───────────────────
async function onPomodoroComplete() {
  const result = await postComplete();

  xpGainText.textContent = `+${result.xp_gained} XP`;
  if (result.level > prevLevel) {
    levelUpMsg.textContent = `🎊 レベルアップ！ Lv.${result.level} 「${getLevelTitle(result.level)}」`;
  } else {
    levelUpMsg.textContent = '';
  }
  prevLevel = result.level;

  newBadgesList.innerHTML = '';
  (result.new_badges || []).forEach(b => {
    const chip = document.createElement('div');
    chip.className = 'new-badge-chip';
    chip.textContent = `${b.icon} ${b.name}`;
    newBadgesList.appendChild(chip);
  });

  overlay.classList.add('visible');

  // 状態更新
  const state = await fetchState();
  updateHUD(state);
  renderBadges(state.badges);
  renderStats(state);
}

overlayCloseBtn.addEventListener('click', () => {
  overlay.classList.remove('visible');
});

// ─── Chart tab ───────────────────────────────
document.getElementById('weekTabBtn').addEventListener('click', async () => {
  chartMode = 'week';
  document.getElementById('weekTabBtn').classList.add('active');
  document.getElementById('monthTabBtn').classList.remove('active');
  const state = await fetchState();
  renderStats(state);
});

document.getElementById('monthTabBtn').addEventListener('click', async () => {
  chartMode = 'month';
  document.getElementById('monthTabBtn').classList.add('active');
  document.getElementById('weekTabBtn').classList.remove('active');
  const state = await fetchState();
  renderStats(state);
});

// ─── Init ─────────────────────────────────────
(async () => {
  const state = await fetchState();
  prevLevel = state.level;
  updateHUD(state);
  renderBadges(state.badges);
  renderStats(state);
  updateTimerDisplay();
})();
