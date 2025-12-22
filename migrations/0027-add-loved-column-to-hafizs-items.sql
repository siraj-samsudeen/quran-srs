-- Add loved column to hafizs_items table for marking favorite pages
ALTER TABLE hafizs_items ADD COLUMN loved INTEGER DEFAULT 0;
