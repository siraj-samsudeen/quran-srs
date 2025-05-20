-- Changes on the Items table
ALTER TABLE items ADD COLUMN active INTEGER;
ALTER TABLE items DROP COLUMN page_number;


-- Renaming part_number to part but couldn't able to change the datatype
-- so creating a new column and copyingg the value to the new column.
ALTER TABLE items ADD COLUMN part TEXT;
UPDATE items SET part = CAST(part_number AS TEXT);

-- To reorder the columns as we want to part column near the page_id
CREATE TABLE temp_table AS SELECT * FROM items;

DROP TABLE items;

CREATE TABLE items (
    id         INTEGER PRIMARY KEY,
    item_type  TEXT,
    surah_id   INTEGER REFERENCES surahs (id) ON UPDATE CASCADE
                                              ON DELETE CASCADE,
    surah_name TEXT,
    page_id    INTEGER REFERENCES pages (id) ON UPDATE CASCADE
                                             ON DELETE CASCADE,
    part       TEXT,
    start_text TEXT,
    part_type  TEXT,
    hafiz_id   INTEGER REFERENCES hafizs (id) ON UPDATE CASCADE
                                              ON DELETE CASCADE,
    lines      TEXT,
    active     INTEGER
);

INSERT INTO items (
                      id,
                      item_type,
                      surah_id,
                      surah_name,
                      page_id,
                      part,
                      start_text,
                      part_type,
                      hafiz_id,
                      lines,
                      active
                  )
                  SELECT id,
                         item_type,
                         surah_id,
                         surah_name,
                         page_id,
                         part,
                         start_text,
                         part_type,
                         hafiz_id,
                         lines,
                         active
                    FROM temp_table;

DROP TABLE temp_table;