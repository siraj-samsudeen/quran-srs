# Quran SRS Data Model

## Core Architecture Principles

### Mushaf-Page-Surah Relationship
**Mushafs are layout systems**, not content variations. The Quran content is universal, but different mushafs present it with different page layouts:
- **Madinah Mushaf**: 15 lines per page = 604 pages
- **Indo-Pak Mushaf**: 15 lines per page = 604 pages (different page breaks)
- **Hypothetical 30-line Mushaf**: Would have ~300 pages

**Key Design Decisions:**
1. **Surahs are mushaf-independent**: The 114 surahs are universal across all mushafs
2. **Pages are mushaf-dependent**: Pages cannot exist without mushaf context (a page IS a mushaf-specific concept)
3. **Items reference both**: Items can reference surahs (universal) and/or pages (mushaf-specific)
4. **Mushaf context flows through pages**: Items don't need direct mushaf_id as they get it through page_id when relevant

**Note on mushaf_id in items**: Currently excluded from items table. May be reconsidered when implementing multi-mushaf support to handle cases where users switch between mushafs for the same surah.

## Master Data Tables

### mushafs
```
mushafs:
  id (PK, integer)
  name (string)
  description (text)
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```
Stores different Quran layout editions. A mushaf defines how the Quran text is divided into pages (15 lines, 13 lines, etc).

### surahs
```
surahs:
  id (PK, integer)
  number (integer)           # 1-114
  name (string)             # Surah name
  total_ayat (integer)      # Total verses in surah
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```
Stores the 114 universal surahs of the Quran. Surahs exist independently of any mushaf layout.

### pages
```
pages:
  id (PK, integer)
  page_number (integer)     # 1-604 (for 15-line mushafs)
  juz_number (integer)      # 1-30 (Para/Juz - 20 pages each)
  start_text (text)         # First words on page for identification
  mushaf_id (FK -> mushafs) # REQUIRED - pages are mushaf-specific
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```
Stores pages within each mushaf. Page count varies by mushaf layout (604 for 15-line mushafs).

**Juz (Para) Division:**
- The Quran is divided into 30 Juz (plural: Ajza), each typically 20 pages
- Juz 1: Pages 1-21 (starts with Al-Fatihah)
- Juz 2: Pages 22-41 (starts in Al-Baqarah "Sayaqool")
- Juz 3: Pages 42-61, and so on...
- Juz 30: Pages 582-604 (includes extra pages to complete the Quran)
- This division helps with planning monthly Quran completion (1 Juz per day)

### ayahs
```
ayahs:
  id (PK, integer)
  ayah_ref (string, unique)    # e.g., "1:1", "2:255"
  ayah_number (integer)         # Verse number within surah
  text_arabic (text)            # Arabic text of the ayah
  surah_id (FK -> surahs)
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```
Stores individual verses with unique reference format and Arabic text.

### items
```
items:
  id (PK, integer)
  
  # Type and scope
  item_type (string)            # "page", "partial_page", "surah", "ayah_range"
  standard (boolean, default: true)  # True for system items, False for user-created
  
  # Relationships (NO mushaf_id - see architecture notes above)
  page_id (FK -> pages)         # For page/partial_page items (carries mushaf context)
  surah_id (FK -> surahs)       # For surah items AND partial_page (which surah it belongs to)
  start_ayah_id (FK -> ayahs)   # For ayah_range items
  end_ayah_id (FK -> ayahs)     # For ayah_range items  
  end_page_id (FK -> pages)     # For items spanning multiple pages
  
  # Range boundaries
  start_line (integer)          # For partial pages (e.g., 1 from "1-5")
  end_line (integer)            # For partial pages (e.g., 5 from "1-5")
  part_number (integer)         # For partial pages ordering (1, 2, 3)
  part_title (string)           # Optional text e.g. "Surah Nisa End"
  
  # Text markers
  start_text (text)             # First words for identification
  
  # Metadata
  title (string)                # Display title
  tags (array of strings)       # For categorization
  
  # Ownership
  created_by_user_id (FK -> users)  # For user-created items (standard=false)
  
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```

