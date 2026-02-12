/* ============================================
   FITNESS DASHBOARD — DATA LAYER v2
   Handles incremental sync + deduplication
   ============================================ */

// ============================================
// SYNC ENGINE
// ============================================
const SyncEngine = {
  CACHE_KEY: 'fd_cache',
  CACHE_META: 'fd_sync_meta',

  async load() {
    const meta = JSON.parse(localStorage.getItem(this.CACHE_META) || '{}');
    const cached = JSON.parse(localStorage.getItem(this.CACHE_KEY) || 'null');

    if (cached && meta.lastSync) {
      const ageHours = (Date.now() - meta.lastSync) / 3_600_000;
      if (ageHours < 1) return cached;
    }

    return this.fetchFromDrive();
  },

  async fetchFromDrive() {
    // In production: fetch from Google Drive processed JSON
    // const url = 'https://drive.google.com/...';
    // const response = await fetch(url);
    // const data = await response.json();
    const data = FITNESS_DATA_STATIC;

    localStorage.setItem(this.CACHE_KEY, JSON.stringify(data));
    localStorage.setItem(this.CACHE_META, JSON.stringify({ lastSync: Date.now() }));
    return data;
  },

  deduplicateActivities(activities) {
    const seen = new Map();
    for (const a of activities) {
      const key = `${a.start_time}_${a.type}_${a.duration}`;
      if (!seen.has(key)) seen.set(key, a);
    }
    return Array.from(seen.values()).sort((a, b) => b.start_time.localeCompare(a.start_time));
  },

  mergeIncremental(existing, incoming) {
    const merged = [...existing];
    for (const item of incoming) {
      const idx = merged.findIndex(e => e.id === item.id);
      if (idx >= 0) merged[idx] = item;
      else merged.push(item);
    }
    return this.deduplicateActivities(merged);
  }
};

