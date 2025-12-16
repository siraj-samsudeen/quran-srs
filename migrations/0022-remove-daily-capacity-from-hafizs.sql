-- Remove daily_capacity column from hafizs table
-- This column is no longer used - Full Cycle now shows all unreviewed items

ALTER TABLE hafizs DROP COLUMN daily_capacity;
