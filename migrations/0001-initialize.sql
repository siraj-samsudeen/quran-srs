--
-- File generated with SQLiteStudio v3.4.17 on Mon May 19 10:02:50 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: hafizs
CREATE TABLE [hafizs] (
   [id] INTEGER PRIMARY KEY,
   [name] TEXT,
   [age_group] TEXT,
   [daily_capacity] INTEGER
);
INSERT INTO hafizs (id, name, age_group, daily_capacity) VALUES (1, 'Siraj', NULL, NULL);


-- Table: hafizs_items
CREATE TABLE [hafizs_items] (
   [id] INTEGER PRIMARY KEY,
   [hafiz_id] INTEGER REFERENCES [hafizs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [item_id] INTEGER REFERENCES [items]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [page_number] INTEGER,
   [item_type] TEXT,
   [part_type] TEXT,
   [status] TEXT,
   [mode_id] INTEGER REFERENCES [modes]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [active] INTEGER,
   [revision_count] INTEGER,
   [last_revision_date] TEXT,
   [last_revision_rating] INTEGER,
   [total_score] INTEGER,
   [good_streak] INTEGER,
   [bad_streak] INTEGER
);

-- Table: hafizs_users
CREATE TABLE [hafizs_users] (
   [id] INTEGER PRIMARY KEY,
   [user_id] INTEGER REFERENCES [users]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [hafiz_id] INTEGER REFERENCES [hafizs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [relationship] TEXT,
   [granted_by_user_id] INTEGER,
   [granted_at] TEXT
);
INSERT INTO hafizs_users (id, user_id, hafiz_id, relationship, granted_by_user_id, granted_at) VALUES (1, 1, 1, 'self', NULL, NULL);

-- Table: items
CREATE TABLE [items] (
   [id] INTEGER PRIMARY KEY,
   [item_type] TEXT,
   [surah_id] INTEGER REFERENCES [surahs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [surah_name] TEXT,
   [page_id] INTEGER REFERENCES [pages]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [page_number] INTEGER,
   [part_number] INTEGER,
   [start_text] TEXT,
   [part_type] TEXT,
   [hafiz_id] INTEGER REFERENCES [hafizs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [lines] TEXT
);

-- Table: modes
CREATE TABLE [modes] (
   [id] INTEGER PRIMARY KEY,
   [name] TEXT,
   [description] TEXT
);

-- Table: mushafs
CREATE TABLE [mushafs] (
   [id] INTEGER PRIMARY KEY,
   [name] TEXT,
   [description] TEXT,
   [total_pages] INTEGER,
   [lines_per_page] INTEGER
);

-- Table: pages
CREATE TABLE [pages] (
   [id] INTEGER PRIMARY KEY,
   [mushaf_id] INTEGER,
   [page_number] INTEGER,
   [juz_number] TEXT,
   [start_text] TEXT,
   [starting_verse] TEXT,
   [ending_verse] TEXT
);

-- Table: plans
CREATE TABLE [plans] (
   [id] INTEGER PRIMARY KEY,
   [hafiz_id] INTEGER REFERENCES [hafizs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [start_date] TEXT,
   [end_date] TEXT,
   [start_page] INTEGER,
   [end_page] INTEGER,
   [revision_count] INTEGER,
   [page_count] INTEGER,
   [completed] INTEGER
);

-- Table: revisions
CREATE TABLE [revisions] (
   [id] INTEGER PRIMARY KEY,
   [hafiz_id] INTEGER REFERENCES [hafizs]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [item_id] INTEGER REFERENCES [items]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [revision_date] TEXT,
   [rating] INTEGER,
   [mode_id] INTEGER REFERENCES [modes]([id]) ON UPDATE CASCADE ON DELETE CASCADE,
   [plan_id] INTEGER,
   [notes] TEXT
);

-- Table: surahs
CREATE TABLE [surahs] (
   [id] INTEGER PRIMARY KEY,
   [number] INTEGER,
   [name] TEXT,
   [total_ayat] INTEGER
);

-- Table: users
CREATE TABLE [users] (
   [id] INTEGER PRIMARY KEY,
   [name] TEXT,
   [email] TEXT,
   [password] TEXT,
   [role] TEXT
);
INSERT INTO users (id, name, email, password, role) VALUES (1, 'Siraj', 'mailsiraj@gmail.com', '123', 'hafiz');


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
