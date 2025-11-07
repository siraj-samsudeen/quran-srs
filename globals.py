import os
import sqlite3
from fasthtml.common import database
from fastmigrate.core import (
    create_db,
    run_migrations,
    _ensure_meta_table,
    _set_db_version,
)

# Mode Codes (2-character primary keys)
FULL_CYCLE_MODE_CODE = "FC"
NEW_MEMORIZATION_MODE_CODE = "NM"
DAILY_REPS_MODE_CODE = "DR"
WEEKLY_REPS_MODE_CODE = "WR"
SRS_MODE_CODE = "SR"

RATING_MAP = {"1": "✅ Good", "0": "😄 Ok", "-1": "❌ Bad"}

# Database configuration per environment
DB_CONFIG = {
    "test": "data/quran_test.db",
    "dev": "data/quran_v10.db",
    "prod": "data/quran_v10.db",
}


def create_and_migrate_db(db_path):
    migrations_dir = "migrations/"
    try:
        create_db(db_path)
    except sqlite3.Error:
        # if the table is already exsist, and doesn't have meta table, create it
        _ensure_meta_table(db_path)
        _set_db_version(db_path, 1)
    success = run_migrations(db_path, migrations_dir, verbose=False)
    if not success:
        # Handle migration failure
        print("Database migration failed!")


def get_database_connection():
    """Get configured database connection with migrations"""
    DB_PATH = get_database_path()
    create_and_migrate_db(DB_PATH)
    db = database(DB_PATH)

    # Configure auto-checkpoint every 50 pages to prevent large WAL files
    db.execute("PRAGMA wal_autocheckpoint=50;")

    return db


def get_database_path():
    """
    Get the database file path based on ENV environment variable.

    Environments:
    - test: Uses data/quran_test.db (for E2E tests)
    - dev: Uses data/quran_v10.db (default for local development)
    - prod: Uses data/quran_v10.db (production database)
    """
    env = os.getenv("ENV", "dev")
    return DB_CONFIG.get(env, DB_CONFIG["dev"])


DB_PATH = get_database_path()
create_and_migrate_db(DB_PATH)
db = get_database_connection()


hafizs = db.t.hafizs
hafizs_items = db.t.hafizs_items
items = db.t.items
modes = db.t.modes
pages = db.t.pages
plans = db.t.plans
revisions = db.t.revisions
surahs = db.t.surahs
users = db.t.users

(
    Hafiz,
    Hafiz_Items,
    Item,
    Mode,
    Page,
    Plan,
    Revision,
    Surah,
    User,
) = (
    hafizs.dataclass(),
    hafizs_items.dataclass(),
    items.dataclass(),
    modes.dataclass(),
    pages.dataclass(),
    plans.dataclass(),
    revisions.dataclass(),
    surahs.dataclass(),
    users.dataclass(),
)
