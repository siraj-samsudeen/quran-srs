-- Migration: Allow NULL mode_code for not-memorized pages
-- When a page is not memorized, mode_code is irrelevant and should be NULL

-- SQLite doesn't support ALTER COLUMN, so we need to recreate the table
-- Create new table without NOT NULL constraint on mode_code

CREATE TABLE hafizs_items_new (
    id                         INTEGER PRIMARY KEY,
    hafiz_id                   INTEGER NOT NULL REFERENCES hafizs (id) ON DELETE CASCADE,
    item_id                    INTEGER NOT NULL REFERENCES items (id),
    page_number                INTEGER,
    mode_code                  CHAR(2) REFERENCES modes (code),  -- Removed NOT NULL
    next_review                TEXT,
    last_review                TEXT,
    good_streak                INTEGER,
    bad_streak                 INTEGER,
    last_interval              INTEGER,
    next_interval              INTEGER,
    srs_start_date             TEXT,
    memorized                  BOOLEAN DEFAULT FALSE,
    custom_daily_threshold     INTEGER,
    custom_weekly_threshold    INTEGER,
    custom_fortnightly_threshold INTEGER,
    custom_monthly_threshold   INTEGER
);

-- Copy data from old table
INSERT INTO hafizs_items_new (
    id, hafiz_id, item_id, page_number, mode_code,
    next_review, last_review, good_streak, bad_streak,
    last_interval, next_interval, srs_start_date, memorized,
    custom_daily_threshold, custom_weekly_threshold,
    custom_fortnightly_threshold, custom_monthly_threshold
)
SELECT
    id, hafiz_id, item_id, page_number, mode_code,
    next_review, last_review, good_streak, bad_streak,
    last_interval, next_interval, srs_start_date, memorized,
    custom_daily_threshold, custom_weekly_threshold,
    custom_fortnightly_threshold, custom_monthly_threshold
FROM hafizs_items;

-- Drop old table and rename new one
DROP TABLE hafizs_items;
ALTER TABLE hafizs_items_new RENAME TO hafizs_items;

-- Recreate index
CREATE INDEX idx_hafizs_items_hafiz_id ON hafizs_items (hafiz_id);
