## User Personas for Quran SRS System

### Short Summary of 5 key User Personas

1. Ahmed: Complete Hafiz - Software engineer who completed Quran memorization 3 years ago. His key challenge is maintaining his revision, especially during travel and improving his performance on the weak pages.
2. Fatima: Parent-Hafiz - mother of 3 young Hafiz - Zahran who memorises 1 page new per day, Abdur Rahman does 5 lines per day (Finished last 5 Juz and is now memorising from surah 32 saba onwards) and Maryam does 3 lines per day (finished Juz 30 and progressing through Juz 29, starting with surah mulk). In addition to her children, she is also doing Hifz.
3. Ustadh Abdullah: Professional Quran Teacher - professional Quran teacher managing 10 students, at different levels of Hifz. He needs to share the performance of his students with the parents and to assign some homework to them to be supervised by the parents
4. Zainab: Teen Hafiz - Part of Fatima family, but she has indepdendent access to her Hifz. In addition to her Hifz,she listens to the revisions of her younger siblings - hence she has access to update their revisions.
5. Basheer : Casual Memorizer - Working professional who has memorised Juz Amma but finding it hard to revise it properly, amidst demanding working schedule.

### 1. Ahmed: Complete Hafiz

- **Profile**: 35-year-old software engineer who completed Quran memorization 3 years ago
- **Challenges**:
  - Maintaining consistent revision with busy work schedule
  - Strengthening weak pages that are deteriorating
  - Adapting revision during frequent travel periods
  - Managing similar-sounding passages that cause confusion
- **Goals**:
  - Maintain his complete memorization without backsliding
  - Improve quality of recitation for weak portions
  - Establish sustainable revision habits that fit his lifestyle
  - Track progress to stay motivated

### 2. Fatima: Parent-Hafiz

- **Profile**: 42-year-old mother of 3 young Hafiz children with different memorization levels
  - Zahran: Advanced (1 page per day, sequential memorization)
  - Abdur Rahman: Intermediate (5 lines per day, working through middle surahs)
  - Maryam: Beginner (3 lines per day, completed Juz 30, working on Juz 29)
- **Challenges**:
  - Managing multiple memorization journeys simultaneously
  - Tracking progress across different children and herself
  - Creating appropriate assignments based on individual ability
  - Finding time for her own memorization while supporting children
- **Goals**:
  - Provide structured guidance for her children
  - Maintain overview of everyone's progress
  - Balance her own memorization journey
  - Create sustainable family memorization routine

### 3. Ustadh Abdullah: Professional Quran Teacher

- **Profile**: 38-year-old professional Quran teacher managing 10 students at different levels
- **Challenges**:
  - Efficiently tracking progress of multiple students
  - Creating personalized memorization plans
  - Communicating effectively with parents
  - Identifying struggling students before they fall behind
  - Maximizing limited class time
- **Goals**:
  - Provide targeted instruction based on data
  - Share meaningful progress reports with parents
  - Assign appropriate homework for parent supervision
  - Identify patterns across students to improve teaching methods
  - Prepare students for competitions and evaluations

### 4. Zainab: Teen Hafiz with Mentoring Role

- **Profile**: 16-year-old with her own memorization journey who also helps supervise younger siblings
- **Challenges**:
  - Balancing school responsibilities with memorization
  - Managing her own progress while helping siblings
  - Transitioning to more independent memorization
  - Maintaining motivation through teenage years
- **Goals**:
  - Take ownership of her memorization journey
  - Develop mentoring skills while helping siblings
  - Track her contributions to family memorization efforts
  - Prepare for advanced memorization competitions

### 5. Basheer: Casual Memorizer

- **Profile**: 40-year-old working professional who has memorized Juz Amma (Juz 30)
- **Challenges**:
  - Maintaining limited memorization amid demanding work schedule
  - Finding consistent revision time
  - Lack of structure leading to forgetting
  - Uncertainty about how to expand memorization efficiently
- **Goals**:
  - Establish minimal but effective revision routine
  - Strengthen existing memorization of short surahs
  - Gradually expand memorization when possible
  - Use memorization effectively in daily prayers

These personas represent the diverse user base for your Quran SRS system, each with unique needs that your application will address through its various features and flexibility.

## User Management

- A single user might have more than 1 hafiz under him/her. For example, Fatima has 3 hafiz accounts for her memorising children and one for herself.
- Zainab, the teenage daughter of Fatima, has independent access to her account with her own login - but she can access data of her sibling as well.
- Both parents might need access to a child's account
- To enable all these scenarios, users and hafizs tables are individual tables with the many-to-many relationship stored in an association table hafizs_users