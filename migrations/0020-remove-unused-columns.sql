-- Note: Keeping mushafs table for future multi-mushaf support

-- Remove unused columns from users table
ALTER TABLE users DROP COLUMN role;

-- Remove unused columns from surahs table
ALTER TABLE surahs DROP COLUMN number;
ALTER TABLE surahs DROP COLUMN total_ayat;

-- Remove unused columns from items table
ALTER TABLE items DROP COLUMN part;
ALTER TABLE items DROP COLUMN lines;
ALTER TABLE items DROP COLUMN part_type;
ALTER TABLE items DROP COLUMN hafiz_id;

-- Remove unused columns from pages table
-- Note: Keeping mushaf_id for future multi-mushaf support
ALTER TABLE pages DROP COLUMN start_text;
ALTER TABLE pages DROP COLUMN starting_verse;
ALTER TABLE pages DROP COLUMN ending_verse;
ALTER TABLE pages DROP COLUMN multiple_surahs;

-- Remove unused columns from plans table
ALTER TABLE plans DROP COLUMN start_date;
ALTER TABLE plans DROP COLUMN end_date;
ALTER TABLE plans DROP COLUMN end_page;
ALTER TABLE plans DROP COLUMN revision_count;
ALTER TABLE plans DROP COLUMN page_count;

-- Remove unused columns from hafizs_items table
ALTER TABLE hafizs_items DROP COLUMN watch_list_graduation_date;
ALTER TABLE hafizs_items DROP COLUMN current_interval;
ALTER TABLE hafizs_items DROP COLUMN good_count;
ALTER TABLE hafizs_items DROP COLUMN bad_count;
ALTER TABLE hafizs_items DROP COLUMN score;
ALTER TABLE hafizs_items DROP COLUMN count;

-- Remove unused columns from revisions table
ALTER TABLE revisions DROP COLUMN notes;
ALTER TABLE revisions DROP COLUMN current_interval;
ALTER TABLE revisions DROP COLUMN last_interval;
