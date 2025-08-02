# Quran SRS Phoenix Migration - Project Overview

## Project Goal

Migrate a FastHTML Quran memorization application to Phoenix LiveView with PostgreSQL, implementing a revolutionary 3-layer architecture that separates algorithms from user patterns from runtime assignments.

## Current System

- **FastHTML application** with SQLite database (15 tables)
- **Multi-user architecture**: One account can manage multiple hafiz profiles (family/teaching scenarios)
- **Fixed modes**: "Full cycle", "Daily Reps", "Weekly Reps", "SRS", "New Memorization"
- **Basic tracking**: Good/OK/Bad ratings with simple statistics
- **Single production user** (willing to experience migration inconveniences)

## Revolutionary 3-Layer Architecture Vision

**Current Problem**: Existing systems mix memorization algorithms with user preferences, making customization impossible.

**Our Solution**: 
1. **Algorithm Layer**: 3 core memorization algorithms (New Memorization, Sequential Maintenance, Targeted Strengthening)
2. **Pattern Layer**: User-configurable behaviors that combine algorithms with personal preferences 
3. **Assignment Layer**: Real-time state tracking for each hafiz-item combination

**Result**: Infinite customization while maintaining clean, maintainable code.

## Key User Personas

1. **Ahmed**: Complete hafiz & tech professional (travel challenges, performance analytics)
2. **Fatima**: Multi-hafiz family manager (managing 4 people, needs family dashboard)
3. **Ustadh Abdullah**: Professional teacher (classroom management, parent communication)
4. **Basheer**: Casual memorizer (maintaining Juz 30 + part of Juz 29)
5. **Dr. Amina**: Complete hafiz with shift work (irregular healthcare schedule)

## Enhanced Features Required

### Multi-User Coordination
- **Family coordination**: Parents manage children's memorization with strengths/weaknesses dashboards
- **Teacher-student-parent triangulation**: Shared access with appropriate permissions
- **Admin impersonation**: Login as any user for testing without passwords

### Advanced Day Planning
- **Future pulling**: Pull items from next 2-3 days when extra time available
- **Intelligent skipping**: Skip items with automatic rescheduling
- **Context awareness**: Adapt to travel, illness, busy periods

### Pattern System
- **Infinite customization**: Users create patterns like "Travel Focus", "Competition Prep"
- **Community marketplace**: Share successful patterns as templates
- **Family pattern libraries**: Parents create collections for their children

### User Analytics & Monitoring
- **Login patterns**: Track frequency, duration, consistency
- **Feature adoption**: Monitor which features are used vs ignored
- **Drop-off analysis**: Identify where users get stuck
- **Admin dashboard**: Real-time analytics for user engagement

### Similar Passage Management
- **Community-driven**: Identify commonly confused verses
- **Grouped practice**: Practice similar passages together
- **Pattern integration**: Specialized patterns for confusion resolution

## Technical Decisions

- **Database**: PostgreSQL (production-ready, better JSON support)
- **Testing**: PhoenixTest (Playwright-style LiveView testing)
- **Architecture**: Clean separation of concerns through 3-layer design
- **Migration**: Zero data loss, intelligent transformation of existing data

## Success Criteria

- **Zero data loss**: All existing functionality preserved and enhanced
- **Infinite flexibility**: Pattern system enables any memorization approach
- **Family coordination**: Multi-user households get seamless coordination tools
- **Performance improvement**: Faster and more responsive than current system
- **Community features**: Pattern sharing enables collective improvement

## Migration Philosophy

**"Migrate with confidence, enhance with intelligence."**

Don't just copy the existing system - transform it into the intelligent, flexible, community-driven platform that respects traditional memorization methods while embracing modern technology capabilities.

---

**Request**: Please create a detailed step-by-step migration plan that implements this vision using Phoenix LiveView best practices, with particular attention to the 3-layer architecture and comprehensive user analytics.