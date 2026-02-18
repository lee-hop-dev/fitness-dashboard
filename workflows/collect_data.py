"""
FITNESS DASHBOARD — DATA COLLECTOR v4.4
Fetches from Intervals.icu + Strava + Concept2 and saves to docs/data/
"""

import os, json, time, logging, argparse, requests
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

ATHLETE_ID           = os.getenv('INTERVALS_ATHLETE_ID', '5718022')
API_KEY              = os.getenv('INTERVALS_API_KEY', '')
STRAVA_CLIENT_ID     = os.getenv('STRAVA_CLIENT_ID', '')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET', '')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN', '')
CONCEPT2_USERNAME    = os.getenv('CONCEPT2_USERNAME', '')
CONCEPT2_PASSWORD    = os.getenv('CONCEPT2_PASSWORD', '')
BASE_URL             = 'https://intervals.icu/api/v1'
HISTORY_START        = '2025-01-01'
OUTPUT_DIR           = Path(__file__).parent.parent / 'docs' / 'data'


class IntervalsClient:
    def __init__(self, athlete_id, api_key):
        self.athlete_id = athlete_id
        self.session = requests.Session()
        self.session.auth = ('API_KEY', api_key)
        self.session.headers['Content-Type'] = 'application/json'

    def _get(self, endpoint, params=None, retries=3):
        url = f'{BASE_URL}/{endpoint}'
        for attempt in range(retries):
            try:
                time.sleep(0.5)
                r = self.session.get(url, params=params or {})
                r.raise_for_status()
                return r.json()
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    log.warning('Rate limited, waiting 60s...')
                    time.sleep(60)
                else:
                    raise
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))

    def get_athlete(self):
        return self._get(f'athlete/{self.athlete_id}')

    def get_activities(self, oldest=HISTORY_START):
        log.info(f'Fetching Intervals activities from {oldest}')
        data = self._get(f'athlete/{self.athlete_id}/activities', {'oldest': oldest})
        log.info(f'Got {len(data)} raw activities from Intervals')
        
        # Normalize each activity before returning
        normalized_data = [self.normalize_intervals_activity(activity) for activity in data]
        log.info(f'Normalized {len(normalized_data)} activities')
        
        return normalized_data

    def get_wellness(self, oldest=HISTORY_START):
        today = datetime.now().strftime('%Y-%m-%d')
        data = self._get(f'athlete/{self.athlete_id}/wellness', {'oldest': oldest, 'newest': today})
        log.info(f'Got {len(data)} wellness entries')
        return data

    def normalize_intervals_activity(self, activity):
        """
        Normalize Intervals.icu field names to standard format.
        Handles the non-standard naming convention used by Intervals.icu API.
        """
        # Create normalized copy
        normalized = activity.copy()
        
        # Map power fields
        if 'icu_average_watts' in activity:
            normalized['avg_power'] = activity['icu_average_watts']
        
        if 'icu_weighted_avg_watts' in activity:
            normalized['norm_power'] = activity['icu_weighted_avg_watts']
        
        # Map heart rate fields (note the field name)
        if 'average_heartrate' in activity:
            normalized['avg_hr'] = activity['average_heartrate']
        
        if 'max_heartrate' in activity:
            normalized['max_hr'] = activity['max_heartrate']
        
        # Map and convert intensity factor (percentage to decimal)
        if 'icu_intensity' in activity and activity['icu_intensity'] is not None:
            normalized['intensity_factor'] = activity['icu_intensity'] / 100.0
        
        # Map FTP and W'bal
        if 'icu_ftp' in activity:
            normalized['ftp'] = activity['icu_ftp']
        
        if 'icu_w_prime' in activity:
            normalized['w_prime'] = activity['icu_w_prime']
        
        # Map weight
        if 'icu_weight' in activity:
            normalized['weight'] = activity['icu_weight']
        
        return normalized

    def fetch_power_curve(self, days=90):
        """
        Fetch power curve data for Critical Power calculations.
        
        Args:
            days: Number of days to look back (default 90)
        
        Returns:
            dict: Power curve data with duration:watts mappings
        """
        try:
            # Fetch power curve endpoint
            url = f'athlete/{self.athlete_id}/power-curve'
            params = {
                'period': f'{days}d',
                'type': 'power'
            }
            
            response = self._get(url, params=params)
            
            # Transform into usable format
            power_curve = {}
            if response and 'curve' in response:
                for point in response['curve']:
                    duration = point.get('secs', 0)
                    watts = point.get('watts', 0)
                    if duration > 0:
                        power_curve[duration] = watts
                
                log.info(f'Fetched power curve: {len(power_curve)} data points')
            else:
                log.warning('No power curve data available')
            
            return power_curve
            
        except Exception as e:
            log.error(f'Error fetching power curve: {e}')
            return {}

    def calculate_cp_metrics(self, power_curve):
        """
        Calculate Critical Power (CP) and W' from power curve data.
        Uses 5-minute and 20-minute power values.
        
        Args:
            power_curve: dict mapping duration (seconds) to watts
        
        Returns:
            dict: CP metrics including CP, W', and peak powers
        """
        # Standard durations for CP calculation
        DURATION_1MIN = 60
        DURATION_5MIN = 300
        DURATION_20MIN = 1200
        
        # Get power values (with fallback to 0)
        power_1min = power_curve.get(DURATION_1MIN, 0)
        power_5min = power_curve.get(DURATION_5MIN, 0)
        power_20min = power_curve.get(DURATION_20MIN, 0)
        
        if power_5min == 0 or power_20min == 0:
            log.warning('Insufficient data for CP calculation')
            return {
                'cp': 0,
                'w_prime': 0,
                'power_1min': power_1min,
                'power_5min': power_5min,
                'power_20min': power_20min
            }
        
        # Calculate CP using 2-parameter model
        # W' = (P5 - P20) * (t1 * t2) / (t2 - t1)
        # CP = (P5 * t1 - P20 * t2) / (t1 - t2)
        
        t1, t2 = 300, 1200
        p1, p2 = power_5min, power_20min
        
        w_prime = (p1 - p2) * (t1 * t2) / (t2 - t1)
        cp = (p1 * t1 - p2 * t2) / (t1 - t2)
        
        log.info(f'Calculated CP: {cp:.1f}W, W\': {w_prime:.0f}J')
        
        return {
            'cp': round(cp, 1),
            'w_prime': round(w_prime, 0),
            'power_1min': power_1min,
            'power_5min': power_5min,
            'power_20min': power_20min
        }


