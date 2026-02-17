/* =========================================================
   Training OS — charts.js
   Clean, fast, accurate chart rendering
========================================================= */

const Charts = (() => {

  const fontFamily = "'DM Mono', monospace";

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        labels: {
          color: '#aaa',
          font: { family: fontFamily }
        }
      },
      tooltip: {
        backgroundColor: '#111',
        borderColor: '#333',
        borderWidth: 1,
        titleFont: { family: fontFamily },
        bodyFont: { family: fontFamily },
        padding: 10
      }
    },
    scales: {
      x: {
        ticks: { color: '#777', font: { family: fontFamily }},
        grid: { color: '#1a1a1a' }
      },
      y: {
        ticks: { color: '#777', font: { family: fontFamily }},
        grid: { color: '#1a1a1a' }
      }
    }
  };

  /* =========================================================
     FITNESS / FORM CHART (CTL / ATL / TSB)
  ========================================================= */

  function renderFitnessChart(ctx, data) {

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.date),
        datasets: [
          {
            label: 'CTL',
            data: data.map(d => d.ctl ?? null),
            borderWidth: 2,
            tension: 0.35
          },
          {
            label: 'ATL',
            data: data.map(d => d.atl ?? null),
            borderWidth: 2,
            tension: 0.35
          },
          {
            label: 'TSB',
            data: data.map(d => d.tsb ?? null),
            borderWidth: 2,
            tension: 0.35,
            borderDash: [6,4]
          }
        ]
      },
      options: {
        ...baseOptions,
        scales: {
          ...baseOptions.scales,
          y: {
            ...baseOptions.scales.y,
            beginAtZero: false
          }
        }
      }
    });
  }

  /* =========================================================
     WEEKLY TSS BAR CHART
  ========================================================= */

  function renderTSSChart(ctx, weeklyData) {

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: weeklyData.map(w => `W${w.week}`),
        datasets: [{
          label: 'Weekly TSS',
          data: weeklyData.map(w => w.total ?? 0)
        }]
      },
      options: {
        ...baseOptions,
        plugins: {
          ...baseOptions.plugins,
          legend: { display: false }
        }
      }
    });
  }

  /* =========================================================
     HRV + SLEEP CHART
  ========================================================= */

  function renderHRVSleepChart(ctx, wellness) {

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: wellness.map(d => d.date),
        datasets: [
          {
            label: 'HRV',
            data: wellness.map(d => d.hrv ?? null),
            yAxisID: 'y'
          },
          {
            label: 'Sleep (hrs)',
            data: wellness.map(d => d.sleep_hours ?? null),
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        ...baseOptions,
        scales: {
          ...baseOptions.scales,
          y: {
            ...baseOptions.scales.y,
            position: 'left'
          },
          y1: {
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#777', font: { family: fontFamily }}
          }
        }
      }
    });
  }

  /* =========================================================
     PACE CHART (INVERTED AXIS — FASTER ON TOP)
  ========================================================= */

  function renderPaceChart(ctx, activities) {

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: activities.map(a => a.date),
        datasets: [{
          label: 'Pace',
          data: activities.map(a => a.avg_pace ?? null),
          borderWidth: 2,
          tension: 0.35
        }]
      },
      options: {
        ...baseOptions,
        scales: {
          ...baseOptions.scales,
          y: {
            ...baseOptions.scales.y,
            reverse: true,   // 👈 THIS FIXES PACE ORIENTATION
            ticks: {
              color: '#777',
              font: { family: fontFamily },
              callback: (value) => formatPace(value)
            }
          }
        },
        plugins: {
          ...baseOptions.plugins,
          tooltip: {
            ...baseOptions.plugins.tooltip,
            callbacks: {
              label: (ctx) => ` ${formatPace(ctx.parsed.y)}`
            }
          }
        }
      }
    });
  }

  /* =========================================================
     HELPERS
  ========================================================= */

  function formatPace(secondsPerKm) {
    if (!secondsPerKm) return '—';
    const min = Math.floor(secondsPerKm / 60);
    const sec = Math.round(secondsPerKm % 60);
    return `${min}:${sec.toString().padStart(2,'0')}/km`;
  }

  return {
    renderFitnessChart,
    renderTSSChart,
    renderHRVSleepChart,
    renderPaceChart
  };

})();
