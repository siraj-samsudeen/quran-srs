-- Note: Keeping mushafs table for future multi-mushaf support

-- Remove unused columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS role;

-- Remove unused columns from surahs table
ALTER TABLE surahs DROP COLUMN IF EXISTS number;
ALTER TABLE surahs DROP COLUMN IF EXISTS total_ayat;

-- Remove unused columns from items table
ALTER TABLE items DROP COLUMN IF EXISTS part;
ALTER TABLE items DROP COLUMN IF EXISTS lines;
ALTER TABLE items DROP COLUMN IF EXISTS part_type;
ALTER TABLE items DROP COLUMN IF EXISTS hafiz_id;

-- Remove unused columns from pages table
-- Note: Keeping mushaf_id for future multi-mushaf support
ALTER TABLE pages DROP COLUMN IF EXISTS start_text;
ALTER TABLE pages DROP COLUMN IF EXISTS starting_verse;
ALTER TABLE pages DROP COLUMN IF EXISTS ending_verse;
ALTER TABLE pages DROP COLUMN IF EXISTS multiple_surahs;

-- Remove unused columns from plans table
ALTER TABLE plans DROP COLUMN IF EXISTS start_date;
ALTER TABLE plans DROP COLUMN IF EXISTS end_date;
ALTER TABLE plans DROP COLUMN IF EXISTS end_page;
ALTER TABLE plans DROP COLUMN IF EXISTS revision_count;
ALTER TABLE plans DROP COLUMN IF EXISTS page_count;

-- Remove unused columns from hafizs_items table
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS watch_list_graduation_date;
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS current_interval;
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS good_count;
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS bad_count;
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS score;
ALTER TABLE hafizs_items DROP COLUMN IF EXISTS count;

-- Remove unused columns from revisions table
ALTER TABLE revisions DROP COLUMN IF EXISTS notes;
ALTER TABLE revisions DROP COLUMN IF EXISTS current_interval;