// ============================================
// STATIC SAMPLE DATA (replace with Drive fetch)
// ============================================
const FITNESS_DATA_STATIC = {
  athlete: { name: "Lee Hopkins", ytd: { distance: 1842, hours: 87.4, tss: 6240 } },

  fitness: { ctl: 48.5, atl: 45.5, tsb: 3.0, hrv: 47, resting_hr: 52, sleep: 6.8 },

  // 365 days fitness trend
  fitness_trend: generateFitnessTrend(365),

  // 12 weeks TSS by type
  weekly_tss: generateWeeklyTSS(52),

  // Recent activities (last 14 days)
  recent_activities: [
    { id:"a1", name:"Zwift Race: Redline Rally - Navy B", type:"VirtualRide", date:"2026-02-10", duration:2820, distance:38400, avg_power:228, avg_hr:158, tss:88, if_val:0.91 },
    { id:"a2", name:"Easy Z2 Ride", type:"VirtualRide", date:"2026-02-09", duration:4200, distance:38100, avg_power:175, avg_hr:135, tss:62, if_val:0.71 },
    { id:"a3", name:"Threshold Run", type:"VirtualRun", date:"2026-02-08", duration:3600, distance:11700, avg_pace:308, avg_hr:162, tss:74, if_val:0.86 },
    { id:"a4", name:"Morning Zwift Ride", type:"VirtualRide", date:"2026-02-07", duration:3000, distance:24200, avg_power:195, avg_hr:145, tss:55, if_val:0.79 },
    { id:"a5", name:"Rowing Session 8km", type:"Rowing", date:"2026-02-06", duration:2400, distance:8000, avg_hr:148, tss:42, if_val:0.72 },
    { id:"a6", name:"Recovery Run", type:"VirtualRun", date:"2026-02-05", duration:1800, distance:5200, avg_pace:346, avg_hr:130, tss:28, if_val:0.62 },
    { id:"a7", name:"Strength & Conditioning", type:"Workout", date:"2026-02-04", duration:3600, distance:0, avg_hr:132, tss:35, if_val:0.68 },
    { id:"a8", name:"Zwift Race: Crit City B", type:"VirtualRide", date:"2026-02-03", duration:2400, distance:26800, avg_power:238, avg_hr:165, tss:72, if_val:0.96 },
    { id:"a9", name:"Long Z2 Run", type:"VirtualRun", date:"2026-02-02", duration:5400, distance:16100, avg_pace:335, avg_hr:138, tss:85, if_val:0.78 },
    { id:"a10", name:"Club Ride", type:"Ride", date:"2026-02-01", duration:7200, distance:58200, avg_power:192, avg_hr:142, tss:95, if_val:0.77 },
    { id:"a11", name:"Zwift Race: Watopia Flat", type:"VirtualRide", date:"2026-01-30", duration:3300, distance:42100, avg_power:215, avg_hr:155, tss:78, if_val:0.87 },
    { id:"a12", name:"Easy Run", type:"Run", date:"2026-01-29", duration:2700, distance:7800, avg_pace:346, avg_hr:132, tss:32, if_val:0.64 },
    { id:"a13", name:"Concept2 Intervals", type:"Rowing", date:"2026-01-28", duration:2100, distance:7200, avg_hr:162, tss:55, if_val:0.88 },
    { id:"a14", name:"Zwift Tempo Ride", type:"VirtualRide", date:"2026-01-27", duration:3600, distance:36400, avg_power:205, avg_hr:148, tss:68, if_val:0.83 }
  ],

  // 365-day wellness
  wellness_trend: generateWellnessTrend(365),

  // Power bests (90-day)
  power_bests: [
    { label:"5s",    value:890, hr:158 }, { label:"10s",   value:820, hr:160 },
    { label:"15s",   value:775, hr:162 }, { label:"30s",   value:680, hr:165 },
    { label:"1min",  value:560, hr:172 }, { label:"2min",  value:440, hr:178 },
    { label:"3min",  value:390, hr:180 }, { label:"5min",  value:338, hr:182 },
    { label:"6min",  value:322, hr:181 }, { label:"8min",  value:305, hr:180 },
    { label:"10min", value:290, hr:178 }, { label:"12min", value:278, hr:177 },
    { label:"15min", value:265, hr:175 }, { label:"20min", value:252, hr:173 },
    { label:"30min", value:238, hr:170 }, { label:"40min", value:228, hr:168 },
    { label:"60min", value:215, hr:165 }, { label:"90min", value:198, hr:161 }
  ],

  // Running bests (distance, total seconds to cover it)
  pace_bests: [
    { label:"400m",     distM:400,    totalSec:82,    hr:185 },
    { label:"800m",     distM:800,    totalSec:176,   hr:183 },
    { label:"1k",       distM:1000,   totalSec:222,   hr:182 },
    { label:"1500m",    distM:1500,   totalSec:348,   hr:181 },
    { label:"1600m",    distM:1600,   totalSec:374,   hr:180 },
    { label:"2k",       distM:2000,   totalSec:472,   hr:179 },
    { label:"3k",       distM:3000,   totalSec:720,   hr:177 },
    { label:"5k",       distM:5000,   totalSec:1245,  hr:174 },
    { label:"8k",       distM:8000,   totalSec:2040,  hr:172 },
    { label:"10k",      distM:10000,  totalSec:2580,  hr:170 },
    { label:"15k",      distM:15000,  totalSec:3960,  hr:168 },
    { label:"16.1k",    distM:16100,  totalSec:4278,  hr:167 },
    { label:"20k",      distM:20000,  totalSec:5400,  hr:165 },
    { label:"Marathon", distM:42195,  totalSec:11700, hr:160 }
  ],

  // Heatmap (3 years)
  heatmap_3y: generateHeatmap(1095),
  heatmap_1y: generateHeatmap(365),

  // Calendar (current month + 3 back)
  calendar: generateCalendar(),

  // PB markers for fitness chart
  pb_markers: generatePBMarkers(),

  segments: {
    cycling: [
      { name:"Rhondda Valley Climb",  distance:3200, time:"8:42",  power:285, rank:2, pr:false },
      { name:"Bwlch Mountain Sprint", distance:1850, time:"4:15",  power:318, rank:1, pr:true },
      { name:"Caerphilly Mountain",   distance:5100, time:"18:35", power:265, rank:4, pr:false },
      { name:"Taff Trail TT",         distance:8200, time:"22:10", power:258, rank:3, pr:false },
      { name:"Pontypridd Ramp",       distance:900,  time:"2:05",  power:342, rank:1, pr:true }
    ],
    running: [
      { name:"Bute Park Loop",           distance:5000, time:"22:14", pace:"4:27/km", rank:1, pr:true },
      { name:"Taff Embankment Mile",     distance:1609, time:"6:48",  pace:"4:13/km", rank:2, pr:false },
      { name:"Pontcanna Fields Sprint",  distance:400,  time:"1:21",  pace:"3:22/km", rank:3, pr:false }
    ]
  }
};

// ============================================
// GENERATORS
// ============================================
function generateFitnessTrend(days) {
  const result = [];
  const end = new Date("2026-02-11");
  let ctl = 28, atl = 26;
  for (let i = days; i >= 0; i--) {
    const d = new Date(end);
    d.setDate(end.getDate() - i);
    const tss = Math.random() > 0.35 ? Math.floor(Math.random() * 140 + 20) : 0;
    ctl = ctl + (tss - ctl) / 42;
    atl = atl + (tss - atl) / 7;
    result.push({
      date: d.toISOString().split('T')[0],
      ctl: Math.round(ctl * 10) / 10,
      atl: Math.round(atl * 10) / 10,
      tsb: Math.round((ctl - atl) * 10) / 10,
      tss
    });
  }
  return result;
}

