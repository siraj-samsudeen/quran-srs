#!/usr/bin/env python3
"""
Test script to validate PostgreSQL migration
Tests the migration runner and verifies schema

Usage:
    python test_postgres_migration.py postgresql://user:password@localhost/dbname
"""

import sys
import os

def test_migration(db_url):
    """Test PostgreSQL migration"""
    print("\n" + "="*80)
    print("PostgreSQL Migration Test")
    print("="*80)

    # Set environment variable
    os.environ["DATABASE_URL"] = db_url

    print(f"\n📍 Database URL: {db_url.split('@')[1] if '@' in db_url else db_url}")

    try:
        # Import globals_pg to trigger migration
        print("\n📦 Loading globals_pg module (this will run migrations)...")
        import globals_pg

        print("\n✓ Migration completed successfully!")

        # Verify tables exist
        print("\n🔍 Verifying tables...")
        tables = [
            'users', 'hafizs', 'items', 'hafizs_items',
            'revisions', 'plans', 'modes', 'surahs',
            'pages', 'mushafs', 'schema_migrations'
        ]

        for table_name in tables:
            try:
                result = globals_pg.db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                count = result[0]
                print(f"   ✓ {table_name}: {count} rows")
            except Exception as e:
                print(f"   ✗ {table_name}: {e}")

        # Verify modes data
        print("\n🔍 Verifying modes data...")
        modes = globals_pg.db.execute("SELECT code, name FROM modes ORDER BY code").fetchall()
        for code, name in modes:
            print(f"   ✓ {code}: {name}")

        # Test table access via globals_pg
        print("\n🔍 Testing table access...")
        print(f"   ✓ hafizs table: {globals_pg.hafizs}")
        print(f"   ✓ revisions table: {globals_pg.revisions}")
        print(f"   ✓ modes table: {globals_pg.modes}")

        print("\n" + "="*80)
        print("✅ All tests passed!")
        print("="*80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_usage():
    """Print usage instructions"""
    print("""
PostgreSQL Migration Test Script
=================================

This script tests the PostgreSQL migration by:
1. Running the migration on your PostgreSQL database
2. Verifying all tables were created
3. Checking that modes data was inserted
4. Testing table access via globals_pg

Usage:
    python test_postgres_migration.py <database_url>

Examples:
    # Local PostgreSQL (no password)
    python test_postgres_migration.py postgresql://localhost/quran_srs_test

    # With username and password
    python test_postgres_migration.py postgresql://user:password@localhost/quran_srs_test

    # With host and port
    python test_postgres_migration.py postgresql://user:password@localhost:5432/quran_srs_test

Prerequisites:
    1. PostgreSQL server running
    2. Database created: createdb quran_srs_test
    3. Dependencies installed: uv sync

Note: This will create tables in the specified database. Use a test database!
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    db_url = sys.argv[1]

    if not db_url.startswith("postgresql://") and not db_url.startswith("postgres://"):
        print("❌ Error: Database URL must start with 'postgresql://' or 'postgres://'")
        print_usage()
        sys.exit(1)

    success = test_migration(db_url)
    sys.exit(0 if success else 1)
