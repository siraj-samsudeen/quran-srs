-- Migration: Convert hafizs_users M2M relationship to simple 1-to-many
-- This simplifies the data model by adding user_id directly to hafizs table
-- and removes the junction table hafizs_users

-- Step 1: Add user_id column to hafizs table
ALTER TABLE hafizs ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Step 2: Migrate data from hafizs_users to hafizs.user_id
-- Since we're converting M2M to 1-to-many, we take the first user for each hafiz
UPDATE hafizs
SET user_id = (
    SELECT user_id
    FROM hafizs_users
    WHERE hafizs_users.hafiz_id = hafizs.id
    LIMIT 1
);

-- Step 3: Drop the age_group column from hafizs (no longer needed in UI)
-- First, recreate the table without age_group
PRAGMA foreign_keys = OFF;

CREATE TABLE hafizs_new (
    id INTEGER PRIMARY KEY,
    name TEXT,
    daily_capacity INTEGER,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    current_date TEXT
);

INSERT INTO hafizs_new (id, name, daily_capacity, user_id, current_date)
SELECT id, name, daily_capacity, user_id, current_date
FROM hafizs;

DROP TABLE hafizs;

ALTER TABLE hafizs_new RENAME TO hafizs;

PRAGMA foreign_keys = ON;

-- Step 4: Drop the hafizs_users junction table (no longer needed)
DROP TABLE hafizs_users;

-- Verification queries (as comments for manual checking)
-- SELECT id, name, user_id FROM hafizs ORDER BY id;
-- SELECT COUNT(*) as hafiz_count FROM hafizs;
