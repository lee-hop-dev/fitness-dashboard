/* ============================================
   FITNESS DASHBOARD — CHARTS
   ============================================ */

Chart.defaults.color = '#8891a4';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'DM Mono', monospace";
Chart.defaults.font.size = 11;

const COLORS = {
  accent:  '#00e5ff',
  green:   '#00ff87',
  orange:  '#ff6b2b',
  purple:  '#a855f7',
  yellow:  '#ffd600',
  red:     '#ff3b5c',
  muted:   '#4a5168'
};

function buildGradient(ctx, color, alpha1 = 0.3, alpha2 = 0) {
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  gradient.addColorStop(0, color.replace(')', `,${alpha1})`).replace('rgb', 'rgba'));
  gradient.addColorStop(1, color.replace(')', `,${alpha2})`).replace('rgb', 'rgba'));
  return gradient;
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgb(${r},${g},${b})`;
}

// ============================================
// FITNESS TREND CHART (CTL/ATL/TSB)
// ============================================
function buildFitnessChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = data.map(d => d.date.slice(5)); // MM-DD
  const ctl = data.map(d => d.ctl);
  const atl = data.map(d => d.atl);
  const tsb = data.map(d => d.tsb);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'CTL',
          data: ctl,
          borderColor: COLORS.accent,
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: COLORS.accent
        },
        {
          label: 'ATL',
          data: atl,
          borderColor: COLORS.orange,
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: COLORS.orange
        },
        {
          label: 'TSB',
          data: tsb,
          borderColor: COLORS.green,
          borderWidth: 1.5,
          borderDash: [4, 3],
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: COLORS.green,
          yAxisID: 'yTSB'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#181b22',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { maxTicksLimit: 7 }
        },
        y: {
          position: 'left',
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { maxTicksLimit: 5 }
        },
        yTSB: {
          position: 'right',
          grid: { display: false },
          ticks: { maxTicksLimit: 5, color: COLORS.green }
        }
      }
    }
  });
}

// ============================================
// WEEKLY TSS STACKED BAR
// ============================================
function buildTSSChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.week),
      datasets: [
        {
          label: 'Ride',
          data: data.map(d => d.ride),
          backgroundColor: 'rgba(0,229,255,0.7)',
          borderRadius: 2
        },
        {
          label: 'Run',
          data: data.map(d => d.run),
          backgroundColor: 'rgba(0,255,135,0.7)',
          borderRadius: 2
        },
        {
          label: 'Row',
          data: data.map(d => d.row),
          backgroundColor: 'rgba(168,85,247,0.7)',
          borderRadius: 2
        },
        {
          label: 'Other',
          data: data.map(d => d.other),
          backgroundColor: 'rgba(255,107,43,0.7)',
          borderRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#181b22',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { maxTicksLimit: 8 }
        },
        y: {
          stacked: true,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { maxTicksLimit: 4 }
        }
      }
    }
  });
}

// ============================================
// HRV / SLEEP LINE CHARTS
// ============================================
function buildWellnessChart(canvasId, labels, data, color, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: color,
        borderWidth: 2,
        fill: true,
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx: c, chartArea } = chart;
          if (!chartArea) return 'transparent';
          const gradient = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          const rgb = hexToRgb(color);
          gradient.addColorStop(0, rgb.replace('rgb', 'rgba').replace(')', ',0.3)'));
          gradient.addColorStop(1, rgb.replace('rgb', 'rgba').replace(')', ',0)'));
          return gradient;
        },
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: color,
        pointBorderColor: '#0a0b0e',
        pointBorderWidth: 2,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#181b22',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { maxTicksLimit: 4 }
        }
      }
    }
  });
}

// ============================================
// POWER BESTS CHART
// ============================================
function buildPowerBestsChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.label),
      datasets: [
        {
          label: 'Power (W)',
          data: data.map(d => d.value),
          borderColor: COLORS.accent,
          borderWidth: 2.5,
          fill: true,
          backgroundColor: 'rgba(0,229,255,0.08)',
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: COLORS.accent,
          pointBorderColor: '#0a0b0e',
          pointBorderWidth: 2,
          yAxisID: 'yPower'
        },
        {
          label: 'HR (bpm)',
          data: data.map(d => d.hr),
          borderColor: COLORS.red,
          borderWidth: 1.5,
          borderDash: [4, 3],
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 3,
          yAxisID: 'yHR'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#181b22',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: ctx => ctx.datasetIndex === 0
              ? ` ${ctx.parsed.y}W`
              : ` ${ctx.parsed.y} bpm`
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' } },
        yPower: {
          position: 'left',
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { maxTicksLimit: 5, callback: v => v + 'W' }
        },
        yHR: {
          position: 'right',
          grid: { display: false },
          ticks: { maxTicksLimit: 5, color: COLORS.red }
        }
      }
    }
  });
}

// ============================================
// PACE BESTS CHART (inverted - lower is better)
// ============================================
function buildPaceBestsChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.label),
      datasets: [
        {
          label: 'Pace (sec/km)',
          data: data.map(d => d.value / (parseFloat(d.label) || 1)),
          borderColor: COLORS.green,
          borderWidth: 2.5,
          fill: true,
          backgroundColor: 'rgba(0,255,135,0.08)',
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: COLORS.green,
          pointBorderColor: '#0a0b0e',
          pointBorderWidth: 2,
          yAxisID: 'yPace'
        },
        {
          label: 'HR (bpm)',
          data: data.map(d => d.hr),
          borderColor: COLORS.red,
          borderWidth: 1.5,
          borderDash: [4, 3],
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          yAxisID: 'yHR'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' } },
        yPace: {
          position: 'left',
          reverse: false,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            maxTicksLimit: 5,
            callback: v => {
              const m = Math.floor(v / 60);
              const s = Math.floor(v % 60);
              return `${m}:${String(s).padStart(2,'0')}`;
            }
          }
        },
        yHR: {
          position: 'right',
          grid: { display: false },
          ticks: { maxTicksLimit: 5, color: COLORS.red }
        }
      }
    }
  });
}

// ============================================
// POWER CURVE CHART (Cycling page)
// ============================================
function buildPowerCurveChart(canvasId, current, prev) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = current.map(d => d.label);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '90-day bests',
          data: current.map(d => d.value),
          borderColor: COLORS.accent,
          borderWidth: 2.5,
          fill: true,
          backgroundColor: 'rgba(0,229,255,0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: COLORS.accent,
          pointBorderColor: '#0a0b0e',
          pointBorderWidth: 2
        },
        prev && {
          label: 'Previous period',
          data: prev.map(d => d.value),
          borderColor: 'rgba(255,255,255,0.15)',
          borderWidth: 1.5,
          borderDash: [4, 3],
          fill: false,
          tension: 0.4,
          pointRadius: 0
        }
      ].filter(Boolean)
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: !!prev },
        tooltip: {
          backgroundColor: '#181b22',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: { label: ctx => ` ${ctx.parsed.y}W` }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { callback: v => v + 'W', maxTicksLimit: 6 }
        }
      }
    }
  });
}
