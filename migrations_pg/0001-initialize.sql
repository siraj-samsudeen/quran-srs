--
-- PostgreSQL Schema for Quran SRS
-- This represents the final schema after all SQLite migrations (0001-0019)
--

-- Table: users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT
);

-- Table: surahs
CREATE TABLE surahs (
    id SERIAL PRIMARY KEY,
    number INTEGER,
    name TEXT,
    total_ayat INTEGER
);

-- Table: mushafs
CREATE TABLE mushafs (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    total_pages INTEGER,
    lines_per_page INTEGER
);

-- Table: pages
CREATE TABLE pages (
    id SERIAL PRIMARY KEY,
    mushaf_id INTEGER,
    page_number INTEGER,
    juz_number TEXT,
    start_text TEXT,
    starting_verse TEXT,
    ending_verse TEXT
);

-- Table: modes (using code as PRIMARY KEY, not id)
CREATE TABLE modes (
    code CHAR(2) PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Insert standard modes
INSERT INTO modes (code, name, description) VALUES
    ('FC', 'Full Cycle', 'Sequential revision of all memorized pages'),
    ('NM', 'New Memorization', 'Learning new pages'),
    ('DR', 'Daily Reps', 'Daily repetition after initial memorization'),
    ('WR', 'Weekly Reps', 'Weekly repetition after daily graduation'),
    ('SR', 'SRS Mode', 'Spaced repetition for problematic pages');

-- Table: hafizs
CREATE TABLE hafizs (
    id SERIAL PRIMARY KEY,
    name TEXT,
    daily_capacity INTEGER,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    current_date TEXT
);

-- Table: items
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    item_type TEXT,
    surah_id INTEGER REFERENCES surahs(id) ON UPDATE CASCADE ON DELETE CASCADE,
    surah_name TEXT,
    page_id INTEGER REFERENCES pages(id) ON UPDATE CASCADE ON DELETE CASCADE,
    page_number INTEGER,
    part_number INTEGER,
    start_text TEXT,
    part_type TEXT,
    hafiz_id INTEGER REFERENCES hafizs(id) ON UPDATE CASCADE ON DELETE CASCADE,
    lines TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Table: hafizs_items
CREATE TABLE hafizs_items (
    id SERIAL PRIMARY KEY,
    hafiz_id INTEGER NOT NULL REFERENCES hafizs(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    page_number INTEGER,
    mode_code CHAR(2) NOT NULL REFERENCES modes(code),
    next_review TEXT,
    last_review TEXT,
    watch_list_graduation_date TEXT,
    good_streak INTEGER,
    bad_streak INTEGER,
    last_interval INTEGER,
    current_interval INTEGER,
    next_interval INTEGER,
    srs_start_date TEXT,
    good_count INTEGER,
    bad_count INTEGER,
    score INTEGER,
    count INTEGER,
    memorized BOOLEAN DEFAULT FALSE
);

-- Table: plans
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    hafiz_id INTEGER REFERENCES hafizs(id) ON UPDATE CASCADE ON DELETE CASCADE,
    start_date TEXT,
    end_date TEXT,
    start_page INTEGER,
    end_page INTEGER,
    revision_count INTEGER,
    page_count INTEGER,
    completed INTEGER
);

-- Table: revisions
CREATE TABLE revisions (
    id SERIAL PRIMARY KEY,
    hafiz_id INTEGER NOT NULL REFERENCES hafizs(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    revision_date TEXT NOT NULL,
    rating INTEGER,
    mode_code CHAR(2) NOT NULL REFERENCES modes(code),
    plan_id INTEGER REFERENCES plans(id),
    notes TEXT,
    last_interval INTEGER,
    current_interval INTEGER,
    next_interval INTEGER
);

-- Create indexes for frequently queried columns
CREATE INDEX idx_hafizs_items_hafiz_id ON hafizs_items(hafiz_id);
CREATE INDEX idx_hafizs_items_mode_code ON hafizs_items(mode_code);
CREATE INDEX idx_hafizs_items_next_review ON hafizs_items(next_review);
CREATE INDEX idx_revisions_hafiz_id ON revisions(hafiz_id);
CREATE INDEX idx_revisions_revision_date ON revisions(revision_date);
CREATE INDEX idx_revisions_mode_code ON revisions(mode_code);
CREATE INDEX idx_items_page_number ON items(page_number);
CREATE INDEX idx_hafizs_user_id ON hafizs(user_id);
