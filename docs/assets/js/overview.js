/* ============================================
   FITNESS DASHBOARD — OVERVIEW PAGE
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  const D = FITNESS_DATA;

  // Update header YTD stats
  document.getElementById('ytd-distance').textContent = D.athlete.ytd.distance.toLocaleString();
  document.getElementById('ytd-hours').textContent = D.athlete.ytd.hours.toFixed(1);
  document.getElementById('ytd-tss').textContent = D.athlete.ytd.tss.toLocaleString();

  // Update metric cards
  document.getElementById('ctl-value').textContent = D.fitness.ctl.toFixed(1);
  document.getElementById('atl-value').textContent = D.fitness.atl.toFixed(1);
  document.getElementById('tsb-value').textContent = (D.fitness.tsb > 0 ? '+' : '') + D.fitness.tsb.toFixed(1);
  document.getElementById('hrv-value').textContent = D.fitness.hrv;
  document.getElementById('sleep-value').textContent = D.fitness.sleep.toFixed(1);
  document.getElementById('rhr-value').textContent = D.fitness.resting_hr;

  // Build charts
  buildFitnessChart('fitnessChart', D.fitness_trend);
  buildTSSChart('tssChart', D.weekly_tss);
  buildWellnessChart('hrvChart', D.wellness_trend.dates, D.wellness_trend.hrv, '#a855f7', 'HRV');
  buildWellnessChart('sleepChart', D.wellness_trend.dates, D.wellness_trend.sleep, '#ffd600', 'Sleep');
  buildPowerBestsChart('powerBestsChart', D.power_bests);
  buildPaceBestsChart('paceBestsChart', D.pace_bests);

  // Render activity cards
  renderActivityCards(D.recent_activities);

  // Render calendar
  renderCalendar(D.calendar);

  // Render heatmap
  renderHeatmap(D.heatmap);

  // Render bests tables
  renderPowerBests(D.power_bests);
  renderPaceBests(D.pace_bests);

  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.dataset.tab;
      document.querySelectorAll('.bests-container').forEach(c => c.classList.add('hidden'));
      document.getElementById(target).classList.remove('hidden');
    });
  });
});

// ============================================
// ACTIVITY CARDS
// ============================================
function getTypeInfo(type) {
  const map = {
    'VirtualRide': { label: 'Cycling', colorClass: 'type-ride', dotClass: 'dot-ride', icon: '⬡' },
    'Ride':        { label: 'Cycling', colorClass: 'type-ride', dotClass: 'dot-ride', icon: '⬡' },
    'VirtualRun':  { label: 'Running', colorClass: 'type-run',  dotClass: 'dot-run',  icon: '▷' },
    'Run':         { label: 'Running', colorClass: 'type-run',  dotClass: 'dot-run',  icon: '▷' },
    'Rowing':      { label: 'Rowing',  colorClass: 'type-row',  dotClass: 'dot-row',  icon: '⊕' },
    'Workout':     { label: 'Workout', colorClass: 'type-workout', dotClass: 'dot-workout', icon: '◎' }
  };
  return map[type] || { label: type, colorClass: 'type-default', dotClass: 'dot-default', icon: '○' };
}

function renderActivityCards(activities) {
  const container = document.getElementById('activity-cards');
  if (!container) return;

  const totalDistance = activities.reduce((s, a) => s + (a.distance || 0), 0) / 1000;
  const totalDuration = activities.reduce((s, a) => s + (a.duration || 0), 0) / 3600;
  document.getElementById('week-summary').textContent =
    `${activities.length} activities · ${totalDistance.toFixed(0)} km · ${totalDuration.toFixed(1)} hrs`;

  container.innerHTML = activities.map(a => {
    const info = getTypeInfo(a.type);
    const isPower = a.avg_power;
    const isPace  = a.avg_pace && !a.avg_power;

    const stat1 = isPower
      ? { value: `${a.avg_power}W`, label: 'Avg Power' }
      : isPace
        ? { value: formatPace(a.avg_pace), label: 'Avg Pace' }
        : { value: a.avg_hr ? `${a.avg_hr}` : '—', label: 'Avg HR' };

    const stat2 = a.distance
      ? { value: (a.distance / 1000).toFixed(1), label: 'km' }
      : { value: formatDuration(a.duration), label: 'Duration' };

    return `
      <div class="activity-card" data-id="${a.id}">
        <div class="activity-card-type ${info.colorClass}">
          <span class="type-dot ${info.dotClass}"></span>
          ${info.label}
        </div>
        <div class="activity-card-name">${a.name}</div>
        <div class="activity-card-stats">
          <div class="activity-stat">
            <span class="activity-stat-value">${formatDuration(a.duration)}</span>
            <span class="activity-stat-label">Duration</span>
          </div>
          <div class="activity-stat">
            <span class="activity-stat-value">${stat2.value}</span>
            <span class="activity-stat-label">${stat2.label}</span>
          </div>
          <div class="activity-stat">
            <span class="activity-stat-value">${stat1.value}</span>
            <span class="activity-stat-label">${stat1.label}</span>
          </div>
          <div class="activity-stat">
            <span class="activity-stat-value">${a.avg_hr || '—'}</span>
            <span class="activity-stat-label">Avg HR</span>
          </div>
        </div>
        <div class="activity-card-date">${a.date}</div>
      </div>`;
  }).join('');
}

// ============================================
// CALENDAR
// ============================================
function renderCalendar(weeks) {
  const grid = document.getElementById('calendar-grid');
  if (!grid) return;

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  // Header row
  let html = '<div class="cal-header"></div>';
  days.forEach(d => { html += `<div class="cal-header">${d}</div>`; });

  // Week rows
  weeks.forEach((week, wi) => {
    html += `
      <div class="cal-week-label">W${wi + 1}</div>`;
    week.days.forEach(day => {
      const dotColor = day.type === 'ride' ? '#00e5ff' : day.type === 'run' ? '#00ff87' : day.type === 'row' ? '#a855f7' : '#ff6b2b';
      html += `
        <div class="cal-day ${day.hasActivity ? 'has-activity' : ''}">
          <div class="cal-day-num">${day.date}</div>
          ${day.hasActivity ? `<span class="cal-activity-dot" style="background:${dotColor}"></span>` : ''}
        </div>`;
    });
  });

  grid.innerHTML = html;
}

// ============================================
// HEATMAP
// ============================================
function renderHeatmap(cells) {
  const grid = document.getElementById('heatmap-grid');
  if (!grid) return;

  grid.innerHTML = cells.map(c =>
    `<div class="heatmap-cell" data-level="${c.level}" title="${c.date} · Level ${c.level}"></div>`
  ).join('');
}

// ============================================
// BESTS TABLES
// ============================================
function renderPowerBests(bests) {
  const grid = document.getElementById('power-bests-grid');
  if (!grid) return;

  grid.innerHTML = bests.map(b => `
    <div class="best-row">
      <span class="best-duration">${b.label}</span>
      <span class="best-value">${b.value}W</span>
    </div>`
  ).join('');
}

function renderPaceBests(bests) {
  const grid = document.getElementById('pace-bests-grid');
  if (!grid) return;

  grid.innerHTML = bests.map(b => {
    const distKm = parseFloat(b.label) || (b.label === 'Marathon' ? 42.195 : 1);
    const secPerKm = b.value / distKm;
    const m = Math.floor(secPerKm / 60);
    const s = Math.floor(secPerKm % 60);
    return `
      <div class="best-row">
        <span class="best-duration">${b.label}</span>
        <span class="best-value">${m}:${String(s).padStart(2,'0')}/km</span>
      </div>`;
  }).join('');
}
