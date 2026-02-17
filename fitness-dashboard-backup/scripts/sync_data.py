#!/usr/bin/env python3
"""
Main Sync Script
Fetches data from all sources and stores in Google Drive
"""

import os
import sys
import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.intervals_icu import IntervalsICUConnector
from connectors.concept2 import Concept2Connector
from connectors.google_drive import GoogleDriveStorage


class FitnessDataSync:
    """Main orchestrator for fitness data synchronization"""
    
    def __init__(self, config_path: str):
        """
        Initialize sync with configuration
        
        Args:
            config_path: Path to config.yaml
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize connectors
        self.intervals = IntervalsICUConnector(
            api_key=self.config['intervals_icu']['api_key'],
            athlete_id=self.config['intervals_icu']['athlete_id']
        )
        
        self.concept2 = Concept2Connector(
            username=self.config['concept2']['username'],
            password=self.config['concept2']['password']
        )
        
        # Initialize storage
        self.storage = GoogleDriveStorage(
            credentials_path=self.config['google_drive']['credentials_file'],
            folder_structure={
                'raw': self.config['google_drive']['raw_folder'],
                'processed': self.config['google_drive']['processed_folder']
            }
        )
        
        print("✓ Initialized all connectors and storage")
    
    def sync_activities(self, days_back: int = 7) -> Dict:
        """
        Sync activities from all sources
        
        Args:
            days_back: Number of days to sync (default: 7 for daily sync)
            
        Returns:
            Dictionary with sync statistics
        """
        print(f"\n{'='*60}")
        print(f"SYNCING ACTIVITIES ({days_back} days)")
        print(f"{'='*60}")
        
        newest = datetime.now().strftime('%Y-%m-%d')
        oldest = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        all_activities = []
        stats = {
            'intervals_icu': 0,
            'concept2': 0,
            'total': 0,
            'by_type': {}
        }
        
        # Fetch from Intervals.icu
        print("\n📊 Fetching from Intervals.icu...")
        try:
            intervals_activities = self.intervals.get_activities(
                oldest=oldest,
                newest=newest
            )
            
            for activity in intervals_activities:
                standardized = self.intervals.standardize_activity(activity)
                all_activities.append(standardized)
                
                # Update stats
                activity_type = standardized['type']
                stats['by_type'][activity_type] = stats['by_type'].get(activity_type, 0) + 1
            
            stats['intervals_icu'] = len(intervals_activities)
            print(f"  ✓ Retrieved {len(intervals_activities)} activities")
            
        except Exception as e:
            print(f"  ✗ Error fetching from Intervals.icu: {e}")
        
        # Fetch from Concept2
        print("\n🚣 Fetching from Concept2...")
        try:
            if self.concept2.authenticate():
                c2_workouts = self.concept2.get_workouts(
                    from_date=oldest,
                    to_date=newest
                )
                
                for workout in c2_workouts:
                    standardized = self.concept2.standardize_workout(workout)
                    
                    # Check if already in activities (from Intervals sync)
                    already_exists = any(
                        a.get('raw_data', {}).get('id') == workout.get('id')
                        for a in all_activities
                    )
                    
                    if not already_exists:
                        all_activities.append(standardized)
                        activity_type = standardized['type']
                        stats['by_type'][activity_type] = stats['by_type'].get(activity_type, 0) + 1
                
                stats['concept2'] = len(c2_workouts)
                print(f"  ✓ Retrieved {len(c2_workouts)} workouts")
            else:
                print("  ✗ Concept2 authentication failed")
                
        except Exception as e:
            print(f"  ✗ Error fetching from Concept2: {e}")
        
        stats['total'] = len(all_activities)
        
        # Save to Google Drive
        if all_activities:
            filename = f"activities_{oldest}_to_{newest}.json"
            print(f"\n💾 Saving {len(all_activities)} activities to Google Drive...")
            
            try:
                self.storage.upload_json(
                    {
                        'sync_date': datetime.now().isoformat(),
                        'date_range': {'oldest': oldest, 'newest': newest},
                        'count': len(all_activities),
                        'activities': all_activities
                    },
                    filename,
                    'raw'
                )
                print(f"  ✓ Saved to {filename}")
            except Exception as e:
                print(f"  ✗ Error saving activities: {e}")
        
        return stats
    
    def sync_wellness(self, days_back: int = 7) -> Dict:
        """
        Sync wellness data from Intervals.icu
        
        Args:
            days_back: Number of days to sync
            
        Returns:
            Dictionary with sync statistics
        """
        print(f"\n{'='*60}")
        print(f"SYNCING WELLNESS DATA ({days_back} days)")
        print(f"{'='*60}")
        
        newest = datetime.now().strftime('%Y-%m-%d')
        oldest = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        stats = {'total': 0}
        
        print("\n💤 Fetching wellness from Intervals.icu...")
        try:
            wellness_data = self.intervals.get_wellness(
                oldest=oldest,
                newest=newest
            )
            
            standardized_wellness = [
                self.intervals.standardize_wellness(w)
                for w in wellness_data
            ]
            
            stats['total'] = len(standardized_wellness)
            print(f"  ✓ Retrieved {len(standardized_wellness)} wellness records")
            
            # Save to Google Drive
            if standardized_wellness:
                filename = f"wellness_{oldest}_to_{newest}.json"
                print(f"\n💾 Saving wellness data to Google Drive...")
                
                self.storage.upload_json(
                    {
                        'sync_date': datetime.now().isoformat(),
                        'date_range': {'oldest': oldest, 'newest': newest},
                        'count': len(standardized_wellness),
                        'wellness': standardized_wellness
                    },
                    filename,
                    'raw'
                )
                print(f"  ✓ Saved to {filename}")
                
        except Exception as e:
            print(f"  ✗ Error syncing wellness: {e}")
        
        return stats
    
    def sync_fitness_trends(self, days_back: int = 30) -> Dict:
        """
        Sync fitness trends (CTL/ATL/TSB) from Intervals.icu
        
        Args:
            days_back: Number of days to sync (default: 30 for trends)
            
        Returns:
            Dictionary with sync statistics
        """
        print(f"\n{'='*60}")
        print(f"SYNCING FITNESS TRENDS ({days_back} days)")
        print(f"{'='*60}")
        
        newest = datetime.now().strftime('%Y-%m-%d')
        oldest = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        stats = {'total': 0}
        
        print("\n📈 Fetching fitness trends from Intervals.icu...")
        try:
            fitness_data = self.intervals.get_fitness_trends(
                oldest=oldest,
                newest=newest
            )
            
            standardized_fitness = [
                self.intervals.standardize_fitness(f)
                for f in fitness_data
            ]
            
            stats['total'] = len(standardized_fitness)
            print(f"  ✓ Retrieved {len(standardized_fitness)} fitness records")
            
            # Save to Google Drive
            if standardized_fitness:
                filename = f"fitness_{oldest}_to_{newest}.json"
                print(f"\n💾 Saving fitness trends to Google Drive...")
                
                self.storage.upload_json(
                    {
                        'sync_date': datetime.now().isoformat(),
                        'date_range': {'oldest': oldest, 'newest': newest},
                        'count': len(standardized_fitness),
                        'fitness': standardized_fitness
                    },
                    filename,
                    'raw'
                )
                print(f"  ✓ Saved to {filename}")
                
        except Exception as e:
            print(f"  ✗ Error syncing fitness trends: {e}")
        
        return stats
    
    def sync_all(self, days_back: int = 7, full_sync: bool = False):
        """
        Sync all data sources
        
        Args:
            days_back: Number of days to sync for daily updates
            full_sync: If True, do initial historical sync
        """
        if full_sync:
            days_back = self.config['sync'].get('historical_days', 365)
            print(f"\n🔄 FULL SYNC MODE - Fetching {days_back} days of historical data")
        else:
            print(f"\n🔄 INCREMENTAL SYNC - Fetching last {days_back} days")
        
        start_time = datetime.now()
        
        # Sync activities
        activity_stats = self.sync_activities(days_back)
        
        # Sync wellness
        wellness_stats = self.sync_wellness(days_back)
        
        # Sync fitness trends (use longer window)
        fitness_days = 30 if not full_sync else days_back
        fitness_stats = self.sync_fitness_trends(fitness_days)
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print("SYNC COMPLETE")
        print(f"{'='*60}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"\n📊 Activities:")
        print(f"   Total: {activity_stats['total']}")
        print(f"   Intervals.icu: {activity_stats['intervals_icu']}")
        print(f"   Concept2: {activity_stats['concept2']}")
        print(f"\n   By Type:")
        for activity_type, count in sorted(activity_stats['by_type'].items()):
            print(f"     {activity_type}: {count}")
        print(f"\n💤 Wellness: {wellness_stats['total']} records")
        print(f"📈 Fitness: {fitness_stats['total']} records")
        print(f"{'='*60}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync fitness data from multiple sources')
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to config file (default: config/config.yaml)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to sync (default: 7)'
    )
    parser.add_argument(
        '--full-sync',
        action='store_true',
        help='Do full historical sync'
    )
    
    args = parser.parse_args()
    
    # Check config exists
    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        print("Copy config.yaml.template to config.yaml and fill in your API keys")
        sys.exit(1)
    
    # Run sync
    try:
        sync = FitnessDataSync(args.config)
        sync.sync_all(days_back=args.days, full_sync=args.full_sync)
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
