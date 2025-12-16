#!/usr/bin/env python3
"""
Download latest production database backup from quransrs.com using Chrome MCP.

Saves to: data_backup/quran_prod_latest.db

Usage:
    python scripts/download_prod_backup.py
"""

import os
import sys
import shutil
from pathlib import Path

PROD_BACKUP_PATH = "data_backup/quran_prod_latest.db"
CHROME_MCP_DOWNLOAD_DIR = ".playwright-mcp"


def download_prod_backup():
    """Download production backup and save to data_backup folder."""

    mcp_download_path = Path(CHROME_MCP_DOWNLOAD_DIR) / "quran-backup.db"

    print("📋 Download Instructions:")
    print("   1. Chrome MCP extension must be connected (red AI icon)")
    print("   2. Visit https://quransrs.com/admin/backup in Chrome")
    print("   3. Select a hafiz if needed")
    print("   4. File downloads to .playwright-mcp/quran-backup.db")
    print()

    # Check if Chrome MCP download exists
    if not mcp_download_path.exists():
        print(f"❌ Error: {mcp_download_path} not found")
        print()
        print("Download the backup first:")
        print("  → Open Chrome and visit: https://quransrs.com/admin/backup")
        print()
        sys.exit(1)

    # Ensure data_backup directory exists
    os.makedirs("data_backup", exist_ok=True)

    # Copy to data_backup folder
    print(f"📥 Copying to {PROD_BACKUP_PATH}...")
    shutil.copy2(mcp_download_path, PROD_BACKUP_PATH)

    file_size = os.path.getsize(PROD_BACKUP_PATH) / (1024 * 1024)
    print(f"✅ Production backup saved: {PROD_BACKUP_PATH} ({file_size:.2f} MB)")
    print()
    print("Next steps:")
    print(f"  → Run: python scripts/init_from_backup.py")
    print(f"  → This will copy {PROD_BACKUP_PATH} to data/quran_v10.db")

    return PROD_BACKUP_PATH


if __name__ == "__main__":
    try:
        download_prod_backup()
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