function generateWeeklyTSS(weeks) {
  const result = [];
  for (let i = weeks; i >= 0; i--) {
    const wnum = ((52 - i) % 52) + 1;
    result.push({
      week: `W${wnum}`,
      ride:  Math.floor(Math.random() * 300 + 150),
      run:   Math.floor(Math.random() * 100 + 40),
      row:   Math.floor(Math.random() * 60 + 10),
      other: Math.floor(Math.random() * 40)
    });
  }
  return result;
}

function generateWellnessTrend(days) {
  const dates = [], hrv = [], sleep = [], rhr = [];
  const end = new Date("2026-02-11");
  for (let i = days; i >= 0; i--) {
    const d = new Date(end);
    d.setDate(end.getDate() - i);
    dates.push(d.toISOString().split('T')[0]);
    hrv.push(Math.round(38 + Math.random() * 18));
    sleep.push(Math.round((5.5 + Math.random() * 2.5) * 10) / 10);
    rhr.push(Math.round(48 + Math.random() * 10));
  }
  return { dates, hrv, sleep, rhr };
}

function generateHeatmap(days = 365) {
  const cells = [];
  const end = new Date("2026-02-11");
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(end);
    d.setDate(end.getDate() - i);
    const rand = Math.random();
    let level = 0;
    if (rand > 0.42) {
      if (rand > 0.92) level = 5;
      else if (rand > 0.80) level = 4;
      else if (rand > 0.67) level = 3;
      else if (rand > 0.55) level = 2;
      else level = 1;
    }
    cells.push({ date: d.toISOString().split('T')[0], level });
  }
  return cells;
}

function generateCalendar() {
  const weeks = [];
  const today = new Date("2026-02-11");
  const startOfMonth = new Date(today.getFullYear(), today.getMonth() - 3, 1);
  const current = new Date(startOfMonth);
  const dow = current.getDay();
  current.setDate(current.getDate() - (dow === 0 ? 6 : dow - 1));

  const activities = FITNESS_DATA_STATIC?.recent_activities || [];

  while (current <= today || weeks.length < 4) {
    const week = { weekNum: getWeekNum(current), days: [], tss: 0, distance: 0 };
    for (let d = 0; d < 7; d++) {
      const dateStr = current.toISOString().split('T')[0];
      const acts = activities.filter(a => a.date === dateStr);
      week.days.push({
        date: new Date(current),
        dateStr,
        dayNum: current.getDate(),
        inRange: current >= startOfMonth && current <= today,
        isToday: dateStr === "2026-02-11",
        activities: acts
      });
      week.tss += acts.reduce((s, a) => s + (a.tss || 0), 0);
      week.distance += acts.reduce((s, a) => s + (a.distance || 0), 0);
      current.setDate(current.getDate() + 1);
    }
    weeks.push(week);
    if (current > today && weeks.length >= 4) break;
  }
  return weeks.slice(-4);
}

function generatePBMarkers() {
  const trend = generateFitnessTrend(365);
  const markers = [];
  const types = ['cycling', 'running'];
  const tiers = ['gold', 'silver', 'bronze'];
  trend.forEach((d, i) => {
    if (Math.random() > 0.97) {
      markers.push({
        date: d.date,
        index: i,
        type: types[Math.floor(Math.random() * 2)],
        tier: tiers[Math.floor(Math.random() * 3)]
      });
    }
  });
  return markers;
}

function getWeekNum(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// ============================================
// FORMATTERS
// ============================================
function formatDuration(seconds) {
  if (!seconds) return '—';
  if (seconds >= 3600) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  }
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatPace(secPerKm) {
  if (!secPerKm) return '—';
  const m = Math.floor(secPerKm / 60);
  const s = Math.round(secPerKm % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatPaceFromBest(totalSec, distM) {
  const secPerKm = (totalSec / distM) * 1000;
  return formatPace(secPerKm);
}

function formatDistance(meters) {
  return meters >= 1000 ? (meters / 1000).toFixed(1) + ' km' : meters + ' m';
}

function getTypeInfo(type) {
  const map = {
    'VirtualRide': { label:'Cycling',  colorClass:'type-ride',    dotClass:'dot-ride',    page:'cycling.html' },
    'Ride':        { label:'Cycling',  colorClass:'type-ride',    dotClass:'dot-ride',    page:'cycling.html' },
    'VirtualRun':  { label:'Running',  colorClass:'type-run',     dotClass:'dot-run',     page:'running.html' },
    'Run':         { label:'Running',  colorClass:'type-run',     dotClass:'dot-run',     page:'running.html' },
    'Rowing':      { label:'Rowing',   colorClass:'type-row',     dotClass:'dot-row',     page:'rowing.html'  },
    'Workout':     { label:'Workout',  colorClass:'type-workout', dotClass:'dot-workout', page:'cardio.html'  },
    'Walk':        { label:'Walking',  colorClass:'type-walk',    dotClass:'dot-walk',    page:'other.html'   }
  };
  return map[type] || { label: type, colorClass:'type-default', dotClass:'dot-default', page:'other.html' };
}

const FITNESS_DATA = FITNESS_DATA_STATIC;
