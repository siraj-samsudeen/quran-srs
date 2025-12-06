import os
import sqlite3
from dataclasses import dataclass
from fasthtml.common import database
from fastmigrate.core import (
    create_db,
    run_migrations,
    _ensure_meta_table,
    _set_db_version,
)


# =============================================================================
# Dataclass Definitions (explicit for IDE support)
# These mirror the database schema - keep in sync with migrations
# Note: Hafiz moved to hafiz_model.py (Phoenix MVC pattern)
# =============================================================================

from dataclasses import dataclass


@dataclass
class User:
    """User account (can have multiple hafiz profiles)."""

    id: int
    name: str | None = None
    email: str | None = None
    password: str | None = None


@dataclass
class Mode:
    """Revision mode (FC, NM, DR, WR, SR)."""

    code: str
    name: str
    description: str | None = None


@dataclass
class Item:
    """Quran page or page-part."""

    id: int
    item_type: str | None = None
    surah_id: int | None = None
    surah_name: str | None = None
    page_id: int | None = None
    start_text: str | None = None
    active: int | None = None
    description: str | None = None


@dataclass
class Page:
    """Quran page metadata."""

    id: int
    mushaf_id: int | None = None
    page_number: int | None = None
    juz_number: int | None = None


@dataclass
class Surah:
    """Quran surah metadata."""

    id: int
    name: str | None = None


@dataclass
class Plan:
    """Full Cycle plan for a hafiz."""

    id: int
    hafiz_id: int | None = None
    completed: int | None = None


@dataclass
class Hafiz_Items:
    """Tracks a hafiz's progress on each item."""

    id: int
    hafiz_id: int
    item_id: int
    mode_code: str
    page_number: int | None = None
    next_review: str | None = None
    last_review: str | None = None
    good_streak: int | None = None
    bad_streak: int | None = None
    last_interval: int | None = None
    next_interval: int | None = None
    srs_start_date: str | None = None
    memorized: bool = False


@dataclass
class Revision:
    """Single review record."""

    id: int
    hafiz_id: int
    item_id: int
    revision_date: str
    rating: int | None = None
    mode_code: str | None = None
    plan_id: int | None = None
    next_interval: int | None = None


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
    """Get database path based on ENV (test/dev/prod)."""
    env = os.getenv("ENV", "dev")
    return DB_CONFIG.get(env, DB_CONFIG["dev"])


DB_PATH = get_database_path()
create_and_migrate_db(DB_PATH)
db = get_database_connection()


# =============================================================================
# Table References (for CRUD operations)
# Note: Dataclasses moved to respective model files (Phoenix pattern)
# Table.cls assignments happen in each model file
# =============================================================================

# Tables (hafizs imported from hafiz_model)
hafizs_items = db.t.hafizs_items
hafizs_items.cls = Hafiz_Items

items = db.t.items
items.cls = Item

modes = db.t.modes
modes.cls = Mode

pages = db.t.pages
pages.cls = Page

plans = db.t.plans
plans.cls = Plan

revisions = db.t.revisions
revisions.cls = Revision

surahs = db.t.surahs
surahs.cls = Surah

users = db.t.users
users.cls = User
