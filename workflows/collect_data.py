"""
FITNESS DASHBOARD — DATA COLLECTOR
Fetches from Intervals.icu and saves to docs/data/ for static site serving
"""

import os
import json
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

ATHLETE_ID  = os.getenv('INTERVALS_ATHLETE_ID', '5718022')
API_KEY     = os.getenv('INTERVALS_API_KEY', '')
BASE_URL    = 'https://intervals.icu/api/v1'
HISTORY_START = '2025-01-01'
OUTPUT_DIR  = Path(__file__).parent.parent / 'docs' / 'data'


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
        log.info(f'Fetching activities from {oldest}')
        data = self._get(f'athlete/{self.athlete_id}/activities', {'oldest': oldest})
        log.info(f'Got {len(data)} activities')
        return data

    def get_wellness(self, oldest=HISTORY_START):
        today = datetime.now().strftime('%Y-%m-%d')
        log.info(f'Fetching wellness {oldest} → {today}')
        data = self._get(f'athlete/{self.athlete_id}/wellness', {
            'oldest': oldest,
            'newest': today
        })
        log.info(f'Got {len(data)} wellness entries')
        return data


def deduplicate(items, key='id'):
    seen = set()
    result = []
    for item in items:
        k = str(item.get(key, ''))
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def process_activities(raw):
    processed = []
    for a in raw:
        if a.get('_note') or not a.get('type'):
            continue
        processed.append({
            'id':          str(a.get('id', '')),
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
            'if_val':      round(a.get('icu_intensity') / 100, 2) if a.get('icu_intensity') else None,
            'ftp':         a.get('icu_ftp'),
            'w_prime':     a.get('icu_w_prime'),
            'weight':      a.get('icu_weight'),
            'device':      a.get('device_name') or '',
            'is_garmin':   'garmin' in (a.get('device_name') or '').lower()
        })
    return sorted(processed, key=lambda x: x['date'], reverse=True)


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


def aggregate_weekly_tss(activities):
    weeks = {}
    for a in activities:
        if not a['date']:
            continue
        d = datetime.strptime(a['date'], '%Y-%m-%d')
        # ISO week key
        iso = d.isocalendar()
        key = f'{iso[0]}-W{iso[1]:02d}'
        if key not in weeks:
            weeks[key] = {'week': f'W{iso[1]}', 'year': iso[0], 'ride': 0, 'run': 0, 'row': 0, 'other': 0}
        tss = a['tss'] or 0
        t = a['type']
        if t in ('Ride', 'VirtualRide'):
            weeks[key]['ride'] += tss
        elif t in ('Run', 'VirtualRun'):
            weeks[key]['run'] += tss
        elif t in ('Rowing', 'Kayaking'):
            weeks[key]['row'] += tss
        else:
            weeks[key]['other'] += tss
    return sorted(weeks.values(), key=lambda x: (x['year'], x['week']))


def calc_ytd(activities):
    year = str(datetime.now().year)
    ytd = [a for a in activities if a['date'].startswith(year)]
    cycling = [a for a in ytd if a['type'] in ('Ride', 'VirtualRide')]
    running = [a for a in ytd if a['type'] in ('Run', 'VirtualRun')]

    def s(arr):
        return {
            'distance': round(sum(a['distance'] or 0 for a in arr) / 1000),
            'hours':    round(sum(a['duration'] or 0 for a in arr) / 3600, 1),
            'tss':      sum(a['tss'] or 0 for a in arr),
            'count':    len(arr)
        }

    return {'total': s(ytd), 'cycling': s(cycling), 'running': s(running)}


def build_heatmap(activities, days=365):
    act_by_date = {}
    for a in activities:
        if not a['date']:
            continue
        tss = a['tss'] or 0
        act_by_date[a['date']] = act_by_date.get(a['date'], 0) + tss

    cells = []
    end = datetime.now()
    for i in range(days - 1, -1, -1):
        d = end - timedelta(days=i)
        date_str = d.strftime('%Y-%m-%d')
        tss = act_by_date.get(date_str, 0)
        level = 0
        if tss > 0:   level = 1
        if tss > 40:  level = 2
        if tss > 80:  level = 3
        if tss > 120: level = 4
        if tss > 180: level = 5
        cells.append({'date': date_str, 'level': level, 'tss': tss})
    return cells


def save_json(data, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    log.info(f'Saved {path} ({len(json.dumps(data)) // 1024}kb)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oldest', default=HISTORY_START)
    args = parser.parse_args()

    if not API_KEY:
        raise ValueError('INTERVALS_API_KEY environment variable not set')

    client = IntervalsClient(ATHLETE_ID, API_KEY)

    # Athlete info
    log.info('Fetching athlete info...')
    athlete = client.get_athlete()

    # Activities
    log.info('Fetching activities...')
    raw_activities = client.get_activities(args.oldest)
    raw_activities = deduplicate(raw_activities)
    activities = process_activities(raw_activities)
    save_json(activities, 'activities.json')

    # Wellness
    log.info('Fetching wellness...')
    raw_wellness = client.get_wellness(args.oldest)
    wellness = process_wellness(raw_wellness)
    save_json(wellness, 'wellness.json')

    # Aggregates
    log.info('Building aggregates...')
    save_json(aggregate_weekly_tss(activities), 'weekly_tss.json')
    save_json(calc_ytd(activities), 'ytd.json')
    save_json(build_heatmap(activities, 365), 'heatmap_1y.json')
    save_json(build_heatmap(activities, 1095), 'heatmap_3y.json')

    # Meta
    save_json({
        'last_updated': datetime.now().isoformat(),
        'activity_count': len(activities),
        'oldest_date': args.oldest
    }, 'meta.json')

    # Extract weight/ftp/wbal from activities, fall back to wellness
    weight  = next((a['weight']  for a in activities if a.get('weight')),  None)
    ftp     = next((a['ftp']     for a in activities if a.get('ftp')),     None)
    w_prime = next((a['w_prime'] for a in activities if a.get('w_prime')), None)
    if weight is None:
        weight = next((w['weight'] for w in reversed(wellness) if w.get('weight')), None)
    save_json({'id': ATHLETE_ID, 'name': athlete.get('name',''), 'weight': weight, 'ftp': ftp, 'w_prime': w_prime}, 'athlete.json')
    log.info('All data saved to docs/data/')


if __name__ == '__main__':
    main()