class StravaClient:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.session = requests.Session()

    def authenticate(self):
        log.info('Authenticating with Strava...')
        r = requests.post('https://www.strava.com/oauth/token', data={
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type':    'refresh_token'
        })
        r.raise_for_status()
        self.access_token = r.json()['access_token']
        self.session.headers['Authorization'] = f'Bearer {self.access_token}'
        log.info('Strava authentication successful')

    def _get(self, endpoint, params=None):
        url = f'https://www.strava.com/api/v3/{endpoint}'
        for attempt in range(3):
            try:
                time.sleep(0.3)
                r = self.session.get(url, params=params or {})
                if r.status_code == 429:
                    log.warning('Strava rate limited, waiting 60s...')
                    time.sleep(60)
                    continue
                r.raise_for_status()
                return r.json()
            except Exception as e:
                if attempt == 2:
                    log.error(f'Strava request failed: {e}')
                    return None
                time.sleep(5 * (attempt + 1))

    def get_activities(self, after_timestamp):
        log.info('Fetching Strava activities...')
        all_acts = []
        page = 1
        while True:
            data = self._get('athlete/activities', {'after': after_timestamp, 'per_page': 100, 'page': page})
            if not data:
                break
            all_acts.extend(data)
            if len(data) < 100:
                break
            page += 1
        log.info(f'Fetched {len(all_acts)} Strava activities')
        return all_acts


