-- Revisions
PRAGMA foreign_keys = 0;

DROP TABLE IF EXISTS sqlitestudio_temp_table;
CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM revisions;

DROP TABLE revisions;

CREATE TABLE revisions (
    id               INTEGER PRIMARY KEY,
    hafiz_id         INTEGER REFERENCES hafizs (id) ON DELETE CASCADE,
    item_id          INTEGER REFERENCES items (id),
    revision_date    TEXT,
    rating           INTEGER,
    mode_id          INTEGER REFERENCES modes (id),
    plan_id          INTEGER REFERENCES plans (id),
    notes            TEXT,
    last_interval    INTEGER,
    current_interval INTEGER,
    next_interval    INTEGER
);

INSERT INTO revisions (
                          id,
                          hafiz_id,
                          item_id,
                          revision_date,
                          rating,
                          mode_id,
                          plan_id,
                          notes,
                          last_interval,
                          current_interval,
                          next_interval
                      )
                      SELECT id,
                             hafiz_id,
                             item_id,
                             revision_date,
                             rating,
                             mode_id,
                             plan_id,
                             notes,
                             last_interval,
                             current_interval,
                             next_interval
                        FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;

-- Hafizs_items
PRAGMA foreign_keys = 0;

DROP TABLE IF EXISTS sqlitestudio_temp_table;
CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM hafizs_items;

DROP TABLE hafizs_items;

CREATE TABLE hafizs_items (
    id                         INTEGER PRIMARY KEY,
    hafiz_id                   INTEGER REFERENCES hafizs (id) ON DELETE CASCADE,
    item_id                    INTEGER REFERENCES items (id),
    page_number                INTEGER,
    mode_id                    INTEGER REFERENCES modes (id),
    next_review                TEXT,
    last_review                TEXT,
    watch_list_graduation_date TEXT,
    srs_booster_pack_id        INTEGER REFERENCES srs_booster_pack (id),
    good_streak                INTEGER,
    bad_streak                 INTEGER,
    last_interval              INTEGER,
    current_interval           INTEGER,
    next_interval              INTEGER,
    srs_start_date             TEXT,
    good_count                 INTEGER,
    bad_count                  INTEGER,
    score                      INTEGER,
    count                      INTEGER,
    status_id                  INTEGER REFERENCES statuses (id),
    booster_pack_id            INTEGER REFERENCES booster_packs (id) 
);

INSERT INTO hafizs_items (
                             id,
                             hafiz_id,
                             item_id,
                             page_number,
                             mode_id,
                             next_review,
                             last_review,
                             watch_list_graduation_date,
                             srs_booster_pack_id,
                             good_streak,
                             bad_streak,
                             last_interval,
                             current_interval,
                             next_interval,
                             srs_start_date,
                             good_count,
                             bad_count,
                             score,
                             count,
                             status_id,
                             booster_pack_id
                         )
                         SELECT id,
                                hafiz_id,
                                item_id,
                                page_number,
                                mode_id,
                                next_review,
                                last_review,
                                watch_list_graduation_date,
                                srs_booster_pack_id,
                                good_streak,
                                bad_streak,
                                last_interval,
                                current_interval,
                                next_interval,
                                srs_start_date,
                                good_count,
                                bad_count,
                                score,
                                count,
                                status_id,
                                booster_pack_id
                           FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;

-- Hafizs_users
PRAGMA foreign_keys = 0;

DROP TABLE IF EXISTS sqlitestudio_temp_table;
CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM hafizs_users;

DROP TABLE hafizs_users;

CREATE TABLE hafizs_users (
    id                 INTEGER PRIMARY KEY,
    user_id            INTEGER REFERENCES users (id) ON DELETE CASCADE,
    hafiz_id           INTEGER REFERENCES hafizs (id) ON DELETE CASCADE,
    relationship       TEXT,
    granted_by_user_id INTEGER,
    granted_at         TEXT
);

INSERT INTO hafizs_users (
                             id,
                             user_id,
                             hafiz_id,
                             relationship,
                             granted_by_user_id,
                             granted_at
                         )
                         SELECT id,
                                user_id,
                                hafiz_id,
                                relationship,
                                granted_by_user_id,
                                granted_at
                           FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;

-- Plans
PRAGMA foreign_keys = 0;

DROP TABLE IF EXISTS sqlitestudio_temp_table;
CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM plans;

DROP TABLE plans;

CREATE TABLE plans (
    id             INTEGER PRIMARY KEY,
    hafiz_id       INTEGER REFERENCES hafizs (id) ON DELETE CASCADE,
    start_date     TEXT,
    end_date       TEXT,
    start_page     INTEGER,
    end_page       INTEGER,
    revision_count INTEGER,
    page_count     INTEGER,
    completed      INTEGER
);

INSERT INTO plans (
                      id,
                      hafiz_id,
                      start_date,
                      end_date,
                      start_page,
                      end_page,
                      revision_count,
                      page_count,
                      completed
                  )
                  SELECT id,
                         hafiz_id,
                         start_date,
                         end_date,
                         start_page,
                         end_page,
                         revision_count,
                         page_count,
                         completed
                    FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
