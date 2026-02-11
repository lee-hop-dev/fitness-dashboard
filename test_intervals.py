from connectors.intervals_icu import IntervalsICUConnector
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("INTERVALS_API_KEY")
athlete_id = "5718022"

connector = IntervalsICUConnector(api_key, athlete_id)

# Try fetching last 30 days worth
start_date = "2026-01-15"
end_date = "2026-02-10"  # Yesterday

print(f"Fetching from {start_date} to {end_date}")

try:
    activities = connector.get_activities(start_date=start_date, end_date=end_date)
    print(f"✅ Retrieved {len(activities)} activities")
    
    if activities:
        print(f"\nMost recent: {activities[0].get('name')} on {activities[0].get('start_date_local')}")
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Try without date parameters (gets all recent)
    print("\nTrying to fetch without date range...")
    try:
        activities = connector.get_activities()
        print(f"✅ Retrieved {len(activities)} activities")
    except Exception as e2:
        print(f"❌ Still failed: {e2}")