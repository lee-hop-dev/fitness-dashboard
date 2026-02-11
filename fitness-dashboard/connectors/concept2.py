"""
Concept2 Logbook API Connector
Fetches rowing workouts and performance data
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Concept2Connector:
    """Connector for Concept2 Logbook API"""
    
    BASE_URL = "https://log.concept2.com/api"
    
    def __init__(self, username: str, password: str):
        """
        Initialize Concept2 connector
        
        Args:
            username: Concept2 Logbook username
            password: Concept2 Logbook password
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
    
    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def authenticate(self) -> bool:
        """
        Authenticate and get access token
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Authenticating Concept2 user: {self.username}")
        
        try:
            auth_url = f"{self.BASE_URL}/auth/token"
            
            payload = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password"
            }
            
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get("access_token")
            
            # Tokens typically expire after 1 hour
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            logger.info("Authentication successful")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed. Check username/password.")
            else:
                logger.error(f"HTTP error during authentication: {e}")
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expiry:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Concept2")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request with error handling
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response as dict
        """
        self._ensure_authenticated()
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning("Token expired, re-authenticating...")
                self.authenticate()
                return self._make_request(endpoint, params)  # Retry
            else:
                logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_user_info(self) -> Dict:
        """Get user profile information"""
        logger.info("Fetching user profile")
        return self._make_request("user")
    
    def get_workouts(self,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     workout_type: Optional[str] = None) -> List[Dict]:
        """
        Get workouts for date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            workout_type: Filter by type (e.g., 'rower', 'skierg')
            
        Returns:
            List of workout dictionaries
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching workouts from {start_date} to {end_date}")
        
        params = {
            "from": start_date,
            "to": end_date
        }
        
        if workout_type:
            params["type"] = workout_type
        
        workouts = self._make_request("users/me/results", params)
        
        logger.info(f"Retrieved {len(workouts.get('data', []))} workouts")
        return workouts.get("data", [])
    
    def get_workout_details(self, workout_id: str) -> Dict:
        """
        Get detailed information for a specific workout
        
        Args:
            workout_id: Workout ID
            
        Returns:
            Detailed workout data including splits
        """
        logger.info(f"Fetching details for workout: {workout_id}")
        return self._make_request(f"users/me/results/{workout_id}")
    
    def get_rankings(self, 
                     distance: Optional[int] = None,
                     time: Optional[int] = None,
                     workout_type: str = "rower") -> List[Dict]:
        """
        Get world rankings for distance/time
        
        Args:
            distance: Distance in meters (e.g., 2000, 5000)
            time: Time in seconds (e.g., 3600 for 60min)
            workout_type: Type of machine
            
        Returns:
            Ranking data
        """
        params = {
            "type": workout_type
        }
        
        if distance:
            params["distance"] = distance
        if time:
            params["time"] = time
        
        logger.info(f"Fetching rankings for {distance}m or {time}s")
        return self._make_request("rankings", params)
    
    def standardize_workout(self, raw_workout: Dict) -> Dict:
        """
        Convert Concept2 workout to standard schema
        
        Args:
            raw_workout: Raw workout from API
            
        Returns:
            Standardized activity dict matching data_schema.json
        """
        # Concept2 uses centiseconds (1/100 second)
        duration_seconds = raw_workout.get("time", 0) / 100
        
        # Calculate pace (seconds per 500m)
        distance = raw_workout.get("distance", 0)
        avg_pace = (duration_seconds / distance * 500) if distance > 0 else None
        
        return {
            "id": str(raw_workout.get("id")),
            "source": "concept2",
            "type": "Rowing",
            "start_time": raw_workout.get("date"),
            "duration": duration_seconds,
            "distance": distance,
            "name": f"Rowing - {distance}m" if distance else f"Rowing - {duration_seconds}s",
            "description": raw_workout.get("comments"),
            "metrics": {
                "avg_heart_rate": raw_workout.get("heart_rate", {}).get("average"),
                "max_heart_rate": raw_workout.get("heart_rate", {}).get("max"),
                "avg_cadence": raw_workout.get("stroke_rate"),  # Strokes per minute
                "avg_pace": avg_pace,
                "calories": raw_workout.get("calories")
            },
            "splits": self._parse_splits(raw_workout.get("splits", [])),
            "raw_data": raw_workout
        }
    
    def _parse_splits(self, raw_splits: List[Dict]) -> List[Dict]:
        """
        Parse Concept2 splits into standard format
        
        Args:
            raw_splits: Raw split data from API
            
        Returns:
            List of standardized splits
        """
        splits = []
        
        for split in raw_splits:
            split_time = split.get("time", 0) / 100  # Convert centiseconds
            split_distance = split.get("distance", 0)
            
            splits.append({
                "distance": split_distance,
                "time": split_time,
                "avg_pace": (split_time / split_distance * 500) if split_distance > 0 else None,
                "avg_heart_rate": split.get("heart_rate")
            })
        
        return splits


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    username = os.getenv("CONCEPT2_USERNAME", "LH_Hoppy")
    password = os.getenv("CONCEPT2_PASSWORD")
    
    if not password:
        print("Error: CONCEPT2_PASSWORD not found in environment")
        exit(1)
    
    connector = Concept2Connector(username, password)
    
    # Test connection
    try:
        if connector.authenticate():
            user = connector.get_user_info()
            print(f"Connected successfully! User: {user.get('username')}")
            
            # Get recent workouts
            workouts = connector.get_workouts(
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            )
            print(f"Retrieved {len(workouts)} workouts from last 30 days")
            
            if workouts:
                latest = workouts[0]
                print(f"Most recent: {latest.get('distance')}m in {latest.get('time')/100}s")
        else:
            print("Authentication failed")
            
    except Exception as e:
        print(f"Error testing connector: {e}")
