-- Changes on the hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN good_count INTEGER;
ALTER TABLE hafizs_items ADD COLUMN bad_count INTEGER;
ALTER TABLE hafizs_items ADD COLUMN score INTEGER;
ALTER TABLE hafizs_items ADD COLUMN count INTEGER;
ALTER TABLE hafizs_items RENAME COLUMN last_interval TO current_interval;
ALTER TABLE hafizs_items RENAME COLUMN planned_last_interval TO last_interval;

-- Changes on the revisions table
ALTER TABLE revisions RENAME COLUMN actual_interval TO current_interval;
ALTER TABLE revisions RENAME COLUMN planned_interval TO last_interval;