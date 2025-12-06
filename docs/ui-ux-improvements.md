# UI/UX Improvement Roadmap

> **Purpose**: Prioritized list of UI/UX improvements for Quran SRS, organized by effort and impact to guide implementation after refactoring.
>
> **Created**: December 2024
>
> **Philosophy**: Start with low-hanging fruits (low effort, high impact), then progress to larger features.

---

## Quick Reference: Priority Matrix

```
                    HIGH IMPACT
                        │
        ┌───────────────┼───────────────┐
        │   QUICK WINS  │  BIG BETS     │
        │   Do First    │  Plan Well    │
        │   (Section A) │  (Section C)  │
LOW ────┼───────────────┼───────────────┼──── HIGH
EFFORT  │   MAYBE       │  LATER        │    EFFORT
        │   Low Priority│  When Ready   │
        │   (Section D) │  (Section B)  │
        └───────────────┼───────────────┘
                        │
                    LOW IMPACT
```

---

## Section A: Quick Wins (Low Effort, High Impact)

*Do these first - maximum value for minimum work*

| # | Feature | Impact | Effort | Description |
|---|---------|--------|--------|-------------|
| A1 | **Compact page numbers** | 🔥🔥🔥 | Low | Show just "45" instead of "45 - Al-Baqarah" in table rows. Surah name moves to section header. Halves row height on mobile. |
| A2 | **Truncate start text** | 🔥🔥🔥 | Low | CSS `text-overflow: ellipsis` to prevent long Arabic text from wrapping. Max 3-4 words visible. |
| A3 | **Hide start text for consecutive pages** | 🔥🔥🔥 | Low | If pages 45,46,47 are sequential, only show start text for 45. Others show "● ● ●" with tap-to-reveal. Forces active recall. |
| A4 | **Loading states for HTMX** | 🔥🔥 | Low | Add `.htmx-request { opacity: 0.7 }` CSS. Shows user their action registered. |
| A5 | **Muted colors for rated items** | 🔥🔥 | Low | Already-rated rows become visually quieter. Eye naturally goes to unrated items. |
| A6 | **Persist active tab in URL** | 🔥🔥 | Low | Use URL hash (`#FC`, `#SR`) so refresh doesn't reset to Full Cycle. Alpine.js `$watch` on activeTab. |
| A7 | **Better empty states** | 🔥🔥 | Low | When no items due: "All caught up! No pages due for review." with subtle checkmark icon. |
| A8 | **Sticky tab bar on mobile** | 🔥🔥 | Low | Keep mode tabs visible while scrolling: `sticky top-16 bg-base-100 z-40`. |
| A9 | **Touch-friendly checkboxes** | 🔥🔥 | Low | Wrap checkboxes in larger clickable Label with `p-3 cursor-pointer`. |
| A10 | **Color-blind friendly ratings** | 🔥 | Low | Add icons alongside colors: ✓ (green), − (yellow), ✗ (red). Not just color-dependent. |

---

## Section B: Medium Effort, High Impact

*Plan these carefully - significant value, requires more work*

| # | Feature | Impact | Effort | Description |
|---|---------|--------|--------|-------------|
| B1 | **Group items by Surah** | 🔥🔥🔥 | Medium | Collapsible surah headers: "📖 Al-Baqarah (pages 2-24)". Rows show only page number. Reduces repetition, adds context. |
| B2 | **Inline rating buttons (mobile)** | 🔥🔥🔥 | Medium | Replace dropdown with three tappable buttons: `[✓] [−] [✗]`. Much faster for tick-tick-tick workflow. |
| B3 | **Tap-to-reveal animation** | 🔥🔥 | Medium | When revealing hidden start text, use subtle blur→clear or slide animation. Makes "peeking" feel intentional. |
| B4 | **Section-level "Rate All" button** | 🔥🔥 | Medium | In surah header: `[✓ All Good]` button. Rate entire section in one tap for consecutive pages reviewed together. |
| B5 | **Show next interval before rating** | 🔥🔥🔥 | Medium | In SRS mode, show what each rating means: "Good → 11 days, Ok → 7 days, Bad → 5 days". Educational + encourages honest ratings. |
| B6 | **"Unrated only" filter toggle** | 🔥🔥 | Medium | Quick toggle: `[Show all] [Unrated only (3)]`. When 20 pages but only 3 left, see just those. |
| B7 | **Page statistics popup** | 🔥🔥 | Medium | Tap page number to see: total reviews, rating distribution, trend (improving/declining), days since memorized, current interval. |
| B8 | **Prominent system date display** | 🔥🔥 | Low-Med | Make current date a badge/pill instead of plain text. More visually prominent. |
| B9 | **Collapsible mobile navigation** | 🔥🔥 | Medium | Hamburger menu on mobile instead of 9 items in header. Drawer slides out. |
| B10 | **Show Juz number in headers** | 🔥🔥 | Low-Med | "📖 Al-Baqarah (Juz 1)" - Hafiz think in Juz, not just Surah/Page. |

