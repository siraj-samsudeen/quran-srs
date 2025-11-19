-- Remove the status_id column from the hafizs_items table
ALTER TABLE hafizs_items DROP COLUMN status_id;

-- Drop the statuses table
DROP TABLE statuses;
