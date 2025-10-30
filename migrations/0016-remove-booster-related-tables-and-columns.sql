-- Drop foreign key columns from hafizs_items first
ALTER TABLE hafizs_items DROP COLUMN srs_booster_pack_id;
ALTER TABLE hafizs_items DROP COLUMN booster_pack_id;

-- Drop the booster-related tables
DROP TABLE IF EXISTS srs_booster_pack;
DROP TABLE IF EXISTS booster_packs;
