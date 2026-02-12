/* ============================================
   FITNESS DASHBOARD — CONFIG
   ============================================ */
const CONFIG = {
  athlete_id: '5718022',
  api_key: '3nxpa26knlwkdc3aikwhofr6r',
  base_url: 'https://intervals.icu/api/v1',
  history_start: '2025-01-01',

  get auth_header() {
    return 'Basic ' + btoa('API_KEY:' + this.api_key);
  },

  get headers() {
    return {
      'Authorization': this.auth_header,
      'Content-Type': 'application/json'
    };
  }
};