class Concept2Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = 'https://log.concept2.com/api'

    def authenticate(self):
        log.info('Authenticating with Concept2...')
        try:
            r = self.session.post(f'{self.base_url}/auth', json={
                'username': self.username,
                'password': self.password
            })
            if r.status_code == 200:
                log.info('Concept2 authentication successful')
                return True
            else:
                log.error(f'Concept2 auth failed: {r.status_code}')
                return False
        except Exception as e:
            log.error(f'Concept2 auth error: {e}')
            return False

    def get_workouts(self, oldest):
        log.info('Fetching Concept2 workouts...')
        try:
            from_date = datetime.strptime(oldest, '%Y-%m-%d')
            to_date = datetime.now()
            r = self.session.get(f'{self.base_url}/users/me/results', params={
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'type': 'rower'
            })
            if r.status_code == 200:
                data = r.json()
                log.info(f'Fetched {len(data.get("data", []))} Concept2 workouts')
                return data.get('data', [])
            else:
                log.error(f'Concept2 workouts fetch failed: {r.status_code}')
                return []
        except Exception as e:
            log.error(f'Concept2 workouts error: {e}')
            return []


def normalize_strava_activity(s):
    sport_map = {
        'Ride': 'Ride', 'VirtualRide': 'VirtualRide',
        'Run': 'Run', 'VirtualRun': 'VirtualRun',
        'Rowing': 'Rowing', 'Kayaking': 'Kayaking',
        'WeightTraining': 'WeightTraining', 'Workout': 'Workout', 'Crossfit': 'Crossfit',
        'Elliptical': 'Cardio', 'StairStepper': 'Cardio', 'RockClimbing': 'Cardio',
        'Yoga': 'Yoga', 'Walk': 'Walk', 'Hike': 'Hike',
        'Swim': 'Swim', 'NordicSki': 'NordicSki', 'AlpineSki': 'AlpineSki'
    }
    return {
        'id': s['id'],
        'strava_id': s['id'],
        'name': s.get('name', ''),
        'type': sport_map.get(s.get('sport_type') or s.get('type'), s.get('type', 'Other')),
        'date': s['start_date'][:10] if s.get('start_date') else '',
        'duration': s.get('moving_time', 0),
        'distance': s.get('distance', 0),
        'avg_power': s.get('average_watts'),
        'norm_power': s.get('weighted_average_watts'),
        'avg_hr': s.get('average_heartrate'),
        'max_hr': s.get('max_heartrate'),
        'tss': s.get('suffer_score'),
        'source': 'STRAVA'
    }


def normalize_concept2_workout(c):
    return {
        'id': f"c2_{c.get('id', '')}",
        'name': f"Concept2 {c.get('type', 'Rowing')}",
        'type': 'Rowing',
        'date': c.get('date', '')[:10] if c.get('date') else '',
        'duration': c.get('time', 0),
        'distance': c.get('distance', 0),
        'avg_power': c.get('watts'),
        'avg_hr': c.get('heart_rate', {}).get('average') if isinstance(c.get('heart_rate'), dict) else None,
        'source': 'CONCEPT2'
    }


def merge_activities(intervals, strava, concept2):
    log.info('Merging activities from all sources...')
    
    # Start with normalized Intervals data (already normalized in get_activities)
    activities = intervals.copy()
    
    # Track Strava IDs we already have from Intervals
    strava_ids_from_intervals = set()
    for a in intervals:
        if a.get('strava_id'):
            strava_ids_from_intervals.add(str(a['strava_id']))
    
    # Add Strava activities that aren't already in Intervals
    for s in strava:
        sid = str(s['id'])
        if sid not in strava_ids_from_intervals:
            activities.append(normalize_strava_activity(s))
    
    # Add Concept2 activities
    for c in concept2:
        activities.append(normalize_concept2_workout(c))
    
    # Sort by date, newest first
    activities.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    log.info(f'Total merged activities: {len(activities)}')
    return activities


