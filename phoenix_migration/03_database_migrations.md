# Database Migrations - 3-Layer Architecture Implementation

## Business Context

**Objective**: Transform the existing SQLite schema into a PostgreSQL-based 3-layer architecture that separates algorithms (what the system can do) from patterns (how users configure it) from assignments (current runtime state).

**Success Criteria**: Zero data loss while enabling infinite user customization through the pattern system.

---

## Migration Strategy Overview

### Current State Analysis
- **15 SQLite tables** with embedded business logic in application code
- **Mode system** using crude numbering for sorting (0=Full cycle, 1=Daily, etc.)
- **Booster packs** as separate hardcoded entities
- **hafizs_items** table carrying both configuration and state

### Target Architecture
- **Algorithm Layer**: 3 core memorization algorithms with configurable parameters
- **Pattern Layer**: User-defined configurations that can be shared and customized
- **Assignment Layer**: Real-time state tracking with rich performance analytics

---

## Core Tables Migration

### 1. Foundation Tables (Direct Migration)

**Business Requirements:**
- **mushafs, surahs, pages**: Direct migration with PostgreSQL type improvements
- **users**: Enhanced with role-based access and UI preferences
- **hafizs**: Enhanced with daily capacity planning and personalization features
- **hafizs_users**: Extended with granular permission system for family/teacher scenarios

**Key Enhancements:**
- **User roles**: Support for 'hafiz', 'parent', 'teacher', 'admin' use cases
- **Hafiz capacity**: Daily page limits and preferred study times
- **Multi-user relationships**: Family members can manage each other's progress with appropriate permissions

### 2. Algorithm Layer Implementation

**Business Requirements:**

**algorithms table**: Define the three core memorization approaches
- **New Memorization**: For learning completely new content with intensive repetition
- **Sequential Maintenance**: Systematic review of all memorized content
- **Targeted Strengthening**: Address weakened pages with SRS and configurable intensity

**algorithm_parameters table**: Define what each algorithm can be configured with
- **Flexible parameter system**: Each algorithm exposes different configuration options
- **Type safety**: Parameters have types (integer, boolean, array, object) with constraints
- **Default values**: Sensible defaults for each parameter to minimize user configuration burden

### 3. Pattern Layer Transformation

**Business Requirements:**

**revision_patterns table**: Transform current modes + booster_packs into flexible user patterns
- **Current modes mapping**:
  - "0. Full cycle" → Sequential Maintenance algorithm + full-cycle pattern
  - "1. Daily Reps" → Targeted Strengthening + daily pattern
  - "2. Weekly Reps" → Targeted Strengthening + weekly pattern  
  - "4. SRS - Variable Reps" → Targeted Strengthening + SRS pattern
  - "5. New Memorization" → New Memorization algorithm + intensive pattern

**Key Pattern Features:**
- **Pattern inheritance**: Users can create variations of existing patterns
- **Template sharing**: Successful patterns become templates for community use
- **JSONB configuration**: Flexible parameter storage that can grow without schema changes
- **Usage tracking**: Monitor which patterns are most effective

**pattern_sharing table**: Enable community pattern marketplace
- **Teacher-student sharing**: Teachers can assign specific patterns to students
- **Family pattern libraries**: Parents can create pattern collections for their children
- **Community templates**: Popular patterns become available as starting points

### 4. Assignment Layer Enhancement

**Business Requirements:**

**hafiz_item_assignments table**: Transform hafizs_items into pattern-aware assignments
- **Pattern context**: Each assignment knows which pattern governs its behavior
- **Performance analytics**: Rich JSONB statistics tracking beyond simple good/ok/bad
- **Graduation tracking**: Monitor progress toward pattern completion or advancement
- **Scheduling intelligence**: Smart next-review-date calculation based on pattern + performance

**Key Assignment Features:**
- **One assignment per hafiz-item pair**: Clean state management
- **Graduation workflows**: Items can graduate between patterns (e.g., Daily → SRS → Full Cycle)
- **Performance analytics**: Track streaks, trends, and pattern-specific metrics
- **Flexible status management**: Active, paused, graduating, completed states

---

## Enhanced Day Planning System

### Business Requirements

**day_plans table**: Support advanced day planning features that users requested
- **Future pulling**: Pull items from next 2-3 days when extra time is available
- **Intelligent skipping**: Skip scheduled items with automatic rescheduling logic
- **Plan modification tracking**: Record when and why users change auto-generated plans
- **Flexibility controls**: Each plan defines its own tolerance for changes

**day_plan_modifications table**: Track user customizations to auto-generated plans
- **Modification types**: Skip item, add item, pull from future, change pattern
- **Reason tracking**: Understanding why users modify plans improves future auto-generation
- **User learning**: System learns from modifications to create better default plans

