import os
import sqlite3
from fasthtml.common import database
from fastmigrate.core import (
    create_db,
    run_migrations,
    _ensure_meta_table,
    _set_db_version,
)
from utils import table_to_dataclass_name, current_time

# Database configuration per environment
# Note: Tests use dev database - no separate test database
DB_CONFIG = {
    "dev": "data/quran_v10.db",
    "prod": "data/quran_v10.db",
}


def create_and_migrate_db(db_path):
    migrations_dir = "migrations/"
    try:
        create_db(db_path)
    except sqlite3.Error:
        # if the table already exists, and doesn't have meta table, create the metatable
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
    """Get database path based on ENV (dev/prod). Defaults to dev."""
    env = os.getenv("ENV", "dev")
    return DB_CONFIG.get(env, DB_CONFIG["dev"])


def backup_database(backup_dir="data/backup"):
    """Create a backup of the current database with WAL flush.

    Flushes the WAL (Write-Ahead Log) to ensure all data is included in the backup,
    then creates a timestamped backup file.

    Args:
        backup_dir: Directory where backup will be saved (default: "data/backup")

    Returns:
        Path to the created backup file

    Raises:
        FileNotFoundError: If database file doesn't exist
        Exception: If WAL flush or backup fails
    """
    db_path = get_database_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # First flush WAL to ensure all data is in main DB
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL);")
    finally:
        conn.close()

    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = current_time("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_name = f"{os.path.splitext(db_name)[0]}_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)

    # Connect to source database
    source = sqlite3.connect(db_path)

    # Connect to destination database (will create it if it doesn't exist)
    destination = sqlite3.connect(backup_path)

    # Use SQLite's backup API to create the backup
    source.backup(destination)

    # Close connections
    source.close()
    destination.close()

    return backup_path


db = get_database_connection()

# List of database table names
_TABLE_NAMES = [
    "hafizs",
    "items",
    "hafizs_items",
    "modes",
    "pages",
    "plans",
    "revisions",
    "surahs",
    "users",
]

# Initialize table references and dataclasses
# Instead of manually creating each table reference and dataclass, we use a function
# to generate and export them automatically from the table names list above.
for table_name in _TABLE_NAMES:
    table_ref = getattr(db.t, table_name)
    dataclass_name = table_to_dataclass_name(table_name)
    # Make each database table available as a global variable like 'hafizs', 'items', etc.
    globals()[table_name] = table_ref
    # Also expose the dataclass that mirrors each table's schema, e.g., 'Hafiz', 'Item', etc.
    globals()[dataclass_name] = table_ref.dataclass()

# Explicit exports - all public functions, table references, and dataclasses
# Hides private/internal implementation: _TABLE_NAMES, DB_CONFIG, create_and_migrate_db, get_database_connection, DB_PATH, get_database_path
__all__ = [
    # Database functions
    "backup_database",
    # Database connection
    "db",
    # Table references
    "hafizs",
    "hafizs_items",
    "items",
    "modes",
    "pages",
    "plans",
    "revisions",
    "surahs",
    "users",
    # Dataclasses
    "Hafiz",
    "Hafiz_Items",
    "Item",
    "Mode",
    "Page",
    "Plan",
    "Revision",
    "Surah",
    "User",
]
