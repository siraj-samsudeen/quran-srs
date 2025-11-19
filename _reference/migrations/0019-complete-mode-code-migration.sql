-- Migration: Complete migration from mode_id to mode_code
-- Makes code the PRIMARY KEY in modes table and removes all mode_id columns

-- SQLite doesn't support dropping columns or modifying constraints easily,
-- so we need to recreate tables with the new schema

PRAGMA foreign_keys = OFF;

-- Step 1: Recreate modes table with code as PRIMARY KEY
CREATE TABLE modes_new (
    code CHAR(2) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Copy data from old modes table
INSERT INTO modes_new (code, name, description)
SELECT code, name, description FROM modes;

DROP TABLE modes;

ALTER TABLE modes_new RENAME TO modes;

-- Step 2: Recreate hafizs_items table without mode_id
CREATE TABLE hafizs_items_new (
    id                         INTEGER PRIMARY KEY,
    hafiz_id                   INTEGER NOT NULL REFERENCES hafizs (id) ON DELETE CASCADE,
    item_id                    INTEGER NOT NULL REFERENCES items (id),
    page_number                INTEGER,
    mode_code                  CHAR(2) NOT NULL REFERENCES modes (code),
    next_review                TEXT,
    last_review                TEXT,
    watch_list_graduation_date TEXT,
    good_streak                INTEGER,
    bad_streak                 INTEGER,
    last_interval              INTEGER,
    current_interval           INTEGER,
    next_interval              INTEGER,
    srs_start_date             TEXT,
    good_count                 INTEGER,
    bad_count                  INTEGER,
    score                      INTEGER,
    count                      INTEGER,
    memorized                  BOOLEAN DEFAULT FALSE
);

-- Copy data from old hafizs_items table (excluding mode_id)
INSERT INTO hafizs_items_new (
    id, hafiz_id, item_id, page_number, mode_code,
    next_review, last_review, watch_list_graduation_date,
    good_streak, bad_streak, last_interval, current_interval, next_interval,
    srs_start_date, good_count, bad_count, score, count, memorized
)
SELECT
    id, hafiz_id, item_id, page_number, mode_code,
    next_review, last_review, watch_list_graduation_date,
    good_streak, bad_streak, last_interval, current_interval, next_interval,
    srs_start_date, good_count, bad_count, score, count, memorized
FROM hafizs_items;

DROP TABLE hafizs_items;

ALTER TABLE hafizs_items_new RENAME TO hafizs_items;

-- Step 3: Recreate revisions table without mode_id
CREATE TABLE revisions_new (
    id               INTEGER PRIMARY KEY,
    hafiz_id         INTEGER NOT NULL REFERENCES hafizs (id) ON DELETE CASCADE,
    item_id          INTEGER NOT NULL REFERENCES items (id),
    revision_date    TEXT NOT NULL,
    rating           INTEGER,
    mode_code        CHAR(2) NOT NULL REFERENCES modes (code),
    plan_id          INTEGER REFERENCES plans (id),
    notes            TEXT,
    last_interval    INTEGER,
    current_interval INTEGER,
    next_interval    INTEGER
);

-- Copy data from old revisions table (excluding mode_id)
INSERT INTO revisions_new (
    id, hafiz_id, item_id, revision_date, rating, mode_code,
    plan_id, notes, last_interval, current_interval, next_interval
)
SELECT
    id, hafiz_id, item_id, revision_date, rating, mode_code,
    plan_id, notes, last_interval, current_interval, next_interval
FROM revisions;

DROP TABLE revisions;

ALTER TABLE revisions_new RENAME TO revisions;

PRAGMA foreign_keys = ON;

-- Verification queries (as comments for manual checking)
-- SELECT code, name, description FROM modes ORDER BY code;
-- SELECT mode_code, COUNT(*) FROM hafizs_items GROUP BY mode_code ORDER BY mode_code;
-- SELECT mode_code, COUNT(*) FROM revisions GROUP BY mode_code ORDER BY mode_code;
-- PRAGMA foreign_key_check;
