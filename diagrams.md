# Quran SRS - User Journey Diagrams

Visual walkthrough of the codebase showing which files are touched during each user journey.

---

## 1. High-Level Architecture Overview

```mermaid
graph TB
    subgraph "Browser"
        U[User]
    end

    subgraph "Controllers"
        UC[users_controller.py]
        HC[hafiz_controller.py]
        MAIN[main.py]
        REV[revision.py]
    end

    subgraph "Views"
        UV[users_view.py]
        HV[hafiz_view.py]
        HMV[home_view.py]
        RV[revision_view.py]
    end

    subgraph "Models"
        UM[users_model.py]
        HM[hafiz_model.py]
        RM[revision_model.py]
        CF[common_function.py]
    end

    subgraph "Business Logic"
        FR[fixed_reps.py]
        SR[srs_reps.py]
        NM[new_memorization.py]
    end

    subgraph "Database Tables"
        USERS[(users)]
        HAFIZS[(hafizs)]
        HI[(hafizs_items)]
        REVS[(revisions)]
        PLANS[(plans)]
        ITEMS[(items)]
    end

    U --> UC & HC & MAIN & REV
    UC --> UV & UM
    HC --> HV & HM
    MAIN --> HMV & CF & FR & SR & NM
    REV --> RV & RM

    UM --> USERS
    HM --> HAFIZS & HI & PLANS & ITEMS
    RM --> REVS & HI
    CF --> REVS & HI
    FR & SR & NM --> HI
```

---

## 2. Signup Journey

**Route**: `POST /users/signup`

**Files touched**: `users_controller.py` → `users_view.py` → `users_model.py` → `users` table

```mermaid
sequenceDiagram
    participant B as Browser
    participant UC as users_controller.py:76
    participant UV as users_view.py:91
    participant UM as users_model.py:43
    participant DB as users table

    B->>UC: GET /users/signup
    UC->>UV: render_signup_form()
    UV-->>B: HTML Form

    B->>UC: POST /users/signup (email, password, name)
    UC->>UM: get_user_by_email(email)
    UM->>DB: SELECT * FROM users WHERE email=?
    DB-->>UM: None (not found)
    UC->>DB: users.insert(User)
    DB-->>UC: new user_id
    UC-->>B: Redirect → /users/login
```

---

## 3. Login Journey

**Route**: `POST /users/login`

**Files touched**: `users_controller.py` → `users_view.py` → `users_model.py` → `users` table

```mermaid
sequenceDiagram
    participant B as Browser
    participant UC as users_controller.py:40
    participant UV as users_view.py:64
    participant UM as users_model.py:43
    participant DB as users table
    participant S as Session

    B->>UC: GET /users/login
    UC->>UV: render_login_form()
    UV-->>B: HTML Form

    B->>UC: POST /users/login (email, password)
    UC->>UM: get_user_by_email(email)
    UM->>DB: SELECT * FROM users WHERE email=?
    DB-->>UM: User object
    UC->>UC: compare passwords (hmac)
    UC->>S: sess["user_auth"] = user.id
    UC-->>B: Redirect → /hafiz/selection
```

---

## 4. Hafiz Selection & Creation Journey

**Routes**: `GET /hafiz/selection`, `POST /hafiz/add`, `POST /hafiz/selection`

**Files touched**: `hafiz_controller.py` → `hafiz_view.py` → `hafiz_model.py` → `hafizs`, `hafizs_items`, `plans`, `items` tables

```mermaid
sequenceDiagram
    participant B as Browser
    participant HC as hafiz_controller.py
    participant HV as hafiz_view.py
    participant HM as hafiz_model.py
    participant DB as Database

    B->>HC: GET /hafiz/selection
    HC->>HM: get_hafizs_for_user(user_id)
    HM->>DB: SELECT * FROM hafizs WHERE user_id=?
    DB-->>HM: [Hafiz list]
    HC->>HV: render_hafiz_selection_page()
    HV-->>B: HTML with hafiz cards

    Note over B,DB: Creating New Hafiz
    B->>HC: POST /hafiz/add (name)
    HC->>DB: hafizs.insert(Hafiz)
    DB-->>HC: new hafiz_id
    HC->>HM: populate_hafiz_items(hafiz_id)
    HM->>DB: INSERT INTO hafizs_items (604 items)
    HC->>HM: create_new_plan(hafiz_id)
    HM->>DB: INSERT INTO plans
    HC-->>B: Redirect → /hafiz/selection

    Note over B,DB: Selecting Hafiz
    B->>HC: POST /hafiz/selection (hafiz_id)
    HC->>HC: sess["auth"] = hafiz_id
    HC-->>B: Redirect → /
```

---

## 5. Home Page Dashboard Journey

**Route**: `GET /`

**Files touched**: `main.py` → `common_function.py` → `home_view.py` → `hafizs`, `hafizs_items`, `revisions`, `items`, `modes`, `plans` tables