def build_segments(strava, activities):
    log.info('Fetching Strava segment efforts...')
    segments = {'cycling': [], 'running': []}
    seen = set()
    
    for act in activities[:50]:
        if not act.get('strava_id'):
            continue
        try:
            data = strava._get(f'activities/{act["strava_id"]}')
            if not data or 'segment_efforts' not in data:
                continue
            for e in data['segment_efforts']:
                seg = e.get('segment', {})
                sid = seg.get('id')
                if not sid or sid in seen:
                    continue
                seen.add(sid)
                entry = {
                    'id': sid, 'name': seg.get('name',''),
                    'distance': seg.get('distance',0),
                    'time': e.get('elapsed_time',0),
                    'pr': e.get('pr_rank') == 1,
                    'rank': e.get('pr_rank'),
                    'date': act['date']
                }
                if act['type'] in ('Ride','VirtualRide'):
                    entry['avg_power'] = e.get('average_watts')
                    segments['cycling'].append(entry)
                else:
                    entry['avg_hr'] = e.get('average_heartrate')
                    segments['running'].append(entry)
        except Exception as e:
            log.warning(f'Segment fetch failed for activity {act["strava_id"]}: {e}')
    
    log.info(f'Segments: {len(segments["cycling"])} cycling, {len(segments["running"])} running')
    return segments


def process_wellness(raw):
    processed = []
    for w in raw:
        processed.append({
            'date':       w.get('id') or '',
            'ctl':        w.get('ctl'),
            'atl':        w.get('atl'),
            'tsb':        w.get('tsb'),
            'tss':        w.get('trainingLoad') or 0,
            'hrv':        w.get('hrv'),
            'resting_hr': w.get('restingHR'),
            'sleep':      round(w['sleepSecs'] / 3600, 1) if w.get('sleepSecs') else None,
            'weight':     w.get('weight'),
            'fatigue':    w.get('fatigue'),
            'mood':       w.get('mood')
        })
    return sorted(processed, key=lambda x: x['date'])


def deduplicate(items, key='id'):
    seen = set()
    result = []
    for item in items:
        k = str(item.get(key, ''))
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def aggregate_weekly_tss(activities):
    weeks = {}
    for a in activities:
        if not a['date']:
            continue
        d = datetime.strptime(a['date'], '%Y-%m-%d')
        iso = d.isocalendar()
        key = f'{iso[0]}-W{iso[1]:02d}'
        if key not in weeks:
            weeks[key] = {'week': f'W{iso[1]}', 'year': iso[0], 'ride': 0, 'run': 0, 'row': 0, 'other': 0}
        tss = a['tss'] or 0
        t = a['type']
        if t in ('Ride','VirtualRide'):   weeks[key]['ride'] += tss
        elif t in ('Run','VirtualRun'):   weeks[key]['run'] += tss
        elif t in ('Rowing','Kayaking'):  weeks[key]['row'] += tss
        else:                              weeks[key]['other'] += tss
    return sorted(weeks.values(), key=lambda x: (x['year'], x['week']))


def calc_ytd(activities):
    year = str(datetime.now().year)
    ytd     = [a for a in activities if a['date'].startswith(year)]
    cycling = [a for a in ytd if a['type'] in ('Ride','VirtualRide')]
    running = [a for a in ytd if a['type'] in ('Run','VirtualRun')]
    rowing  = [a for a in ytd if a['type'] in ('Rowing',)]
    def s(arr):
        return {
            'distance': round(sum(a['distance'] or 0 for a in arr)/1000),
            'hours':    round(sum(a['duration'] or 0 for a in arr)/3600, 1),
            'tss':      sum(a['tss'] or 0 for a in arr),
            'count':    len(arr)
        }
    return {'total': s(ytd), 'cycling': s(cycling), 'running': s(running), 'rowing': s(rowing)}


def build_heatmap(activities, days=365):
    act_by_date = {}
    for a in activities:
        if not a['date']:
            continue
        act_by_date[a['date']] = act_by_date.get(a['date'], 0) + (a['tss'] or 0)
    cells = []
    end = datetime.now()
    for i in range(days - 1, -1, -1):
        d = end - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        tss = act_by_date.get(ds, 0)
        level = 0
        if tss > 0:   level = 1
        if tss > 40:  level = 2
        if tss > 80:  level = 3
        if tss > 120: level = 4
        if tss > 180: level = 5
        cells.append({'date': ds, 'level': level, 'tss': tss})
    return cells


