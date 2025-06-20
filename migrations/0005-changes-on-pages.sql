PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM pages;

DROP TABLE pages;

CREATE TABLE pages (
    id              INTEGER PRIMARY KEY,
    mushaf_id       INTEGER REFERENCES mushafs (id),
    page_number     INTEGER,
    juz_number      INTEGER,
    start_text      TEXT,
    starting_verse  TEXT,
    ending_verse    TEXT,
    multiple_surahs INTEGER
);

INSERT INTO pages (
                      id,
                      mushaf_id,
                      page_number,
                      juz_number,
                      start_text,
                      starting_verse,
                      ending_verse,
                      multiple_surahs
                  )
                  SELECT id,
                         mushaf_id,
                         page_number,
                         juz_number,
                         start_text,
                         starting_verse,
                         ending_verse,
                         multiple_surahs
                    FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
