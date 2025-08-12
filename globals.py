import sqlite3
from fasthtml.common import database
from fastmigrate.core import (
    create_db,
    run_migrations,
    _ensure_meta_table,
    _set_db_version,
)


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
    """Get the database file path"""
    return "data/quran_v10.db"


DB_PATH = get_database_path()
create_and_migrate_db(DB_PATH)
db = get_database_connection()


booster_pack = db.t.booster_pack
hafizs = db.t.hafizs
hafizs_items = db.t.hafizs_items
hafizs_users = db.t.hafizs_users
items = db.t.items
modes = db.t.modes
pages = db.t.pages
plans = db.t.plans
revisions = db.t.revisions
srs_booster_pack = db.t.srs_booster_pack
statuses = db.t.statuses
surahs = db.t.surahs
users = db.t.users

(
    Booster_Pack,
    Hafiz,
    Hafiz_Items,
    Hafiz_Users,
    Item,
    Mode,
    Page,
    Plan,
    Revision,
    SRS_Booster_Pack,
    Status,
    Surah,
    User,
) = (
    booster_pack.dataclass(),
    hafizs.dataclass(),
    hafizs_items.dataclass(),
    hafizs_users.dataclass(),
    items.dataclass(),
    modes.dataclass(),
    pages.dataclass(),
    plans.dataclass(),
    revisions.dataclass(),
    srs_booster_pack.dataclass(),
    statuses.dataclass(),
    surahs.dataclass(),
    users.dataclass(),
)
