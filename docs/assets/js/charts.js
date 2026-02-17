/* =========================================================
   CALENDAR + HEATMAP RENDERERS
   ADD THIS BLOCK INSIDE charts.js (near bottom, before return)
========================================================= */


/* ============================================
   TRAINING CALENDAR (last 28 days)
============================================ */

function renderCalendar(activities) {

  const container = document.getElementById('calendar-wrap');
  if (!container) return;

  if (!activities || activities.length === 0) {
    container.innerHTML = `<div class="calendar-empty">No training data</div>`;
    return;
  }

  const last28 = activities.slice(-28);

  container.innerHTML = last28.map(a => {

    const tss = a.tss || 0;

    let level = 'rest';
    if (tss >= 120) level = 'huge';
    else if (tss >= 80) level = 'hard';
    else if (tss >= 40) level = 'medium';
    else if (tss > 0) level = 'easy';

    return `
      <div class="calendar-day ${level}">
        <div class="calendar-date">${a.date.slice(5)}</div>
        <div class="calendar-tss">${tss}</div>
      </div>
    `;

  }).join('');
}


/* ============================================
   1 YEAR HEATMAP
============================================ */

function renderHeatmap(heatmapData) {

  const container = document.getElementById('heatmap-inner');
  if (!container) return;

  if (!heatmapData || heatmapData.length === 0) {
    container.innerHTML = `<div class="heatmap-empty">No heatmap data</div>`;
    return;
  }

  const max = Math.max(...heatmapData.map(d => d.value), 1);

  container.innerHTML = heatmapData.map(d => {

    const intensity = d.value / max;

    let opacity = 0;

    if (intensity > 0)
      opacity = Math.max(0.15, intensity);

    return `
      <div class="heat-cell"
        title="${d.date} · ${d.value} TSS"
        style="background: rgba(0,255,140,${opacity})">
      </div>
    `;

  }).join('');
}
