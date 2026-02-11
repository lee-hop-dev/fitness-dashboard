"""
Main Data Collection Script
Orchestrates fetching data from all sources and storing in Google Drive
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.intervals_icu import IntervalsICUConnector
from connectors.concept2 import Concept2Connector
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollector:
    """Main data collection orchestrator"""
    
    def __init__(self, days_back: int = 7):
        """
        Initialize data collector
        
        Args:
            days_back: Number of days to fetch (default: 7 for daily updates)
        """
        load_dotenv()
        
        self.days_back = days_back
        self.start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize connectors
        self.intervals = self._init_intervals()
        self.concept2 = self._init_concept2()
        
        # Storage paths
        self.data_dir = Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_intervals(self) -> IntervalsICUConnector:
        """Initialize Intervals.icu connector"""
        api_key = os.getenv("INTERVALS_API_KEY")
        athlete_id = "5718022"
        
        if not api_key:
            logger.error("INTERVALS_API_KEY not found in environment")
            raise ValueError("Missing Intervals.icu API key")
        
        logger.info("Initializing Intervals.icu connector")
        return IntervalsICUConnector(api_key, athlete_id)
    
    def _init_concept2(self) -> Concept2Connector:
        """Initialize Concept2 connector"""
        username = os.getenv("CONCEPT2_USERNAME")
        password = os.getenv("CONCEPT2_PASSWORD")
        
        if not username or not password:
            logger.warning("Concept2 credentials not found - skipping")
            return None
        
        logger.info("Initializing Concept2 connector")
        try:
            connector = Concept2Connector(username, password)
            if connector.authenticate():
                return connector
            else:
                logger.warning("Concept2 authentication failed - skipping")
                return None
        except Exception as e:
            logger.warning(f"Concept2 connector failed: {e} - skipping")
            return None
    
    def collect_intervals_data(self) -> Dict:
        """Collect all data from Intervals.icu"""
        logger.info(f"Collecting Intervals.icu data from {self.start_date} to {self.end_date}")
        
        data = {
            "activities": [],
            "wellness": [],
            "fitness_trend": []
        }
        
        try:
            # Fetch activities
            logger.info("Fetching activities...")
            raw_activities = self.intervals.get_activities(
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # Standardize activities
            for activity in raw_activities:
                standardized = self.intervals.standardize_activity(activity)
                data["activities"].append(standardized)
            
            logger.info(f"Retrieved {len(data['activities'])} activities")
            
            # Fetch wellness data
            logger.info("Fetching wellness data...")
            raw_wellness = self.intervals.get_wellness_data(
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # Standardize wellness
            for wellness in raw_wellness:
                standardized = self.intervals.standardize_wellness(wellness)
                data["wellness"].append(standardized)
            
            logger.info(f"Retrieved {len(data['wellness'])} wellness entries")
            
            # Fetch fitness trend (CTL/ATL/TSB)
            logger.info("Fetching fitness trend...")
            data["fitness_trend"] = self.intervals.get_fitness_trend(
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            logger.info(f"Retrieved {len(data['fitness_trend'])} fitness data points")
            
            # Save raw data
            self._save_json(
                data,
                self.raw_dir / f"intervals_icu_{self.end_date}.json"
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect Intervals.icu data: {e}")
            raise
    
    def collect_concept2_data(self) -> Dict:
        """Collect data from Concept2 (if available)"""
        if not self.concept2:
            logger.info("Concept2 connector not available - skipping")
            return {"workouts": []}
        
        logger.info(f"Collecting Concept2 data from {self.start_date} to {self.end_date}")
        
        data = {"workouts": []}
        
        try:
            # Fetch workouts
            logger.info("Fetching rowing workouts...")
            raw_workouts = self.concept2.get_workouts(
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # Standardize workouts
            for workout in raw_workouts:
                standardized = self.concept2.standardize_workout(workout)
                data["workouts"].append(standardized)
            
            logger.info(f"Retrieved {len(data['workouts'])} workouts")
            
            # Save raw data
            self._save_json(
                data,
                self.raw_dir / f"concept2_{self.end_date}.json"
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect Concept2 data: {e}")
            return {"workouts": []}
    
    def aggregate_data(self, intervals_data: Dict, concept2_data: Dict) -> Dict:
        """
        Combine and aggregate data from all sources
        
        Args:
            intervals_data: Data from Intervals.icu
            concept2_data: Data from Concept2
            
        Returns:
            Aggregated dataset
        """
        logger.info("Aggregating data from all sources")
        
        aggregated = {
            "last_updated": datetime.now().isoformat(),
            "date_range": {
                "start": self.start_date,
                "end": self.end_date
            },
            "activities": intervals_data["activities"],
            "wellness": intervals_data["wellness"],
            "training_load": intervals_data["fitness_trend"],
            "summary": self._calculate_summary(intervals_data, concept2_data)
        }
        
        # Add Concept2 workouts if available (avoid duplicates with Intervals)
        c2_workouts = concept2_data.get("workouts", [])
        if c2_workouts:
            logger.info(f"Adding {len(c2_workouts)} Concept2 workouts")
            # Note: In production, you'd want to deduplicate based on timestamp
            aggregated["concept2_workouts"] = c2_workouts
        
        # Save aggregated data
        self._save_json(
            aggregated,
            self.processed_dir / f"aggregated_{self.end_date}.json"
        )
        
        return aggregated
    
    def _calculate_summary(self, intervals_data: Dict, concept2_data: Dict) -> Dict:
        """Calculate summary statistics"""
        activities = intervals_data["activities"]
        
        total_distance = sum(a.get("distance") or 0 for a in activities) / 1000  # km
        total_duration = sum(a.get("duration") or 0 for a in activities) / 3600  # hours
        total_activities = len(activities)
        
        # Group by activity type
        by_type = {}
        for activity in activities:
            activity_type = activity.get("type", "Unknown")
            if activity_type not in by_type:
                by_type[activity_type] = {
                    "count": 0,
                    "distance": 0,
                    "duration": 0
                }
            
            by_type[activity_type]["count"] += 1
            by_type[activity_type]["distance"] += (activity.get("distance") or 0) / 1000
            by_type[activity_type]["duration"] += (activity.get("duration") or 0) / 3600
        
        # Get latest wellness metrics
        wellness = intervals_data["wellness"]
        latest_wellness = wellness[-1] if wellness else {}
        
        # Get latest fitness metrics
        fitness = intervals_data["fitness_trend"]
        latest_fitness = fitness[-1] if fitness else {}
        
        return {
            "total_activities": total_activities,
            "total_distance_km": round(total_distance, 2),
            "total_duration_hours": round(total_duration, 2),
            "by_activity_type": by_type,
            "latest_wellness": {
                "date": latest_wellness.get("date"),
                "hrv": latest_wellness.get("hrv"),
                "resting_hr": latest_wellness.get("resting_hr"),
                "sleep_time": latest_wellness.get("sleep_time"),
                "weight": latest_wellness.get("weight")
            },
            "latest_fitness": {
                "date": latest_fitness.get("date"),
                "ctl": latest_fitness.get("ctl"),
                "atl": latest_fitness.get("atl"),
                "tsb": latest_fitness.get("tsb")
            }
        }
    
    def _save_json(self, data: Dict, filepath: Path):
        """Save data as JSON"""
        logger.info(f"Saving data to {filepath}")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self) -> Dict:
        """Run full data collection pipeline"""
        logger.info("=" * 60)
        logger.info("Starting data collection")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
        logger.info("=" * 60)
        
        try:
            # Collect from all sources
            intervals_data = self.collect_intervals_data()
            concept2_data = self.collect_concept2_data()
            
            # Aggregate
            aggregated = self.aggregate_data(intervals_data, concept2_data)
            
            logger.info("=" * 60)
            logger.info("Data collection complete!")
            logger.info(f"Total activities: {aggregated['summary']['total_activities']}")
            logger.info(f"Total distance: {aggregated['summary']['total_distance_km']} km")
            logger.info(f"Total duration: {aggregated['summary']['total_duration_hours']} hours")
            logger.info("=" * 60)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect fitness data from all sources")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to fetch (default: 7)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Fetch full history (365 days)"
    )
    
    args = parser.parse_args()
    
    days = 365 if args.full else args.days
    
    collector = DataCollector(days_back=days)
    collector.run()


if __name__ == "__main__":
    main()
