"""
Run Full Pipeline Locally
Test the complete data collection and sync process
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from workflows.collect_data import DataCollector
from workflows.sync_to_drive import GoogleDriveSync

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the full pipeline"""
    
    print("=" * 70)
    print("FITNESS DASHBOARD - LOCAL TEST RUN")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Collect data
        print("STEP 1: Collecting data from APIs...")
        print("-" * 70)
        collector = DataCollector(days_back=7)  # Last 7 days
        data = collector.run()
        print()
        
        # Step 2: Sync to Google Drive
        print("STEP 2: Syncing to Google Drive...")
        print("-" * 70)
        sync = GoogleDriveSync()
        
        # Upload raw data
        raw_uploaded = sync.sync_directory(Path("data/raw"), "raw")
        print(f"✅ Uploaded {raw_uploaded} raw data files")
        
        # Upload processed data
        processed_uploaded = sync.sync_directory(Path("data/processed"), "processed")
        print(f"✅ Uploaded {processed_uploaded} processed data files")
        print()
        
        # Summary
        print("=" * 70)
        print("SUCCESS! Pipeline completed")
        print("=" * 70)
        print()
        print("Summary:")
        summary = data.get("summary", {})
        print(f"  📊 Total activities: {summary.get('total_activities', 0)}")
        print(f"  📏 Total distance: {summary.get('total_distance_km', 0)} km")
        print(f"  ⏱️  Total duration: {summary.get('total_duration_hours', 0):.1f} hours")
        print()
        
        # Activity breakdown
        by_type = summary.get('by_activity_type', {})
        if by_type:
            print("By activity type:")
            for activity_type, stats in by_type.items():
                print(f"  {activity_type}:")
                print(f"    Count: {stats['count']}")
                print(f"    Distance: {stats['distance']:.1f} km")
                print(f"    Duration: {stats['duration']:.1f} hours")
        print()
        
        # Latest metrics
        latest_wellness = summary.get('latest_wellness', {})
        if latest_wellness.get('date'):
            print(f"Latest wellness ({latest_wellness['date']}):")
            if latest_wellness.get('hrv'):
                print(f"  HRV: {latest_wellness['hrv']} ms")
            if latest_wellness.get('resting_hr'):
                print(f"  Resting HR: {latest_wellness['resting_hr']} bpm")
            if latest_wellness.get('sleep_time'):
                print(f"  Sleep: {latest_wellness['sleep_time']:.1f} hours")
        print()
        
        latest_fitness = summary.get('latest_fitness', {})
        if latest_fitness.get('date'):
            print(f"Latest fitness ({latest_fitness['date']}):")
            if latest_fitness.get('ctl'):
                print(f"  Fitness (CTL): {latest_fitness['ctl']:.1f}")
            if latest_fitness.get('atl'):
                print(f"  Fatigue (ATL): {latest_fitness['atl']:.1f}")
            if latest_fitness.get('tsb'):
                print(f"  Form (TSB): {latest_fitness['tsb']:.1f}")
        print()
        
        print("✅ Data is now in Google Drive and ready for dashboard!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ PIPELINE FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        logger.exception("Pipeline error details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
