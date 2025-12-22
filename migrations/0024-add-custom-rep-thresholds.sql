-- Add custom repetition threshold columns to hafizs_items table
-- These allow per-item custom repetition targets for each rep mode
-- NULL means use the global default from DEFAULT_REP_COUNTS

ALTER TABLE hafizs_items ADD COLUMN custom_daily_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_weekly_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_fortnightly_threshold INTEGER;
ALTER TABLE hafizs_items ADD COLUMN custom_monthly_threshold INTEGER;
