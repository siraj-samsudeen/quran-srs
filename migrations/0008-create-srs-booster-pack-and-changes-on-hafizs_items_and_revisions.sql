CREATE TABLE srs_booster_pack (
    id                INTEGER PRIMARY KEY,
    name              TEXT,
    description       TEXT,
    min_interval      INTEGER,
    max_interval      INTEGER,
    interval_days     TEXT
);


-- Changes on the hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN srs_booster_pack_id INTEGER REFERENCES srs_booster_pack(id);
ALTER TABLE hafizs_items ADD COLUMN good_streak INTEGER;
ALTER TABLE hafizs_items ADD COLUMN bad_streak INTEGER;
ALTER TABLE hafizs_items ADD COLUMN last_interval INTEGER;
ALTER TABLE hafizs_items ADD COLUMN next_interval INTEGER;

--Changes on revisions table'
ALTER TABLE revisions ADD COLUMN planned_interval INTEGER;
ALTER TABLE revisions ADD COLUMN actual_interval INTEGER;
ALTER TABLE revisions ADD COLUMN next_interval INTEGER;