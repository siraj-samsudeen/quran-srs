# PostgreSQL Migration Guide

This guide explains how to migrate your Quran SRS application from SQLite to PostgreSQL.

## Overview

The migration setup includes:
- `globals_pg.py` - New database module supporting both SQLite and PostgreSQL
- `migrations_pg/0001-initialize.sql` - Complete PostgreSQL schema (equivalent to all 19 SQLite migrations)
- DIY migration runner (no Alembic complexity!)
- Automatic detection of SQLite vs PostgreSQL based on `DATABASE_URL`

## Prerequisites

### 1. Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Verify installation:**
```bash
psql --version
```

### 2. Install Python Dependencies

```bash
uv sync
```

This will install:
- `fastsql` - FastHTML's PostgreSQL adapter (MiniDataAPI)
- `psycopg2-binary` - PostgreSQL driver for Python

## Testing the Migration (Recommended First Step)

### Step 1: Create a Test Database

```bash
# Connect to PostgreSQL
psql postgres

# Inside psql:
CREATE DATABASE quran_srs_test;
\q
```

### Step 2: Run the Test Script

```bash
# Test with local PostgreSQL (no password)
python test_postgres_migration.py postgresql://localhost/quran_srs_test

# Or with username/password
python test_postgres_migration.py postgresql://your_username:your_password@localhost/quran_srs_test
```

**Expected output:**
```
============================================================
PostgreSQL Migration Test
============================================================

📍 Database URL: localhost/quran_srs_test

📦 Loading globals_pg module (this will run migrations)...
🐘 Using PostgreSQL database
Connecting to PostgreSQL: localhost/quran_srs_test

📝 Applying migration 0001-initialize.sql...
✓ Successfully applied 0001-initialize.sql

✓ Successfully applied 1 migration(s)

✓ Migration completed successfully!

🔍 Verifying tables...
   ✓ users: 0 rows
   ✓ hafizs: 0 rows
   ✓ items: 0 rows
   ✓ hafizs_items: 0 rows
   ✓ revisions: 0 rows
   ✓ plans: 0 rows
   ✓ modes: 5 rows
   ...

🔍 Verifying modes data...
   ✓ DR: Daily Reps
   ✓ FC: Full Cycle
   ✓ NM: New Memorization
   ✓ SR: SRS Mode
   ✓ WR: Weekly Reps

============================================================
✅ All tests passed!
============================================================
```

### Step 3: Inspect the Database (Optional)

```bash
psql quran_srs_test

# Inside psql:
\dt                    # List all tables
\d hafizs              # Describe hafizs table
SELECT * FROM modes;   # Check modes data
\q
```

## Migrating Your Application

### Option A: Switch Completely to PostgreSQL

1. **Create production database:**
   ```bash
   createdb quran_srs_dev
   ```

2. **Update your application to use `globals_pg.py`:**
   ```bash
   # Rename current globals.py as backup
   mv globals.py globals_sqlite.py

   # Use the new PostgreSQL-compatible version
   mv globals_pg.py globals.py
   ```

3. **Configure database URL:**
   ```bash
   # Create .env file
   cp .env.example .env

   # Edit .env and set:
   DATABASE_URL=postgresql://localhost/quran_srs_dev
   ```

4. **Run your application:**
   ```bash
   uv run main.py
   ```

   On first run, the migration will automatically create all tables.

5. **Migrate your data from SQLite:**
   See "Data Migration" section below.

### Option B: Test PostgreSQL Alongside SQLite

You can keep both `globals.py` (SQLite) and `globals_pg.py` (PostgreSQL) and switch between them:

**For SQLite (current):**
```bash
# Use globals.py (no changes needed)
uv run main.py
```

**For PostgreSQL (testing):**
```bash
# Temporarily rename globals
mv globals.py globals_sqlite.py
mv globals_pg.py globals.py

# Set DATABASE_URL
export DATABASE_URL=postgresql://localhost/quran_srs_dev

# Run app
uv run main.py

# Switch back when done
mv globals.py globals_pg.py
mv globals_sqlite.py globals.py
```

## Data Migration (SQLite → PostgreSQL)

Once you've verified the PostgreSQL schema works, you need to migrate your actual data.

### Option 1: Manual Export/Import (Recommended for Small Datasets)

```bash
# Export data from SQLite to CSV
python export_sqlite_data.py

# Import CSV files to PostgreSQL
python import_to_postgresql.py postgresql://localhost/quran_srs_dev
```