def save_json(data, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    log.info(f'Saved {path} ({len(json.dumps(data))//1024}kb)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oldest', default=HISTORY_START)
    args = parser.parse_args()

    if not API_KEY:
        raise ValueError('INTERVALS_API_KEY environment variable not set')

    # Initialize Intervals client
    client = IntervalsClient(ATHLETE_ID, API_KEY)
    athlete = client.get_athlete()
    raw_intervals = deduplicate(client.get_activities(args.oldest))

    # Fetch power curve and calculate CP metrics
    power_curve = client.fetch_power_curve(days=90)
    cp_metrics = client.calculate_cp_metrics(power_curve)

    # Fetch Strava data
    strava_acts = []
    strava = None
    if STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN:
        try:
            strava = StravaClient(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN)
            strava.authenticate()
            oldest_ts = int(datetime.strptime(args.oldest, '%Y-%m-%d').timestamp())
            strava_acts = strava.get_activities(oldest_ts)
        except Exception as e:
            log.error(f'Strava fetch failed: {e}')
    else:
        log.warning('Strava credentials not configured')

    # Fetch Concept2 data
    concept2_acts = []
    if CONCEPT2_USERNAME and CONCEPT2_PASSWORD:
        try:
            concept2 = Concept2Client(CONCEPT2_USERNAME, CONCEPT2_PASSWORD)
            if concept2.authenticate():
                concept2_acts = concept2.get_workouts(args.oldest)
        except Exception as e:
            log.error(f'Concept2 fetch failed: {e}')
    else:
        log.warning('Concept2 credentials not configured')

    # Merge all activities
    activities = merge_activities(raw_intervals, strava_acts, concept2_acts)
    save_json(activities, 'activities.json')

    # Process wellness data
    wellness = process_wellness(client.get_wellness(args.oldest))
    save_json(wellness, 'wellness.json')

    # Get latest metrics
    weight  = next((a['weight']  for a in activities if a.get('weight')),  None)
    ftp     = next((a['ftp']     for a in activities if a.get('ftp')),     None)
    w_prime = next((a['w_prime'] for a in activities if a.get('w_prime')), None)
    if weight is None:
        weight = next((w['weight'] for w in reversed(wellness) if w.get('weight')), None)

    # Save athlete data
    save_json({
        'id': ATHLETE_ID, 
        'name': athlete.get('name',''), 
        'weight': weight, 
        'ftp': ftp, 
        'w_prime': w_prime
    }, 'athlete.json')

    # Save cycling-specific metrics
    cycling_metrics = {
        'cp_90d': cp_metrics['cp'],
        'w_prime': cp_metrics['w_prime'],
        'ftp': ftp or 0,
        'weight': weight or 0,
        'w_per_kg': round(cp_metrics['cp'] / weight, 2) if cp_metrics['cp'] and weight else 0,
        'peak_power': {
            '1min': cp_metrics['power_1min'],
            '5min': cp_metrics['power_5min'],
            '20min': cp_metrics['power_20min']
        },
        'power_curve': power_curve,
        'last_updated': datetime.now().isoformat()
    }
    save_json(cycling_metrics, 'cycling_metrics.json')

    # Save other data files
    save_json(aggregate_weekly_tss(activities), 'weekly_tss.json')
    save_json(calc_ytd(activities), 'ytd.json')
    save_json(build_heatmap(activities, 365), 'heatmap_1y.json')

    # Save segments if Strava available
    if strava:
        try:
            save_json(build_segments(strava, activities), 'segments.json')
        except Exception as e:
            log.error(f'Segment fetch failed: {e}')
            save_json({'cycling':[], 'running':[]}, 'segments.json')
    else:
        save_json({'cycling':[], 'running':[]}, 'segments.json')

    # Save metadata
    save_json({
        'last_updated': datetime.now().isoformat(),
        'activity_count': len(activities),
        'oldest_date': args.oldest,
        'weight': weight, 
        'ftp': ftp, 
        'w_prime': w_prime,
        'cp_90d': cp_metrics['cp']
    }, 'meta.json')

    log.info(f'Done. {len(activities)} total activities')


if __name__ == '__main__':
    main()
