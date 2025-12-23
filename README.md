# Quran SRS

A sophisticated Spaced Repetition System designed specifically for Quran memorization and revision. Built with FastHTML, it combines the wisdom of traditional madrasa methods with modern memory science.

## The Problem

> "I used Anki to learn classical Arabic and French in a surprisingly short time. Motivated by SRS, I tried implementing it for Quran... after about 6 months, the review queue had grown so big it totally demotivated me."
>
> — From [Product Vision](docs/product-vision.md)

Traditional SRS tools like Anki work brilliantly for vocabulary cards, but struggle with Quran memorization:

- **Reset Overwhelm**: One mistake on page 47? Back to day 1.
- **Lost Context**: Page 234 today, page 233 tomorrow - no sequential flow
- **Interval Explosion**: Pages reaching 90-100 day intervals when you want to review often
- **Memory Interference**: Similar passages interfere with each other unpredictably

## Our Solution

A three-layer architecture that unifies traditional madrasa wisdom with SRS science:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ALGORITHM LAYER                              │
│  Sequential Maintenance • New Memorization • Targeted Strengthening │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PATTERN LAYER                               │
│   Daily Reps • Weekly Reps • Full Cycle • SRS Intensive Care     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ASSIGNMENT LAYER                              │
│     Smart Day Planning • Graduation Workflows • Analytics        │
└─────────────────────────────────────────────────────────────────┘
```

### Five Memorization Modes

| Mode | Purpose | Interval |
|------|---------|----------|
| **New Memorization (NM)** | Learning new pages | Daily for 7 days |
| **Daily Reps (DR)** | Intensive foundation | 1-day fixed |
| **Weekly Reps (WR)** | Regular reinforcement | 7-day fixed |
| **Full Cycle (FC)** | Sequential maintenance | All memorized pages in order |
| **SRS Mode (SR)** | ICU for struggling pages | Adaptive (prime number intervals) |

> "The goal was never to replace the traditional methods of Quran memorization, but to enhance them with intelligence, flexibility, and community wisdom."
>
> — From [Design Vision](docs/design.md)

## Key Features

### Multi-User Architecture
One account can manage multiple hafiz profiles - perfect for families and teachers:

> "I have four different memorization journeys to track - my three children plus myself. How can I manage this without losing my mind?"
>
> — Fatima, from [User Personas](docs/user_personas.md)

### Intelligent Mode Progression
Pages naturally progress through modes based on performance:
- NM → DR (after first review, marked as memorized)
- DR → WR (after 7 reviews at 1-day intervals)
- WR → FC (after 7 reviews at 7-day intervals)
- FC → SR (when struggling, triggered by Ok/Bad ratings)
- SR → FC (when next_interval exceeds 99 days)

### SRS "Intensive Care Unit"
When pages become "sick" in Full Cycle, they get admitted to SRS mode with adaptive intervals based on prime numbers:

```
Interval progression: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37...
- Bad rating (-1): Move to previous prime
- Ok rating (0): Stay at current prime
- Good rating (1): Advance to next prime
```

> "Just like in medicine, healthy pages follow their regular routine, but when pages get 'sick', they need intensive care."
>
> — From [SRS Mode Design](docs/srs-mode-design.md)

### Virtual Date System
Each hafiz has their own `current_date`, enabling:
- Independent timelines for different profiles
- Testing and demo scenarios
- "Close Date" operation to process all daily reviews

## Tech Stack

- **Backend**: [FastHTML](https://www.fastht.ml/) (Python)
- **Database**: SQLite with fastmigrate
- **Frontend**: HTMX + Alpine.js + DaisyUI
- **UI Components**: MonsterUI

## Quick Start

```bash
# Clone the repository
git clone https://github.com/siraj-samsudeen/quran-srs.git
cd quran-srs

# Install dependencies
uv sync

# Run the application
uv run main.py

# Visit http://localhost:5001
```

## Running Tests

```bash
# All tests
uv run pytest -v

# By type (fast to slow)
uv run pytest tests/unit -v           # Pure Python logic
uv run pytest tests/integration -v    # TestClient HTTP tests
uv run pytest tests/e2e -v            # Playwright browser tests
```

See [Testing Approach](docs/testing-approach.md) for our test pyramid philosophy.

## Documentation

| Document | Purpose |
|----------|---------|
| [Product Vision](docs/product-vision.md) | Complete system philosophy, user personas, and benefits |
| [Design Vision](docs/design.md) | Interactive conversations showing system in action |
| [SRS Mode Design](docs/srs-mode-design.md) | Detailed SRS algorithm with examples |
| [User Personas](docs/user_personas.md) | 9 comprehensive personas from learners to administrators |
| [Testing Approach](docs/testing-approach.md) | Test pyramid and FastHTML testing patterns |
| [CLAUDE.md](CLAUDE.md) | Developer reference for codebase patterns |

## Who Is This For?

> "Each persona demonstrates different needs that the flexible pattern system addresses."
>
> — From [Product Vision](docs/product-vision.md)

- **Complete Huffaz** like Ahmed: Maintaining 604 pages with travel-friendly patterns
- **Family Managers** like Fatima: Coordinating multiple children's journeys
- **Teachers** like Ustadh Imran: Tracking student progress with parent reports
- **Adult Learners** like Khalid: Self-guided memorization with flexible scheduling
- **Institutions** like Shaykh Shameem's madrasa: School-wide analytics and oversight

## Benefits

### For Learners
- Adaptive scheduling that learns from your performance
- Smart balance between new memorization and revision
- Travel mode and irregular schedule handling

### For Families
- Single dashboard managing multiple journeys
- Early warning system for declining performance
- Shared celebration of milestones

### For Teachers
- Real-time visibility into home practice
- Automated progress reports for parents
- Performance-based student grouping

## Philosophy

> "Your mind isn't the same every day, and different parts of the Quran need different types of attention."
>
> — System greeting to Maryam, from [Design Vision](docs/design.md)

The system respects that:
1. **80% of pages that start strong, stay strong** - focus intensive work on the 20% that need it
2. **Memory interference is real** - similar passages affect each other unpredictably
3. **Sequential review has value** - there's joy in reciting pages in order
4. **Flexibility without chaos** - structured patterns that adapt to life

## Contributing

This is an active project. See [CLAUDE.md](CLAUDE.md) for development patterns and conventions.

## License

MIT