---

## Section C: Higher Effort, High Impact (Big Bets)

*Major features - plan thoroughly before implementing*

| # | Feature | Impact | Effort | Description |
|---|---------|--------|--------|-------------|
| C1 | **Focus View mode** | 🔥🔥🔥 | High | Single-page review mode: shows Quran text, rating buttons at bottom, "Coming up" preview of next 2-3 pages. Toggle between Table/Focus view. |
| C2 | **Progressive hint system** | 🔥🔥🔥 | High | Contextual learning: hints appear when features first encountered, fade after 5-6 exposures, user can dismiss or reset. Teaches system as user goes. |
| C3 | **Close Date review screen** | 🔥🔥 | High | Before closing, show summary + decisions: pages about to graduate from SRS, struggling pages, option to keep/remove from SRS. User agency over algorithm. |
| C4 | **Smart SRS ordering** | 🔥🔥 | High | Prioritize by: overdue days, historical difficulty, time since last review. Show user why pages are in this order. Allow reordering preference. |
| C5 | **Visual strength indicator** | 🔥🔥 | Medium-High | Per-page strength bar: `████░` based on recent rating history. Helps user know which pages need attention. |
| C6 | **Swipe-to-rate gestures** | 🔥🔥 | High | Mobile: swipe right = Good, swipe left = Bad, tap = Ok. Natural gesture, very fast. |
| C7 | **Load management for heavy days** | 🔥🔥 | Medium-High | When 30+ pages due: "Review all" vs "Top 15 priority" vs "Split across 2 days". Prevents overwhelm. |
| C8 | **Header hafiz switcher dropdown** | 🔥🔥 | Medium | Quick hafiz switch from header dropdown instead of full page navigation. Faster for multi-hafiz accounts. |

---

## Section D: Lower Priority (Nice to Have)

*Implement when core UX is solid*

| # | Feature | Impact | Effort | Description |
|---|---------|--------|--------|-------------|
| D1 | **Custom confirmation modals** | 🔥 | Medium | Replace browser `confirm()` with styled modal. More context, better UX, but not core workflow. |
| D2 | **Toast notifications** | 🔥 | Medium | Success/error messages without page reload. HTMX response headers trigger toasts. |
| D3 | **Keyboard shortcuts** | 🔥 | Medium | `g/o/b` for Good/Ok/Bad, `j/k` for next/prev, `1-4` for tabs. Power user feature, most use mobile. |
| D4 | **Dark mode toggle** | 🔥 | Low | Essential for evening revision. DaisyUI supports it, just need toggle in settings. |
| D5 | **Micro-interactions** | 🔥 | Low-Med | Subtle animations: rating button scale on hover, checkbox check animation, tab fade transitions. Polish, not essential. |
| D6 | **Auto-advance after rating** | 🔥 | Low | In Focus View, auto-move to next page after rating. Optional setting. |
| D7 | **Pull-to-refresh** | 🔥 | Medium | Natural mobile pattern for reloading data. |
| D8 | **"What comes before/after" peek** | 🔥 | Medium | Long-press page to see surrounding context. Helps with page transitions. |
| D9 | **Natural break point markers** | 🔥 | Low | Show start-of-surah (🟢), end-of-surah, sajdah (🔻) indicators. Mental landmarks. |
| D10 | **Barakah counter** | 🔥 | Low | "Today: 12 pages. This week: 67 pages." Simple effort tracking, optional. |

