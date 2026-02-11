#!/usr/bin/env python3
"""
Test Script
Validates all connectors and configuration before first sync
"""

import os
import sys
import yaml
import json
from datetime import datetime, timedelta

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print formatted section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def test_config():
    """Test configuration file exists and is valid"""
    print_header("Testing Configuration")
    
    config_path = 'config/config.yaml'
    
    # Check config exists
    if not os.path.exists(config_path):
        print_error(f"Config file not found: {config_path}")
        print_warning("Copy config.yaml.template to config.yaml and fill in your API keys")
        return None
    
    print_success("Config file exists")
    
    # Load and validate config
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print_success("Config file is valid YAML")
    except Exception as e:
        print_error(f"Config file parse error: {e}")
        return None
    
    # Check required fields
    required_fields = {
        'intervals_icu': ['api_key', 'athlete_id'],
        'concept2': ['username', 'password'],
        'google_drive': ['credentials_file', 'raw_folder', 'processed_folder']
    }
    
    all_valid = True
    for section, fields in required_fields.items():
        if section not in config:
            print_error(f"Missing section: {section}")
            all_valid = False
            continue
        
        for field in fields:
            if field not in config[section]:
                print_error(f"Missing field: {section}.{field}")
                all_valid = False
            elif not config[section][field] or 'YOUR_' in str(config[section][field]):
                print_error(f"Field not configured: {section}.{field}")
                all_valid = False
            else:
                print_success(f"Configured: {section}.{field}")
    
    if not all_valid:
        print_error("Config validation failed")
        return None
    
    print_success("All required fields configured")
    return config

def test_google_drive(config):
    """Test Google Drive connection"""
    print_header("Testing Google Drive Connection")
    
    credentials_path = config['google_drive']['credentials_file']
    
    # Check credentials file exists
    if not os.path.exists(credentials_path):
        print_error(f"Credentials file not found: {credentials_path}")
        print_warning("See docs/GOOGLE_DRIVE_SETUP.md for setup instructions")
        return False
    
    print_success("Credentials file exists")
    
    # Validate JSON
    try:
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        if creds.get('type') != 'service_account':
            print_error("Credentials are not for a service account")
            return False
        
        print_success("Valid service account credentials")
        print(f"   Service account: {creds.get('client_email', 'Unknown')}")
        
    except Exception as e:
        print_error(f"Credentials file error: {e}")
        return False
    
    # Test connection
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from connectors.google_drive import GoogleDriveStorage
        
        storage = GoogleDriveStorage(
            credentials_path=credentials_path,
            folder_structure={
                'raw': config['google_drive']['raw_folder'],
                'processed': config['google_drive']['processed_folder']
            }
        )
        
        print_success("Successfully connected to Google Drive")
        
        # Test upload
        test_data = {
            'test': True,
            'timestamp': datetime.now().isoformat()
        }
        
        file_id = storage.upload_json(test_data, 'test_connection.json', 'raw')
        print_success("Test file uploaded successfully")
        
        # Test download
        downloaded = storage.download_json('test_connection.json', 'raw')
        if downloaded and downloaded.get('test'):
            print_success("Test file downloaded successfully")
        else:
            print_error("Downloaded data doesn't match")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Google Drive connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intervals_icu(config):
    """Test Intervals.icu connection"""
    print_header("Testing Intervals.icu Connection")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from connectors.intervals_icu import IntervalsICUConnector
        
        connector = IntervalsICUConnector(
            api_key=config['intervals_icu']['api_key'],
            athlete_id=config['intervals_icu']['athlete_id']
        )
        
        # Test athlete info
        athlete = connector.get_athlete_info()
        print_success(f"Connected as: {athlete.get('name', 'Unknown')}")
        
        # Test activity fetch
        newest = datetime.now().strftime('%Y-%m-%d')
        oldest = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        activities = connector.get_activities(oldest=oldest, newest=newest)
        print_success(f"Retrieved {len(activities)} activities (last 7 days)")
        
        # Test wellness fetch
        wellness = connector.get_wellness(oldest=oldest, newest=newest)
        print_success(f"Retrieved {len(wellness)} wellness records (last 7 days)")
        
        # Test fitness trends
        fitness = connector.get_fitness_trends(oldest=oldest, newest=newest)
        print_success(f"Retrieved {len(fitness)} fitness records (last 7 days)")
        
        return True
        
    except Exception as e:
        print_error(f"Intervals.icu connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concept2(config):
    """Test Concept2 connection"""
    print_header("Testing Concept2 Logbook Connection")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from connectors.concept2 import Concept2Connector
        
        connector = Concept2Connector(
            username=config['concept2']['username'],
            password=config['concept2']['password']
        )
        
        # Test authentication
        if not connector.authenticate():
            print_error("Authentication failed - check username/password")
            return False
        
        print_success("Successfully authenticated")
        
        # Test workout fetch
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        workouts = connector.get_workouts(from_date=from_date, to_date=to_date)
        print_success(f"Retrieved {len(workouts)} workouts (last 30 days)")
        
        if workouts:
            sample = workouts[0]
            print(f"   Sample: {sample.get('distance')}m in {sample.get('time')}s")
        
        return True
        
    except Exception as e:
        print_error(f"Concept2 connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test Python dependencies"""
    print_header("Testing Dependencies")
    
    required = [
        'requests',
        'yaml',
        'google.auth',
        'googleapiclient',
        'pandas',
        'numpy'
    ]
    
    all_installed = True
    for module_name in required:
        try:
            __import__(module_name.replace('.', '/'))
            print_success(f"{module_name} installed")
        except ImportError:
            print_error(f"{module_name} not installed")
            all_installed = False
    
    if not all_installed:
        print_warning("Install missing dependencies: pip install -r requirements.txt")
    
    return all_installed

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print("Fitness Dashboard - Configuration Test")
    print(f"{'='*60}{RESET}\n")
    
    results = {}
    
    # Test dependencies
    results['dependencies'] = test_dependencies()
    
    # Test config
    config = test_config()
    if not config:
        print_error("\n❌ Configuration test failed. Fix config.yaml before proceeding.")
        sys.exit(1)
    results['config'] = True
    
    # Test connectors
    results['google_drive'] = test_google_drive(config)
    results['intervals_icu'] = test_intervals_icu(config)
    results['concept2'] = test_concept2(config)
    
    # Summary
    print_header("Test Summary")
    
    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n{GREEN}{'='*60}")
        print("✓ ALL TESTS PASSED!")
        print(f"{'='*60}{RESET}\n")
        print("You're ready to run your first sync:")
        print(f"{YELLOW}python scripts/sync_data.py --days 7{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*60}")
        print("✗ SOME TESTS FAILED")
        print(f"{'='*60}{RESET}\n")
        print("Fix the errors above before proceeding.")
        print("See README.md and docs/ for setup instructions.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
