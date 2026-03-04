#!/usr/bin/env python3
"""Standalone auto-sourcing script for cron / CLI execution.

Usage:
    python run_auto_sourcing.py              # incremental scan
    python run_auto_sourcing.py --full       # force full scan

Cron example (every Sunday 2:00 AM):
    0 2 * * 0 cd /path/to/Recruitment && python run_auto_sourcing.py >> logs/auto_sourcing.log 2>&1
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("auto_sourcing")


def main():
    parser = argparse.ArgumentParser(description="Run automated talent sourcing")
    parser.add_argument("--full", action="store_true", help="Force full scan instead of incremental")
    args = parser.parse_args()

    from recruitment_agent import RecruitmentAgent
    from auto_sourcer import AutoSourcer

    logger.info("=== Auto Sourcing Run Started at %s ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("Mode: %s", "FULL" if args.full else "INCREMENTAL")

    agent = RecruitmentAgent()
    sourcer = AutoSourcer(agent)

    try:
        run_id = sourcer.run(force_full=args.full)
        runs = sourcer.get_run_history()
        run_info = next((r for r in runs if r["id"] == run_id), None)

        if run_info:
            logger.info("Run completed successfully:")
            logger.info("  Run ID:      %s", run_id)
            logger.info("  Type:        %s", run_info["run_type"])
            logger.info("  HCs matched: %d", run_info["hc_count"])
            logger.info("  Scanned:     %d resumes", run_info["talent_scanned"])
            logger.info("  Matches:     %d (score >= 60)", run_info["matches_found"])
            logger.info("  Duration:    %.1fs", run_info["duration_seconds"])
        else:
            logger.info("Run completed. ID: %s", run_id)

        # Print summary for cron email notification
        if run_info and run_info["matches_found"] > 0:
            shortlist = sourcer.get_shortlist(run_id=run_id)
            print(f"\n📋 New matches found: {len(shortlist)}")
            for sl in shortlist[:20]:
                print(f"  - {sl.get('candidate_name', 'Unknown')} → "
                      f"{sl.get('role_title', '')} "
                      f"({sl.get('score', 0):.0f}/100, {sl.get('verdict', '')})")
            if len(shortlist) > 20:
                print(f"  ... and {len(shortlist) - 20} more")

    except Exception:
        logger.exception("Auto sourcing run failed")
        sys.exit(1)

    logger.info("=== Auto Sourcing Run Finished ===")


if __name__ == "__main__":
    main()
