# Quran SRS Phoenix Migration Plan

## Project Overview
Migrate a FastHTML Quran memorization application to Phoenix LiveView, implementing a revolutionary 3-layer architecture that separates algorithms from user patterns from runtime assignments.

## Architecture Vision: 3-Layer System
1. **Algorithm Layer**: Core memorization algorithms (pure functions)
2. **Pattern Layer**: User-configurable behaviors combining algorithms with preferences  
3. **Assignment Layer**: Real-time state tracking for each hafiz-item combination

---

## Migration Plan (16 Steps)

### Phase 1: Foundation (4 steps)
- [x] **Step 1-2**: Generate Phoenix app with SQLite3 + start server
- [ ] **Step 3**: Add authentication system (`mix phx.gen.auth` + multi-hafiz customization)
- [ ] **Step 4**: Design core schema (Accounts, Hafiz, Quran structure, migration from 15 tables)
- [ ] **Step 5**: Seed Quran data (114 surahs, 6236 ayahs) + test users

### Phase 2: 3-Layer Architecture (4 steps)
- [ ] **Step 6**: Algorithm Layer - Core memorization algorithms as contexts
  - NewMemorization: Progressive introduction of new content
  - SequentialMaintenance: Systematic review of known content  
  - TargetedStrengthening: Focus on weak areas
- [ ] **Step 7**: Pattern Layer - User-configurable behavior templates
  - Pattern struct with algorithm combinations
  - Community marketplace foundation
  - Family pattern libraries
- [ ] **Step 8**: Assignment Layer - Real-time hafiz-item state tracking
  - LiveView streams for real-time updates
  - State machine for item progression
  - Performance analytics integration
- [ ] **Step 9**: Integration - Connect all 3 layers with clean interfaces

### Phase 3: Core Features (4 steps)
- [ ] **Step 10**: Dashboard LiveView - Family coordination & hafiz overview
  - Multi-hafiz family dashboard
  - Strengths/weaknesses visualization
  - Parent-child management interface
- [ ] **Step 11**: Day Planning LiveView - Daily assignments & scheduling
  - Future pulling (2-3 days ahead when extra time available)
  - Intelligent skipping with automatic rescheduling
  - Context awareness (travel, illness, busy periods)
- [ ] **Step 12**: Practice Session LiveView - Rating system & real-time updates
  - Good/OK/Bad rating system
  - Real-time progress updates across tabs
  - Session analytics and performance tracking
- [ ] **Step 13**: Pattern Management - Create/edit/share patterns
  - Pattern editor interface
  - Community template sharing
  - Import/export functionality

### Phase 4: Advanced Features (3 steps)
- [ ] **Step 14**: Admin system - User analytics & impersonation
  - Login patterns tracking
  - Feature adoption monitoring
  - Drop-off analysis
  - Admin impersonation (login as any user for testing)
- [ ] **Step 15**: Similar passage management - Community-driven confusion tracking
  - Identify commonly confused verses
  - Grouped practice sessions
  - Pattern integration for confusion resolution
- [ ] **Step 16**: Data migration utilities - SQLite → Phoenix transformation
  - Intelligent transformation of existing 15-table structure
  - Zero data loss migration
  - Data validation and integrity checks

### Phase 5: Polish (1 step)
- [ ] **Step 17**: Final testing & optimization
  - End-to-end workflow testing
  - Performance optimization
  - User acceptance testing with existing user

---

## Key User Personas to Design For

1. **Ahmed**: Complete hafiz & tech professional (travel challenges, performance analytics)
2. **Fatima**: Multi-hafiz family manager (managing 4 people, needs family dashboard)  
3. **Ustadh Abdullah**: Professional teacher (classroom management, parent communication)
4. **Basheer**: Casual memorizer (maintaining Juz 30 + part of Juz 29)
5. **Dr. Amina**: Complete hafiz with shift work (irregular healthcare schedule)

## Success Criteria

- **Zero data loss**: All existing functionality preserved and enhanced
- **Infinite flexibility**: Pattern system enables any memorization approach
- **Family coordination**: Multi-user households get seamless coordination tools
- **Performance improvement**: Faster and more responsive than current system
- **Community features**: Pattern sharing enables collective improvement

## Technical Stack

- **Framework**: Phoenix LiveView 1.1+ 
- **Database**: SQLite3 (for development, PostgreSQL for production)
- **Testing**: PhoenixTest (Playwright-style LiveView testing)
- **Authentication**: Phoenix.gen.auth with multi-hafiz extensions
- **Real-time**: Phoenix PubSub + LiveView streams
- **UI**: TailwindCSS + DaisyUI with custom components

## Migration Philosophy

**"Migrate with confidence, enhance with intelligence."**

Transform the existing system into an intelligent, flexible, community-driven platform that respects traditional memorization methods while embracing modern technology capabilities.

---

## Notes

- Current system: 1 production user willing to experience migration inconveniences
- Original: FastHTML + Python + HTMX + SQLite (15 tables)
- Target: Phoenix LiveView + Elixir + SQLite/PostgreSQL
- Focus: Clean architecture, infinite customization, family coordination