/* ============================================
   FITNESS DASHBOARD — API LAYER
   Direct Intervals.icu fetch with caching
   ============================================ */

const API = {
  CACHE_TTL: 60 * 60 * 1000, // 1 hour

  _cacheKey(key) { return `fd_${key}`; },

  _cacheGet(key) {
    try {
      const raw = sessionStorage.getItem(this._cacheKey(key));
      if (!raw) return null;
      const { ts, data } = JSON.parse(raw);
      if (Date.now() - ts > this.CACHE_TTL) return null;
      return data;
    } catch { return null; }
  },

  _cacheSet(key, data) {
    try {
      sessionStorage.setItem(this._cacheKey(key), JSON.stringify({ ts: Date.now(), data }));
    } catch {}
  },

  async _fetch(endpoint, params = {}) {
    const url = new URL(`${CONFIG.base_url}/${endpoint}`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));

    const res = await fetch(url.toString(), { headers: CONFIG.headers });
    if (!res.ok) throw new Error(`API error ${res.status}: ${endpoint}`);
    return res.json();
  },

  async getAthlete() {
    const cached = this._cacheGet('athlete');
    if (cached) return cached;
    const data = await this._fetch(`athlete/${CONFIG.athlete_id}`);
    this._cacheSet('athlete', data);
    return data;
  },

  async getActivities(oldest = CONFIG.history_start) {
    const cacheKey = `activities_${oldest}`;
    const cached = this._cacheGet(cacheKey);
    if (cached) return cached;

    const data = await this._fetch(`athlete/${CONFIG.athlete_id}/activities`, { oldest });

    // Deduplicate by id
    const seen = new Set();
    const deduped = data.filter(a => {
      if (seen.has(a.id)) return false;
      seen.add(a.id);
      return true;
    });

    this._cacheSet(cacheKey, deduped);
    return deduped;
  },

  async getWellness(oldest = CONFIG.history_start) {
    const cacheKey = `wellness_${oldest}`;
    const cached = this._cacheGet(cacheKey);
    if (cached) return cached;

    const data = await this._fetch(`athlete/${CONFIG.athlete_id}/wellness`, {
      oldest,
      newest: new Date().toISOString().split('T')[0]
    });

    this._cacheSet(cacheKey, data);
    return data;
  },

  async getFitnessTrend(oldest = CONFIG.history_start) {
    // Fitness trend comes from wellness data (contains ctl/atl/tsb)
    return this.getWellness(oldest);
  },

  async getPowerCurve() {
    const cached = this._cacheGet('power_curve');
    if (cached) return cached;

    // Fetch 90-day power curve
    const end = new Date().toISOString().split('T')[0];
    const start = new Date(Date.now() - 90 * 864e5).toISOString().split('T')[0];

    const data = await this._fetch(`athlete/${CONFIG.athlete_id}/power-curves`, {
      start, end,
      curves: 'best'
    });

    this._cacheSet('power_curve', data);
    return data;
  },

  async getWeightHistory(oldest = CONFIG.history_start) {
    const wellness = await this.getWellness(oldest);
    return wellness
      .filter(w => w.weight != null)
      .map(w => ({ date: w.id, weight: w.weight }));
  },

  // Force refresh — clears session cache
  clearCache() {
    Object.keys(sessionStorage)
      .filter(k => k.startsWith('fd_'))
      .forEach(k => sessionStorage.removeItem(k));
  },

  // ============================================
  // DATA PROCESSORS
  // ============================================

  processActivities(raw) {
    return raw.map(a => ({
      id:          String(a.id),
      name:        a.name || 'Activity',
      type:        a.type || 'Unknown',
      date:        (a.start_date_local || '').slice(0, 10),
      duration:    a.moving_time || 0,
      distance:    a.distance || 0,
      elevation:   a.total_elevation_gain || 0,
      avg_power:   a.average_watts || null,
      norm_power:  a.weighted_average_watts || null,
      avg_hr:      a.average_hr || null,
      max_hr:      a.max_hr || null,
      avg_pace:    a.average_speed ? Math.round(1000 / a.average_speed) : null,
      avg_cadence: a.average_cadence || null,
      calories:    a.calories || null,
      tss:         Math.round(a.icu_training_load || 0),
      if_val:      a.icu_intensity ? Math.round(a.icu_intensity * 100) / 100 : null,
      device:      a.device_name || '',
      is_garmin:   (a.device_name || '').toLowerCase().includes('garmin')
    }));
  },

  processWellness(raw) {
    return raw.map(w => ({
      date:       w.id,
      ctl:        w.ctl,
      atl:        w.atl,
      tsb:        w.tsb,
      tss:        w.trainingLoad || 0,
      hrv:        w.hrv,
      resting_hr: w.restingHR,
      sleep:      w.sleepSecs ? Math.round((w.sleepSecs / 3600) * 10) / 10 : null,
      weight:     w.weight,
      fatigue:    w.fatigue,
      mood:       w.mood
    }));
  },

  // Aggregate weekly TSS by type from activities
  aggregateWeeklyTSS(activities) {
    const weeks = {};
    activities.forEach(a => {
      if (!a.date) return;
      const d = new Date(a.date);
      const wk = getISOWeek(d);
      const key = `${d.getFullYear()}-W${String(wk).padStart(2,'0')}`;
      if (!weeks[key]) weeks[key] = { week: `W${wk}`, ride: 0, run: 0, row: 0, other: 0 };
      const tss = a.tss || 0;
      const t = a.type;
      if (t === 'Ride' || t === 'VirtualRide') weeks[key].ride += tss;
      else if (t === 'Run' || t === 'VirtualRun') weeks[key].run += tss;
      else if (t === 'Rowing' || t === 'Kayaking') weeks[key].row += tss;
      else weeks[key].other += tss;
    });
    return Object.values(weeks).slice(-52);
  },

  // YTD breakdown by sport
  calcYTD(activities) {
    const year = new Date().getFullYear();
    const ytd = activities.filter(a => a.date?.startsWith(String(year)));

    const cycling = ytd.filter(a => a.type === 'Ride' || a.type === 'VirtualRide');
    const running = ytd.filter(a => a.type === 'Run' || a.type === 'VirtualRun');

    const sum = arr => ({
      distance: Math.round(arr.reduce((s, a) => s + (a.distance || 0), 0) / 1000),
      hours:    Math.round(arr.reduce((s, a) => s + (a.duration || 0), 0) / 360) / 10,
      tss:      arr.reduce((s, a) => s + (a.tss || 0), 0)
    });

    return {
      total:   sum(ytd),
      cycling: sum(cycling),
      running: sum(running)
    };
  },

  // Latest wellness metrics
  latestWellness(wellness) {
    const recent = [...wellness].reverse().find(w => w.ctl != null);
    const latestHRV    = [...wellness].reverse().find(w => w.hrv != null);
    const latestSleep  = [...wellness].reverse().find(w => w.sleep != null);
    const latestWeight = [...wellness].reverse().find(w => w.weight != null);
    return {
      ctl:        recent?.ctl,
      atl:        recent?.atl,
      tsb:        recent?.tsb,
      hrv:        latestHRV?.hrv,
      resting_hr: latestHRV?.resting_hr,
      sleep:      latestSleep?.sleep,
      weight:     latestWeight?.weight
    };
  },

  // Build 90-day power bests from activities (fallback if power curve API unavailable)
  buildPowerBests(activities) {
    const durations = [5, 10, 15, 30, 60, 120, 180, 300, 360, 480, 600, 720, 900, 1200, 1800, 2400, 3600, 5400];
    const labels = ['5s','10s','15s','30s','1min','2min','3min','5min','6min','8min','10min','12min','15min','20min','30min','40min','60min','90min'];
    const cutoff = new Date(Date.now() - 90 * 864e5).toISOString().split('T')[0];
    const rides = activities.filter(a =>
      (a.type === 'Ride' || a.type === 'VirtualRide') && a.date >= cutoff
    );
    // Use max power available — in real data this would come from streams
    // For now return structured placeholder to be replaced by power curve API
    return labels.map((label, i) => ({
      label,
      duration: durations[i],
      value: null, // populated by power curve endpoint
      hr: null
    }));
  }
};

function getISOWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}
