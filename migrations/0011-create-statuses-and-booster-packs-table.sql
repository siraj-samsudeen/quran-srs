-- create statuses table
CREATE TABLE statuses (
    id     INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT
    
);

-- create booster_packs table
CREATE TABLE booster_packs(
    id                INTEGER PRIMARY KEY,
    name              TEXT,
    description       TEXT,
    daily_reps        INTEGER,
    weekly_reps       INTEGER
);

-- add status_id and booster_pack_id column to hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN status_id INTEGER REFERENCES statuses(id);
ALTER TABLE hafizs_items ADD COLUMN booster_pack_id INTEGER REFERENCES booster_packs(id);
