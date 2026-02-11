import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("INTERVALS_API_KEY")
athlete_id = "5718022"

print("Test: Activities with oldest as date")
response = requests.get(
    f"https://intervals.icu/api/v1/athlete/{athlete_id}/activities",
    params={"oldest": "2026-01-01"},  # Date string instead of boolean
    auth=("API_KEY", api_key)
)
print(f"Status: {response.status_code}")
if response.ok:
    activities = response.json()
    print(f"✅ Got {len(activities)} activities")
    if activities:
        print(f"\nFirst activity: {activities[0].get('name')} on {activities[0].get('start_date_local')}")
        print(f"Last activity: {activities[-1].get('name')} on {activities[-1].get('start_date_local')}")
else:
    print(f"❌ Error: {response.text}")