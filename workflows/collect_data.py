"""
FITNESS DASHBOARD — DATA COLLECTOR v4.2
Fetches from Intervals.icu + Strava and saves to docs/data/
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
        return data

    def get_wellness(self, oldest=HISTORY_START):
        today = datetime.now().strftime('%Y-%m-%d')
        data = self._get(f'athlete/{self.athlete_id}/wellness', {'oldest': oldest, 'newest': today})
        log.info(f'Got {len(data)} wellness entries')
        return data


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
        log.info(f'Got {len(all_acts)} activities from Strava')
        return all_acts

    def get_activity_segments(self, activity_id):
        data = self._get(f'activities/{activity_id}', {'include_all_efforts': True})
        return data.get('segment_efforts', []) if data else []


def process_intervals_activity(a):
    raw_if = a.get('icu_intensity')
    if_val = round(raw_if / 100, 2) if raw_if else None
    return {
        'id':          str(a.get('id', '')),
        'strava_id':   str(a.get('strava_id', '')) if a.get('strava_id') else None,
        'source':      a.get('source', 'INTERVALS'),
        'name':        a.get('name') or 'Activity',
        'type':        a.get('type') or 'Unknown',
        'date':        (a.get('start_date_local') or '')[:10],
        'duration':    a.get('moving_time') or 0,
        'distance':    a.get('distance') or 0,
        'elevation':   a.get('total_elevation_gain') or 0,
        'avg_power':   a.get('icu_average_watts'),
        'norm_power':  a.get('icu_weighted_avg_watts'),
        'avg_hr':      a.get('average_heartrate'),
        'max_hr':      a.get('max_heartrate'),
        'avg_speed':   a.get('average_speed'),
        'avg_cadence': a.get('average_cadence'),
        'calories':    a.get('calories'),
        'tss':         round(a.get('icu_training_load') or 0),
        'if_val':      if_val,
        'ftp':         a.get('icu_ftp'),
        'w_prime':     a.get('icu_w_prime'),
        'weight':      a.get('icu_weight'),
        'device':      a.get('device_name') or '',
        'is_garmin':   'garmin' in (a.get('device_name') or '').lower()
    }


def process_strava_activity(a):
    type_map = {
        'Ride':'Ride','VirtualRide':'VirtualRide','Run':'Run','VirtualRun':'VirtualRun',
        'Rowing':'Rowing','Kayaking':'Kayaking','WeightTraining':'WeightTraining',
        'Workout':'Workout','Yoga':'Yoga','Walk':'Walk','Hike':'Hike','Swim':'Swim',
        'Crossfit':'Crossfit','Elliptical':'Cardio','StairStepper':'Cardio'
    }
    act_type = type_map.get(a.get('sport_type') or a.get('type',''), a.get('sport_type','Other'))
    return {
        'id':          f"strava_{a.get('id','')}",
        'strava_id':   str(a.get('id','')),
        'source':      'STRAVA',
        'name':        a.get('name') or 'Activity',
        'type':        act_type,
        'date':        (a.get('start_date_local') or '')[:10],
        'duration':    a.get('moving_time') or 0,
        'distance':    a.get('distance') or 0,
        'elevation':   a.get('total_elevation_gain') or 0,
        'avg_power':   a.get('average_watts'),
        'norm_power':  a.get('weighted_average_watts'),
        'avg_hr':      a.get('average_heartrate'),
        'max_hr':      a.get('max_heartrate'),
        'avg_speed':   a.get('average_speed'),
        'avg_cadence': a.get('average_cadence'),
        'calories':    a.get('calories'),
        'tss':         0,
        'if_val':      None,
        'ftp':         None,
        'w_prime':     None,
        'weight':      None,
        'device':      a.get('device_name') or '',
        'is_garmin':   False
    }


def merge_activities(intervals_raw, strava_acts):
    processed = []
    strava_ids_covered = set()
    skipped = 0

    for a in intervals_raw:
        if a.get('_note') or not a.get('type'):
            if a.get('strava_id'):
                strava_ids_covered.add(str(a.get('strava_id')))
            skipped += 1
            continue
        act = process_intervals_activity(a)
        if act['strava_id']:
            strava_ids_covered.add(act['strava_id'])
        processed.append(act)

    log.info(f'Intervals: {len(processed)} real activities, {skipped} stubs')

    added = 0
    for a in strava_acts:
        if str(a.get('id','')) not in strava_ids_covered:
            processed.append(process_strava_activity(a))
            added += 1

    log.info(f'Strava: added {added} additional activities')
    return sorted(processed, key=lambda x: x['date'], reverse=True)


def build_segments(strava, activities):
    segments = {'cycling': [], 'running': []}
    cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    recent = [a for a in activities if a.get('strava_id') and a['date'] >= cutoff][:10]
    seen = set()

    for act in recent:
        efforts = strava.get_activity_segments(act['strava_id'])
        for e in efforts:
            seg = e.get('segment', {})
            sid = seg.get('id')
            if sid in seen:
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
    def s(arr):
        return {
            'distance': round(sum(a['distance'] or 0 for a in arr)/1000),
            'hours':    round(sum(a['duration'] or 0 for a in arr)/3600, 1),
            'tss':      sum(a['tss'] or 0 for a in arr),
            'count':    len(arr)
        }
    return {'total': s(ytd), 'cycling': s(cycling), 'running': s(running)}


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

    client = IntervalsClient(ATHLETE_ID, API_KEY)
    athlete = client.get_athlete()
    raw_intervals = deduplicate(client.get_activities(args.oldest))

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

    activities = merge_activities(raw_intervals, strava_acts)
    save_json(activities, 'activities.json')

    wellness = process_wellness(client.get_wellness(args.oldest))
    save_json(wellness, 'wellness.json')

    weight  = next((a['weight']  for a in activities if a.get('weight')),  None)
    ftp     = next((a['ftp']     for a in activities if a.get('ftp')),     None)
    w_prime = next((a['w_prime'] for a in activities if a.get('w_prime')), None)
    if weight is None:
        weight = next((w['weight'] for w in reversed(wellness) if w.get('weight')), None)

    save_json({'id': ATHLETE_ID, 'name': athlete.get('name',''), 'weight': weight, 'ftp': ftp, 'w_prime': w_prime}, 'athlete.json')
    save_json(aggregate_weekly_tss(activities), 'weekly_tss.json')
    save_json(calc_ytd(activities), 'ytd.json')
    save_json(build_heatmap(activities, 365), 'heatmap_1y.json')

    if strava:
        try:
            save_json(build_segments(strava, activities), 'segments.json')
        except Exception as e:
            log.error(f'Segment fetch failed: {e}')
            save_json({'cycling':[], 'running':[]}, 'segments.json')
    else:
        save_json({'cycling':[], 'running':[]}, 'segments.json')

    save_json({
        'last_updated': datetime.now().isoformat(),
        'activity_count': len(activities),
        'oldest_date': args.oldest,
        'weight': weight, 'ftp': ftp, 'w_prime': w_prime
    }, 'meta.json')

    log.info(f'Done. {len(activities)} total activities')


if __name__ == '__main__':
    main()
