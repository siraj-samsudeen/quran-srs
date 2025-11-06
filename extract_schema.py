#!/usr/bin/env python3
"""
Extract schema from SQLite database and convert to PostgreSQL syntax
"""
import sqlite3
import sys

def extract_schema(db_path):
    """Extract CREATE TABLE statements from SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables (excluding sqlite internal tables)
    cursor.execute("""
        SELECT name, sql
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        AND name != 'fastmigrate_meta'
        AND name != 'schema_migrations'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    print("="*80)
    print(f"Found {len(tables)} tables in {db_path}")
    print("="*80)

    for table_name, create_sql in tables:
        print(f"\n-- Table: {table_name}")
        print(create_sql)
        print()

    conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/quran_v10.db"
    extract_schema(db_path)
