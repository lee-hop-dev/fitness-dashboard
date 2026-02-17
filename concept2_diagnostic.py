"""
CONCEPT2 DIAGNOSTIC & FIX SCRIPT
Tests direct Concept2 API connection and fixes common issues
Run this to diagnose your Concept2 sync problems
"""

import os, json, requests
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

CONCEPT2_USERNAME = os.getenv('CONCEPT2_USERNAME', '')  # Your Concept2 username
CONCEPT2_PASSWORD = os.getenv('CONCEPT2_PASSWORD', '')  # Your Concept2 password

def test_concept2_connection():
    """Test direct Concept2 API connection with enhanced diagnostics"""
    
    print("🚣 CONCEPT2 API DIAGNOSTIC TEST")
    print("=" * 50)
    
    # Check credentials
    print(f"Username: {CONCEPT2_USERNAME}")
    print(f"Password: {'SET' if CONCEPT2_PASSWORD else 'MISSING'}")
    
    if not CONCEPT2_USERNAME or not CONCEPT2_PASSWORD:
        print("❌ ERROR: Concept2 credentials not set!")
        print("Set environment variables:")
        print("export CONCEPT2_USERNAME='your_username'")
        print("export CONCEPT2_PASSWORD='your_password'")
        return False
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    try:
        auth_response = requests.post('https://log.concept2.com/api/auth/token', 
            data={
                'username': CONCEPT2_USERNAME,
                'password': CONCEPT2_PASSWORD,
                'grant_type': 'password'
            },
            timeout=30
        )
        
        print(f"Auth Response Status: {auth_response.status_code}")
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            
            if auth_response.status_code == 400:
                print("💡 Check your username/password - they might be incorrect")
            elif auth_response.status_code == 401:
                print("💡 Invalid credentials - verify your Concept2 account login")
            return False
        
        auth_data = auth_response.json()
        access_token = auth_data.get('access_token')
        expires_in = auth_data.get('expires_in', 3600)
        
        print("✅ Authentication successful!")
        print(f"Token expires in: {expires_in} seconds")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test data retrieval
    print("\n📊 Testing workout data retrieval...")
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get user profile first
        profile_response = requests.get('https://log.concept2.com/api/user', 
            headers=headers, timeout=30)
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"✅ Profile retrieved: {profile.get('username', 'Unknown')}")
        else:
            print(f"⚠️ Profile request failed: {profile_response.status_code}")
        
        # Get recent workouts
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        workouts_response = requests.get('https://log.concept2.com/api/users/me/results',
            headers=headers,
            params={'from': start_date, 'to': end_date},
            timeout=30
        )
        
        print(f"Workouts Response Status: {workouts_response.status_code}")
        
        if workouts_response.status_code != 200:
            print(f"❌ Workouts request failed: {workouts_response.text}")
            return False
        
        workouts_data = workouts_response.json()
        print(f"Raw API Response Keys: {list(workouts_data.keys())}")
        
        if 'data' in workouts_data:
            workouts = workouts_data['data']
            print(f"✅ Found {len(workouts)} workouts in last 90 days")
            
            if workouts:
                print("\n📋 Sample workout data:")
                sample = workouts[0]
                print(json.dumps(sample, indent=2)[:1000] + "...")
                
                # Analyze workout structure
                print(f"\n🔍 Workout fields: {list(sample.keys())}")
                print(f"Date: {sample.get('date', 'MISSING')}")
                print(f"Time: {sample.get('time', 'MISSING')} (centiseconds)")
                print(f"Distance: {sample.get('distance', 'MISSING')} meters")
                print(f"Stroke Rate: {sample.get('stroke_rate', 'MISSING')}")
                
                # Test time conversion
                if sample.get('time'):
                    time_centiseconds = sample['time']
                    time_seconds = time_centiseconds / 100
                    print(f"Time conversion: {time_centiseconds}cs = {time_seconds}s = {time_seconds/60:.1f}min")
                
                return True
            else:
                print("⚠️ No workouts found - try adding some activities to your Concept2 logbook")
                return True
        else:
            print(f"❌ Unexpected response format: {workouts_data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Data retrieval error: {e}")
        return False

def fix_data_collection():
    """Apply fixes to your data collection workflow"""
    print("\n🔧 APPLYING FIXES TO DATA COLLECTION")
    print("=" * 50)
    
    # The main fix is ensuring process_concept2_activity handles the data correctly
    print("Key fixes needed in your collect_data.py:")
    print("1. Handle Concept2 time format (centiseconds → seconds)")
    print("2. Proper heart rate data extraction")
    print("3. Ensure 'CONCEPT2' source is set correctly")
    print("4. Better error handling for failed workouts")
    
    print("\nReplace your process_concept2_activity function with:")
    print("""
def process_concept2_activity(w):
    try:
        # Fix time format (Concept2 uses centiseconds)
        duration_centiseconds = w.get('time', 0)
        duration_seconds = duration_centiseconds / 100
        
        distance = w.get('distance', 0)
        
        # Handle heart rate data properly
        hr_data = w.get('heart_rate', {})
        avg_hr = None
        max_hr = None
        
        if isinstance(hr_data, dict):
            avg_hr = hr_data.get('average')
            max_hr = hr_data.get('max')
        elif isinstance(hr_data, (int, float)):
            avg_hr = hr_data
        
        return {
            'id': f"concept2_{w.get('id', '')}",
            'strava_id': None,
            'source': 'CONCEPT2',  # Ensure this is set correctly
            'name': f"Rowing - {distance}m" if distance else f"Rowing - {int(duration_seconds)}s",
            'type': 'Rowing',
            'date': w.get('date', '')[:10],
            'duration': duration_seconds,
            'distance': distance,
            'elevation': 0,
            'avg_power': None,
            'norm_power': None,
            'avg_hr': avg_hr,
            'max_hr': max_hr,
            'avg_speed': distance / duration_seconds if duration_seconds > 0 else None,
            'avg_cadence': w.get('stroke_rate'),  # This is your stroke rate!
            'calories': w.get('calories'),
            'tss': 0,
            'if_val': None,
            'ftp': None,
            'w_prime': None,
            'weight': None,
            'device': 'Concept2 RowErg',
            'is_garmin': False
        }
    except Exception as e:
        print(f"Error processing Concept2 workout: {e}")
        return None  # Return None to skip this workout instead of crashing
    """)

if __name__ == "__main__":
    print("🚣 Starting Concept2 Diagnostic...")
    
    # Load environment variables if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("dotenv not available - using environment variables directly")
    
    success = test_concept2_connection()
    
    if success:
        print("\n✅ DIAGNOSIS COMPLETE - Connection working!")
        fix_data_collection()
    else:
        print("\n❌ DIAGNOSIS FAILED - Fix connection issues first")
        print("\nTroubleshooting steps:")
        print("1. Verify your Concept2 account credentials")
        print("2. Check if you can log into https://log.concept2.com manually")
        print("3. Ensure your account has workout data")
        print("4. Try updating your Concept2 password")