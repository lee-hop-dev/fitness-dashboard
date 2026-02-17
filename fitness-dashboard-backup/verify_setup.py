#!/usr/bin/env python3
"""
Setup Verification Script
Checks that all configuration is correct and APIs are accessible
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from connectors.intervals_icu import IntervalsICUConnector
from connectors.concept2 import Concept2Connector

def check_env_vars():
    """Check that required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "INTERVALS_API_KEY",
        "CONCEPT2_USERNAME",
        "CONCEPT2_PASSWORD"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("   Create a .env file with these variables")
        return False
    
    print("✅ All required environment variables found")
    return True

def check_config_file():
    """Check that config.yaml exists"""
    print("\n🔍 Checking configuration file...")
    
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ config/config.yaml not found")
        print("   Copy config.yaml.template to config.yaml and fill in values")
        return False
    
    print("✅ Configuration file found")
    return True

def test_intervals_connection():
    """Test Intervals.icu API connection"""
    print("\n🔍 Testing Intervals.icu connection...")
    
    api_key = os.getenv("INTERVALS_API_KEY")
    athlete_id = "5718022"
    
    try:
        connector = IntervalsICUConnector(api_key, athlete_id)
        athlete = connector.get_athlete_info()
        
        print(f"✅ Connected to Intervals.icu")
        print(f"   Athlete: {athlete.get('name')}")
        print(f"   ID: {athlete_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Intervals.icu: {e}")
        return False

def test_concept2_connection():
    """Test Concept2 API connection"""
    print("\n🔍 Testing Concept2 connection...")
    
    username = os.getenv("CONCEPT2_USERNAME")
    password = os.getenv("CONCEPT2_PASSWORD")
    
    try:
        connector = Concept2Connector(username, password)
        
        if connector.authenticate():
            user = connector.get_user_info()
            print(f"✅ Connected to Concept2 Logbook")
            print(f"   Username: {username}")
            return True
        else:
            print("❌ Failed to authenticate with Concept2")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Concept2: {e}")
        return False

def check_directory_structure():
    """Verify directory structure is correct"""
    print("\n🔍 Checking directory structure...")
    
    required_dirs = [
        "config",
        "connectors",
        "workflows",
        "data",
        "docs",
        ".github/workflows"
    ]
    
    missing = []
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing.append(dir_name)
    
    if missing:
        print(f"❌ Missing directories: {', '.join(missing)}")
        return False
    
    print("✅ Directory structure is correct")
    return True

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Fitness Dashboard - Setup Verification")
    print("=" * 60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env file")
    
    # Run checks
    checks = [
        check_directory_structure(),
        check_env_vars(),
        check_config_file(),
        test_intervals_connection(),
        test_concept2_connection()
    ]
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\nYou're ready to run:")
        print("  python workflows/collect_data.py")
        return 0
    else:
        print(f"❌ {total - passed} check(s) failed ({passed}/{total} passed)")
        print("\nPlease fix the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
