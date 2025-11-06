import os
import sqlite3
from pathlib import Path

# Mode Codes (2-character primary keys)
FULL_CYCLE_MODE_CODE = 'FC'
NEW_MEMORIZATION_MODE_CODE = 'NM'
DAILY_REPS_MODE_CODE = 'DR'
WEEKLY_REPS_MODE_CODE = 'WR'
SRS_MODE_CODE = 'SR'


def run_postgresql_migrations(db_url, migrations_dir="migrations_pg/"):
    """
    Run SQL migrations for PostgreSQL.
    Tracks applied migrations in schema_migrations table.
    """
    import psycopg2

    print(f"Connecting to PostgreSQL: {db_url.split('@')[1] if '@' in db_url else db_url}")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Create migration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Get applied versions
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied = set(row[0] for row in cursor.fetchall())
        print(f"Already applied migrations: {sorted(applied) if applied else 'None'}")

        # Find and apply pending migrations
        migrations_path = Path(migrations_dir)
        if not migrations_path.exists():
            print(f"⚠️  Warning: Migration directory '{migrations_dir}' not found")
            cursor.close()
            conn.close()
            return

        migration_files = sorted(migrations_path.glob("*.sql"))
        pending_count = 0

        for sql_file in migration_files:
            # Extract version number from filename (e.g., "0001-initialize.sql" -> 1)
            version = int(sql_file.stem.split('-')[0])

            if version not in applied:
                pending_count += 1
                print(f"\n📝 Applying migration {sql_file.name}...")

                sql = sql_file.read_text()

                # Remove SQLite-specific commands
                sql = sql.replace("PRAGMA foreign_keys = off;", "-- PRAGMA removed (PostgreSQL)")
                sql = sql.replace("PRAGMA foreign_keys = on;", "-- PRAGMA removed (PostgreSQL)")
                sql = sql.replace("PRAGMA foreign_keys = 0;", "-- PRAGMA removed (PostgreSQL)")
                sql = sql.replace("PRAGMA foreign_keys = 1;", "-- PRAGMA removed (PostgreSQL)")

                try:
                    cursor.execute(sql)
                    cursor.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (version,)
                    )
                    conn.commit()
                    print(f"✓ Successfully applied {sql_file.name}")
                except Exception as e:
                    conn.rollback()
                    print(f"✗ Failed to apply {sql_file.name}: {e}")
                    raise

        if pending_count == 0:
            print("\n✓ All migrations already applied, database is up to date")
        else:
            print(f"\n✓ Successfully applied {pending_count} migration(s)")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise


def run_sqlite_migrations(db_path):
    """Run SQLite migrations using fastmigrate (existing behavior)"""
    from fastmigrate.core import (
        create_db,
        run_migrations,
        _ensure_meta_table,
        _set_db_version,
    )

    migrations_dir = "migrations/"
    try:
        create_db(db_path)
    except sqlite3.Error:
        # if the table already exists and doesn't have meta table, create it
        _ensure_meta_table(db_path)
        _set_db_version(db_path, 1)

    success = run_migrations(db_path, migrations_dir, verbose=False)
    if not success:
        print("Database migration failed!")
        raise Exception("SQLite migration failed")


def get_database_connection():
    """
    Get configured database connection with migrations.
    Supports both SQLite and PostgreSQL based on DATABASE_URL env var.
    """
    db_url = os.getenv("DATABASE_URL", "")

    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        # PostgreSQL mode
        print("🐘 Using PostgreSQL database")
        from fastsql.core import database

        run_postgresql_migrations(db_url)
        db = database(db_url)

    else:
        # SQLite mode (default)
        print("📁 Using SQLite database")
        from fasthtml.common import database

        db_path = db_url if db_url else "data/quran_v10.db"
        run_sqlite_migrations(db_path)
        db = database(db_path)

        # Configure auto-checkpoint every 50 pages to prevent large WAL files
        db.execute("PRAGMA wal_autocheckpoint=50;")

    return db


def get_database_path():
    """Get the database file path (legacy for SQLite)"""
    return "data/quran_v10.db"


# Initialize database connection
print("\n" + "="*60)
print("INITIALIZING DATABASE")
print("="*60)
db = get_database_connection()
print("="*60 + "\n")

# Table references
hafizs = db.t.hafizs
hafizs_items = db.t.hafizs_items
items = db.t.items
modes = db.t.modes
pages = db.t.pages
plans = db.t.plans
revisions = db.t.revisions
surahs = db.t.surahs
users = db.t.users

# Dataclasses
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
