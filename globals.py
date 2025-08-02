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
