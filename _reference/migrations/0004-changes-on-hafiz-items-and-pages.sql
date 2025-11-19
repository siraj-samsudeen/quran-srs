-- Changes on Hafizs_Items table
ALTER TABLE hafizs_items DROP COLUMN item_type;
ALTER TABLE hafizs_items DROP COLUMN part_type;
ALTER TABLE hafizs_items DROP COLUMN active;

-- Changes on pages table
-- Adding multiple_surahs column which contains
ALTER TABLE pages ADD COLUMN multiple_surahs INTEGER;