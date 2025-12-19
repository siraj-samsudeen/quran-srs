-- Add page_size column to hafizs table for configurable pagination
ALTER TABLE hafizs ADD COLUMN page_size INTEGER DEFAULT 20;
