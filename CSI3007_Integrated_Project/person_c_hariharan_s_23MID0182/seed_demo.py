"""Generate clearly-labelled simulated demo data for Person C.

Usage (from person_c_smart_electricity/):
    python seed_demo.py [--months 6] [--force]
"""

from __future__ import annotations

import argparse

from database import SessionLocal, init_db
from services.demo_service import seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed simulated electricity demo data")
    parser.add_argument("--months", type=int, default=6, choices=range(1, 13))
    parser.add_argument("--force", action="store_true", help="Replace existing demo data")
    args = parser.parse_args()
    init_db()
    with SessionLocal() as db:
        result = seed_demo(db, months=args.months, force=args.force)
    print("SIMULATED DEMO DATA CREATED")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
