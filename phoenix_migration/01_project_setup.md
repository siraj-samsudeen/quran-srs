# Step 1: Phoenix Project Setup

## Project Overview

**Quran SRS** is a sophisticated Spaced Repetition System for Quran memorization and revision with revolutionary 3-layer architecture. We're migrating from FastHTML to Phoenix LiveView with major enhancements.

### Revolutionary 3-Layer Architecture

**Current Problem**: Existing systems mix memorization algorithms with user preferences, making customization impossible.

**Our Solution**: Separate what the system can do (algorithms) from how users want to use it (patterns) from what's currently happening (assignments).

1. **Algorithm Layer**: 3 core memorization algorithms built into the system
   - **New Memorization**: Initial learning with intensive repetition and graduation criteria
   - **Sequential Maintenance**: Systematic review of all memorized content in order
   - **Targeted Strengthening**: Address weakened pages with SRS and configurable intensity

2. **Pattern Layer**: User-configurable behaviors that combine algorithms with personal preferences
   - **Infinite customization**: Users create patterns like "Travel Focus", "Competition Prep", "Gentle Recovery"
   - **Community sharing**: Successful patterns become templates for others
   - **Family coordination**: Parents create pattern libraries for their children

3. **Assignment Layer**: Real-time state tracking for each hafiz-item combination
   - **Pattern-aware**: Each assignment knows which pattern governs its behavior
   - **Performance analytics**: Rich statistics beyond simple good/ok/bad ratings
   - **Graduation workflows**: Items can graduate between patterns automatically

### Current FastHTML Features Being Enhanced

- **Multi-user architecture**: Enhanced with role-based permissions and family coordination tools
- **Flexible memorization units**: Pages, page-parts, surahs, with personalized items per hafiz
- **Multiple revision modes**: Transformed into flexible pattern system with infinite customization
- **Rating system**: Enhanced with confidence levels, difficulty perception, and context tracking
- **Spaced repetition**: Multiple SRS strategies (conservative, aggressive, adaptive) within patterns

## Key User Personas

The system serves diverse users with different memorization needs and family situations:

### 1. Ahmed: Complete Hafiz & Tech Professional
**Profile**: 35-year-old software engineer, complete hafiz, travels 2-3 weeks monthly
**Pattern Needs**: 
- **"Home Maintenance Pattern"**: 20 pages/day sequential revision
- **"Travel Focus Pattern"**: 8-12 weakest pages during travel
- **"Competition Prep Pattern"**: Intensive review for community competitions
**Key Challenge**: Travel disruption and performance analytics for weak spots

### 2. Fatima: Multi-Hafiz Family Manager  
**Profile**: 42-year-old mother managing 4 hafiz profiles (3 children + herself)
**Family Context**:
- **Zahran (14)**: Advanced - 1 page/day, competition prep
- **Abdur Rahman (11)**: Intermediate - 5 lines/day, middle surahs
- **Maryam (8)**: Beginner - 3 lines/day, Juz 29 after completing Juz 30
- **Herself**: Personal journey interrupted by family responsibilities
**Pattern Needs**: Family dashboard with strengths/weaknesses analysis, age-appropriate patterns, emergency flexibility
**Key Challenge**: Overwhelming complexity of tracking 4 different memorization journeys and identifying who needs help

### 3. Ustadh Abdullah: Professional Quran Teacher
**Profile**: 38-year-old professional teacher managing 10+ students across different levels
**Pattern Needs**:
- **Professional Teaching Dashboard**: Student overview with performance indicators and strengths/weaknesses analysis
- **Automated Progress Reports**: Generated summaries with strengths/weaknesses for parent meetings
- **Early Warning System**: Alerts for students showing decline in specific areas
- **Parent Coordination**: Shared dashboard access for parents to see their child's progress
**Key Challenge**: Individual tracking within group setting, parent communication, identifying specific areas where each student needs support

