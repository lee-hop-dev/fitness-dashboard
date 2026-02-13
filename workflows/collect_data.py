#!/usr/bin/env python3
"""
Intervals.icu Data Collector for Fitness Dashboard
Updated version with comprehensive error handling and data validation
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class IntervalsClient:
    """Client for Intervals.icu API with proper error handling"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://intervals.icu/api/v1"
        self.athlete_id = "5718022"  # Lee Hopkins athlete ID
        self.session = requests.Session()
        self.session.auth = ('API_KEY', api_key)
        self.session.headers.update({
            'User-Agent': 'FitnessDashboard/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with error handling and retries"""
        url = f"{self.base_url}/athlete/{self.athlete_id}/{endpoint}"
        
        for attempt in range(3):  # 3 retry attempts
            try:
                print(f"Making request to: {endpoint} (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    print(f"Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                else:
                    print(f"API request failed: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < 2:  # Don't wait on last attempt
                    time.sleep(10)
        
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
        
        # Filter out Strava stub activities and map fields correctly
        valid_activities = []
        for activity in activities:
            # Skip Strava stubs
            if activity.get('_note') or not activity.get('type'):
                continue
            
            # Map fields correctly according to API documentation
            mapped_activity = self._map_activity_fields(activity)
            valid_activities.append(mapped_activity)
        
        print(f"After filtering: {len(valid_activities)} valid activities")
        return valid_activities
    
    def _map_activity_fields(self, activity: Dict) -> Dict:
        """Map activity fields to correct names"""
        # Create a copy to avoid modifying the original
        mapped = activity.copy()
        
        # Map power fields correctly
        if 'icu_average_watts' in activity:
            mapped['average_watts'] = activity['icu_average_watts']
        if 'icu_weighted_avg_watts' in activity:
            mapped['weighted_average_watts'] = activity['icu_weighted_avg_watts']
        if 'icu_intensity' in activity:
            mapped['intensity_factor'] = activity['icu_intensity'] / 100  # Convert from percentage
        
        # Map heart rate fields
        if 'average_heartrate' in activity:
            mapped['average_hr'] = activity['average_heartrate']
        if 'max_heartrate' in activity:
            mapped['max_hr'] = activity['max_heartrate']
        
        # Map weight and FTP fields
        if 'icu_weight' in activity:
            mapped['weight'] = activity['icu_weight']
        if 'icu_ftp' in activity:
            mapped['ftp'] = activity['icu_ftp']
        if 'icu_w_prime' in activity:
            mapped['w_prime'] = activity['icu_w_prime']
        
        return mapped
    
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
            if activity.get('icu_weight') and not latest_weight:
                latest_weight = activity['icu_weight']
            if activity.get('icu_ftp') and not latest_ftp:
                latest_ftp = activity['icu_ftp']
            if activity.get('icu_w_prime') and not latest_w_prime:
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
            if not activity.get('start_date_local') or not activity.get('tss'):
                continue
            
            activity_date = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
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
            
            tss = activity['tss']
            weeks[week_key]['tss'] += tss
            
            # Categorize by activity type
            activity_type = activity.get('type', '').lower()
            if activity_type in ['ride', 'virtualride']:
                weeks[week_key]['cycling_tss'] += tss
            elif activity_type in ['run', 'virtualrun']:
                weeks[week_key]['running_tss'] += tss
            else:
                weeks[week_key]['other_tss'] += tss
        
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
            if not activity.get('start_date_local'):
                continue
            
            activity_date = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
            if activity_date.year != current_year:
                continue
            
            distance = activity.get('distance', 0)
            time = activity.get('moving_time', activity.get('elapsed_time', 0))
            elevation = activity.get('total_elevation_gain', 0)
            
            # Update totals
            ytd_data['total']['distance'] += distance
            ytd_data['total']['time'] += time
            ytd_data['total']['elevation'] += elevation
            ytd_data['total']['count'] += 1
            
            # Update by category
            activity_type = activity.get('type', '').lower()
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
        
        self._save_json('ytd.json', ytd_data)
        print(f"Saved YTD totals for {current_year}")
    
    def _save_heatmap_data(self, activities: List[Dict]):
        """Generate heatmap data for calendar view"""
        # 1 year heatmap
        one_year_ago = datetime.now() - timedelta(days=365)
        heatmap_1y = self._generate_heatmap(activities, one_year_ago)
        self._save_json('heatmap_1y.json', heatmap_1y)
        
        # 3 year heatmap (removed as per requirements)
        # three_years_ago = datetime.now() - timedelta(days=365*3)
        # heatmap_3y = self._generate_heatmap(activities, three_years_ago)
        # self._save_json('heatmap_3y.json', heatmap_3y)
        
        print("Saved heatmap data")
    
    def _generate_heatmap(self, activities: List[Dict], start_date: datetime) -> Dict:
        """Generate heatmap data structure"""
        heatmap_data = {}
        
        for activity in activities:
            if not activity.get('start_date_local'):
                continue
            
            activity_date = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00'))
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
            
            heatmap_data[date_key]['activities'].append({
                'type': activity.get('type'),
                'name': activity.get('name', ''),
                'tss': activity.get('tss', 0)
            })
            
            heatmap_data[date_key]['tss'] += activity.get('tss', 0)
            heatmap_data[date_key]['distance'] += activity.get('distance', 0)
            heatmap_data[date_key]['time'] += activity.get('moving_time', activity.get('elapsed_time', 0))
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'data': heatmap_data
        }
    
    def _save_meta(self):
        """Save metadata about the data collection"""
        meta = {
            'last_updated': datetime.now().isoformat(),
            'collection_version': '2.0',
            'data_source': 'intervals.icu',
            'athlete_id': self.client.athlete_id
        }
        
        self._save_json('meta.json', meta)
        print("Saved metadata")
    
    def _save_json(self, filename: str, data: Any):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            sys.exit(1)

def main():
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
        sys.exit(1)

if __name__ == "__main__":
    main()