---

## Section E: Future Considerations

*Ideas for later roadmap, not immediate priority*

| # | Feature | Impact | Effort | Description |
|---|---------|--------|--------|-------------|
| E1 | **Visual memorization map** | 🔥🔥 | High | Heatmap of all 604 pages showing memorization status and retention strength. |
| E2 | **Progress charts/analytics** | 🔥🔥 | High | Pages reviewed per day, rating distribution over time, streak tracking. |
| E3 | **Family dashboard** | 🔥🔥 | High | For parents/teachers: overview of all hafiz progress, cross-hafiz comparison. |
| E4 | **Gamification elements** | 🔥 | Medium | Streaks, achievements, milestones. Motivational but can be distracting. |
| E5 | **Offline support (PWA)** | 🔥🔥 | Very High | Service worker, IndexedDB for pending sync. Complex but valuable for travelers. |
| E6 | **Smart recommendations** | 🔥🔥 | High | "Pages 50-55 have low retention - add to SRS?" AI-assisted suggestions. |
| E7 | **Bottom navigation bar (mobile)** | 🔥 | Medium | Move primary actions to thumb-reachable bottom bar. Alternative to hamburger menu. |

---

## Implementation Notes

### Dependencies Between Features

```
A1 (Compact page numbers) ──┐
A3 (Hide consecutive text) ─┼──► B1 (Group by Surah) ──► C1 (Focus View)
A2 (Truncate text) ─────────┘

B5 (Show intervals) ──► C3 (Close Date review) ──► C4 (Smart ordering)

C2 (Hint system) is independent, can be built anytime
```

### Suggested Implementation Phases

**Phase 1: Density & Readability** (A1-A3, A5, A8)
- Compact page numbers
- Truncate start text
- Hide consecutive page hints
- Muted rated rows
- Sticky tabs

**Phase 2: Interaction Polish** (A4, A6, A7, A9, B2)
- Loading states
- Persist tab selection
- Empty states
- Touch targets
- Inline rating buttons

**Phase 3: Surah Grouping** (B1, B4, B10)
- Group by surah headers
- Section-level rate all
- Juz indicators

**Phase 4: SRS Transparency** (B5, B7, C3)
- Show next intervals
- Page statistics
- Close Date review

**Phase 5: Focus View** (C1, D6)
- Single-page review mode
- Auto-advance option

**Phase 6: Learning System** (C2)
- Progressive hints
- Milestone celebrations
- Struggle detection

---

## Design Principles to Follow

1. **Minimize scrolling** - Every pixel of vertical space matters on mobile
2. **Support tick-tick-tick** - Quick consecutive ratings without friction
3. **Active recall over recognition** - Hide hints, make user remember
4. **Explain as you go** - Teach the system through usage, not manuals
5. **Respect user agency** - Let them control, not just the algorithm
6. **One-handed mobile use** - Thumb-reachable, large tap targets
7. **Progressive disclosure** - Simple by default, power features discoverable

---

## Metrics to Track (Future)

Once implemented, measure:
- Time to complete daily review session
- Rating distribution (are people being honest?)
- SRS graduation rate
- Retention (pages staying in Full Cycle)
- Session frequency (daily habit)
- Feature discovery rate

---

## Notes from Discussion

### Key User Insights
- Users often review 3-4 pages in a row, want quick tick-tick-tick
- Surah name repetition wastes space, grouping provides context
- Hidden start text forces recall (memorization principle)
- Mobile is primary device, one-handed operation important
- System should teach itself to new users, then get out of the way
- Users want to understand intervals and have agency over SRS decisions

### Excluded Features
- Audio playback (explicitly excluded per user preference)

---

*Document created from UI/UX review session. Return to this after refactoring is complete.*
