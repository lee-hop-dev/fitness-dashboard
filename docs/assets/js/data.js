/* ============================================
   FITNESS DASHBOARD — SAMPLE DATA
   Replace with real data from Google Drive
   ============================================ */

const FITNESS_DATA = {
  athlete: {
    name: "Lee Hopkins",
    ytd: { distance: 1842, hours: 87.4, tss: 6240 }
  },

  // Latest fitness metrics
  fitness: {
    ctl: 48.5, atl: 45.5, tsb: 3.0,
    hrv: 47, resting_hr: 52, sleep: 6.8
  },

  // 42-day CTL/ATL/TSB trend
  fitness_trend: [
    { date: "2025-12-31", ctl: 38.2, atl: 35.1, tsb: 3.1, tss: 0 },
    { date: "2026-01-03", ctl: 39.1, atl: 42.0, tsb: -2.9, tss: 95 },
    { date: "2026-01-07", ctl: 40.5, atl: 38.5, tsb: 2.0, tss: 60 },
    { date: "2026-01-10", ctl: 41.2, atl: 44.1, tsb: -2.9, tss: 110 },
    { date: "2026-01-14", ctl: 42.0, atl: 39.8, tsb: 2.2, tss: 75 },
    { date: "2026-01-17", ctl: 42.8, atl: 46.2, tsb: -3.4, tss: 125 },
    { date: "2026-01-21", ctl: 43.9, atl: 41.0, tsb: 2.9, tss: 55 },
    { date: "2026-01-24", ctl: 44.5, atl: 48.3, tsb: -3.8, tss: 135 },
    { date: "2026-01-28", ctl: 45.1, atl: 42.5, tsb: 2.6, tss: 65 },
    { date: "2026-01-31", ctl: 45.9, atl: 50.1, tsb: -4.2, tss: 145 },
    { date: "2026-02-04", ctl: 46.8, atl: 43.9, tsb: 2.9, tss: 70 },
    { date: "2026-02-07", ctl: 47.5, atl: 49.2, tsb: -1.7, tss: 120 },
    { date: "2026-02-10", ctl: 48.2, atl: 46.8, tsb: 1.4, tss: 88 },
    { date: "2026-02-11", ctl: 48.5, atl: 45.5, tsb: 3.0, tss: 42 }
  ],

  // Weekly TSS by type (last 12 weeks)
  weekly_tss: [
    { week: "W46", ride: 280, run: 85, row: 40, other: 20 },
    { week: "W47", ride: 320, run: 95, row: 55, other: 0 },
    { week: "W48", ride: 180, run: 60, row: 0,  other: 35 },
    { week: "W49", ride: 350, run: 110, row: 60, other: 15 },
    { week: "W50", ride: 290, run: 80, row: 45, other: 25 },
    { week: "W51", ride: 420, run: 130, row: 70, other: 0 },
    { week: "W52", ride: 160, run: 45, row: 20, other: 10 },
    { week: "W1",  ride: 310, run: 90, row: 55, other: 20 },
    { week: "W2",  ride: 380, run: 115, row: 65, other: 0 },
    { week: "W3",  ride: 295, run: 85, row: 50, other: 30 },
    { week: "W4",  ride: 340, run: 100, row: 60, other: 15 },
    { week: "W5",  ride: 355, run: 88, row: 42, other: 22 }
  ],

  // Last 7 days activities
  recent_activities: [
    {
      id: "1", name: "Zwift Race: Redline Rally - Navy B",
      type: "VirtualRide", date: "2026-02-10",
      duration: 2820, distance: 38400,
      avg_power: 228, avg_hr: 158, tss: 88
    },
    {
      id: "2", name: "Easy Z2 Ride",
      type: "VirtualRide", date: "2026-02-09",
      duration: 4200, distance: 38100,
      avg_power: 175, avg_hr: 135, tss: 62
    },
    {
      id: "3", name: "Threshold Run",
      type: "VirtualRun", date: "2026-02-08",
      duration: 3600, distance: 11700,
      avg_pace: 308, avg_hr: 162, tss: 74
    },
    {
      id: "4", name: "Morning Zwift Ride",
      type: "VirtualRide", date: "2026-02-07",
      duration: 3000, distance: 24200,
      avg_power: 195, avg_hr: 145, tss: 55
    },
    {
      id: "5", name: "Rowing Session",
      type: "Rowing", date: "2026-02-06",
      duration: 2400, distance: 8000,
      avg_hr: 148, tss: 42
    },
    {
      id: "6", name: "Recovery Run",
      type: "VirtualRun", date: "2026-02-05",
      duration: 1800, distance: 5200,
      avg_pace: 346, avg_hr: 130, tss: 28
    },
    {
      id: "7", name: "Strength & Conditioning",
      type: "Workout", date: "2026-02-04",
      duration: 3600, distance: 0,
      avg_hr: 132, tss: 35
    }
  ],

  // 42-day wellness data
  wellness_trend: {
    dates:  ["Jan 01","Jan 05","Jan 10","Jan 15","Jan 20","Jan 25","Jan 30","Feb 03","Feb 07","Feb 11"],
    hrv:    [44, 46, 41, 48, 43, 50, 45, 49, 47, 47],
    sleep:  [7.2, 6.8, 7.5, 6.5, 7.0, 6.9, 7.3, 6.7, 7.1, 6.8],
    rhr:    [53, 52, 55, 51, 54, 50, 53, 51, 52, 52]
  },

  // 90-day power bests (watts)
  power_bests: [
    { label: "5s",    value: 890,  hr: 158 },
    { label: "10s",   value: 820,  hr: 160 },
    { label: "15s",   value: 775,  hr: 162 },
    { label: "30s",   value: 680,  hr: 165 },
    { label: "1min",  value: 560,  hr: 172 },
    { label: "2min",  value: 440,  hr: 178 },
    { label: "3min",  value: 390,  hr: 180 },
    { label: "5min",  value: 338,  hr: 182 },
    { label: "6min",  value: 322,  hr: 181 },
    { label: "8min",  value: 305,  hr: 180 },
    { label: "10min", value: 290,  hr: 178 },
    { label: "12min", value: 278,  hr: 177 },
    { label: "15min", value: 265,  hr: 175 },
    { label: "20min", value: 252,  hr: 173 },
    { label: "30min", value: 238,  hr: 170 },
    { label: "40min", value: 228,  hr: 168 },
    { label: "60min", value: 215,  hr: 165 },
    { label: "90min", value: 198,  hr: 161 }
  ],

  // 90-day running bests (seconds per km → displayed as min:sec/km)
  pace_bests: [
    { label: "400m",    value: 82,   hr: 185 },
    { label: "800m",    value: 176,  hr: 183 },
    { label: "1k",      value: 222,  hr: 182 },
    { label: "1500m",   value: 348,  hr: 181 },
    { label: "1600m",   value: 374,  hr: 180 },
    { label: "2k",      value: 472,  hr: 179 },
    { label: "3k",      value: 720,  hr: 177 },
    { label: "5k",      value: 1245, hr: 174 },
    { label: "8k",      value: 2040, hr: 172 },
    { label: "10k",     value: 2580, hr: 170 },
    { label: "15k",     value: 3960, hr: 168 },
    { label: "16.1k",   value: 4278, hr: 167 },
    { label: "20k",     value: 5400, hr: 165 },
    { label: "Marathon",value: 11700, hr: 160 }
  ],

  // Yearly heatmap (Jan 1 – today, TSS levels 0-5)
  heatmap: generateHeatmap(),

  // 4-week calendar
  calendar: generateCalendar(),

  // Strava segments
  segments: {
    cycling: [
      { name: "Rhondda Valley Climb", distance: 3200, time: "8:42", power: 285, rank: 2, pr: false },
      { name: "Bwlch Mountain Sprint", distance: 1850, time: "4:15", power: 318, rank: 1, pr: true },
      { name: "Caerphilly Mountain", distance: 5100, time: "18:35", power: 265, rank: 4, pr: false },
      { name: "Taff Trail TT", distance: 8200, time: "22:10", power: 258, rank: 3, pr: false },
      { name: "Pontypridd Ramp", distance: 900,  time: "2:05",  power: 342, rank: 1, pr: true }
    ],
    running: [
      { name: "Bute Park Loop", distance: 5000, time: "22:14", pace: "4:27/km", rank: 1, pr: true },
      { name: "Taff Embankment Mile", distance: 1609, time: "6:48", pace: "4:13/km", rank: 2, pr: false },
      { name: "Pontcanna Fields Sprint", distance: 400, time: "1:21", pace: "3:22/km", rank: 3, pr: false }
    ]
  }
};

