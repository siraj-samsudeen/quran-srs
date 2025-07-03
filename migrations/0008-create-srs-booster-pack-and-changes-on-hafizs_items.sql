CREATE TABLE srs_booster_pack (
    id                INTEGER PRIMARY KEY,
    name              TEXT,
    description       TEXT,
    max_interval      INTEGER,
    interval_days     TEXT,
    is_system_default INTEGER
);


-- Changes on the hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN srs_booster_pack_id INTEGER;
ALTER TABLE hafizs_items ADD COLUMN last_interval INTEGER;
ALTER TABLE hafizs_items ADD COLUMN next_interval INTEGER;