### Enhanced Planning Intelligence
- **Workload balancing**: Avoid overloading catch-up days
- **Context awareness**: Plans adapt to travel, illness, busy periods
- **Pattern coordination**: Multiple patterns per hafiz coordinate through unified daily planning

---

## Revision System Enhancement

### Business Requirements

**revisions table**: Enhanced tracking with pattern context and analytics
- **Pattern awareness**: Each revision knows which pattern and assignment it belongs to
- **Rich context**: Scheduled vs catch-up vs extra practice vs competition prep
- **Performance metrics**: Beyond rating, track confidence level and difficulty perception
- **SRS integration**: Proper interval tracking for spaced repetition patterns
- **Device awareness**: Track mobile vs desktop usage patterns

### Analytics and Intelligence
- **Trend analysis**: Identify declining performance before it becomes problematic
- **Pattern effectiveness**: Measure which patterns work best for which users
- **Similar passage detection**: Community-driven identification of confusing verse groups
- **Personalization data**: Feed user behavior back to improve pattern recommendations

---

## Similar Passage Management

### Business Requirements

**similar_passage_groups + similar_passage_items**: Address the common challenge of confusing similar verses
- **System-defined groups**: Pre-populated groups for commonly confused passages
- **User-defined groups**: Allow hafizs to create custom confusion groups
- **Category classification**: Pronunciation, meaning, structure, or user-defined similarities
- **Pattern integration**: Similar passages can be practiced together through specialized patterns

### Community Intelligence
- **Collective wisdom**: Popular confusion patterns become system defaults
- **Teacher contributions**: Educators can contribute professionally identified similar passage groups
- **Family patterns**: Parents can create custom groups based on their children's specific confusion patterns

---

## Migration Data Intelligence

### Current Production Data Analysis

**Intelligent Migration Strategy**: Don't just copy data, enhance it based on actual usage patterns
- **Performance pattern analysis**: Identify which pages are consistently weak vs strong
- **Usage behavior extraction**: Create personalized default patterns based on current hafizs_items data
- **Similar passage discovery**: Analyze revision history to identify commonly confused pages
- **Family pattern creation**: Extract multi-hafiz household coordination patterns

### Migration Transformation Logic

**From modes to patterns**:
- **Preserve all mode functionality** while enabling infinite customization
- **Create personalized defaults** based on current usage rather than generic templates
- **Extract implicit patterns** from current hafizs_items performance data
- **Enhance graduation logic** based on current score and streak patterns

**From hafizs_items to assignments**:
- **Preserve all performance history** while adding rich pattern context
- **Create assignment-pattern relationships** based on current mode usage
- **Enhanced performance stats** that capture more than just basic ratings
- **Graduation progress tracking** for items ready to move between patterns

---

## Data Integrity and Migration Safety

### Migration Validation Requirements

**Pre-migration verification**:
- **Complete backup** of production SQLite database
- **Schema validation** against current production data
- **Test migration** on copy of production data with full verification

**Post-migration verification**:
- **Row count verification**: Every table must have expected number of records
- **Relationship integrity**: All foreign keys must resolve correctly
- **Data transformation verification**: Enhanced data must be logically consistent
- **Performance baseline**: New system must perform at least as well as current system

### Rollback Strategy
- **Migration reversibility**: Ability to roll back if issues discovered
- **Data export capability**: Extract enhanced data in multiple formats if needed
- **Incremental migration option**: Ability to migrate in phases if full migration has issues

---

## Expected Outcomes

### Immediate Benefits
- **Zero data loss**: All existing functionality preserved
- **Enhanced flexibility**: Pattern system enables infinite customization
- **Better performance**: PostgreSQL performance improvements over SQLite
- **Multi-user support**: Family and teacher coordination becomes seamless

### Long-term Capabilities
- **Pattern marketplace**: Community sharing of effective memorization strategies
- **AI-powered optimization**: JSONB fields enable future ML-driven pattern suggestions
- **Advanced analytics**: Rich performance data enables sophisticated progress tracking
- **Integration readiness**: Clean architecture supports future API development

### User Experience Improvements
- **Personalized defaults**: System starts with patterns optimized for each user
- **Intelligent suggestions**: System learns from behavior to suggest better patterns
- **Family coordination**: Multi-hafiz households get tools designed for their complexity
- **Teacher support**: Professional educators get classroom management capabilities

This migration transforms a good memorization system into an intelligent, flexible, community-driven platform that can adapt to any memorization approach while preserving the traditional methods that have worked for centuries.