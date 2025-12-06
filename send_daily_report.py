#!/usr/bin/env python3
# This file was developed with assistance from Claude Code (Anthropic)
# for implementation, debugging, and code optimization.
# Core design decisions and project architecture are original work.
# All code is understood and can be explained by the author.

"""
Daily Donation Report CLI Script
Sends the daily donation report to ADMIN_EMAIL.

Usage:
    python send_daily_report.py                    # Report for yesterday
    python send_daily_report.py --date 2025-12-05  # Report for specific date

Cron example (daily at 00:15):
    15 0 * * * cd /path/to/ngue-bvs-app && /path/to/venv/bin/python send_daily_report.py >> /var/log/ngue-report.log 2>&1
"""

import argparse
import sys
import logging
from datetime import date, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Send daily donation report to admin email'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Report date in YYYY-MM-DD format (default: yesterday)',
        default=None
    )
    args = parser.parse_args()

    # Parse date
    if args.date:
        try:
            report_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        report_date = date.today() - timedelta(days=1)

    logger.info(f"Generating donation report for {report_date.strftime('%d.%m.%Y')}...")

    # Import Flask app and email service
    try:
        from app import app
        from email_service import email_service
    except ImportError as e:
        logger.error(f"Failed to import app modules: {e}")
        sys.exit(1)

    # Send report within app context
    with app.app_context():
        try:
            success = email_service.send_daily_donation_report(report_date)

            if success:
                logger.info(f"Report sent successfully for {report_date.strftime('%d.%m.%Y')}")
                sys.exit(0)
            else:
                logger.error(f"Failed to send report for {report_date.strftime('%d.%m.%Y')}")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Error sending report: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