function generateHeatmap() {
  const cells = [];
  const start = new Date("2026-01-01");
  const today = new Date("2026-02-11");
  for (let d = new Date(start); d <= today; d.setDate(d.getDate() + 1)) {
    const rand = Math.random();
    let level = 0;
    if (rand > 0.45) {
      if (rand > 0.9) level = 5;
      else if (rand > 0.78) level = 4;
      else if (rand > 0.65) level = 3;
      else if (rand > 0.55) level = 2;
      else level = 1;
    }
    cells.push({ date: d.toISOString().split("T")[0], level });
  }
  return cells;
}

function generateCalendar() {
  const weeks = [];
  const today = new Date("2026-02-11");
  for (let w = 3; w >= 0; w--) {
    const week = { days: [], tss: 0 };
    for (let d = 0; d < 7; d++) {
      const date = new Date(today);
      date.setDate(today.getDate() - (w * 7) - (6 - d));
      const hasActivity = Math.random() > 0.45;
      const tss = hasActivity ? Math.floor(Math.random() * 120 + 20) : 0;
      week.days.push({ date: date.getDate(), hasActivity, tss, type: ["ride","run","row","workout"][Math.floor(Math.random()*4)] });
      week.tss += tss;
    }
    weeks.push(week);
  }
  return weeks;
}

// Helper: format seconds as h:mm or mm:ss
function formatDuration(seconds) {
  if (seconds >= 3600) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  }
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2,"0")}`;
}

// Helper: format pace (sec/km → m:ss/km)
function formatPace(secPerKm) {
  const m = Math.floor(secPerKm / 60);
  const s = secPerKm % 60;
  return `${m}:${String(s).padStart(2,"0")}`;
}

// Helper: distance in km
function formatDistance(meters) {
  return meters >= 1000 ? (meters / 1000).toFixed(1) + " km" : meters + " m";
}
