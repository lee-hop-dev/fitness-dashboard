"""
Intervals.icu API Connector
Fetches activities, wellness data, and training load metrics
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntervalsICUConnector:
    """Connector for Intervals.icu API"""
    
    BASE_URL = "https://intervals.icu/api/v1"
    
    def __init__(self, api_key: str, athlete_id: str):
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.session = requests.Session()
        self.session.auth = ("API_KEY", api_key)
        self.session.headers.update({"Content-Type": "application/json"})
        self.last_request_time = 0
        self.min_request_interval = 0.5
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        self._rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed. Check your API key.")
            elif e.response.status_code == 429:
                logger.error("Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_athlete_info(self) -> Dict:
        logger.info(f"Fetching athlete info for ID: {self.athlete_id}")
        return self._make_request(f"athlete/{self.athlete_id}")
    
    def get_activities(self, start_date: Optional[str] = None, end_date: Optional[str] = None, oldest_first: bool = False) -> List[Dict]:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching activities from {start_date} to {end_date}")
        
        params = {"oldest": start_date}
        endpoint = f"athlete/{self.athlete_id}/activities"
        activities = self._make_request(endpoint, params)
        
        filtered = []
        for activity in activities:
            activity_date = activity.get("start_date_local", "")[:10]
            if start_date <= activity_date <= end_date:
                filtered.append(activity)
        
        logger.info(f"Retrieved {len(filtered)} activities")
        return filtered
    
    def get_activity_details(self, activity_id: str) -> Dict:
        logger.info(f"Fetching details for activity: {activity_id}")
        return self._make_request(f"activity/{activity_id}")
    
    def get_wellness_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching wellness data from {start_date} to {end_date}")
        
        endpoint = f"athlete/{self.athlete_id}/wellness"
        wellness_data = self._make_request(endpoint)
        
        filtered = []
        for entry in wellness_data:
            entry_date = entry.get("id", "")
            if start_date <= entry_date <= end_date:
                filtered.append(entry)
        
        logger.info(f"Retrieved {len(filtered)} wellness entries")
        return filtered
    
    def get_fitness_trend(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching fitness trend from {start_date} to {end_date}")
        wellness_data = self.get_wellness_data(start_date, end_date)
        
        fitness_data = []
        for entry in wellness_data:
            fitness_entry = {
                "date": entry.get("id"),
                "ctl": entry.get("ctl"),
                "atl": entry.get("atl"),
                "tsb": entry.get("tsb"),
                "daily_tss": entry.get("trainingLoad")
            }
            fitness_data.append(fitness_entry)
        
        return fitness_data
    
    def standardize_activity(self, raw_activity: Dict) -> Dict:
        return {
            "id": str(raw_activity.get("id")),
            "source": "intervals_icu",
            "type": raw_activity.get("type", "Unknown"),
            "start_time": raw_activity.get("start_date_local"),
            "duration": raw_activity.get("moving_time"),
            "distance": raw_activity.get("distance"),
            "elevation_gain": raw_activity.get("total_elevation_gain"),
            "name": raw_activity.get("name"),
            "description": raw_activity.get("description"),
            "metrics": {
                "avg_heart_rate": raw_activity.get("average_hr"),
                "max_heart_rate": raw_activity.get("max_hr"),
                "avg_power": raw_activity.get("average_watts"),
                "normalized_power": raw_activity.get("weighted_average_watts"),
                "max_power": raw_activity.get("max_watts"),
                "avg_cadence": raw_activity.get("average_cadence"),
                "avg_speed": raw_activity.get("average_speed"),
                "max_speed": raw_activity.get("max_speed"),
                "calories": raw_activity.get("calories"),
                "tss": raw_activity.get("icu_training_load"),
                "intensity_factor": raw_activity.get("icu_intensity"),
                "variability_index": raw_activity.get("variability_index")
            },
            "raw_data": raw_activity
        }
    
    def standardize_wellness(self, raw_wellness: Dict) -> Dict:
        return {
            "date": raw_wellness.get("id"),
            "sleep_time": raw_wellness.get("sleepSecs", 0) / 3600 if raw_wellness.get("sleepSecs") else None,
            "sleep_quality": raw_wellness.get("sleepQuality"),
            "hrv": raw_wellness.get("hrv"),
            "resting_hr": raw_wellness.get("restingHR"),
            "weight": raw_wellness.get("weight"),
            "fatigue": raw_wellness.get("fatigue"),
            "mood": raw_wellness.get("mood"),
            "soreness": raw_wellness.get("soreness"),
            "stress": raw_wellness.get("stress"),
            "spo2": raw_wellness.get("spO2"),
            "notes": raw_wellness.get("notes")
        }


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("INTERVALS_API_KEY")
    athlete_id = "5718022"
    
    if not api_key:
        print("Error: INTERVALS_API_KEY not found")
        exit(1)
    
    connector = IntervalsICUConnector(api_key, athlete_id)
    
    try:
        athlete = connector.get_athlete_info()
        print(f"Connected successfully! Athlete: {athlete.get('name')}")
        
        activities = connector.get_activities(start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        print(f"Retrieved {len(activities)} activities from last 7 days")
        
        if activities:
            print(f"Most recent: {activities[0].get('name')} on {activities[0].get('start_date_local')}")
        
        wellness = connector.get_wellness_data(start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        print(f"Retrieved {len(wellness)} wellness entries from last 7 days")
        
    except Exception as e:
        print(f"Error: {e}")