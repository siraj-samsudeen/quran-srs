# Quran SRS Data Model - Phoenix Architecture

## Design Philosophy

**"Every hafiz is unique, every memorization journey is different, every life situation requires flexibility."**

This architecture separates **what the system can do** (algorithms) from **how users want to use it** (patterns) from **what's currently happening** (assignments). This enables infinite customization while maintaining clean, maintainable code.

## Architecture Overview

### **3-Layer Architecture**
1. **Algorithm Layer**: Core memorization/revision logic (code-driven)
2. **Pattern Layer**: User-configurable behaviors (data-driven)  
3. **Assignment Layer**: Runtime state and active tracking (dynamic)

### **Core Principles**
- **User agency**: Users control their experience through pattern customization
- **Family flexibility**: Multiple users, multiple hafizs, shared patterns
- **Progressive enhancement**: Start simple, customize as needed
- **Data preservation**: Zero data loss during migration
- **Algorithm separation**: Clean code boundaries

---

## Layer 1: Algorithm Foundation

### algorithms
**The core memorization/revision logic types built into the system.**
```sql
CREATE TABLE algorithms (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**System algorithms:**
- `new_memorization`: Initial learning with intensive repetition
- `sequential_maintenance`: Systematic review of all memorized content  
- `targeted_strengthening`: Address weakened pages with configurable intensity

### algorithm_parameters
**Defines what each algorithm can be configured with.**
```sql
CREATE TABLE algorithm_parameters (
  id SERIAL PRIMARY KEY,
  algorithm_id INTEGER REFERENCES algorithms(id),
  parameter_name TEXT NOT NULL,
  parameter_type TEXT NOT NULL, -- 'integer', 'boolean', 'array', 'object'
  default_value JSONB,
  constraints JSONB, -- min/max values, allowed options
  description TEXT
);
```

---

## Layer 2: User Configuration

### revision_patterns  
**User-defined behaviors that combine algorithms with personal preferences.**
```sql
CREATE TABLE revision_patterns (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  algorithm_id INTEGER REFERENCES algorithms(id),
  config JSONB NOT NULL, -- Algorithm-specific configuration
  
  -- Pattern metadata
  created_by_user_id INTEGER REFERENCES users(id),
  created_by_hafiz_id INTEGER REFERENCES hafizs(id), -- For hafiz-specific patterns
  is_system_default BOOLEAN DEFAULT FALSE,
  is_template BOOLEAN DEFAULT FALSE, -- Shareable templates
  parent_pattern_id INTEGER REFERENCES revision_patterns(id), -- Pattern inheritance
  
  -- Usage tracking
  usage_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Example pattern configs:**
```json
-- Intensive Learning (New Memorization)
{
  "daily_reps": 7,
  "weekly_reps": 7,
  "duration_weeks": 4,
  "graduation_threshold": {"good_streak": 3, "score_minimum": 15},
  "break_on_failure": true
}

-- Travel Maintenance (Sequential)  
{
  "pages_per_day": 3,
  "skip_on_travel": false,
  "flexible_scheduling": true,
  "catch_up_multiplier": 1.5
}

-- Gentle Recovery (Targeted Strengthening)
{
  "daily_reps": 3,
  "weekly_reps": 3,
  "srs_intervals": [1, 2, 3, 5, 8, 13, 21],
  "graduation_criteria": {"consecutive_goods": 2}
}
```

### pattern_sharing
**Enable teachers and families to share effective patterns.**
```sql
CREATE TABLE pattern_sharing (
  id SERIAL PRIMARY KEY,
  pattern_id INTEGER REFERENCES revision_patterns(id),
  shared_by_user_id INTEGER REFERENCES users(id),
  shared_with_user_id INTEGER REFERENCES users(id),
  shared_with_hafiz_id INTEGER REFERENCES hafizs(id),
  permission_level TEXT DEFAULT 'read', -- 'read', 'copy', 'modify'
  shared_at TIMESTAMP DEFAULT NOW()
);
```

---

## Layer 3: Runtime State

### hafiz_item_assignments
**The active tracking of what each hafiz is doing with each item right now.**
```sql
CREATE TABLE hafiz_item_assignments (
  id SERIAL PRIMARY KEY,
  hafiz_id INTEGER REFERENCES hafizs(id),
  item_id INTEGER REFERENCES items(id),
  pattern_id INTEGER REFERENCES revision_patterns(id),
  
  -- Scheduling
  assigned_date DATE NOT NULL,
  next_review_date DATE,
  last_review_date DATE,
  
  -- Performance tracking
  performance_stats JSONB, -- Live statistics specific to this assignment
  status TEXT DEFAULT 'active', -- 'active', 'paused', 'graduating', 'completed'
  
  -- Graduation tracking
  graduation_progress JSONB, -- Progress toward pattern completion
  expected_graduation_date DATE,
  
  -- Assignment metadata
  assigned_by_user_id INTEGER REFERENCES users(id),
  notes TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(hafiz_id, item_id) -- One active assignment per hafiz-item pair
);
```

**Example performance_stats:**
```json
{
  "total_reviews": 23,
  "good_count": 15,
  "ok_count": 6, 
  "bad_count": 2,
  "current_streak": 3,
  "best_streak": 7,
  "score": 13,
  "interval_history": [1, 1, 2, 3, 5, 8],
  "pattern_specific": {
    "weeks_completed": 2,
    "reps_remaining": {"daily": 3, "weekly": 1}
  }
}
```

---

## Enhanced User Management

### users
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'hafiz', -- 'hafiz', 'parent', 'teacher', 'admin'
  
  -- User preferences
  timezone TEXT DEFAULT 'UTC',
  ui_preferences JSONB,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### hafizs
```sql
CREATE TABLE hafizs (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  
  -- Capacity and preferences
  daily_capacity INTEGER DEFAULT 5,
  preferred_time_of_day TEXT, -- 'morning', 'afternoon', 'evening', 'flexible'
  
  -- Day management
  current_date DATE DEFAULT CURRENT_DATE,
  day_planning_horizon_days INTEGER DEFAULT 3, -- Look ahead for planning
  
  -- Display preferences
  bulk_entry_page_count INTEGER DEFAULT 5,
  default_pattern_id INTEGER REFERENCES revision_patterns(id),
  
  -- Progress tracking
  memorization_level TEXT DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced', 'hafiz'
  total_pages_memorized INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### hafizs_users
```sql
CREATE TABLE hafizs_users (
  id SERIAL PRIMARY KEY,
  hafiz_id INTEGER REFERENCES hafizs(id),
  user_id INTEGER REFERENCES users(id),
  relationship TEXT NOT NULL, -- 'self', 'parent', 'teacher', 'sibling', 'guardian'
  permissions JSONB, -- Granular permissions for different actions
  granted_by_user_id INTEGER REFERENCES users(id),
  granted_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(hafiz_id, user_id)
);
```

---

## Enhanced Quran Structure

### similar_passage_groups
**Handle the challenge of confusing similar verses.**
```sql
CREATE TABLE similar_passage_groups (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  category TEXT, -- 'pronunciation', 'meaning', 'structure', 'user_defined'
  created_by_user_id INTEGER REFERENCES users(id),
  is_system_defined BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP DEFAULT NOW()
);
```

### similar_passage_items
```sql
CREATE TABLE similar_passage_items (
  id SERIAL PRIMARY KEY,
  group_id INTEGER REFERENCES similar_passage_groups(id),
  item_id INTEGER REFERENCES items(id),
  notes TEXT, -- Why this item is confusing with others in the group
  
  UNIQUE(group_id, item_id)
);
```

### items
**Enhanced memorization units with better metadata.**
```sql
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  
  -- Item definition
  item_type TEXT NOT NULL, -- 'page', 'page_part', 'surah', 'ayah_range'
  surah_id INTEGER REFERENCES surahs(id),
  page_id INTEGER REFERENCES pages(id),
  
  -- Content metadata
  part_description TEXT, -- "Top half", "Last 5 lines", "Verses 1-10"
  start_text TEXT,
  end_text TEXT,
  estimated_lines INTEGER,
  difficulty_level INTEGER DEFAULT 3, -- 1-5 scale
  
  -- Personalization (NULL for global items)
  hafiz_id INTEGER REFERENCES hafizs(id),
  created_by_user_id INTEGER REFERENCES users(id),
  
  -- Status
  active BOOLEAN DEFAULT TRUE,
  notes TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Enhanced Day Planning

### day_plans
**Support the enhanced day planning workflow.**
```sql
CREATE TABLE day_plans (
  id SERIAL PRIMARY KEY,
  hafiz_id INTEGER REFERENCES hafizs(id),
  plan_date DATE NOT NULL,
  
  -- Plan metadata
  created_by_user_id INTEGER REFERENCES users(id),
  plan_type TEXT DEFAULT 'auto', -- 'auto', 'manual', 'modified'
  base_pattern_id INTEGER REFERENCES revision_patterns(id),
  
  -- Flexibility features
  allows_future_pulls BOOLEAN DEFAULT TRUE,
  allows_skips BOOLEAN DEFAULT TRUE,
  max_future_pull_days INTEGER DEFAULT 3,
  
  -- Plan state
  status TEXT DEFAULT 'pending', -- 'pending', 'active', 'completed', 'skipped'
  completion_percentage INTEGER DEFAULT 0,
  
  -- Generated plan data
  planned_items JSONB, -- Array of {item_id, pattern_id, priority, source}
  actual_items JSONB,  -- What actually got reviewed
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(hafiz_id, plan_date)
);
```

### day_plan_modifications
**Track when users modify auto-generated plans.**
```sql
CREATE TABLE day_plan_modifications (
  id SERIAL PRIMARY KEY,
  day_plan_id INTEGER REFERENCES day_plans(id),
  modification_type TEXT NOT NULL, -- 'skip_item', 'add_item', 'pull_future', 'change_pattern'
  item_id INTEGER REFERENCES items(id),
  original_value JSONB,
  new_value JSONB,
  reason TEXT,
  modified_by_user_id INTEGER REFERENCES users(id),
  modified_at TIMESTAMP DEFAULT NOW()
);
```

---

## Revision History & Analytics

### revisions
**Enhanced revision tracking with pattern context.**
```sql
CREATE TABLE revisions (
  id SERIAL PRIMARY KEY,
  hafiz_id INTEGER REFERENCES hafizs(id),
  item_id INTEGER REFERENCES items(id),
  assignment_id INTEGER REFERENCES hafiz_item_assignments(id),
  
  -- Review details
  revision_date DATE NOT NULL,
  rating INTEGER NOT NULL, -- -1(Bad), 0(Ok), 1(Good)
  confidence_level INTEGER, -- 1-5 scale, optional
  
  -- Context
  review_context TEXT, -- 'scheduled', 'catch_up', 'extra_practice', 'competition_prep'
  pattern_id INTEGER REFERENCES revision_patterns(id),
  day_plan_id INTEGER REFERENCES day_plans(id),
  
  -- SRS data (for targeted strengthening)
  previous_interval INTEGER,
  calculated_next_interval INTEGER,
  
  -- User input
  notes TEXT,
  difficulty_rating INTEGER, -- 1-5, how hard was this review?
  
  -- Metadata
  review_duration_seconds INTEGER,
  device_type TEXT, -- 'mobile', 'desktop', 'tablet'
  
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Migration Mapping

### **From Current SQLite Schema:**

| **Current Table** | **Maps To** | **Transformation** |
|-------------------|-------------|-------------------|
| `modes` | `algorithms` + `revision_patterns` | Split: logic → algorithms, configs → patterns |
| `booster_packs` | `revision_patterns` | Transform to targeted_strengthening patterns |
| `srs_booster_pack` | `revision_patterns` | Transform to SRS-type patterns with interval arrays |
| `hafizs_items` | `hafiz_item_assignments` | Enhanced with pattern_id and performance_stats |
| `revisions` | `revisions` | Enhanced with assignment context and analytics |
| All other tables | Direct migration | With PostgreSQL type improvements |

### **Migration Intelligence:**
- **Analyze usage patterns** in current data to create personalized default patterns
- **Preserve all revision history** with enhanced context
- **Create intelligent pattern suggestions** based on hafiz performance data
- **Pre-populate similar passage groups** for commonly confused verses

---

## Future Extensibility

This architecture supports future enhancements without schema changes:

- **AI-powered pattern optimization**: Add ML recommendations via JSONB configs
- **Community pattern sharing**: Pattern marketplace through sharing tables
- **Advanced analytics**: Rich performance tracking through JSONB fields
- **Integration APIs**: External apps can create custom patterns
- **Multi-language support**: Pattern descriptions and UI preferences in JSONB
- **Advanced scheduling**: Complex algorithms through flexible config system

The separation of concerns means the core algorithm logic stays clean while user customization can grow infinitely complex.