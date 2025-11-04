-- Migration: Add mode_code column alongside mode_id (incremental migration)
-- This aligns FastHTML with planned Phoenix architecture while keeping backward compatibility

-- Step 1: Add code column to modes table (2-character codes)
ALTER TABLE modes ADD COLUMN code CHAR(2);

-- Step 2: Populate code column based on existing id values
UPDATE modes SET code = CASE id
    WHEN 1 THEN 'FC'
    WHEN 2 THEN 'NM'
    WHEN 3 THEN 'DR'
    WHEN 4 THEN 'WR'
    WHEN 5 THEN 'SR'
END;

-- Step 3: Add mode_code column to hafizs_items table
ALTER TABLE hafizs_items ADD COLUMN mode_code CHAR(2);

-- Step 4: Populate mode_code based on existing mode_id
UPDATE hafizs_items SET mode_code = CASE mode_id
    WHEN 1 THEN 'FC'
    WHEN 2 THEN 'NM'
    WHEN 3 THEN 'DR'
    WHEN 4 THEN 'WR'
    WHEN 5 THEN 'SR'
END;

-- Step 5: Add mode_code column to revisions table
ALTER TABLE revisions ADD COLUMN mode_code CHAR(2);

-- Step 6: Populate mode_code based on existing mode_id
UPDATE revisions SET mode_code = CASE mode_id
    WHEN 1 THEN 'FC'
    WHEN 2 THEN 'NM'
    WHEN 3 THEN 'DR'
    WHEN 4 THEN 'WR'
    WHEN 5 THEN 'SR'
END;

-- Step 7: Verification queries (as comments for manual checking)
-- SELECT id, code, name FROM modes ORDER BY id;
-- SELECT mode_id, mode_code, COUNT(*) FROM hafizs_items GROUP BY mode_id, mode_code ORDER BY mode_id;
-- SELECT mode_id, mode_code, COUNT(*) FROM revisions GROUP BY mode_id, mode_code ORDER BY mode_id;