**Item Type Requirements:**
- **page**: Requires `page_id`. Full page memorization unit.
- **partial_page**: Requires `page_id`, `surah_id`, `start_line`, `end_line`, `part_number`. Used when a page contains multiple surahs or logical breaks.
- **surah**: Requires `surah_id` only. Mushaf-independent surah memorization.
- **ayah_range**: Requires `start_ayah_id`, optional `end_ayah_id`. For specific verse memorization.

## Authentication Tables

### users
```
users:
  id (PK, integer)
  email (citext, unique)       # Case-insensitive email
  hashed_password (string)
  confirmed_at (utc_datetime)  # Email confirmation timestamp
  inserted_at (utc_datetime)
  updated_at (utc_datetime)
```
User accounts with email-based authentication.

### users_tokens
```
users_tokens:
  id (PK, integer)
  user_id (FK -> users, on_delete: cascade)
  token (binary)
  context (string)             # "session", "confirm", "reset_password"
  sent_to (string)             # Email address where token was sent
  authenticated_at (utc_datetime)
  inserted_at (utc_datetime)
```
Manages authentication tokens for sessions, email confirmation, and password resets.

## Future Tables (Not Yet Implemented)

### hafizs
```
hafizs:
  id (PK, integer)
  user_id (FK -> users)
  name (string)                # Hafiz profile name
  description (text)
  is_primary (boolean)         # Primary hafiz for user
  created_at (utc_datetime)
  updated_at (utc_datetime)
```
Hafiz profiles allowing single user to manage multiple memorization contexts.

### modes
```
modes:
  code (PK, string, 2-char)    # "DR", "WR", "FR", "MR", "FC", "NM", "AR"
  name (string)                # "Daily Reps", "Weekly Reps", etc.
  description (text)
  default_interval (integer)   # Days
  is_active (boolean)
```
Memorization modes defining different review schedules.

### statuses
```
statuses:
  id (PK, integer)
  name (string)                # "new", "learning", "reviewing", "mastered"
  description (text)
  color (string)               # UI color code
```
Status types for memorization progress.

### hafizs_items
```
hafizs_items:
  id (PK, integer)
  hafiz_id (FK -> hafizs)
  item_id (FK -> items)
  
  # Memorization tracking
  mode_code (FK -> modes)
  status_id (FK -> statuses)
  current_interval (integer)   # Days until next review
  next_review_date (date)
  quality_history (jsonb)      # Array of recent quality scores
  mastery_level (integer)      # 0-100 proficiency
  
  # Purpose tracking
  purpose (string)             # "memorization", "revision", "trouble_spot"
  is_active (boolean, default: true)
  
  # Timestamps
  first_learned_at (utc_datetime)
  last_reviewed_at (utc_datetime)
  total_reviews (integer)
  created_at (utc_datetime)
  updated_at (utc_datetime)
  
  # Unique constraint on (hafiz_id, item_id)
```
Tracks memorization progress for each hafiz-item combination.

### revisions
```
revisions:
  id (PK, integer)
  hafiz_item_id (FK -> hafizs_items)
  quality (integer)            # 0-5 Anki-style quality rating
  duration_seconds (integer)   # Time spent on review
  difficulty_rating (integer)  # 1-5 subjective difficulty
  notes (text)                 # Optional review notes
  reviewed_at (utc_datetime)
  
  # Calculated fields
  previous_interval (integer)  # Days since last review
  new_interval (integer)       # Days until next review
  easiness_factor (float)      # SM-2 algorithm factor
```
Individual review sessions with quality ratings and spaced repetition data.

### plans
```
plans:
  id (PK, integer)
  hafiz_id (FK -> hafizs)
  name (string)                # "Full Quran 2024", "Surah Al-Baqarah"
  description (text)
  target_completion_date (date)
  is_active (boolean)
  created_at (utc_datetime)
  updated_at (utc_datetime)
```
Long-term memorization plans and goals.

### plan_items
```
plan_items:
  id (PK, integer)
  plan_id (FK -> plans)
  item_id (FK -> items)
  sequence_order (integer)     # Order within plan
  target_date (date)           # When to complete this item
  is_completed (boolean)
  completed_at (utc_datetime)
```
Items within each memorization plan with sequencing and targets.


