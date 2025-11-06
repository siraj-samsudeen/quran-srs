# Quick PostgreSQL Migration Test

## 5-Minute Test Guide

### 1. Install PostgreSQL (if not installed)

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Verify
psql --version
```

### 2. Create Test Database

```bash
createdb quran_srs_test
```

### 3. Install Python Dependencies

```bash
uv sync
```

### 4. Run Test

```bash
python test_postgres_migration.py postgresql://localhost/quran_srs_test
```

### 5. Expected Output

```
============================================================
PostgreSQL Migration Test
============================================================

🐘 Using PostgreSQL database
📝 Applying migration 0001-initialize.sql...
✓ Successfully applied 0001-initialize.sql

🔍 Verifying tables...
   ✓ users: 0 rows
   ✓ hafizs: 0 rows
   ✓ modes: 5 rows
   ...

============================================================
✅ All tests passed!
============================================================
```

### 6. Inspect Database (Optional)

```bash
psql quran_srs_test

# Inside psql:
\dt                    # List tables
SELECT * FROM modes;   # Check modes
\q
```

### 7. Clean Up (Optional)

```bash
dropdb quran_srs_test
```

## What Was Created?

✅ **globals_pg.py** - PostgreSQL-compatible database module
✅ **migrations_pg/0001-initialize.sql** - Complete schema (all 19 SQLite migrations)
✅ **test_postgres_migration.py** - Validation script
✅ **.env.example** - Configuration template
✅ **POSTGRES_MIGRATION_GUIDE.md** - Full documentation

## Next Steps

1. **Review the migration**: Open [migrations_pg/0001-initialize.sql](migrations_pg/0001-initialize.sql)
2. **Read full guide**: See [POSTGRES_MIGRATION_GUIDE.md](POSTGRES_MIGRATION_GUIDE.md)
3. **Migrate your app**: Follow "Migrating Your Application" section

## File Changes Summary

### New Files
```
globals_pg.py                    ← New PostgreSQL-compatible globals
migrations_pg/
  └── 0001-initialize.sql        ← Complete PostgreSQL schema
test_postgres_migration.py       ← Test script
.env.example                     ← Environment config template
POSTGRES_MIGRATION_GUIDE.md      ← Full documentation
QUICK_TEST.md                    ← This file
```

### Modified Files
```
pyproject.toml                   ← Added fastsql & psycopg2-binary
```

### Unchanged Files
```
globals.py                       ← Original SQLite version (still works!)
migrations/                      ← Original SQLite migrations (preserved)
main.py                          ← No changes needed!
app/                             ← No changes needed!
```

## How It Works

1. **Environment Detection**: `globals_pg.py` checks `DATABASE_URL` env var
   - If starts with `postgresql://` → Use PostgreSQL
   - Otherwise → Use SQLite (default)

2. **Migration Runner**: Simple ~80 lines of Python
   - Tracks versions in `schema_migrations` table
   - Runs pending `.sql` files in order
   - No complex framework (no Alembic!)

3. **Schema Equivalence**: Single PostgreSQL migration = All 19 SQLite migrations
   - Extracted final schema from your current database
   - Converted `INTEGER PRIMARY KEY` → `SERIAL PRIMARY KEY`
   - Removed SQLite-specific `PRAGMA` statements
   - Added indexes for performance

## Troubleshooting

**Error: `createdb: command not found`**
```bash
# Add PostgreSQL to PATH (macOS)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

**Error: `psycopg2 not found`**
```bash
uv sync
```

**Error: `connection refused`**
```bash
brew services start postgresql@16  # macOS
sudo systemctl start postgresql    # Linux
```

**Error: `role 'yourusername' does not exist`**
```bash
createuser -s yourusername
```
