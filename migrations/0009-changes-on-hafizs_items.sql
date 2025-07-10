-- Changes on the hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN total_score INTEGER;
ALTER TABLE hafizs_items ADD COLUMN average_score INTEGER;
ALTER TABLE hafizs_items ADD COLUMN good_score INTEGER;
ALTER TABLE hafizs_items ADD COLUMN bad_score INTEGER;
ALTER TABLE hafizs_items RENAME COLUMN planned_last_interval TO planned_interval;
ALTER TABLE hafizs_items RENAME COLUMN last_interval TO actual_interval;

