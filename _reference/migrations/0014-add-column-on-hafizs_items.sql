ALTER TABLE hafizs_items ADD COLUMN memorized BOOLEAN DEFAULT FALSE;

-- Update the 'memorized' status based on revision history.
-- An item is considered memorized if it has at least one corresponding record
-- in the 'revisions' table for the same hafiz.
UPDATE hafizs_items
SET memorized = TRUE
WHERE EXISTS (
    SELECT 1
    FROM revisions
    WHERE revisions.hafiz_id = hafizs_items.hafiz_id
      AND revisions.item_id = hafizs_items.item_id
);