## Key Relationships

### Master Data Flow
```
mushafs (1) → pages (604) → items (836+)
surahs (114) → ayahs (6236) 
```

### User Data Flow
```
users (1) → hafizs (many) → hafizs_items (many) → revisions (many)
items (many) ← hafizs_items → modes, statuses
plans (many) → plan_items (many) → items
```

## Data Validation Rules

### Items Table
- `item_type = "page"`: requires `page_id`, no line boundaries
- `item_type = "partial_page"`: requires `page_id`, `start_line`, `end_line`
- `item_type = "surah"`: requires `surah_id`, `page_id` (starting page)
- `item_type = "ayah_range"`: requires `start_ayah_id`, optional `end_ayah_id`
- `item_type = "custom"`: requires `page_id` (starting page)
- `scope = "user"`: requires `created_by_user_id`

#### Item Type Examples

**1. Ayah range (Ayat Al-Kursi)**
```
item_type: "ayah_range"
start_ayah_id: 262, start_ayah_ref: "2:255"
end_ayah_id: 264, end_ayah_ref: "2:257"
title: "Ayat Al-Kursi and following"
```

**2. Single ayah for mutashabihat**
```
item_type: "ayah_range"
start_ayah_id: 69, start_ayah_ref: "2:62"
end_ayah_id: 69, end_ayah_ref: "2:62"
title: "Inna allatheena aamanoo (1 of 3)"
description: "Similar verses: 5:69, 22:17"
```

**3. Full page (no ayah fields needed)**
```
page_id: 5, item_type: "page", title: "Page 5"
```

**4. Surah (no ayah fields needed)**
```
surah_id: 49, item_type: "surah", title: "Al-Hujurat"
```

### Ayahs Table
- `reference` format: "surah:ayah" (e.g., "1:1", "114:6")
- Unique constraint on `(surah_id, ayah_number)`

### Hafizs_Items Table

- purpose values: "memorization", "revision", "trouble_spot"
- Unique constraint on (hafiz_id, item_id)
- is_active determines whether item appears in review queue


## Real workflow example
### Page 106 - Multiple Surahs Example
# Standard items available for all users:
{id: 106, item_type: "page", scope: "standard", page_id: 106, title: "Page 106 Full", active: true}
{id: 107, item_type: "partial_page", scope: "standard", page_id: 106, part_number: 1, start_line: 1, end_line: 5, title: "Nisa End", active: true}
{id: 108, item_type: "partial_page", scope: "standard", page_id: 106, part_number: 2, start_line: 8, end_line: 15, title: "Maidah Start", active: true}


# User creates custom trouble spot:
{id: 1001, item_type: "partial_page", scope: "user", page_id: 106, created_by_user_id: 123, start_line: 3, end_line: 5, title: "Difficult verses"}

### Days journey

# Day 1: Hafiz starts memorizing page 106 in halves
hafizs_items:
  {hafiz_id: 456, item_id: 107, purpose: "memorization", is_active: true, status_id: 2}  # Part 1
  {hafiz_id: 456, item_id: 108, purpose: "memorization", is_active: true, status_id: 2}  # Part 2

# Day 7: Hafiz graduates to full page
hafizs_items:
  {hafiz_id: 456, item_id: 106, purpose: "revision", is_active: true, status_id: 3}     # Full page
  {hafiz_id: 456, item_id: 107, purpose: "memorization", is_active: false}              # Deactivated
  {hafiz_id: 456, item_id: 108, purpose: "memorization", is_active: false}              # Deactivated

# Day 14: Hafiz struggles with lines 3-5, adds trouble spot
hafizs_items:
  {hafiz_id: 456, item_id: 106, purpose: "revision", is_active: true, next_review_date: "2024-12-20"}    # Still active!
  {hafiz_id: 456, item_id: 1001, purpose: "trouble_spot", is_active: true, next_review_date: "2024-12-16"} # Also active!

# Different review intervals for different purposes
revisions:
  {hafiz_item_id: 501, quality: 4, new_interval: 7}   # Full page - 7 days
  {hafiz_item_id: 502, quality: 2, new_interval: 2}   # Trouble spot - 2 days