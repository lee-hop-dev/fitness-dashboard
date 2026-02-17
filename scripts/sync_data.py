#!/usr/bin/env python3
"""
Main Sync Script
Fetches data from all sources and stores in Google Drive
"""

import os
import sys
import yaml
from datetime import datetime, timedelta
from typing import Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.intervals_icu import IntervalsICUConnector
from connectors.concept2 import Concept2Connector
from connectors.google_drive import GoogleDriveStorage


class FitnessDataSync:
    """Main orchestrator for fitness data synchronization"""

    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.intervals = IntervalsICUConnector(
            api_key=self.config["intervals_icu"]["api_key"],
            athlete_id=self.config["intervals_icu"]["athlete_id"],
        )

        self.concept2 = Concept2Connector(
            username=self.config["concept2"]["username"],
            password=self.config["concept2"]["password"],
        )

        self.storage = GoogleDriveStorage(
            credentials_path=self.config["google_drive"]["credentials_file"],
            folder_structure={
                "raw": self.config["google_drive"]["raw_folder"],
                "processed": self.config["google_drive"]["processed_folder"],
            },
        )

        print("✓ Initialized all connectors and storage")

    # --------------------------------------------------
    # ACTIVITIES
    # --------------------------------------------------
    def sync_activities(self, days_back: int = 7) -> Dict:

        print(f"\n{'='*60}")
        print(f"SYNCING ACTIVITIES ({days_back} days)")
        print(f"{'='*60}")

        newest = datetime.now().strftime("%Y-%m-%d")
        oldest = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        all_activities = []
        stats = {
            "intervals_icu": 0,
            "concept2": 0,
            "total": 0,
            "by_type": {},
        }

        print("\n📊 Fetching from Intervals.icu...")
        try:
            intervals_activities = self.intervals.get_activities(
                start_date=oldest,
                end_date=newest,
            )

            for activity in intervals_activities:
                standardized = self.intervals.standardize_activity(activity)
                all_activities.append(standardized)

                activity_type = standardized["type"]
                stats["by_type"][activity_type] = (
                    stats["by_type"].get(activity_type, 0) + 1
                )

            stats["intervals_icu"] = len(intervals_activities)
            print(f"  ✓ Retrieved {len(intervals_activities)} activities")

        except Exception as e:
            print(f"  ✗ Error fetching from Intervals.icu: {e}")

        stats["total"] = len(all_activities)

        return stats

    # --------------------------------------------------
    # WELLNESS
    # --------------------------------------------------
    def sync_wellness(self, days_back: int = 7) -> Dict:

        print(f"\n{'='*60}")
        print(f"SYNCING WELLNESS DATA ({days_back} days)")
        print(f"{'='*60}")

        newest = datetime.now().strftime("%Y-%m-%d")
        oldest = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        stats = {"total": 0}

        print("\n💤 Fetching wellness from Intervals.icu...")
        try:
            wellness_data = self.intervals.get_wellness_data(
                start_date=oldest,
                end_date=newest,
            )

            standardized = [
                self.intervals.standardize_wellness(w)
                for w in wellness_data
            ]

            stats["total"] = len(standardized)
            print(f"  ✓ Retrieved {len(standardized)} wellness records")

        except Exception as e:
            print(f"  ✗ Error syncing wellness: {e}")

        return stats

    # --------------------------------------------------
    # FITNESS TRENDS
    # --------------------------------------------------
    def sync_fitness_trends(self, days_back: int = 30) -> Dict:

        print(f"\n{'='*60}")
        print(f"SYNCING FITNESS TRENDS ({days_back} days)")
        print(f"{'='*60}")

        newest = datetime.now().strftime("%Y-%m-%d")
        oldest = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        stats = {"total": 0}

        print("\n📈 Fetching fitness trends from Intervals.icu...")
        try:
            fitness_data = self.intervals.get_fitness_trend(
                start_date=oldest,
                end_date=newest,
            )

            stats["total"] = len(fitness_data)
            print(f"  ✓ Retrieved {len(fitness_data)} fitness records")

        except Exception as e:
            print(f"  ✗ Error syncing fitness trends: {e}")

        return stats

    # --------------------------------------------------
    # META (FTP + CP + POWER CURVE)
    # --------------------------------------------------
    def sync_meta(self) -> Dict:

        print(f"\n{'='*60}")
        print("SYNCING META DATA")
        print(f"{'='*60}")

        stats = {"success": False}

        try:
            athlete = self.intervals.get_athlete_info()
            power_curve = self.intervals.get_power_curve(90)

            meta = {
                "last_updated": datetime.now().isoformat(),
                "weight": athlete.get("weight"),
                "ftp": athlete.get("ftp"),
                "w_prime": athlete.get("wPrime"),
                "cp": power_curve.get("cp"),
                "power_curve": power_curve.get("powerCurve"),
            }

            self.storage.upload_json(
                meta,
                "meta.json",
                "processed",
            )

            print("  ✓ Saved meta.json")
            stats["success"] = True

        except Exception as e:
            print(f"  ✗ Error syncing meta: {e}")

        return stats

    # --------------------------------------------------
    # MASTER SYNC
    # --------------------------------------------------
    def sync_all(self, days_back: int = 7, full_sync: bool = False):

        if full_sync:
            days_back = self.config["sync"].get("historical_days", 365)
            print(f"\n🔄 FULL SYNC MODE - Fetching {days_back} days")
        else:
            print(f"\n🔄 INCREMENTAL SYNC - Fetching last {days_back} days")

        start_time = datetime.now()

        activity_stats = self.sync_activities(days_back)
        wellness_stats = self.sync_wellness(days_back)

        fitness_days = 30 if not full_sync else days_back
        fitness_stats = self.sync_fitness_trends(fitness_days)

        meta_stats = self.sync_meta()

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n{'='*60}")
        print("SYNC COMPLETE")
        print(f"{'='*60}")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        print(f"📊 Activities: {activity_stats['total']}")
        print(f"💤 Wellness: {wellness_stats['total']}")
        print(f"📈 Fitness: {fitness_stats['total']}")
        print(f"⚙️ Meta updated: {meta_stats['success']}")
        print(f"{'='*60}\n")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync fitness data from multiple sources"
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config file",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to sync",
    )

    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Do full historical sync",
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)

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
