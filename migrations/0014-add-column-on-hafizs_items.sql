ALTER TABLE hafizs_items ADD COLUMN memorized BOOLEAN DEFAULT FALSE;

UPDATE hafizs_items SET memorized = TRUE WHERE status_id IN (1, 5);
