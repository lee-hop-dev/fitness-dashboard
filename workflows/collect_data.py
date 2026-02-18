"""
<<<<<<< Updated upstream
FITNESS DASHBOARD — DATA COLLECTOR v4.3
Fetches from Intervals.icu + Strava + Concept2 and saves to docs/data/
=======
Intervals.icu Data Collector for Fitness Dashboard
Fixed version with proper null handling
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
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


class Concept2Client:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None

    def authenticate(self):
        log.info('Authenticating with Concept2...')
=======
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < 2:  # Don't wait on last attempt
                    time.sleep(5)
        
        return None
    
    def get_activities(self, oldest: str = "2025-01-01", newest: str = None) -> List[Dict]:
        """Get activities with proper field mapping"""
        if newest is None:
            newest = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            'oldest': oldest,
            'newest': newest
        }
        
        activities = self._make_request('activities', params)
        if not activities:
            print("Failed to fetch activities")
            return []
        
        print(f"Fetched {len(activities)} activities")
        
        # Filter out Strava stub activities
        valid_activities = []
        for activity in activities:
            # Skip Strava stubs
            if activity.get('_note') or not activity.get('type'):
                continue
            
            valid_activities.append(activity)
        
        print(f"After filtering: {len(valid_activities)} valid activities")
        return valid_activities
    
    def get_wellness(self, oldest: str = "2025-01-01", newest: str = None) -> List[Dict]:
        """Get wellness data"""
        if newest is None:
            newest = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            'oldest': oldest,
            'newest': newest
        }
        
        wellness = self._make_request('wellness', params)
        if not wellness:
            print("Failed to fetch wellness data")
            return []
        
        print(f"Fetched {len(wellness)} wellness entries")
        return wellness
    
    def get_athlete(self) -> Dict:
        """Get athlete information"""
        athlete = self._make_request('')  # Empty endpoint for athlete info
        if not athlete:
            print("Failed to fetch athlete data")
            return {}
        
        print("Fetched athlete data")
        return athlete

class DataCollector:
    """Collects and processes fitness data"""
    
    def __init__(self, api_key: str):
        self.client = IntervalsClient(api_key)
        self.data_dir = "docs/data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def collect_all_data(self):
        """Collect all data and save to JSON files"""
        print("Starting data collection...")
        
        # Get data from API
        activities = self.client.get_activities()
        wellness = self.client.get_wellness()
        athlete = self.client.get_athlete()
        
        if not activities:
            print("ERROR: No activities data received")
            sys.exit(1)
        
        # Process and save data
        self._save_activities(activities)
        self._save_wellness(wellness)
        self._save_athlete(athlete, activities)
        self._save_weekly_tss(activities)
        self._save_ytd_totals(activities)
        self._save_heatmap_data(activities)
        self._save_meta()
        
        print("Data collection completed successfully!")
    
    def _safe_get(self, obj: Dict, key: str, default=None):
        """Safely get value from dict with null checking"""
        value = obj.get(key)
        return value if value is not None else default
    
    def _safe_divide(self, numerator, denominator, default=None):
        """Safely divide with null checking"""
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator
    
    def _save_activities(self, activities: List[Dict]):
        """Save activities data"""
        # Sort by date (most recent first)
        activities_sorted = sorted(
            activities, 
            key=lambda x: x.get('start_date_local', ''), 
            reverse=True
        )
        
        self._save_json('activities.json', activities_sorted)
        print(f"Saved {len(activities_sorted)} activities")
    
    def _save_wellness(self, wellness: List[Dict]):
        """Save wellness data"""
        # Sort by date
        wellness_sorted = sorted(
            wellness, 
            key=lambda x: x.get('id', ''), 
            reverse=False
        )
        
        self._save_json('wellness.json', wellness_sorted)
        print(f"Saved {len(wellness_sorted)} wellness entries")
    
    def _save_athlete(self, athlete: Dict, activities: List[Dict]):
        """Save athlete data with latest values from activities"""
        # Extract latest values from activities since they're not in athlete endpoint
        latest_weight = None
        latest_ftp = None
        latest_w_prime = None
        
        for activity in reversed(activities):  # Go through from oldest to newest
            if self._safe_get(activity, 'icu_weight') and not latest_weight:
                latest_weight = activity['icu_weight']
            if self._safe_get(activity, 'icu_ftp') and not latest_ftp:
                latest_ftp = activity['icu_ftp']
            if self._safe_get(activity, 'icu_w_prime') and not latest_w_prime:
                latest_w_prime = activity['icu_w_prime']
        
        # Update athlete data with latest values
        athlete_data = athlete.copy()
        if latest_weight:
            athlete_data['weight'] = latest_weight
        if latest_ftp:
            athlete_data['ftp'] = latest_ftp
        if latest_w_prime:
            athlete_data['w_prime'] = latest_w_prime
        
        self._save_json('athlete.json', athlete_data)
        print(f"Saved athlete data (weight: {latest_weight}, ftp: {latest_ftp}, w': {latest_w_prime})")
    
    def _save_weekly_tss(self, activities: List[Dict]):
        """Calculate and save weekly TSS data"""
        weekly_data = []
        
        # Group activities by week
        weeks = {}
        for activity in activities:
            start_date = self._safe_get(activity, 'start_date_local')
            tss = self._safe_get(activity, 'tss', 0)
            
            if not start_date:
                continue
            
            try:
                activity_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                # Get Monday of the week
                week_start = activity_date - timedelta(days=activity_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weeks:
                    weeks[week_key] = {
                        'week': week_key,
                        'start_date': week_key,
                        'tss': 0,
                        'cycling_tss': 0,
                        'running_tss': 0,
                        'other_tss': 0
                    }
                
                weeks[week_key]['tss'] += tss
                
                # Categorize by activity type
                activity_type = self._safe_get(activity, 'type', '').lower()
                if activity_type in ['ride', 'virtualride']:
                    weeks[week_key]['cycling_tss'] += tss
                elif activity_type in ['run', 'virtualrun']:
                    weeks[week_key]['running_tss'] += tss
                else:
                    weeks[week_key]['other_tss'] += tss
                    
            except (ValueError, TypeError) as e:
                print(f"Error parsing date {start_date}: {e}")
                continue
        
        # Convert to list and sort by date
        weekly_data = sorted(weeks.values(), key=lambda x: x['week'])
        
        self._save_json('weekly_tss.json', weekly_data)
        print(f"Saved {len(weekly_data)} weeks of TSS data")
    
    def _save_ytd_totals(self, activities: List[Dict]):
        """Calculate and save year-to-date totals"""
        current_year = datetime.now().year
        
        ytd_data = {
            'year': current_year,
            'cycling': {'distance': 0, 'time': 0, 'elevation': 0, 'count': 0},
            'running': {'distance': 0, 'time': 0, 'elevation': 0, 'count': 0},
            'total': {'distance': 0, 'time': 0, 'elevation': 0, 'count': 0}
        }
        
        for activity in activities:
            start_date = self._safe_get(activity, 'start_date_local')
            if not start_date:
                continue
            
            try:
                activity_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if activity_date.year != current_year:
                    continue
                
                distance = self._safe_get(activity, 'distance', 0)
                time = self._safe_get(activity, 'moving_time', self._safe_get(activity, 'elapsed_time', 0))
                elevation = self._safe_get(activity, 'total_elevation_gain', 0)
                
                # Update totals
                ytd_data['total']['distance'] += distance
                ytd_data['total']['time'] += time
                ytd_data['total']['elevation'] += elevation
                ytd_data['total']['count'] += 1
                
                # Update by category
                activity_type = self._safe_get(activity, 'type', '').lower()
                if activity_type in ['ride', 'virtualride']:
                    ytd_data['cycling']['distance'] += distance
                    ytd_data['cycling']['time'] += time
                    ytd_data['cycling']['elevation'] += elevation
                    ytd_data['cycling']['count'] += 1
                elif activity_type in ['run', 'virtualrun']:
                    ytd_data['running']['distance'] += distance
                    ytd_data['running']['time'] += time
                    ytd_data['running']['elevation'] += elevation
                    ytd_data['running']['count'] += 1
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing activity date {start_date}: {e}")
                continue
        
        self._save_json('ytd.json', ytd_data)
        print(f"Saved YTD totals for {current_year}")
    
    def _save_heatmap_data(self, activities: List[Dict]):
        """Generate heatmap data for calendar view"""
        # 1 year heatmap
        one_year_ago = datetime.now() - timedelta(days=365)
        heatmap_1y = self._generate_heatmap(activities, one_year_ago)
        self._save_json('heatmap_1y.json', heatmap_1y)
        
        print("Saved heatmap data")
    
    def _generate_heatmap(self, activities: List[Dict], start_date: datetime) -> Dict:
        """Generate heatmap data structure"""
        heatmap_data = {}
        
        for activity in activities:
            start_date_str = self._safe_get(activity, 'start_date_local')
            if not start_date_str:
                continue
            
            try:
                activity_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                if activity_date < start_date:
                    continue
                
                date_key = activity_date.strftime('%Y-%m-%d')
                
                if date_key not in heatmap_data:
                    heatmap_data[date_key] = {
                        'activities': [],
                        'tss': 0,
                        'distance': 0,
                        'time': 0
                    }
                
                activity_tss = self._safe_get(activity, 'tss', 0)
                activity_distance = self._safe_get(activity, 'distance', 0)
                activity_time = self._safe_get(activity, 'moving_time', self._safe_get(activity, 'elapsed_time', 0))
                
                heatmap_data[date_key]['activities'].append({
                    'type': self._safe_get(activity, 'type'),
                    'name': self._safe_get(activity, 'name', ''),
                    'tss': activity_tss
                })
                
                heatmap_data[date_key]['tss'] += activity_tss
                heatmap_data[date_key]['distance'] += activity_distance
                heatmap_data[date_key]['time'] += activity_time
                
            except (ValueError, TypeError) as e:
                print(f"Error processing heatmap activity date {start_date_str}: {e}")
                continue
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'data': heatmap_data
        }
    
    def _save_meta(self):
        """Save metadata about the data collection"""
        meta = {
            'last_updated': datetime.now().isoformat(),
            'collection_version': '2.1',
            'data_source': 'intervals.icu',
            'athlete_id': self.client.athlete_id
        }
        
        self._save_json('meta.json', meta)
        print("Saved metadata")
    
    def _save_json(self, filename: str, data: Any):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
>>>>>>> Stashed changes
        try:
            r = requests.post('https://log.concept2.com/api/auth/token', data={
                'username': self.username,
                'password': self.password,
                'grant_type': 'password'
            })
            r.raise_for_status()
            data = r.json()
            self.access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            self.session.headers['Authorization'] = f'Bearer {self.access_token}'
            log.info('Concept2 authentication successful')
            return True
        except Exception as e:
            log.error(f'Concept2 authentication failed: {e}')
            return False

    def _get(self, endpoint, params=None):
        if not self.access_token or datetime.now() >= self.token_expiry:
            if not self.authenticate():
                return None
        
        url = f'https://log.concept2.com/api/{endpoint}'
        try:
            time.sleep(0.5)
            r = self.session.get(url, params=params or {})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f'Concept2 request failed: {e}')
            return None

    def get_workouts(self, start_date):
        log.info('Fetching Concept2 workouts...')
        end_date = datetime.now().strftime('%Y-%m-%d')
        data = self._get('users/me/results', {'from': start_date, 'to': end_date})
        
        if data and 'data' in data:
            workouts = data['data']
            log.info(f'Got {len(workouts)} workouts from Concept2')
            return workouts
        else:
            log.warning('No Concept2 workout data returned')
            return []


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


def process_concept2_activity(w):
    try:
        # Enhanced time handling for Concept2's centisecond format
        duration_raw = w.get('time', 0)
        if duration_raw == 0:
            print(f"⚠️ Concept2 workout missing time: {w.get('id')}")
            return None
            
        # Concept2 time is in centiseconds (1/100 second)
        duration_seconds = duration_raw / 100
        distance = w.get('distance', 0)
        
        # Enhanced heart rate processing
        hr_data = w.get('heart_rate', {})
        avg_hr = None
        max_hr = None
        
        if isinstance(hr_data, dict):
            avg_hr = hr_data.get('average')
            max_hr = hr_data.get('max')
        elif isinstance(hr_data, (int, float)):
            avg_hr = hr_data
            
        # Calculate average pace (seconds per 500m)
        avg_pace = (duration_seconds / distance * 500) if distance > 0 else None
        
        # Enhanced workout naming
        workout_date = w.get('date', '')[:10] if w.get('date') else 'Unknown'
        if distance > 0:
            workout_name = f"Concept2 Rowing - {distance}m"
        elif duration_seconds > 0:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            workout_name = f"Concept2 Rowing - {minutes}:{seconds:02d}"
        else:
            workout_name = "Concept2 Rowing"
            
        activity = {
            'id':          f"concept2_{w.get('id', '')}",
            'strava_id':   None,
            'source':      'CONCEPT2',  # This is key!
            'name':        workout_name,
            'type':        'Rowing',    # This is key!
            'date':        workout_date,
            'duration':    duration_seconds,
            'distance':    distance,
            'elevation':   0,
            'avg_power':   None,
            'norm_power':  None,
            'avg_hr':      avg_hr,
            'max_hr':      max_hr,
            'avg_speed':   distance / duration_seconds if duration_seconds > 0 else None,
            'avg_cadence': w.get('stroke_rate'),  # Stroke rate in strokes per minute
            'calories':    w.get('calories'),
            'tss':         0,
            'if_val':      None,
            'ftp':         None,
            'w_prime':     None,
            'weight':      None,
            'device':      'Concept2 RowErg',
            'is_garmin':   False
        }
        
        print(f"✅ Processed Concept2: {workout_name} on {workout_date}")
        return activity
        
    except Exception as e:
        print(f"❌ Error processing Concept2 workout {w.get('id', 'unknown')}: {e}")
        print(f"Raw workout data: {w}")
        return None


def merge_activities(intervals_raw, strava_acts, concept2_acts):
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

    added_strava = 0
    for a in strava_acts:
        if str(a.get('id','')) not in strava_ids_covered:
            processed.append(process_strava_activity(a))
            added_strava += 1

    log.info(f'Strava: added {added_strava} additional activities')

    added_concept2 = 0
    for w in concept2_acts:
        processed.append(process_concept2_activity(w))
        added_concept2 += 1

    log.info(f'Concept2: added {added_concept2} rowing workouts')

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
<<<<<<< Updated upstream
    parser = argparse.ArgumentParser()
    parser.add_argument('--oldest', default=HISTORY_START)
    args = parser.parse_args()
=======
    """Main function"""
    api_key = os.getenv('INTERVALS_API_KEY')
    if not api_key:
        print("ERROR: INTERVALS_API_KEY environment variable not set")
        sys.exit(1)
    
    try:
        collector = DataCollector(api_key)
        collector.collect_all_data()
    except Exception as e:
        print(f"ERROR: Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
>>>>>>> Stashed changes

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

    activities = merge_activities(raw_intervals, strava_acts, concept2_acts)
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
