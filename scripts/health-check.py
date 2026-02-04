#!/usr/bin/env python3
"""
Production Health Check Script
"""

import sys
import requests
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.config import settings


def health_check():
    """Perform comprehensive health check"""

    print("SPORTS CARD AI AGENT - HEALTH CHECK")
    print("=" * 50)

    health_status = True

    # Check 1: Application Health
    print("Checking application health...")
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: Application: HEALTHY")
        else:
            print(f"ERROR: Application: UNHEALTHY (Status: {response.status_code})")
            health_status = False
    except Exception as e:
        print(f"ERROR: Application: ERROR ({e})")
        health_status = False

    # Check 2: Database Connection
    print("\nChecking database connection...")
    try:
        from src.utils.database import get_db

        with get_db() as db:
            result = db.execute("SELECT 1").scalar()
            print("SUCCESS: Database: CONNECTED")
    except Exception as e:
        print(f"ERROR: Database: ERROR ({e})")
        health_status = False

    # Check 3: Configuration
    print("\nChecking configuration...")
    try:
        if settings.DATABASE_URL:
            print("SUCCESS: Database URL: CONFIGURED")
        else:
            print("ERROR: Database URL: MISSING")
            health_status = False

        if settings.EBAY_APP_ID:
            print("SUCCESS: eBay API: CONFIGURED")
        else:
            print("WARNING: eBay API: NOT CONFIGURED (using simulation)")

        if settings.OPENAI_API_KEY:
            print("SUCCESS: OpenAI API: CONFIGURED")
        else:
            print("WARNING: OpenAI API: NOT CONFIGURED (limited features)")

    except Exception as e:
        print(f"ERROR: Configuration: ERROR ({e})")
        health_status = False

    print("\n" + "=" * 50)
    if health_status:
        print("SUCCESS: HEALTH CHECK COMPLETED")
        print("All systems operational!")
    else:
        print("ERROR: HEALTH CHECK FAILED")
        print("Some systems need attention")

    print("=" * 50)
    return health_status


if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
