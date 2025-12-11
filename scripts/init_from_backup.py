#!/usr/bin/env python3
"""
Initialize data folder from production backup.

Copies: data_backup/quran_prod_latest.db → data/quran_v10.db

Usage:
    python scripts/init_from_backup.py              # Default: data/quran_v10.db
    python scripts/init_from_backup.py --target PATH  # Custom target path
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

PROD_BACKUP_PATH = "data_backup/quran_prod_latest.db"
DEFAULT_TARGET = "data/quran_v10.db"


def init_from_backup(target_path: str, skip_backup: bool = False):
    """Initialize database from production backup."""

    # Check if source backup exists
    if not Path(PROD_BACKUP_PATH).exists():
        print(f"❌ Error: {PROD_BACKUP_PATH} not found")
        print()
        print("Download the production backup first:")
        print("  → Run: python scripts/download_prod_backup.py")
        print()
        sys.exit(1)

    # Ensure target directory exists
    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

    # Backup existing database if it exists
    if Path(target_path).exists() and not skip_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{target_path}.{timestamp}.backup"
        print(f"📦 Backing up existing database:")
        print(f"   {target_path} → {backup_path}")
        shutil.copy2(target_path, backup_path)
        print()

    # Copy prod backup to target
    print(f"📥 Initializing database:")
    print(f"   {PROD_BACKUP_PATH} → {target_path}")
    shutil.copy2(PROD_BACKUP_PATH, target_path)

    source_size = os.path.getsize(PROD_BACKUP_PATH) / (1024 * 1024)
    target_size = os.path.getsize(target_path) / (1024 * 1024)

    print()
    print(f"✅ Database initialized successfully")
    print(f"   Source: {source_size:.2f} MB")
    print(f"   Target: {target_size:.2f} MB")
    print()

    if target_path == DEFAULT_TARGET:
        print("Ready for development:")
        print("  → uv run main.py")
        print("  → uv run pytest tests/integration -v")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize database from production backup"
    )
    parser.add_argument(
        "--target",
        "-t",
        help="Custom target path (default: data/quran_v10.db)"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backing up existing database"
    )

    args = parser.parse_args()

    # Determine target path
    target_path = args.target if args.target else DEFAULT_TARGET

    try:
        init_from_backup(target_path, args.skip_backup)
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