```mermaid
sequenceDiagram
    participant B as Browser
    participant M as main.py:47
    participant CF as common_function.py
    participant HV as home_view.py
    participant DB as Database

    B->>M: GET /

    Note over M,DB: Load data for each mode
    M->>CF: get_current_date(auth)
    CF->>DB: SELECT current_date FROM hafizs

    loop For each mode (NM, DR, WR, FC, SR)
        M->>CF: make_summary_table(mode_code)
        CF->>DB: SELECT FROM revisions WHERE mode_code=? AND date=?
        CF->>DB: SELECT FROM hafizs_items WHERE mode_code=?
        CF-->>M: Table HTML
    end

    M->>HV: render_pages_revised_indicator()
    HV->>DB: COUNT revisions for today

    M->>CF: main_area(all_tables)
    CF-->>B: Full dashboard with tabs
```

---

## 6. Adding a Revision Journey

**Route**: `POST /add/{item_id}`

**Files touched**: `main.py` → `common_function.py` → `revisions`, `hafizs_items` tables

```mermaid
sequenceDiagram
    participant B as Browser
    participant M as main.py:336
    participant CF as common_function.py
    participant DB as Database

    B->>M: POST /add/{item_id} (rating, mode_code)

    M->>CF: add_revision_record(item_id, mode_code, date, rating)
    CF->>DB: INSERT INTO revisions

    M->>CF: populate_hafizs_items_stat_columns(item_id)
    CF->>DB: SELECT COUNT(*) FROM revisions (for streaks)
    CF->>DB: UPDATE hafizs_items SET good_streak=?, bad_streak=?

    M->>CF: render_range_row(item)
    CF-->>B: HTMX: Updated table row + indicator
```

---

## 7. Close Date Journey (Most Complex!)

**Route**: `POST /close_date`

**Files touched**: `main.py` → `fixed_reps.py` → `srs_reps.py` → `new_memorization.py` → `home_view.py` → `revision_model.py` → `revisions`, `hafizs_items`, `hafizs`, `plans` tables

```mermaid
sequenceDiagram
    participant B as Browser
    participant M as main.py:255
    participant FR as fixed_reps.py
    participant SR as srs_reps.py
    participant NM as new_memorization.py
    participant HV as home_view.py
    participant RM as revision_model.py
    participant DB as Database

    B->>M: POST /close_date
    M->>DB: SELECT * FROM revisions WHERE date=current_date
    DB-->>M: [Today's revisions]

    loop For each revision
        alt mode = FULL_CYCLE
            M->>HV: update_hafiz_item_for_full_cycle(rev)
            HV->>DB: UPDATE hafizs_items SET last_interval=?
        else mode = NEW_MEMORIZATION
            M->>NM: update_hafiz_item_for_new_memorization(rev)
            NM->>DB: UPDATE hafizs_items SET mode_code='DR', memorized=1
        else mode = DAILY_REPS or WEEKLY_REPS
            M->>FR: update_rep_item(rev)
            FR->>DB: UPDATE hafizs_items (mode transition if 7 reviews)
        else mode = SRS
            M->>SR: update_hafiz_item_for_srs(rev)
            SR->>DB: UPDATE hafizs_items SET next_interval=?
        end
    end

    Note over M,DB: Trigger SRS for Bad/Ok FC items
    M->>SR: start_srs_for_ok_and_bad_rating(auth)
    SR->>DB: SELECT FC revisions with rating <= 0
    SR->>DB: UPDATE hafizs_items SET mode_code='SR', next_interval=3/10

    M->>RM: cycle_full_cycle_plan_if_completed()
    RM->>DB: Check if plan complete, create new plan

    M->>DB: UPDATE hafizs SET current_date = current_date + 1
    M-->>B: Redirect → /
```

---

## 8. Mode Progression State Diagram

Shows how items move through the 5 modes based on reviews and ratings.

```mermaid
stateDiagram-v2
    [*] --> NM: New page added

    NM --> DR: Close Date (first review)

    DR --> WR: 7 reviews at 1-day interval
    DR --> DR: < 7 reviews

    WR --> FC: 7 reviews at 7-day interval
    WR --> WR: < 7 reviews

    FC --> SR: Bad/Ok rating on Close Date
    FC --> FC: Good rating

    SR --> FC: next_interval > 99 days
    SR --> SR: next_interval <= 99 days

    note right of NM: New Memorization
    note right of DR: Daily Reps (1-day)
    note right of WR: Weekly Reps (7-day)
    note right of FC: Full Cycle
    note right of SR: SRS Mode
```

---

## File Touch Summary Table

| Journey | Controllers | Views | Models | DB Tables |
|---------|-------------|-------|--------|-----------|
| **Signup** | users_controller.py | users_view.py | users_model.py | users |
| **Login** | users_controller.py | users_view.py | users_model.py | users |
| **Hafiz Selection** | hafiz_controller.py | hafiz_view.py | hafiz_model.py | hafizs, hafizs_items, plans, items |
| **Home Page** | main.py | home_view.py | common_function.py | hafizs, hafizs_items, revisions, items, modes, plans |
| **Add Revision** | main.py, revision.py | revision_view.py | revision_model.py, common_function.py | revisions, hafizs_items |
| **Close Date** | main.py | home_view.py | revision_model.py, common_function.py | revisions, hafizs_items, hafizs, plans |

---

## Rendering These Diagrams

These Mermaid diagrams can be viewed in:
- **GitHub** - renders automatically in markdown files
- **VS Code** - with Mermaid extension installed
- **Obsidian** - native support
- **Online** - paste at [mermaid.live](https://mermaid.live)