### 4. Basheer: Casual Memorizer with Work Pressure
**Profile**: 40-year-old marketing manager, memorized Juz 30 and part of Juz 29, struggles with consistency
**Pattern Needs**:
- **"Working Professional Pattern"**: Realistic expectations for busy professionals
- **"Maintenance Focus Pattern"**: Strong emphasis on preserving existing memorization
- **"Gentle Expansion Pattern"**: Optional progression to additional memorization when ready
- **Prayer Integration**: Patterns that enhance daily salah experience
**Key Challenge**: Work travel and deadlines disrupt routine, forgetting previously strong surahs, motivation fluctuation

### 5. Dr. Amina: Healthcare Professional with Irregular Schedule
**Profile**: 32-year-old emergency room doctor, complete hafiz, unpredictable work schedule
**Pattern Needs**:
- **"Healthcare Professional Pattern"**: Designed for shift workers' erratic schedules
- **"Crisis Mode Pattern"**: Minimal but effective revision during high-stress periods
- **"Recovery Intensive Pattern"**: Catch-up sessions during lighter work periods
- **"Night Shift Adaptation"**: Revision patterns that work with rotating shifts
**Key Challenge**: 12-hour shifts, mental exhaustion, maintaining full Quran strength despite unpredictable schedule

## Business Requirements

### Pattern System Architecture

**Core Business Value**: Enable infinite customization while maintaining clean, maintainable code through separation of concerns.

**Pattern Creation Workflow**:
1. **Choose Algorithm Base**: New Memorization, Sequential Maintenance, or Targeted Strengthening
2. **Configure Algorithm Parameters**: Each algorithm exposes different settings (daily capacity, intervals, graduation criteria)
3. **Set Context Rules**: Time preferences, device preferences, travel adaptations
4. **Test and Refine**: Pattern performance is tracked and can be optimized over time

**Pattern Sharing and Community**:
- **Template Marketplace**: Successful patterns become templates for community use
- **Family Pattern Libraries**: Parents create collections optimized for their children
- **Professional Patterns**: Teachers share classroom-tested approaches
- **Cultural Adaptations**: Patterns optimized for different cultural contexts (travel, work schedules, age groups)

### Enhanced User Management