(Note: These scripts would need to be created based on your specific data)

### Option 2: Use pgloader (Automatic)

```bash
# Install pgloader
brew install pgloader  # macOS
# OR
sudo apt install pgloader  # Ubuntu

# Migrate automatically
pgloader data/quran_v10.db postgresql://localhost/quran_srs_dev
```

**Note:** pgloader may have issues with SQLite `INTEGER PRIMARY KEY` vs PostgreSQL `SERIAL`. You may need to reset sequences after:

```bash
psql quran_srs_dev -c "SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));"
psql quran_srs_dev -c "SELECT setval('hafizs_id_seq', (SELECT MAX(id) FROM hafizs));"
# ... repeat for all tables with SERIAL primary keys
```

## Shared Database for FastHTML + Phoenix Transition

Once you're on PostgreSQL, you can share the same database between FastHTML and Phoenix:

```
┌─────────────────┐
│   PostgreSQL    │ ← Shared database
│   quran_srs     │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼───┐  ┌───▼────┐
│FastHTML│  │ Phoenix│
│  (5001)│  │  (4000)│
└────────┘  └────────┘
```

**Setup:**
1. Both apps use `DATABASE_URL=postgresql://localhost/quran_srs`
2. Run FastHTML and Phoenix on different ports
3. Gradually migrate routes from FastHTML → Phoenix
4. Both apps see the same data in real-time

**Ecto (Phoenix) Configuration:**
```elixir
# config/dev.exs
config :quran_srs, QuranSrs.Repo,
  username: "postgres",
  password: "",
  hostname: "localhost",
  database: "quran_srs",
  port: 5432
```

## Troubleshooting

### "psycopg2 not found"
```bash
uv add psycopg2-binary
```

### "fastsql not found"
```bash
uv add fastsql
```

### "role 'yourusername' does not exist"
```bash
# Create PostgreSQL user
createuser -s yourusername
```

### "database 'quran_srs_dev' does not exist"
```bash
createdb quran_srs_dev
```

### "connection refused on port 5432"
```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Start if needed
brew services start postgresql@16  # macOS
sudo systemctl start postgresql  # Linux
```

### Migrations not running
```bash
# Check migrations directory exists
ls -la migrations_pg/

# Verify DATABASE_URL is set
echo $DATABASE_URL

# Check PostgreSQL connection manually
psql $DATABASE_URL -c "SELECT version();"
```

## How the Migration System Works

### Automatic Database Detection

`globals_pg.py` automatically detects which database to use:

```python
db_url = os.getenv("DATABASE_URL", "")

if db_url.startswith("postgresql://"):
    # PostgreSQL mode
    run_postgresql_migrations(db_url)
    db = database(db_url)  # Uses fastsql
else:
    # SQLite mode (default)
    run_sqlite_migrations(db_path)
    db = database(db_path)  # Uses fastlite
```

### Migration Tracking

Both systems track applied migrations:
- **SQLite**: `fastmigrate_meta` table
- **PostgreSQL**: `schema_migrations` table

Format:
```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,       -- e.g., 1 (from 0001-initialize.sql)
    applied_at TIMESTAMP DEFAULT NOW()
);
```

### Adding New Migrations

Create new files in `migrations_pg/`:
```
migrations_pg/
├── 0001-initialize.sql
├── 0002-add-new-feature.sql   ← Next migration
└── 0003-another-change.sql
```

The migration runner will automatically apply pending migrations on app startup.

## Reverting to SQLite

If you need to go back to SQLite:

```bash
# Restore original globals.py
mv globals_pg.py globals_postgres_backup.py
mv globals_sqlite.py globals.py  # (if you renamed it)

# Remove DATABASE_URL
unset DATABASE_URL
# OR edit .env and comment out DATABASE_URL

# Run app (will use SQLite)
uv run main.py
```

## Next Steps

1. ✅ Test migration on test database (`quran_srs_test`)
2. ✅ Verify all tables and indexes created correctly
3. ✅ Migrate data from SQLite to PostgreSQL
4. ✅ Test application thoroughly with PostgreSQL
5. ✅ Update production deployment to use PostgreSQL
6. ✅ Start building Phoenix app pointing to same PostgreSQL database

## Support

If you encounter issues:
1. Check the "Troubleshooting" section above
2. Verify PostgreSQL is running: `psql postgres -c "SELECT version();"`
3. Test connection: `psql postgresql://localhost/quran_srs_test`
4. Review migration logs in terminal output