**Multi-User Architecture**: The system handles complex family and educational relationships:
- **Single user accounts can manage multiple hafiz profiles** (Fatima manages 4 hafizs including herself)
- **Independent access with cross-permissions** (Zainab has her own login but can update siblings' data)  
- **Shared access scenarios** (both parents accessing child's memorization data with strengths/weaknesses dashboards)
- **Teacher-student-parent triangulation** (Ustadh Abdullah assigns patterns, parents supervise via shared dashboards, system coordinates)

**Permission System**: Granular permissions through hafizs_users association table:
- **Relationship types**: 'self', 'parent', 'teacher', 'sibling', 'guardian', 'admin'
- **Permission levels**: View-only, update progress, modify patterns, full admin
- **Delegation support**: Users can grant specific permissions to family members or teachers
- **Admin impersonation**: Admins can login as any user to test system from their perspective without knowing passwords

**User Analytics & Monitoring**: Comprehensive tracking for user behavior analysis:
- **Login patterns**: Track frequency, duration, and consistency of user sessions
- **Feature adoption**: Monitor which features new users engage with vs ignore
- **Drop-off analysis**: Identify where users get stuck or abandon the system
- **Usage progression**: Track journey from signup → first login → first revision → regular usage
- **Admin dashboard**: Real-time analytics showing user engagement patterns and potential friction points

### Enhanced Day Planning Intelligence

**Future Pulling**: Pull items from next 2-3 days when extra time is available
**Intelligent Skipping**: Skip scheduled items with automatic rescheduling logic that prevents overload
**Plan Modification Tracking**: Record when and why users change auto-generated plans
**Context Awareness**: Plans adapt to travel, illness, busy periods, and family emergencies
**Load Balancing**: System spreads catch-up work to avoid overwhelming users

### Key Features Being Enhanced

- **User authentication**: Extended with role-based access, hafiz profile switching, and admin impersonation
- **User analytics**: Comprehensive tracking of user behavior, feature adoption, and drop-off patterns
- **Memorization tracking**: Transformed from fixed modes to flexible pattern system
- **Revision scheduling**: Enhanced with future pulls, intelligent skips, and context awareness
- **Progress analytics**: Rich performance data with pattern effectiveness tracking
- **Family coordination**: Specialized tools for multi-hafiz household management with strengths/weaknesses dashboards for parents
- **Similar passage management**: Community-driven identification and practice of confusing verses

## Database Schema Summary

**Migration Strategy**: Transform existing 15 SQLite tables into PostgreSQL-based 3-layer architecture.

### Current SQLite Tables → Target PostgreSQL Architecture

**Layer 1: Algorithm Foundation**
- **algorithms**: 3 core memorization algorithms (new_memorization, sequential_maintenance, targeted_strengthening)
- **algorithm_parameters**: Configurable parameters for each algorithm

**Layer 2: User Configuration** 
- **revision_patterns**: User-defined behaviors combining algorithms with personal preferences (transforms current modes + booster_packs)
- **pattern_sharing**: Community pattern marketplace and family coordination

**Layer 3: Runtime State**
- **hafiz_item_assignments**: Enhanced hafizs_items with pattern context and rich analytics
- **day_plans**: Enhanced day planning with future pulls and intelligent skipping
- **day_plan_modifications**: Track when users modify auto-generated plans

**Enhanced Core Tables**:
- **users, hafizs, hafizs_users**: Enhanced with role-based permissions, family coordination, and admin impersonation
- **user_sessions**: Track login patterns, session duration, and activity for analytics
- **user_events**: Log feature usage, page views, and user actions for behavior analysis
- **mushafs, surahs, pages, items**: Direct migration with PostgreSQL improvements + personalized items
- **revisions**: Enhanced with pattern context, confidence levels, and device tracking
- **similar_passage_groups/items**: Community-driven similar verse management

**New Analytics Tables**:
- **user_analytics**: Aggregated metrics per user (login count, features used, progression stage)
- **feature_usage**: Track which features are being adopted vs ignored by new users
- **user_journey_events**: Track the path from signup → first login → first revision → regular usage
- **hafiz_performance_analytics**: Strengths/weaknesses analysis for parent and teacher dashboards

### Key Architectural Changes

**From Fixed Modes to Flexible Patterns**:
- Current: "0. Full cycle", "1. Daily Reps", "2. Weekly Reps", "4. SRS", "5. New Memorization"
- Target: Unlimited user-defined patterns like "Travel Focus", "Competition Prep", "Family Coordination"

**From Simple Tracking to Rich Analytics**:
- Current: Basic good/ok/bad ratings with simple statistics
- Target: Performance analytics, graduation tracking, pattern effectiveness measurement

**From Single-User to Multi-User Coordination**:
- Current: Basic user-hafiz relationships
- Target: Family networks, teacher-student-parent triangulation, permission management

**From Limited Visibility to Comprehensive Analytics**:
- Current: No insight into user behavior or drop-off patterns
- Target: Real-time analytics showing user engagement, feature adoption, and friction points

## Technical Decisions

### Architecture Choices
- **Database**: PostgreSQL (production-ready, better JSON support than SQLite, proper foreign keys)
- **Testing**: PhoenixTest (Playwright-style testing for LiveView, matches current Playwright test structure)  
- **Asset Management**: esbuild (no Node.js dependency, simpler than current FastHTML setup)
- **Styling**: Tailwind CSS (minimal configuration, matches current styling approach)
- **Authentication**: Phoenix generators extended for multi-hafiz support and role-based permissions

### Migration Philosophy

**"Migrate with confidence, enhance with intelligence."**

- **Preserve all existing functionality** while dramatically improving flexibility
- **Zero data loss**: Every piece of production data is preserved and enhanced
- **Intelligent defaults**: Create personalized patterns based on actual usage data from production
- **Community-driven**: Pattern sharing enables collective improvement of memorization methods

### Development Approach
- **Phoenix generators first**: Use mix phx.gen.auth, mix phx.gen.live, mix phx.gen.context extensively
- **Business-focused modules**: Organize contexts by memorization domain, not technical concerns
- **Test-driven migration**: Comprehensive PhoenixTest coverage matching current Playwright tests
- **Aggressive enhancement**: Don't just migrate features, improve them based on user feedback

## Step 1 Implementation Requirements

### Phoenix Project Creation
```bash
# Create project with PostgreSQL and LiveView support
mix phx.new quran_srs --database postgres --live
cd quran_srs
```

**Required Capabilities**:
- **Playwright-style LiveView testing**: For comprehensive UI testing that matches current test approach
- **Test data generation**: Factory patterns for complex memorization test scenarios
- **JSON handling**: For JSONB pattern configurations and analytics data
- **Timezone support**: For intelligent scheduling across different time zones
- **User analytics**: Telemetry system for tracking user behavior and engagement
- **Metrics collection**: Performance monitoring and user interaction tracking

### Database Configuration
- **PostgreSQL setup**: Configure for production-ready architecture
- **Migration foundation**: Prepare for 3-layer architecture schema
- **Connection settings**: Optimize for memorization data patterns
- **Index planning**: Prepare for performance optimization on revision queries

### Authentication Foundation
```bash
# Generate Phoenix authentication system
mix phx.gen.auth Accounts User users
```

**Authentication Extensions Required**:
- **Multi-hafiz relationships**: Support for one user managing multiple hafiz profiles
- **Role-based permissions**: Different access levels for parents, teachers, admins
- **Family coordination features**: Cross-user permissions for family members
- **Admin impersonation**: Ability to login as another user for testing without passwords
- **User analytics tracking**: Session monitoring and behavior pattern analysis

### Testing Infrastructure
- **PhoenixTest setup**: Configure for LiveView testing that matches current Playwright approach
- **Factory setup**: ExMachina factories for complex memorization data
- **Test database**: Separate test database with proper cleanup

### Asset Pipeline Configuration
- **Tailwind CSS**: Minimal setup matching current FastHTML styling approach
- **esbuild**: Modern asset building without Node.js complexity
- **Static assets**: Prepare for Quran text, audio files, and memorization aids

### Base Layout Structure
```elixir
# Navigation structure ready for:
# - User authentication
# - Hafiz profile switching (added in later steps)
# - Pattern management (added in later steps)  
# - Family dashboard (added in later steps)
# - Admin analytics dashboard (added in later steps)
```

### Analytics Infrastructure
- **Telemetry setup**: Configure Phoenix telemetry for user behavior tracking
- **Event logging**: Capture user actions, page views, and feature interactions
- **Session tracking**: Monitor login patterns, duration, and activity levels
- **Admin analytics views**: Dashboard showing user engagement and drop-off patterns

## Success Criteria

### Functional Requirements
- **Phoenix server runs without errors** on `mix phx.server`
- **User registration and login works** through generated auth system
- **PostgreSQL database creates successfully** with proper permissions
- **All tests pass** including PhoenixTest integration tests
- **Tailwind styling renders correctly** on all pages
- **Asset pipeline compiles** without errors
- **Telemetry system functional** and capturing basic user events

### Architecture Validation
- **Phoenix conventions followed** throughout codebase
- **Database foundation ready** for 3-layer architecture implementation
- **Testing infrastructure complete** for TDD approach to migration
- **No hardcoded business logic** in this foundation step
- **Clean separation** between authentication and memorization concerns

## Migration Readiness Checklist

- [ ] Phoenix project created with PostgreSQL and LiveView
- [ ] Authentication system functional (registration, login, logout)
- [ ] PhoenixTest configured and basic tests passing
- [ ] Tailwind CSS styling working correctly
- [ ] Database migrations run successfully
- [ ] All dependencies installed and configured
- [ ] Telemetry system configured for user analytics
- [ ] Foundation ready for 3-layer architecture implementation

## Next Steps Preview

Step 1 creates the foundation. Subsequent steps will:
- **Step 2**: Implement 3-layer architecture database schema
- **Step 3**: Extend authentication for multi-hafiz support  
- **Step 4**: Create core memorization contexts
- **Step 5+**: Build pattern system, day planning, and advanced features

The foundation must be solid because everything else builds on top of it.